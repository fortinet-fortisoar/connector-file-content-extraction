from connectors.core.connector import get_logger, ConnectorError
from connectors.cyops_utilities.builtins import download_file_from_cyops, extract_artifacts, calculate_hashes
import os
import logging
import json
import shutil

logger = get_logger('file-content-extraction')
#logger.setLevel(logging.WARNING) #Disable for prod

# Const/imports
TMP_PATH = '/tmp/'
TIKA_LOG_PATH = '/var/log/cyops/cyops-integrations/file-content-extraction'
os.environ['TIKA_LOG_PATH'] = TIKA_LOG_PATH
if not os.path.exists(TIKA_LOG_PATH):
    os.makedirs(TIKA_LOG_PATH)
from tika import tika as ttika
ttika.TikaJarPath = r'/opt/cyops-integrations/integrations/workspace/file-content-extraction'
from tika import parser
from tika import config as tika_config


def extract_text(config, params):
    '''Extracts text from file and return it as utf8 or HTML formatted'''
    try:
        _check_health(config)
        file_iri = params.get("file_iri")
        dw_file_md = download_file_from_cyops(file_iri)
        file_path = TMP_PATH + dw_file_md['cyops_file_path']
        html_output_format = params.get("html_output_format")
        if html_output_format is None:
            html_output_format = False            
        parsed_file = parser.from_file(file_path, xmlContent=html_output_format)

        return {"metadata":parsed_file["metadata"],"extracted_text":parsed_file["content"]}

    except Exception as exp:
        logger.error('Error Parsing the File: {}'.format(exp))
        raise ConnectorError('Error Parsing the File: {}'.format(exp))
    finally:
        os.remove(file_path)    #Cleaning up

def extract_indicators(config, params):
    '''Extracts artifacts from extracted text'''
    _check_health(config)
    extracted_text = extract_text(config, params)
    return extract_artifacts(extracted_text)


def get_backend_config(config, params):
    '''Get Tika Server Attr'''
    try:
        _check_health(config)
        verbose_config = params.get("verbose_config")
        parsers = json.loads(tika_config.getParsers())
        mime_types = json.loads(tika_config.getMimeTypes())
        detectors = json.loads(tika_config.getDetectors())
        if verbose_config:
            return {'Parsers':parsers,'MimeTypes':mime_types,'Detectors':detectors}
        else:
            return {'MimeTypes':mime_types}
    except Exception as exp:
        logger.error('Error Reading Engine Config: {}'.format(exp))
        raise ConnectorError('Error Reading Engine Config: {}'.format(exp))

def _check_health(config):
    '''Computes tika's jar md5 hashcode'''

    cyops_tika_jar = '/opt/cyops-search/bin/tika-server.jar'
    connector_workspace = '/opt/cyops-integrations/integrations/workspace/file-content-extraction'
    tika_jar = '/opt/cyops-integrations/integrations/workspace/file-content-extraction/tika-server.jar'
    tika_md5_file = '/opt/cyops-integrations/integrations/workspace/file-content-extraction/tika-server.jar.md5'
    try:
        if not os.path.exists(connector_workspace):
            os.makedirs(connector_workspace)

        if not os.path.exists(tika_jar):
            shutil.copy(cyops_tika_jar, tika_jar)

        if not os.path.exists(tika_md5_file):
            tika_md5 = calculate_hashes(tika_jar)['md5']
            with open(tika_md5_file, 'w') as f:
                f.write(tika_md5)
        logger.debug("Offline Mode with logging dir at: {}".format(os.environ['TIKA_LOG_PATH']))
        return True

    except Exception as exp:
        logger.error('Error initiating local engine: {}'.format(exp))
        raise ConnectorError('Error initiating local engine {}'.format(exp))     

operations = {
    'extract_text': extract_text,
    'extract_indicators': extract_indicators,
    'get_backend_config': get_backend_config
}