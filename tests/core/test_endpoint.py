import pytest
from anydata import Endpoint

@pytest.fixture
def valid_endpoint():
    return Endpoint(
        base_url='https://datausa.io/api/',
        endpoint='/data',
        method='GET',
    )

@pytest.fixture
def invalid_endpoint():
    return Endpoint(
        base_url='https://pokeapi.co/api/v2/',
        endpoint='/pokemon/non-existent-pokemon',
        method='GET'
    )

@pytest.fixture
def endpoint_with_path_params():
    return Endpoint(
        base_url='https://datausa.io/api/',
        endpoint='/data/{year}/{state}',
        method='GET',
        params={'year': 2019, 'other_param': 'value'}
    )

@pytest.fixture
def endpoint_with_path_params_and_no_param_values():
    return Endpoint(
        base_url='https://datausa.io/api/',
        endpoint='/data/{year}/{state}',
        method='GET'
    )

def test_set_path_params(endpoint_with_path_params):
    '''
    Tests the _set_path_params method from the Endpoint class called by the __init__ method.
    '''
    # Asserts all path parameters names and values were captured
    assert list(endpoint_with_path_params.path_params.keys()) == ['year', 'state']
    assert list(endpoint_with_path_params.path_params.values()) == [2019, None]
    # Asserts that only path parameters were removed from the params dictionary
    assert endpoint_with_path_params.params == {'other_param': 'value'}

def test_set_path_params_no_param_values(endpoint_with_path_params_and_no_param_values):
    '''
    Tests the _set_path_params method from the Endpoint class called by the __init__ method.
    '''
    # endpoint_with_path_params_and_no_param_values._set_path_params()
    assert list(endpoint_with_path_params_and_no_param_values.path_params.keys()) == ['year', 'state']
    assert list(endpoint_with_path_params_and_no_param_values.path_params.values()) == [None, None]

def test_set_path_params_no_params(valid_endpoint):
    '''
    Tests the _set_path_params method from the Endpoint class called by the __init__ method.
    '''
    # valid_endpoint._set_path_params()
    assert valid_endpoint.path_params == {}

def test_set_params(valid_endpoint):
    valid_endpoint.set_params({'param1': 'value1', 'param2': 'value2'})
    assert valid_endpoint.params == {'param1': 'value1', 'param2': 'value2'}
    
def test_set_body(valid_endpoint):
    valid_endpoint.set_body({'key1': 'value1', 'key2': 'value2'})
    assert valid_endpoint.body == {'key1': 'value1', 'key2': 'value2'}

def test_merge_params(valid_endpoint):
    valid_endpoint.set_params({'param1': 'value1', 'param2': 'value2'})
    valid_endpoint.merge_params({'param2': 'value4', 'param3': 'value3'})
    assert valid_endpoint.params == {'param1': 'value1', 'param2': 'value4', 'param3': 'value3'}

def test_merge_headers(valid_endpoint):
    valid_endpoint.merge_headers({'header1': 'value1', 'Connection': 'close', 'Accept': 'application/json'})
    assert valid_endpoint.headers['header1'] == 'value1'
    assert valid_endpoint.headers['Connection'] == 'close'
    assert valid_endpoint.headers['Accept'] == 'application/json'
    assert all([header in valid_endpoint.headers for header in ['User-Agent', 'Accept-Encoding']])

def test_endpoint_default_headers(valid_endpoint):
    default_header_params = [
        'User-Agent',
        'Accept-Encoding',
        'Accept',
        'Connection'
    ]
    assert all([header in valid_endpoint.headers for header in default_header_params])

def test_successful_request(valid_endpoint):
    response = valid_endpoint.request()
    assert response.status_code == 200

def test_failed_request(invalid_endpoint):
    # https://pokeapi.co/api/v2/pokemon/non-existent-pokemon will return a 404 with a "Not Found" message.
    with pytest.raises(ValueError):
        invalid_endpoint.request()