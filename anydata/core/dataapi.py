from __future__ import annotations

import re
import json
import copy
import inspect
from typing import Optional, Union, List, Tuple

from ..schemas.core import ABCDataAPI
from ..core.endpoint import Endpoint
from ..parsers.openapi import OpenAPI

try:
    from guidance.models import Model

    is_guidance = True
except ImportError:
    is_guidance = False

if is_guidance:
    from ..engine.functions import dataapi_from_prompt, evaluate_unsuccessful_response


class DataAPI(ABCDataAPI):
    def __init__(
        self,
        base_url: str,
        openapi: Optional[Union[str, dict, OpenAPI]] = None,
        shared_params: Optional[dict] = None,
        shared_headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        auth: Optional[dict] = None,
        timeout: Optional[int] = None,
        allow_redirects: Optional[bool] = True,
        stream: Optional[bool] = False,
        verify: Optional[bool] = True,
        cert: Optional[str] = None,
        lm: Optional[Model] = None,
    ):
        """DataAPI collection to manage Endpoints.

        Examples:
            A DataAPI object can be instantiated with a base URL and Endpoints can be added with the add_endpoint() method.

                $ data_api = DataAPI(base_url="https://api.example.com")
                $ data_api.add_endpoint(endpoint="/users", method="GET")
                $ data_api["/users"].request()

            Smart methods require an OpenAPI specification and a language model to be set.

                $ data_api.set_openapi(OpenAPI(https://api.example.com/openapi.json))
                $ data_api.set_lm(OpenAI("gpt-3.5-turbo"))
                $ data_api.smart_add_endpoint(prompt="List all users", alias="list_users")
                $ data_api["list_users"].request()

            A DataAPI object can also be instantiated directly from an OpenAPI specification.
            The OpenAPI specification is parsed during instantiation and Endpoints are added to the DataAPI object.

                $ data_api = DataAPI.from_openapi(openapi="https://api.example.com/openapi.json")
                $ data_api["/users"].request()

        Attributes:
            base_url (str): Base URL for the Endpoints associated with the DataAPI collection.
            openapi (Union[str, dict, OpenAPI], optional): OpenAPI specification for the DataAPI. Defaults to None.
            shared_params (dict, optional): Shared parameters for the DataAPI. Defaults to None.
            shared_headers (dict, optional): Shared headers for the DataAPI. Defaults to None.
            cookies (dict, optional): Cookies for the DataAPI. Defaults to None.
            auth (dict, optional): Authentication parameters for the DataAPI. Defaults to None.
            timeout (int, optional): Timeout for the DataAPI. Defaults to None.
            allow_redirects (bool, optional): Allow redirects flag for the DataAPI. Defaults to True.
            stream (bool, optional): Stream flag for the DataAPI. Defaults to False.
            verify (bool, optional): Verify flag for the DataAPI. Defaults to True.
            cert (str, optional): Certificate for the DataAPI. Defaults to None.
            lm (Model, optional): Language model for the DataAPI. Defaults to None.

        Methods:
            set_openapi(openapi: Union[str, dict, OpenAPI]) -> None: Set the OpenAPI specification for the DataAPI.
            set_lm(lm: Model) -> None: Set the language model for the DataAPI.
            set_shared_params(params: dict, propagate: bool = True) -> None: Set shared parameters for the DataAPI.
            set_shared_headers(headers: dict, propagate: bool = True) -> None: Set shared headers for the DataAPI.
            endpoints() -> List[Tuple[str, Endpoint]]: List all Endpoints associated with the DataAPI.
            add_endpoint(endpoint: str, method: str, alias: Optional[str] = None, params: Optional[dict] = None, body: Optional[dict] = None, headers: Optional[dict] = None, cookies: Optional[dict] = None, auth: Optional[dict] = None, timeout: Optional[int] = None, allow_redirects: Optional[bool] = None, stream: Optional[bool] = None, verify: Optional[bool] = None, cert: Optional[str] = None, **kwargs) -> None: Add an Endpoint to the DataAPI.
            smart_add_endpoint(prompt: str, alias: Optional[str] = None, echo: bool = False) -> None: Add an Endpoint to the DataAPI using a language model.
            remove_endpoints(endpoints: Union[list, str], regex: bool = False) -> None: Remove the specified Endpoints from the DataAPI.
            keep_endpoints(endpoints: Union[list, str], regex: bool = False) -> None: Keep only the specified Endpoints in the DataAPI.
            from_openapi(openapi: Union[dict, str, OpenAPI], base_url: Optional[str] = None) -> "DataAPI": Create a DataAPI object from an OpenAPI specification.
        """
        self.base_url = base_url
        if openapi:
            self.openapi = (
                OpenAPI(openapi) if not isinstance(openapi, OpenAPI) else openapi
            )
        self.shared_params = shared_params
        self.shared_headers = shared_headers
        self.cookies = cookies
        self.auth = auth
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.stream = stream
        self.verify = verify
        self.cert = cert
        if lm:
            assert is_guidance, ImportError(
                "Please install the 'guidance' package using `pip install guidance` to use language models."
            )
            assert isinstance(
                lm, Model
            ), "Language model must be a valid initiliazied `guidance.models.Model` object."
            self.lm = lm

    def __setitem__(self, key, value) -> None:
        """
        Overwritting __setitem__ to prevent manual assignment of endpoints
        """
        raise NotImplementedError(
            "Manual assignment of endpoints is not allowed. Please use the add_endpoint() method to add an endpoint."
        )

    def _match_endpoints_from_regex(self, endpoints: str) -> List[str]:
        assert isinstance(
            endpoints, str
        ), "If 'regex' is True, 'endpoints' must be a string."
        return [e[0] for e in self.endpoints() if re.search(endpoints, e[0])]

    def _set_endpoint_alias(self, endpoint: str, alias: str) -> None:
        super().__setitem__(alias, self[endpoint])
        self[alias].alias = alias
        del self[endpoint]

    def _reset_endpoint_base_params(self, endpoint: Endpoint) -> None:
        endpoint.base_url = self.base_url
        endpoint.params = self.shared_params
        endpoint.headers = self.shared_headers
        endpoint.cookies = self.cookies
        endpoint.auth = self.auth
        endpoint.timeout = self.timeout
        endpoint.allow_redirects = self.allow_redirects
        endpoint.stream = self.stream
        endpoint.verify = self.verify
        endpoint.cert = self.cert

    def set_openapi(self, openapi: Union[str, dict, OpenAPI]) -> None:
        """Set the OpenAPI specification for the DataAPI.

        Args:
            openapi (Union[str, dict, OpenAPI]): OpenAPI specification for the DataAPI.
        """
        self.openapi = OpenAPI(openapi) if not isinstance(openapi, OpenAPI) else openapi

    def set_lm(self, lm: Model) -> None:
        """Set the language model for the DataAPI.

        Args:
            lm (Model): Language model for the DataAPI.
        """
        assert is_guidance, ImportError(
            "Please install the 'guidance' package using `pip install guidance` to use language models."
        )
        assert isinstance(
            lm, Model
        ), "Language model must be a valid initiliazied `guidance.models.Model` object."
        self.lm = lm

    def set_shared_params(self, params: dict, propagate: bool = True) -> None:
        """
        Update the shared parameters for the DataAPI.
        This method overwrites the 'shared_params' parameter defined at DataAPI instantiation
        and propagate to all attached endpoints, if 'propagate' is True.

        Args:
            params (dict): Shared parameters for the DataAPI.
            propagate (bool, optional): Propagate shared parameters to all attached endpoints. Defaults to True.
        """
        self.shared_params = params
        if propagate:
            for endpoint in self.endpoints():
                self[endpoint[0]].merge_params(copy.deepcopy(params))

    def set_shared_headers(self, headers: dict, propagate: bool = True) -> None:
        """
        Update the shared headers for the DataAPI.
        This method overwrites the 'shared_headers' parameter defined at DataAPI instantiation
        and propagate to all attached endpoints, if 'propagate' is True.

        Args:
            headers (dict): Shared headers for the DataAPI.
            propagate (bool, optional): Propagate shared headers to all attached endpoints. Defaults to True.
        """
        self.shared_headers = headers
        if propagate:
            for endpoint in self.endpoints():
                self[endpoint[0]].merge_headers(copy.deepcopy(headers))

    def endpoints(self) -> List[Tuple[str, Endpoint]]:
        """List all Endpoints associated with the DataAPI.

        Returns:
            List[Tuple[str, Endpoint]]: List of all Endpoints associated with the DataAPI.
        """
        return inspect.getmembers(self, lambda a: isinstance(a, Endpoint))

    def add_endpoint(
        self,
        endpoint: str,
        method: str,
        alias: Optional[str] = None,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        auth: Optional[dict] = None,
        timeout: Optional[int] = None,
        allow_redirects: Optional[bool] = None,
        stream: Optional[bool] = None,
        verify: Optional[bool] = None,
        cert: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add an Endpoint to the DataAPI.

        Args:
            endpoint (str): Endpoint relative URL.
            method (str): Endpoint HTTP method.
            alias (Optional[str], optional): Alias to access the Endpoint from the parent DataAPI object. Defaults to None.
            params (Optional[dict], optional): Path and/or Query parameters to associate with the Endpoint. Defaults to None.
            body (Optional[dict], optional): Body payload to associate with the Endpoint for PUT and POST methods. Defaults to None.
            headers (Optional[dict], optional): Headers to associate with the Endpoint. Defaults to None.
            cookies (Optional[dict], optional): Optional cookies to associate with the Endpoint. Defaults to None.
            auth (Optional[dict], optional): Custom authentication to associate with the Endpoint. Defaults to None.
            timeout (Optional[int], optional): Timeout parameters to associate with the Endpoint. Defaults to None.
            allow_redirects (Optional[bool], optional): Allow redirects flag to associate with the Endpoint. Defaults to None.
            stream (Optional[bool], optional): Stream flag to associate with the Endpoint. Defaults to None.
            verify (Optional[bool], optional): Verify flag to associate with the Endpoint. Defaults to None.
            cert (Optional[str], optional): Custom certificates to associate with the Endpoint. Defaults to None.
        """
        endpoint_object = Endpoint(
            base_url=self.base_url,
            endpoint=endpoint,
            method=method,
            alias=alias,
            params=params or self.shared_params,
            body=body,
            headers=headers or self.shared_headers,
            cookies=cookies or self.cookies,
            auth=auth or self.auth,
            timeout=timeout or self.timeout,
            allow_redirects=self.allow_redirects
            if allow_redirects is None
            else allow_redirects,
            stream=self.stream if stream is None else stream,
            verify=self.verify if verify is None else verify,
            cert=cert or self.cert,
            **kwargs,
        )
        # Merge explicit parameters with shared parameters
        if params and self.shared_params:
            endpoint_object.merge_params(copy.deepcopy(self.shared_params))
        # Merge explicit headers with shared headers
        if headers and self.shared_headers:
            endpoint_object.merge_headers(copy.deepcopy(self.shared_headers))
        # Attach endpoint to DataAPI
        if alias:
            super().__setitem__(alias, endpoint_object)
        else:
            super().__setitem__(endpoint, endpoint_object)

    def smart_add_endpoint(
        self,
        prompt: str,
        alias: Optional[str] = None,
        echo: bool = False,
    ) -> None:
        """Add an Endpoint to the DataAPI with a natural language prompt.
        This method requires an OpenAPI specification and a language model to be set for the DataAPI.

        Args:
            prompt (str): Natural language prompt to determine the Endpoint relative URL, method, and parameters.
            alias (Optional[str], optional): Alias to access the Endpoint from the parent DataAPI object. Defaults to None.
            echo (bool, optional): Print the language model outputs during endpoint instantiation. Defaults to False.
        """
        # TODO: Implement retries with backoff
        assert is_guidance, ImportError(
            "Please install the 'guidance' package using `pip install guidance` to use this method."
        )
        assert self.openapi, "An OpenAPI specification is needed for a smart_add_endpoint. Please define one with the .set_openapi() method."
        assert (
            self.lm is not None
        ), "A language model is needed for a smart_add_endpoint. Please define one with the the .set_lm() method."
        stateless_lm = self.lm.copy()
        stateless_lm.echo = echo
        try:
            stateless_lm += dataapi_from_prompt(prompt, self.openapi)
            # Send test request to the endpoint
            if echo:
                print("Sending test request to the endpoint...")
            test_endpoint = Endpoint(
                base_url=self.base_url,
                endpoint=stateless_lm["endpoint"],
                method=stateless_lm["method"],
                params=json.loads(stateless_lm["parameters"]),
                headers=self.shared_headers,
                raise_unsuccessful=False,
            )
            if self.shared_params:
                test_endpoint.merge_params(copy.deepcopy(self.shared_params))
            test_response = test_endpoint.request()
            print(
                f"Test request to the endpoint '{stateless_lm['endpoint']}' returned status code {test_response.status_code}."
            )
            if test_response.status_code != 200:
                stateless_lm += evaluate_unsuccessful_response(
                    prompt=prompt, response=test_response
                )
            else:
                self.add_endpoint(
                    endpoint=stateless_lm["endpoint"],
                    method=stateless_lm["method"],
                    params=json.loads(stateless_lm["parameters"]),
                    alias=alias,
                )
        except Exception as e:
            print(f"An error occurred while adding endpoint: {e}")
            raise
        print(
            f"""Added endpoint '{stateless_lm['endpoint']}' with method '{stateless_lm['method']}'{f" at alias '{alias}'" if alias else ''} to DataAPI."""
        )

    def remove_endpoints(
        self, endpoints: Union[list, str], regex: bool = False
    ) -> None:
        """
        Remove the specified endpoints. If 'regex' is True, 'endpoints' is treated as a regular expression.

        Args:
            endpoints (Union[list, str]): List of endpoints to remove.
            regex (bool, optional): Treat 'endpoints' as a regular expression. Defaults to False.
        """
        if regex:
            endpoints = self._match_endpoints_from_regex(endpoints)
        else:
            if isinstance(endpoints, str):
                endpoints = [endpoints]
        for e in endpoints:
            del self[e]

    def keep_endpoints(self, endpoints: Union[list, str], regex: bool = False) -> None:
        """
        Keep only the specified endpoints. If 'regex' is True, 'endpoints' is treated as a regular expression.

        Args:
            endpoints (Union[list, str]): List of endpoints to keep.
            regex (bool, optional): Treat 'endpoints' as a regular expression. Defaults to False.
        """
        if regex:
            endpoints = self._match_endpoints_from_regex(endpoints)
        else:
            if isinstance(endpoints, str):
                endpoints = [endpoints]
        for e in self.endpoints():
            if e[0] not in endpoints:
                del self[e[0]]

    @classmethod
    def from_openapi(
        cls, openapi: Union[dict, str, OpenAPI], base_url: Optional[str] = None
    ) -> "DataAPI":
        """Instantiate a DataAPI object from an OpenAPI specification.

        Args:
            openapi (Union[dict, str, OpenAPI]): OpenAPI specification for the DataAPI.
            base_url (Optional[str], optional): Base URL for the DataAPI to be instantiated. This parameter is needed to resolve conflicts in OpenAPI specifications with multiple base URLs. Defaults to None.

        Raises:
            ValueError: Raises on conflicts in OpenAPI specifications with multiple base URLs, if 'base_url' is not explicitly defined.

        Returns:
            DataAPI: A DataAPI object instantiated from the OpenAPI specification.
        """
        if not isinstance(openapi, OpenAPI):
            openapi = OpenAPI(openapi)
        api_servers = [s.url for s in openapi.servers]
        if not base_url:
            if len(api_servers) > 1:
                raise ValueError(
                    "Multiple base URLs (servers) located in the OpenAPI specification. Please explicitly define the base URL with the 'base_url' parameter."
                )
            else:
                base_url = api_servers[0]
        # Instantiate DataAPI object
        data_api = cls(base_url=base_url, openapi=openapi)
        # Attach endpoints from OpenAPI specification
        endpoints_methods = openapi.endpoint_methods
        for endpoint, methods in endpoints_methods:
            if len(methods) > 1:
                for method in methods:
                    data_api.add_endpoint(
                        endpoint=endpoint, method=method, alias=f"{method}:{endpoint}"
                    )
            else:
                data_api.add_endpoint(endpoint=endpoint, method=methods[0])
        return data_api
