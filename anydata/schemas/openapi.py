import inspect
from typing import Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses_json import dataclass_json

OPENAPI_OPERATIONS = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']

@dataclass_json
class OpenAPIABC(ABC):
    ...
    
    def _to_dict(self):
        '''
        Wrapper around to_dict() method to remove None values from the dictionary representation.
        '''
        return {k: v for k, v in self.to_dict().items() if v is not None}
    
    def summarize(self, excluded_properties: List[str]):
        '''
        Returns the object in dictionary format excluding the properties in the excluded_properties list.
        '''
        return {k: v for k, v in self._to_dict().items() if k not in excluded_properties}

# Info OpenAPI Component
@dataclass
class Contact(OpenAPIABC):
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None

@dataclass
class License(OpenAPIABC):
    name: Optional[str] = None
    identifier: Optional[str] = None
    url: Optional[str] = None

@dataclass
class Info(OpenAPIABC):
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None
    version: Optional[str] = None

# Server OpenAPI Component
@dataclass
class Server(OpenAPIABC):
    url: str
    description: Optional[str] = None
    variables: Optional[dict] = None

# Path OpenAPI Component
@dataclass
class ExternalDocumentation(OpenAPIABC):
    url: str
    description: Optional[str] = None

@dataclass
class Operation(OpenAPIABC):
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Optional[List[dict]] = None
    requestBody: Optional[dict] = None
    responses: Optional[dict] = None
    deprecated: Optional[bool] = None

@dataclass
class PathItem(OpenAPIABC):
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None

    def operations(self):
        return inspect.getmembers(self, lambda a: isinstance(a, Operation))