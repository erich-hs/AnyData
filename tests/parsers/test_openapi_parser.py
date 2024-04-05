import json
import os
import pytest
from anydata.parsers.openapi import (
    OpenAPI,
    openapi_dict_from_json_file,
    instantiate_openapi,
)


@pytest.fixture
def sample_swagger() -> str:
    return """
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
        "operationId": "findPets",
        "parameters": [
          {
            "name": "tags",
            "in": "query",
            "description": "tags to filter by",
            "required": false,
            "style": "form",
            "schema": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          {
            "name": "limit",
            "in": "query",
            "description": "maximum number of results to return",
            "required": false,
            "schema": {
              "type": "integer",
              "format": "int32"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "pet response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/Pet"
                  }
                }
              }
            }
          },
          "default": {
            "description": "unexpected error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Error"
                }
              }
            }
          }
        }
      },
      "post": {
        "description": "Creates a new pet in the store. Duplicates are allowed",
        "operationId": "addPet",
        "requestBody": {
          "description": "Pet to add to the store",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/NewPet"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "pet response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Pet"
                }
              }
            }
          },
          "default": {
            "description": "unexpected error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Error"
                }
              }
            }
          }
        }
      }
    },
    "/pets/{id}": {
      "get": {
        "description": "Returns a user based on a single ID, if the user does not have access to the pet",
        "operationId": "find pet by id",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "description": "ID of pet to fetch",
            "required": true,
            "schema": {
              "type": "integer",
              "format": "int64"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "pet response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Pet"
                }
              }
            }
          },
          "default": {
            "description": "unexpected error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Error"
                }
              }
            }
          }
        }
      },
      "delete": {
        "description": "deletes a single pet based on the ID supplied",
        "operationId": "deletePet",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "description": "ID of pet to delete",
            "required": true,
            "schema": {
              "type": "integer",
              "format": "int64"
            }
          }
        ],
        "responses": {
          "204": {
            "description": "pet deleted"
          },
          "default": {
            "description": "unexpected error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Error"
                }
              }
            }
          },
          "404": {
            "description": "mock failed response"
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Pet": {
        "allOf": [
          {
            "$ref": "#/components/schemas/NewPet"
          },
          {
            "type": "object",
            "required": [
              "id"
            ],
            "properties": {
              "id": {
                "type": "integer",
                "format": "int64"
              }
            }
          }
        ]
      },
      "NewPet": {
        "type": "object",
        "required": [
          "name"
        ],
        "properties": {
          "name": {
            "type": "string"
          },
          "tag": {
            "type": "string"
          }
        }
      },
      "Error": {
        "type": "object",
        "required": [
          "code",
          "message"
        ],
        "properties": {
          "code": {
            "type": "integer",
            "format": "int32"
          },
          "message": {
            "type": "string"
          }
        }
      }
    }
  }
}
"""


@pytest.fixture
def openapi(sample_swagger: str) -> OpenAPI:
    return OpenAPI.from_json(sample_swagger)


def test_openapi_from_dict_without_info(sample_swagger: str):
    openapi_dict = json.loads(sample_swagger)
    del openapi_dict["info"]
    openapi = OpenAPI(openapi_dict)
    assert openapi.info is not None


def test_openapi_dict_from_json_file(tmpdir, sample_swagger: str):
    swagger = tmpdir.mkdir("tmp").join("swagger.json")
    with open(swagger, "w") as f:
        f.write(sample_swagger)
    assert openapi_dict_from_json_file(os.path.abspath(swagger)) == json.loads(
        sample_swagger
    )


def test_instantiate_openapi_from_str(sample_swagger: str):
    assert isinstance(instantiate_openapi(sample_swagger), OpenAPI)


def test_instantiate_openapi_from_file(tmpdir, sample_swagger: str):
    swagger = tmpdir.mkdir("tmp").join("swagger.json")
    with open(swagger, "w") as f:
        f.write(sample_swagger)
    assert isinstance(instantiate_openapi(os.path.abspath(swagger)), OpenAPI)


def test_instantiate_openapi_from_dict(sample_swagger: str):
    assert isinstance(instantiate_openapi(json.loads(sample_swagger)), OpenAPI)


def test_failed_instantiate_openapi_from_str():
    with pytest.raises(ValueError):
        instantiate_openapi("{invalid_json}")


def test_openapi_to_dict(openapi: OpenAPI):
    dict_openapi = openapi.to_dict()
    assert isinstance(dict_openapi, dict)
    assert all([key in dict_openapi for key in ["info", "servers", "paths"]])
    assert all(
        [
            key in dict_openapi["info"]
            for key in [
                "version",
                "title",
                "description",
                "termsOfService",
                "contact",
                "license",
            ]
        ]
    )
    assert dict_openapi["servers"][0] == {"url": "https://petstore.swagger.io/v2"}
    assert all([key in dict_openapi["paths"] for key in ["/pets", "/pets/{id}"]])
    assert all([key in dict_openapi["paths"]["/pets"] for key in ["get", "post"]])
    assert all(
        [
            key in dict_openapi["paths"]["/pets"]["get"]
            for key in [
                "tags",
                "summary",
                "description",
                "externalDocs",
                "operationId",
                "parameters",
                "requestBody",
                "responses",
                "deprecated",
            ]
        ]
    )


def test_info_summary_default_excluded_properties(openapi: OpenAPI):
    assert openapi.info_summary() == {
        "title": "Swagger Petstore",
        "description": "A sample API that uses a petstore as an example to demonstrate features in the OpenAPI 3.0 specification",
    }


def test_info_summary_custom_excluded_properties(openapi: OpenAPI):
    assert openapi.info_summary(excluded_info_properties=["title", "description"]) == {
        "termsOfService": "http://swagger.io/terms/",
        "contact": {
            "name": "Swagger API Team",
            "url": "http://swagger.io",
            "email": "apiteam@swagger.io",
        },
        "license": {
            "name": "Apache 2.0",
            "identifier": None,
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        "version": "1.0.0",
    }


def test_servers_summary(openapi: OpenAPI):
    assert openapi.servers_summary() == [{"url": "https://petstore.swagger.io/v2"}]


def test_paths_summary_default_excluded_properties(openapi: OpenAPI):
    path_summary = openapi.paths_summary()
    assert all([key in path_summary.keys() for key in ["/pets", "/pets/{id}"]])
    assert all([key in path_summary["/pets/{id}"].keys() for key in ["get", "delete"]])
    assert all(
        [
            key in path_summary["/pets/{id}"]["get"].keys()
            for key in ["description", "parameters", "responses"]
        ]
    )


def test_paths_summary_custom_excluded_properties(openapi: OpenAPI):
    path_summary = openapi.paths_summary(
        excluded_operation_properties=["description", "parameters"]
    )
    assert all(
        [
            key in path_summary["/pets/{id}"]["get"].keys()
            for key in ["operationId", "responses"]
        ]
    )


def test_paths_summary_excluded_200_response(openapi: OpenAPI):
    path_summary = openapi.paths_summary(exclude_non_2XX_responses=True)
    assert "404" not in path_summary["/pets/{id}"]["delete"]["responses"]


def test_openapi_summary(openapi: OpenAPI):
    summary = openapi.summary()
    assert all([key in summary for key in ["info", "servers", "paths"]])
    assert isinstance(summary, dict)
