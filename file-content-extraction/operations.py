"""
Copyright start
MIT License
Copyright (c) 2025 Fortinet Inc
Copyright end
"""

from connectors.core.connector import get_logger, ConnectorError
from connectors.cyops_utilities.builtins import download_file_from_cyops, extract_artifacts, save_file_in_env, create_cyops_attachment
import os
import json
import requests
from ioc_finder import find_iocs
import pandas as pd

logger = get_logger('file-content-extraction')

# consts
TMP_PATH = '/tmp/'


def extract_text(config, params, *args, **kwargs):
    '''
    Extracts text from file and return it as utf8 or HTML formatted
    '''
    parser, tika_config = _set_env()
    try:
        if params.get('file_iri') and '/api/3/files/' not in params.get('file_iri'):
            file_path = os.path.join(TMP_PATH, params.get('file_iri'))
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
    result = {'segregated_data': [], 'data': {}}
    extracted_text = extract_text(config, params, *args, **kwargs)
    if extracted_text.get('extracted_text') is None:
        return result
    iocs = find_iocs(extracted_text.get('extracted_text', ''))
    for ioc_type, values in iocs.items():
        if values and ioc_type in ['md5s', 'urls', 'ipv4s', 'ipv6s', 'sha1s', 'sha256s', 'sha512s', 'domains', 'email_addresses', 'mac_addresses']:
            result['data'][ioc_type] = values
            result['segregated_data'].extend(
                {'ioc_type': ioc_type, 'value': value} for value in values
            )
    return result


def create_xslx_file_from_json_data(config, params, *args, **kwargs):
    """
    Converts JSON into a XLSX file and creates attachment in FortiSOAR attachment module
    :param str jsonData: The jsonData to be converted into XLSX:return: The attachment module record
    :rtype: dict
    """

    jsonData = params['jsonData']
    fileName = params['fileName']
    xLSXFields = params['xLSXFields']
    if not jsonData and fileName:
        raise ConnectorError("%s" % "CS-CONNECTOR-UTILITY-1: Invalid input :: {0} cannot be blank or null".format('jsonData'))
    df = pd.json_normalize(jsonData)
    if not fileName.endswith(('.xlsx', '.xslx')):
        fileName += '.xlsx'
    if xLSXFields:
        df = df[[item.strip() for item in xLSXFields.split(",")]]
    filePath = TMP_PATH + fileName
    df.to_excel(filePath, index=False)
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


def _set_env():
    try:
        from tika import parser
        from tika import config as tika_config
        return parser, tika_config
    except Exception as exp:
        logger.error('Error initiating local engine: {}'.format(exp))
        raise ConnectorError('Error initiating local engine {}'.format(exp))


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
