import os
import json
import yaml
import requests
from json.decoder import JSONDecodeError
from yaml.parser import ParserError
from urllib.parse import urlparse
from typing import List, Dict, Union, Tuple
from ..schemas.openapi import Info, Server, PathItem, OPENAPI_OPERATIONS
from ..exceptions import InvalidOpenAPIFormat

"""
How-to from swaggerhub to json:
https://support.smartbear.com/swaggerhub/docs/en/manage-apis/download-api-definitions-from-swaggerhub.html#:~:text=Open%20the%20API%20in%20the,desired%20format%20%E2%80%93%20YAML%20or%20JSON.

Example:
https://app.swaggerhub.com/apis-docs/I2875/PM25_Open_Data/1.0.0
Change /apis-docs/ to /apis/ to get to the Full specification hub
https://app.swaggerhub.com/apis/I2875/PM25_Open_Data/1.0.0
Change //app. to //api. to get to the json specification
"""


# %% OpenAPI components parsers
def openapi_info_from_dict(openapi_dict: dict) -> Info:
    try:
        info = Info.from_dict(openapi_dict["info"])
    except KeyError:
        info = Info()
    return info


def openapi_servers_from_dict(openapi_dict: dict) -> List[Server]:
    return Server.schema().load(openapi_dict["servers"], many=True)


def openapi_paths_from_dict(openapi_dict: dict) -> Dict[str, PathItem]:
    return {k: PathItem.from_dict(v) for k, v in openapi_dict["paths"].items()}


# %% Auxiliary functions
def resolve_references(relative_dict, complete_dict):
    """
    Recursively resolves references in a dictionary with values from an external dictionary.
    resolve_ref and resolve are encapsulated for a cleaner namespace.
    """

    def resolve_ref(complete_element, ref_element):
        if ref_element.startswith("#"):
            keys = ref_element.split("/")[1:]
            current = complete_element
            for key in keys:
                current = current[key]
            return current
        return ref_element

    def resolve(element):
        if isinstance(element, dict):
            return {key: resolve(value) for key, value in element.items()}
        elif isinstance(element, list):
            return [resolve(item) for item in element]
        elif isinstance(element, str):
            return resolve_ref(complete_dict, element)
        else:
            return element

    return resolve(relative_dict)


# OpenAPI instantiation functions
def openapi_dict_from_str(openapi_str: str) -> dict:
    try:
        return json.loads(openapi_str)
    except JSONDecodeError:
        pass
    try:
        return yaml.safe_load(openapi_str)
    except ParserError:
        raise InvalidOpenAPIFormat("The input must be a valid JSON or YAML.")


def openapi_dict_from_file(openapi_file: str) -> dict:
    with open(openapi_file, "r") as f:
        openapi_dict = openapi_dict_from_str(f.read())
    return openapi_dict


# %% OpenAPI class
class OpenAPI:
    def __init__(self, openapi_spec: dict) -> None:
        """
        Instantiates an OpenAPI object from a dictionary.
        """
        self.json = openapi_spec
        self.info = openapi_info_from_dict(self._json)
        self.servers = openapi_servers_from_dict(self._json)
        self.paths = openapi_paths_from_dict(self._json)
        # self.json = openapi_dict

    @property
    def json(self):
        return self._json

    @json.setter
    def json(self, openapi_spec: Union[str, dict]):
        if isinstance(openapi_spec, dict):
            self._json = openapi_spec
        elif isinstance(openapi_spec, str):
            if urlparse(openapi_spec).scheme in ["http", "https"]:
                openapi_spec = requests.get(openapi_spec).text
                openapi_spec = openapi_dict_from_str(openapi_spec)
            elif os.path.isfile(openapi_spec):
                openapi_spec = openapi_dict_from_file(openapi_spec)
            else:
                openapi_spec = openapi_dict_from_str(openapi_spec)
            self._json = openapi_spec
        else:
            raise InvalidOpenAPIFormat(
                "The OpenAPI specification must be either a dictionary or as a valid JSON or YAML source."
            )

        # if os.path.isfile(openapi_spec):
        #     self._json = openapi_dict_from_file(openapi_spec)
        # elif isinstance(openapi_spec, str):
        #     if urlparse(openapi_spec).scheme in ["http", "https"]:
        #         openapi_spec = requests.get(openapi_spec).text
        #     self._json = openapi_dict_from_str(openapi_spec)
        # elif isinstance(openapi_spec, dict):
        #     self._json = openapi_spec
        # else:
        #     raise InvalidOpenAPIFormat(
        #         "The OpenAPI specification must be either a dictionary or as a valid JSON or YAML source."
        #     )

    def to_dict(self):
        """
        Returns the OpenAPI object as a dictionary.
        This method doesn't reconstruct the originating OpenAPI dictionary.
        """
        return {
            "info": self.info._to_dict(),
            "servers": [s._to_dict() for s in self.servers],
            "paths": {k: v._to_dict() for k, v in self.paths.items()},
        }

    # Summarizers
    @property
    def endpoint_methods(self) -> List[Tuple[str, List[str]]]:
        """
        Returns a list of tuples with the endpoints and its available methods from OpenAPI paths.
        (endpoint, [methods])
        """
        endpoints_methods = []
        for endpoint, path_item in self.paths.items():
            endpoints_methods.append(
                (endpoint, [o for (o, _) in path_item.operations()])
            )
        return endpoints_methods

    def info_summary(
        self,
        excluded_info_properties: List[str] = [
            "termsOfService",
            "contact",
            "license",
            "version",
        ],
    ) -> dict:
        """
        Returns a summary of the OpenAPI info.
        Parameters:
            - excluded_info_properties: List of properties to exclude from the Info object.
        Returns a dictionary with the remaining properties.
        """
        return self.info.summarize(excluded_properties=excluded_info_properties)

    def servers_summary(
        self, excluded_server_properties: List[str] = [""]
    ) -> List[dict]:
        """
        Returns a summary of the OpenAPI servers.
        --- This function is currently not excluding any properties from the Server objects. ---
        Returns a dictionary with the properties of each Server object.
        """
        return [
            s.summarize(excluded_properties=excluded_server_properties)
            for s in self.servers
        ]

    def paths_summary(
        self,
        excluded_operation_properties: List[str] = ["externalDocs", "operationId"],
        exclude_non_2XX_responses: bool = True,
        resolve_parameter_references: bool = True,
    ) -> dict:
        """
        Returns a summary of the OpenAPI paths and its operations.
        Parameters:
            - excluded_operation_properties: List of properties to exclude from the Operation objects.
            - exclude_non_2XX_responses: If True, excludes non-2XX responses from the 'responses' dictionary of the Operation objects.
            Default: True
        Returns a dictionary with the summarized properties of each PathItem and Operation objects.
        """
        paths_summary = {}
        for path in self.paths:
            # Extract non-openapi-operations properties from each PathItem
            paths_summary[path] = {
                k: v
                for k, v in self.paths[path]._to_dict().items()
                if k not in OPENAPI_OPERATIONS
            }
            for method, operation in self.paths[path].operations():
                # Summarize Operations
                paths_summary[path][method] = operation.summarize(
                    excluded_properties=excluded_operation_properties
                )
                if (
                    exclude_non_2XX_responses
                    and operation.responses
                    and "responses" in paths_summary[path][method]
                ):
                    # Excludes non-2XX responses from the paths_summary 'responses' dictionary
                    for response in list(operation.responses):
                        if response.startswith("2"):
                            pass
                        else:
                            del paths_summary[path][method]["responses"][response]
                if (
                    resolve_parameter_references
                    and "parameters" in paths_summary[path][method]
                ):
                    # Resolves 'parameters' references with values from the base openapi dictionary
                    paths_summary[path][method]["parameters"] = resolve_references(
                        paths_summary[path][method]["parameters"], self.json
                    )
        return paths_summary

    def summary(
        self,
        excluded_info_properties: List[str] = [
            "termsOfService",
            "contact",
            "license",
            "version",
        ],
        excluded_server_properties: List[str] = [""],
        excluded_operation_properties: List[str] = [
            "externalDocs",
            "operationId",
            "parameters",
            "responses",
        ],
        exclude_non_2XX_responses: bool = True,
        resolve_parameter_references: bool = False,
    ):
        """
        Higher-level summary of the OpenAPI object.
        Returns a dictionary that includes a summary of the info, servers, and paths parameters.
        """
        return {
            "info": self.info_summary(excluded_info_properties),
            "servers": self.servers_summary(excluded_server_properties),
            "paths": self.paths_summary(
                excluded_operation_properties,
                exclude_non_2XX_responses,
                resolve_parameter_references,
            ),
        }
