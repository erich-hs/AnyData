import re
import json
import copy
import inspect
from typing import Optional, Union, List, Tuple
from dataclasses import dataclass
from guidance.models import Model
from ..schemas.core import ABCDataAPI
from ..core.endpoint import Endpoint
from ..engine.functions import dataapi_from_prompt, evaluate_unsuccessful_response
from ..parsers.openapi import OpenAPI


@dataclass
class DataAPI(ABCDataAPI):
    base_url: str
    openapi: Optional[Union[str, dict, OpenAPI]] = None
    shared_params: Optional[dict] = None
    shared_headers: Optional[dict] = None
    cookies: Optional[dict] = None
    auth: Optional[dict] = None
    timeout: Optional[int] = None
    allow_redirects: Optional[bool] = True
    stream: Optional[bool] = False
    verify: Optional[bool] = True
    cert: Optional[str] = None
    lm: Optional[Model] = None

    def __post_init__(self) -> None:
        if self.openapi and not isinstance(self.openapi, OpenAPI):
            self.openapi = OpenAPI(self.openapi)

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
        self.openapi = OpenAPI(openapi) if not isinstance(openapi, OpenAPI) else openapi

    def set_lm(self, lm: Model) -> None:
        assert isinstance(
            lm, Model
        ), "Language model must be a valid initiliazied Model object."
        self.lm = lm

    def set_shared_params(self, params: dict, propagate: bool = True) -> None:
        """
        Update the shared parameters for the DataAPI.
        This method overwrites the 'shared_params' parameter defined at DataAPI instantiation
        and propagate to all attached endpoints, if 'propagate' is True.
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
        """
        self.shared_headers = headers
        if propagate:
            for endpoint in self.endpoints():
                self[endpoint[0]].merge_headers(copy.deepcopy(headers))

    def endpoints(self) -> List[Tuple[str, Endpoint]]:
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
        # TODO: Implement retries with backoff
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
