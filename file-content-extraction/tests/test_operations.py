# Edit the config_and_params.json file and add the necessary parameter values.
# Ensure that the provided input_params yield the correct output schema.
# Add logic for validating conditional_output_schema or if schema is other than dict.
# Add any specific assertions in each test case, based on the expected response.

"""
Copyright start
MIT License
Copyright (c) 2024 Fortinet Inc
Copyright end
"""

import pytest
from testframework.conftest import valid_configuration, invalid_configuration, valid_configuration_with_token,\
    connector_id, connector_details, info_json, params_json
from testframework.helpers.test_helpers import run_health_check_success, run_invalid_config_test, run_success_test,\
    run_output_schema_validation, run_invalid_param_test, set_report_metadata
    

@pytest.mark.check_health
def test_check_health_success(valid_configuration, connector_details):
    set_report_metadata(connector_details, "Health Check", "Verify with valid Configuration")
    result = run_health_check_success(valid_configuration, connector_details)
    assert result.get('status') == 'Available'
    

@pytest.mark.extract_text
def test_extract_text_success(cache, valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Text", "Verify with valid Input Parameters")
    for result in run_success_test(cache, connector_details, operation_name='extract_text',
                                   action_params=params_json['extract_text']):
        assert result.get('status') == "Success"


@pytest.mark.extract_text
def test_validate_extract_text_output_schema(cache, valid_configuration_with_token, connector_details,
                                                 info_json, params_json):
    set_report_metadata(connector_details, "Extract Text", "Validate Output Schema")
    run_output_schema_validation(cache, 'extract_text', info_json, params_json['extract_text'])
    

@pytest.mark.extract_text
def test_extract_text_invalid_file_iri(valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Text", "Verify with invalid File IRI/Path")
    result = run_invalid_param_test(connector_details, operation_name='extract_text', param_name='file_iri',
                                    param_type='text', action_params=params_json['extract_text'])
    assert result.get('status') == "failed"
    

@pytest.mark.extract_indicators
def test_extract_indicators_success(cache, valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Artifacts", "Verify with valid Input Parameters")
    for result in run_success_test(cache, connector_details, operation_name='extract_indicators',
                                   action_params=params_json['extract_indicators']):
        assert result.get('status') == "Success"


@pytest.mark.extract_indicators
def test_validate_extract_indicators_output_schema(cache, valid_configuration_with_token, connector_details,
                                                 info_json, params_json):
    set_report_metadata(connector_details, "Extract Artifacts", "Validate Output Schema")
    run_output_schema_validation(cache, 'extract_indicators', info_json, params_json['extract_indicators'])
    

@pytest.mark.extract_indicators
def test_extract_indicators_invalid_file_iri(valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Artifacts", "Verify with invalid File IRI/Path")
    result = run_invalid_param_test(connector_details, operation_name='extract_indicators', param_name='file_iri',
                                    param_type='text', action_params=params_json['extract_indicators'])
    assert result.get('status') == "failed"
    

@pytest.mark.extract_indicators_from_file
def test_extract_indicators_from_file_success(cache, valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Artifacts From File", "Verify with valid Input Parameters")
    for result in run_success_test(cache, connector_details, operation_name='extract_indicators_from_file',
                                   action_params=params_json['extract_indicators_from_file']):
        assert result.get('status') == "Success"


@pytest.mark.extract_indicators_from_file
def test_validate_extract_indicators_from_file_output_schema(cache, valid_configuration_with_token, connector_details,
                                                 info_json, params_json):
    set_report_metadata(connector_details, "Extract Artifacts From File", "Validate Output Schema")
    run_output_schema_validation(cache, 'extract_indicators_from_file', info_json, params_json['extract_indicators_from_file'])
    

@pytest.mark.extract_indicators_from_file
def test_extract_indicators_from_file_invalid_file_iri(valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Extract Artifacts From File", "Verify with invalid File IRI/Path")
    result = run_invalid_param_test(connector_details, operation_name='extract_indicators_from_file', param_name='file_iri',
                                    param_type='text', action_params=params_json['extract_indicators_from_file'])
    assert result.get('status') == "failed"
    

@pytest.mark.get_backend_config
def test_get_backend_config_success(cache, valid_configuration_with_token, connector_details, params_json):
    set_report_metadata(connector_details, "Get Backend Config", "Verify with valid Input Parameters")
    for result in run_success_test(cache, connector_details, operation_name='get_backend_config',
                                   action_params=params_json['get_backend_config']):
        assert result.get('status') == "Success"


@pytest.mark.get_backend_config
def test_validate_get_backend_config_output_schema(cache, valid_configuration_with_token, connector_details,
                                                 info_json, params_json):
    set_report_metadata(connector_details, "Get Backend Config", "Validate Output Schema")
    run_output_schema_validation(cache, 'get_backend_config', info_json, params_json['get_backend_config'])
    
