from connectors.core.connector import get_logger, ConnectorError
from connectors.cyops_utilities.builtins import download_file_from_cyops
from connectors.cyops_utilities.builtins import extract_artifacts

import os
import logging
import tika
import json
import tika.tika
from tika import parser
from tika import language
from tika import translate
from tika import config as tika_config

logger = get_logger('text_extractor')
#logger.setLevel(logging.DEBUG)

#const
TMP_PATH = '/tmp/'
CONNECTOR_DIR = os.path.dirname(os.path.realpath(__file__))
TIKA_SERVER_PATH = "/opt/cyops-search/bin/tika-server.jar"
LANGUAGE_KEYS = CONNECTOR_DIR + '/language-keys'


def _set_env(config):
    ''' Set TIKA_SERVER_JAR env for online or offline modes '''
    try:
        os.environ['TIKA_TRANSLATOR'] = 'org.apache.tika.language.translate.GoogleTranslator'
        if config.get('offline_mode') == True:
            os.environ['TIKA_SERVER_JAR'] = TIKA_SERVER_PATH
            logger.debug("Offline Mode, using local Tika file: {}".format(os.environ['TIKA_SERVER_JAR']))
        else:
            if os.environ.get('TIKA_SERVER_JAR') is not None:
                del os.environ['TIKA_SERVER_JAR']
            #TODO: implement language related actions
            tika.tika.TikaServerClasspath = LANGUAGE_KEYS
            logger.debug("Online Mode with language keys @: {}".format(LANGUAGE_KEYS))
    except Exception as exp:
        logger.error('Error Setting the Env: {}'.format(exp))
        raise ConnectorError('Error Setting the Env: {}'.format(exp))


def extract_text(config, params):
    '''Extracts text from file and return it as utf8 or HTML formatted'''
    _set_env(config)
    try:
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
    extracted_text = extract_text(config, params)
    return extract_artifacts(extracted_text)


def get_backend_config(config, params):
    '''Get Tika Server Attr'''
    _set_env(config)
    try:
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
    _set_env(config)

operations = {
    'extract_text': extract_text,
    'extract_indicators': extract_indicators,
    'get_backend_config': get_backend_config
}