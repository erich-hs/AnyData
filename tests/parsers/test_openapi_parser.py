import json
import os
import pytest
from anydata.parsers.openapi import OpenAPI, openapi_dict_from_str, resolve_references
from anydata.exceptions import InvalidOpenAPIFormat


@pytest.fixture
def sample_json_swagger() -> str:
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
def sample_yaml_swagger() -> str:
    return """
components:
  schemas:
    Error:
      properties:
        code:
          format: int32
          type: integer
        message:
          type: string
      required:
      - code
      - message
      type: object
    NewPet:
      properties:
        name:
          type: string
        tag:
          type: string
      required:
      - name
      type: object
    Pet:
      allOf:
      - $ref: '#/components/schemas/NewPet'
      - properties:
          id:
            format: int64
            type: integer
        required:
        - id
        type: object
info:
  contact:
    email: apiteam@swagger.io
    name: Swagger API Team
    url: http://swagger.io
  description: A sample API that uses a petstore as an example to demonstrate features
    in the OpenAPI 3.0 specification
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
  termsOfService: http://swagger.io/terms/
  title: Swagger Petstore
  version: 1.0.0
openapi: 3.0.0
paths:
  /pets:
    get:
      description: Returns all pets from the system that the user has access to.
      operationId: findPets
      parameters:
      - description: tags to filter by
        in: query
        name: tags
        required: false
        schema:
          items:
            type: string
          type: array
        style: form
      - description: maximum number of results to return
        in: query
        name: limit
        required: false
        schema:
          format: int32
          type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                items:
                  $ref: '#/components/schemas/Pet'
                type: array
          description: pet response
        default:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: unexpected error
    post:
      description: Creates a new pet in the store. Duplicates are allowed
      operationId: addPet
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewPet'
        description: Pet to add to the store
        required: true
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
          description: pet response
        default:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: unexpected error
  /pets/{id}:
    delete:
      description: deletes a single pet based on the ID supplied
      operationId: deletePet
      parameters:
      - description: ID of pet to delete
        in: path
        name: id
        required: true
        schema:
          format: int64
          type: integer
      responses:
        '204':
          description: pet deleted
        '404':
          description: mock failed response
        default:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: unexpected error
    get:
      description: Returns a user based on a single ID, if the user does not have
        access to the pet
      operationId: find pet by id
      parameters:
      - description: ID of pet to fetch
        in: path
        name: id
        required: true
        schema:
          format: int64
          type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
          description: pet response
        default:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: unexpected error
servers:
- url: https://petstore.swagger.io/v2
"""


@pytest.fixture
def openapi(sample_json_swagger: str) -> OpenAPI:
    return OpenAPI(sample_json_swagger)


def test_openapi_from_dict_without_info(sample_json_swagger: str):
    openapi_dict = json.loads(sample_json_swagger)
    del openapi_dict["info"]
    openapi = OpenAPI(openapi_dict)
    assert openapi.info is not None


def test_instantiate_openapi_from_json_str(sample_json_swagger: str):
    openapi = OpenAPI(sample_json_swagger)
    assert isinstance(openapi, OpenAPI)
    assert all([hasattr(openapi, attr) for attr in ["info", "servers", "paths"]])


def test_instantiate_openapi_from_yaml_str(sample_yaml_swagger: str):
    openapi = OpenAPI(sample_yaml_swagger)
    assert isinstance(openapi, OpenAPI)
    assert all([hasattr(openapi, attr) for attr in ["info", "servers", "paths"]])


def test_instantiate_openapi_from_json_file(tmpdir, sample_json_swagger: str):
    swagger = tmpdir.mkdir("tmp").join("swagger.json")
    with open(swagger, "w") as f:
        f.write(sample_json_swagger)
    assert isinstance(OpenAPI(os.path.abspath(swagger)), OpenAPI)


def test_instantiate_openapi_from_yaml_file(tmpdir, sample_yaml_swagger: str):
    swagger = tmpdir.mkdir("tmp").join("swagger.yaml")
    with open(swagger, "w") as f:
        f.write(sample_yaml_swagger)
    assert isinstance(OpenAPI(os.path.abspath(swagger)), OpenAPI)


def test_instantiate_openapi_from_dict(sample_json_swagger: str):
    openapi = OpenAPI(json.loads(sample_json_swagger))
    assert isinstance(openapi, OpenAPI)
    assert all([hasattr(openapi, attr) for attr in ["info", "servers", "paths"]])


def test_instantiate_openapi_from_html():
    openapi = OpenAPI(
        "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/petstore.json"
    )
    assert isinstance(openapi, OpenAPI)


def test_failed_instantiate_openapi_from_invalid_str():
    with pytest.raises(InvalidOpenAPIFormat):
        openapi_dict_from_str("{invalid_string")


def test_resolve_references(sample_json_swagger):
    dict_openapi = json.loads(sample_json_swagger)
    unresolved_refs = dict_openapi["paths"]["/pets"]["get"]["responses"]["200"]
    resolved_refs = resolve_references(unresolved_refs, dict_openapi)
    assert resolved_refs["content"]["application/json"]["schema"]["items"]["$ref"] == {
        "allOf": [
            {"$ref": "#/components/schemas/NewPet"},
            {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "integer", "format": "int64"}},
            },
        ]
    }


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
