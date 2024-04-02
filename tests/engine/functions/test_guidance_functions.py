import pytest
from hub.engine.functions import relative_url_from_openapi, rest_api_operation_from_openapi, rest_api_parameters_from_openapi, dataapi_from_prompt
from hub.parsers.openapi import instantiate_openapi
from guidance.models import MockChat

sample_openapi = '''
{
  "openapi": "3.0.0",
  "info": {
    "version": "1.0.0",
    "title": "Swagger Petstore",
    "description": "A sample API that uses a petstore as an example to demonstrate features in the OpenAPI 3.0 specification",
    "termsOfService": "http://swagger.io/terms/",
    "contact": {
      "name": "Swagger API Team",
      "email": "apiteam@swagger.io",
      "url": "http://swagger.io"
    },
    "license": {
      "name": "Apache 2.0",
      "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    }
  },
  "servers": [
    {
      "url": "https://petstore.swagger.io/v2"
    }
  ],
  "paths": {
    "/pets": {
      "get": {
        "description": "Returns all pets from the system that the user has access to.",
        "operationId": "findPets"
      }
    },
    "/pets/{id}": {
      "get": {
        "description": "Returns a single pet",
        "operationId": "findPets"
      }
    }
  }
}
'''

@pytest.fixture
def openapi():
    return instantiate_openapi(sample_openapi)

@pytest.fixture
def mock_lm():
    return MockChat()

def test_relative_url_from_openapi(mock_lm, openapi):
    lm = mock_lm
    prompt = "Give me a relative URL."
    lm += relative_url_from_openapi(prompt=prompt, openapi=openapi)
    assert prompt in lm.__str__()
    assert all([e in lm.__str__() for e in openapi.paths.keys()])
    assert lm['endpoint']

def test_rest_api_operation_from_openapi_with_explicit_endpoint(mock_lm, openapi, endpoint="/pets/{id}"):
    lm = mock_lm
    prompt = "Give me a REST operation."
    lm += rest_api_operation_from_openapi(prompt=prompt, openapi=openapi, endpoint=endpoint)
    assert prompt in lm.__str__()
    assert endpoint in lm.__str__()
    assert lm['method']

def test_failed_rest_api_operation_from_openapi_without_explicit_endpoint(mock_lm, openapi):
    lm = mock_lm
    prompt = "Give me a REST operation."
    with pytest.raises(AssertionError):
        lm += rest_api_operation_from_openapi(prompt=prompt, openapi=openapi)

def test_rest_api_parameters_from_openapi_with_explicit_endpoint_and_method(mock_lm, openapi, endpoint="/pets/{id}", method="get"):
    lm = mock_lm
    prompt = "Give me the parameters for the REST API."
    lm += rest_api_parameters_from_openapi(prompt=prompt, openapi=openapi, endpoint=endpoint, method=method)
    assert prompt in lm.__str__()
    assert endpoint in lm.__str__()
    assert "Returns a single pet" in lm.__str__()
    assert lm['parameters']

def test_failed_rest_api_parameters_from_openapi_without_explicit_endpoint(mock_lm, openapi):
    lm = mock_lm
    prompt = "Give me the parameters for the REST API."
    with pytest.raises(AssertionError):
        lm += rest_api_parameters_from_openapi(prompt=prompt, openapi=openapi)

def test_failed_rest_api_parameters_from_openapi_without_explicit_method(mock_lm, openapi, endpoint="/pets/{id}"):
    lm = mock_lm
    prompt = "Give me the parameters for the REST API."
    with pytest.raises(AssertionError):
        lm += rest_api_parameters_from_openapi(prompt=prompt, openapi=openapi, endpoint=endpoint)

def test_dataapi_from_prompt(mock_lm, openapi):
    lm = mock_lm
    prompt = "Give me data from a cat with ID=123 from this API."
    lm += dataapi_from_prompt(prompt=prompt, openapi=openapi)
    assert prompt in lm.__str__()
    assert all([p in lm for p in ['endpoint', 'method', 'parameters']])
    