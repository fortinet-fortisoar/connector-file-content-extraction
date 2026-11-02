"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

from connectors.core.connector import get_logger, ConnectorError
from connectors.cyops_utilities.builtins import download_file_from_cyops, extract_artifacts, save_file_in_env, \
    create_cyops_attachment
from django.conf import settings
import os
import json
import hashlib
import shutil
import requests
from ioc_finder import find_iocs
import pandas as pd

logger = get_logger('file-content-extraction')

# consts
TMP_PATH = '/tmp/'


def check_file_traversal(file_path):
    working_directory = os.path.abspath(TMP_PATH)
    requested_path = os.path.relpath(file_path, start=working_directory)
    requested_path = os.path.normpath(os.path.join(working_directory, requested_path))
    common_prefix = os.path.commonpath([requested_path, working_directory])
    if common_prefix != working_directory:
        error_msg = f"This filepath is not accessible: {file_path}"
        logger.error(error_msg)
        raise ConnectorError(error_msg)


def extract_text(config, params, *args, **kwargs):
    '''
    Extracts text from file and return it as utf8 or HTML formatted
    '''
    parser, tika_config = _set_env()
    try:
        if params.get('file_iri') and not params['file_iri'].startswith('/api/3/files/'):
            file_path = os.path.join(TMP_PATH, params.get('file_iri'))
            check_file_traversal(file_path)
        else:
            file_iri = params.get('file_iri')
            dw_file_md = download_file_from_cyops(file_iri)
            file_path = TMP_PATH + dw_file_md['cyops_file_path']
        html_output_format = params.get('html_output_format')
        if html_output_format is None:
            html_output_format = False
        parsed_file = parser.from_file(file_path, xmlContent=html_output_format)
        if os.path.exists(file_path):
            save_file_in_env(kwargs.get('env', {}), file_path)
        return {'metadata': parsed_file['metadata'], 'extracted_text': parsed_file['content']}

    except requests.exceptions.HTTPError as e:
        logger.error('Error: File with IRI:<< {} >> does not exist'.format(file_iri))
        raise ConnectorError('Error: File with IRI:<< {} >> does not exist'.format(file_iri))
    except Exception as exp:
        logger.error('Error Parsing the File: {}'.format(exp))
        raise ConnectorError('Error Parsing the File: {}'.format(exp))


def extract_indicators(config, params, *args, **kwargs):
    '''Extracts artifacts from extracted text'''
    extracted_text = extract_text(config, params, *args, **kwargs)
    return extract_artifacts(extracted_text)


def extract_indicators_from_file(config, params, *args, **kwargs):
    '''Extracts artifacts from extracted text'''
    extracted_text = extract_text(config, params, *args, **kwargs)
    if extracted_text.get('extracted_text') is None:
        return {}
    iocs = find_iocs(extracted_text.get('extracted_text', ''))
    return {k: v for k, v in iocs.items() if
            v != [] and k not in ['attack_mitigations', 'attack_tactics', 'attack_techniques']}


def create_xslx_file_from_json_data(config, params, *args, **kwargs):
    """
    Converts JSON into a XLSX file and creates attachment in FortiSOAR attachment module
    :param str jsonData: The jsonData to be converted into XLSX:return: The attachment module record
    :rtype: dict
    """

    jsonData = params['jsonData']
    fileName = params['fileName']
    xLSXFields = params.get('xLSXFields')
    if not jsonData and fileName:
        raise ConnectorError(
            "%s" % "CS-CONNECTOR-UTILITY-1: Invalid input :: {0} cannot be blank or null".format('jsonData'))
    df = pd.json_normalize(jsonData)
    if not fileName.endswith(('.xlsx', '.xslx')):
        fileName += '.xlsx'
    if xLSXFields:
        df = df[[item.strip() for item in xLSXFields.split(",")]]
    filePath = os.path.join(TMP_PATH, fileName)
    check_file_traversal(filePath)
    # Write cell values as plain strings: disable XlsxWriter's automatic
    # conversion of '='-prefixed strings into executable formulas (CSV/Excel
    # formula injection) and of URL-like strings into live hyperlinks
    df.to_excel(filePath, index=False, engine_kwargs={
        'options': {'strings_to_formulas': False, 'strings_to_urls': False}})
    return create_cyops_attachment(fileName, name=fileName, description='')


def get_backend_config(config, params, *args, **kwargs):
    '''Get Tika Server Attr'''
    parser, tika_config = _set_env()
    try:
        verbose_config = params.get('verbose_config')
        parsers = json.loads(tika_config.getParsers())
        mime_types = json.loads(tika_config.getMimeTypes())
        detectors = json.loads(tika_config.getDetectors())
        if verbose_config:
            return {'Parsers': parsers, 'MimeTypes': mime_types, 'Detectors': detectors}
        else:
            return {'MimeTypes': mime_types}
    except Exception as exp:
        logger.error('Error Reading Engine Config: {}'.format(exp))
        raise ConnectorError('Error Reading Engine Config: {}'.format(exp))


def _md5sum(file_path):
    m = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            m.update(chunk)
    return m.hexdigest()


def _set_env():
    try:
        jar_dir = "/opt/cyops/configs/integrations/external_dependencies"
        os.makedirs(jar_dir, exist_ok=True)

        jar_name = "tika-server-standard-2.9.4.jar"
        # Official Apache Tika 2.9.4 digest (matches Maven Central canonical checksum)
        expected_md5 = "4eec8adf9c7d2a486b2e66f86a36d0f9"
        # Versioned copy as downloaded/verified, and the fixed runtime name
        # python-tika always executes ({TIKA_PATH}/tika-server.jar)
        staged_jar_path = os.path.join(jar_dir, jar_name)
        runtime_jar_path = os.path.join(jar_dir, "tika-server.jar")

        jar_url = f"https://repo.fortisoar.fortinet.com/connectors/deps/tika/{jar_name}"

        # Respect a pre-configured environment variable (e.g. air-gapped deployments
        # where the JAR was placed manually); python-tika reads TIKA_SERVER_JAR and
        # TIKA_PATH at import time, so both must be set before the library is
        # imported below.
        if "TIKA_SERVER_JAR" in os.environ:
            logger.info("Using TIKA_SERVER_JAR from environment.")

        else:
            # Download the JAR with TLS certificate verification enabled
            if not os.path.isfile(staged_jar_path):
                logger.info("Downloading Tika server JAR...")
                response = requests.get(jar_url, stream=True, verify=True, timeout=30)
                response.raise_for_status()

                with open(staged_jar_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # Verify integrity of the downloaded (or pre-placed) JAR before it
            # is ever executed
            if _md5sum(staged_jar_path) != expected_md5:
                raise ConnectorError(
                    "Tika server JAR integrity check failed. "
                    f"The file at '{staged_jar_path}' does not match the expected "
                    f"checksum for '{jar_name}'. Delete it and retry to re-download."
                )

            # Stage the verified JAR under the fixed name python-tika executes,
            # and write the .md5 sidecar (bare hex digest, no newline) that its
            # own checkJarSig() compares against
            shutil.copyfile(staged_jar_path, runtime_jar_path)
            with open(runtime_jar_path + ".md5", "w") as f:
                f.write(expected_md5)

            # Point python-tika at the local, verified JAR. This must happen
            # before `import tika` below: the library binds TIKA_SERVER_JAR at
            # import time and otherwise falls back to downloading over plain
            # HTTP from Maven Central. Run the JAR from the connector's own
            # directory rather than the shared, world-writable /tmp.
            os.environ["TIKA_SERVER_JAR"] = runtime_jar_path
            os.environ["TIKA_PATH"] = jar_dir

        from tika import parser
        from tika import config as tika_config

        return parser, tika_config

    except requests.RequestException as e:
        raise ConnectorError(
            "Unable to download Tika server files. "
            "For air-gapped deployments, place "
            f"'{jar_name}' under '{jar_dir}' "
            "or configure TIKA_SERVER_JAR. "
            f"Error: {e}"
        )


def _check_health(config):
    '''Computes tika's jar md5 hashcode'''
    _set_env()


operations = {
    'extract_text': extract_text,
    'extract_indicators': extract_indicators,
    'get_backend_config': get_backend_config,
    'extract_indicators_from_file': extract_indicators_from_file,
    'create_xslx_file_from_json_data': create_xslx_file_from_json_data
}
