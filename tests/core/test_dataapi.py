import pytest
from anydata import DataAPI

sample_openapi = """
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
def data_api():
    return DataAPI(base_url="https://pokeapi.co/api/v2/")

#%% Core methods
def test_add_endpoint(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    assert "pokemon/{name}" in data_api

def test_add_endpoint_with_alias(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
        alias="get_pikachu",
    )
    assert "get_pikachu" in data_api
    assert "pokemon/{name}" not in data_api

def test_list_endpoints(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
        alias="get_pikachu_encounters"
    )
    assert data_api.endpoints()[1][0] == "pokemon/{name}"
    assert data_api.endpoints()[0][0] == "get_pikachu_encounters"

def test_remove_endpoint(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.remove_endpoints("pokemon/{name}")
    assert "pokemon/{name}" not in data_api

def test_remove_endpoints_with_regex(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
    )
    data_api.remove_endpoints("pokemon/{name}", regex=True)
    assert "pokemon/{name}" not in data_api
    assert "pokemon/{name}/encounters" not in data_api

def test_keep_endpoints(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
    )
    data_api.keep_endpoints("pokemon/{name}")
    assert "pokemon/{name}" in data_api
    assert "pokemon/{name}/encounters" not in data_api

def test_keep_endpoints_with_regex(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/other/1",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/other/2",
        method="GET",
    )
    data_api.keep_endpoints("pokemon/other/", regex=True)
    assert "pokemon/other/1" in data_api
    assert "pokemon/other/2" in data_api
    assert "pokemon/{name}" not in data_api

def test_set_and_propagate_shared_params(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
    )
    data_api.set_shared_params(
        params={
            "limit": 10,
            "offset": 0
        },
        propagate=True
    )
    assert data_api['pokemon/{name}'].params == {"limit": 10, "offset": 0}
    assert data_api['pokemon/{name}'].params == data_api['pokemon/{name}/encounters'].params
    assert data_api.shared_params == {"limit": 10, "offset": 0}

def test_set_and_propagate_shared_headers(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
    )
    data_api.set_shared_headers(
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        propagate=True
    )
    assert all(
        ["Content-Type" in data_api['pokemon/{name}'].headers.keys(),
        "User-Agent" in data_api['pokemon/{name}'].headers.keys()]
    )
    assert data_api['pokemon/{name}'].headers == data_api['pokemon/{name}/encounters'].headers

def test_merge_shared_params(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
        params={"limit": 5}
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
        params={"limit": 5}
    )
    data_api.set_shared_params(
        params={"offset": 0},
        propagate=True
    )
    assert data_api['pokemon/{name}'].params == {"limit": 5, "offset": 0}
    assert data_api['pokemon/{name}'].params == data_api['pokemon/{name}/encounters'].params
    assert data_api.shared_params == {"offset": 0}

def test_merge_shared_path_params(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}/{another_path_param}",
        method="GET",
        params={"name": "pikachu", "another_path_param": "another_value"}
    )
    data_api.add_endpoint(
        endpoint="pokemon/{name}/{another_path_param}/encounters",
        method="GET",
    )
    data_api.set_shared_params(
        params={"name": "bulbasaur"},
        propagate=True
    )
    assert data_api["pokemon/{name}/{another_path_param}"].path_params == {"name": "bulbasaur", "another_path_param": "another_value"}
    assert data_api["pokemon/{name}/{another_path_param}/encounters"].path_params == {"name": "bulbasaur", "another_path_param": None}
    assert data_api.shared_params == {"name": "bulbasaur"}

def test_persisted_shared_params(data_api: DataAPI) -> None:
    data_api.set_shared_params({"name": "pikachu", "limit": 10})
    data_api.add_endpoint(
        endpoint="pokemon/{name}/",
        method="GET",
    )
    assert data_api.shared_params == {"name": "pikachu", "limit": 10}
    data_api.add_endpoint(
        endpoint="pokemon/{name}/encounters",
        method="GET",
    )
    assert data_api.shared_params == {"name": "pikachu", "limit": 10}

def test_instantiate_from_openapir() -> None:
    data_api = DataAPI.from_openapi(sample_openapi)
    endpoints = [
        "get:/pets",
        "post:/pets",
        "get:/pets/{id}",
        "delete:/pets/{id}"
    ]
    assert all([e in data_api for e in endpoints])
    assert (data_api['get:/pets'].method == "get" and data_api['get:/pets'].endpoint == "/pets")
    assert (data_api['post:/pets'].method == "post" and data_api['get:/pets'].endpoint == "/pets")

#%% Auxiliary methods
def test_manual_assignment_failure(data_api: DataAPI) -> None:
    with pytest.raises(NotImplementedError):
        data_api["pokemon/{name}"] = "GET"

def test_set_endpoint_alias(data_api: DataAPI) -> None:
    data_api.add_endpoint(
        endpoint="pokemon/{name}",
        method="GET",
    )
    data_api._set_endpoint_alias("pokemon/{name}", "get_pikachu")
    assert "get_pikachu" in data_api
    assert "pokemon/{name}" not in data_api

#%% ABC methods
def test_delete_inexistent_endpoint(data_api: DataAPI) -> None:
    with pytest.raises(KeyError):
        del data_api["inexistent/endpoint"]

def test_iterable_not_implemented(data_api: DataAPI) -> None:
    with pytest.raises(NotImplementedError):
        iter(data_api)

def test_len_not_implemented(data_api: DataAPI) -> None:
    with pytest.raises(TypeError):
        len(data_api)