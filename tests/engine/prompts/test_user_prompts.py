import pytest
from hub.engine.prompts.user_prompts import relative_url_user_prompt, rest_api_operation_user_prompt, rest_api_parameters_user_prompt

@pytest.fixture
def sample_prompt():
    return "Retrieve something from this API."

@pytest.fixture
def sample_endpoint():
    return '/pets'

@pytest.fixture
def sample_openapi():
    return '''
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
    }
  }
}
'''

def test_relative_url_user_prompt(sample_prompt, sample_openapi):
    processed_prompt = relative_url_user_prompt(prompt=sample_prompt, openapi=sample_openapi, endpoints=['/pets'])
    assert sample_prompt in processed_prompt
    assert sample_openapi in processed_prompt

def test_rest_api_operation_user_prompt(sample_prompt, sample_endpoint, sample_openapi):
    processed_prompt = rest_api_operation_user_prompt(prompt=sample_prompt, endpoint=sample_endpoint, openapi=sample_openapi)
    assert sample_prompt in processed_prompt
    assert sample_endpoint in processed_prompt
    assert sample_openapi in processed_prompt

def test_rest_api_parameters_user_prompt(sample_prompt, sample_endpoint, sample_openapi):
    processed_prompt = rest_api_parameters_user_prompt(prompt=sample_prompt, endpoint=sample_endpoint, openapi=sample_openapi)
    assert sample_prompt in processed_prompt
    assert sample_endpoint in processed_prompt
    assert sample_openapi in processed_prompt