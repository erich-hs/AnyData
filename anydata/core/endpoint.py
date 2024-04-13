from __future__ import annotations

import re
import copy
from requests import Response
from typing import Optional
from collections.abc import Mapping

from ..parsers.response_parser import json_response_to_pandas
from ..schemas.core import EndpointSession


def _handle_response_status_code(resp, *args, **kwargs) -> None:
    # Not implemented with response.raise_for_status() as it
    # fails to capture useful error messages from non-200 responses
    if resp.status_code not in range(200, 400):
        print(resp.text)
        raise ValueError(f"Unsuccessful request with status code {resp.status_code}.")


def _merge_setting(new_setting: dict, base_setting: Optional[dict] = None) -> dict:
    assert isinstance(
        new_setting, Mapping
    ), f"New setting to be merged must be a valid mapping. 'new_setting' provided is of type {type(new_setting)}."
    if base_setting:
        assert isinstance(
            base_setting, Mapping
        ), f"Base setting to be merged must be a valid mapping. 'base_setting' provided is of type {type(base_setting)}."
        merged_setting = copy.deepcopy(new_setting)
        try:
            for key, value in base_setting.items():
                merged_setting.setdefault(key, value)
        except AttributeError:
            pass
        return merged_setting
    return new_setting


class Endpoint(EndpointSession):
    def __init__(
        self,
        base_url: str,
        endpoint: str,
        method: str,
        alias: Optional[str] = None,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        raise_unsuccessful: Optional[bool] = True,
        **kwargs,
    ) -> None:
        """
        Endpoint object to fetch data from and interact with a REST API.
        Endpoint is a wrapper around requests.Session with fixed base URL, relative URL, and HTTP method.
        An Endpoint allows for Session-level states such as cookies or custom authentication mechanisms.

        Examples:
            An endpoint can be defined with a base URL, relative endpoint, and HTTP method.

                $ endpoint = Endpoint(
                    base_url="https://api.example.com",
                    endpoint="/users/{user_id}",
                    method="GET",
                    params={"user_id": 1},
                )
                $ response = endpoint.request()

            As a wrapper around requests.Session, an Endpoint can be used as a context manager.

                $ with endpoint as e:
                $     response = e.request()

        Attributes:
            base_url (str): Base URL of the API.
            endpoint (str): Relative URL of the API.
            method (str): HTTP method to be used for requests.
            alias (str, optional): Alias for the endpoint. This attribute supports Endpoint instantiateds at DataAPI collections. Defaults to None.
            params (dict, optional): Query parameters for the request. Defaults to None.
            body (dict, optional): Body of the request. Defaults to None.
            headers (dict, optional): Custom headers for the request. Defaults to None.
            raise_unsuccessful (bool, optional): Raise an error if the response is not successful. Defaults to True.

        To learn more, please refer to the [requests.Session documentation](https://requests.readthedocs.io/en/latest/user/advanced/).
        """
        # Storing custom headers for __repr__ method
        self._custom_headers = headers
        super().__init__(
            base_url=base_url,
            endpoint=endpoint,
            method=method,
            params=params,
            body=body,
            headers=headers,
            **kwargs,
        )
        if raise_unsuccessful:
            self.hooks["response"].append(_handle_response_status_code)
        self.alias = alias
        self._set_path_params()

    def __repr__(self) -> str:
        params_str = f"params={self.params}, " if self.params else ""
        path_params_str = (
            f"path_params={self.path_params}, " if self.path_params else ""
        )
        body_str = f"body={self.body}, " if self.body else ""
        headers_str = (
            f"headers={self._custom_headers}, " if self._custom_headers else ""
        )
        auth_str = f"auth={self.auth}, " if self.auth else ""
        timeout_str = f"timeout={self.timeout}, " if self.timeout else ""
        stream_str = f"stream={self.stream}, " if self.stream else ""
        cert_str = f"cert={self.cert}, " if self.cert else ""
        return (
            f"Endpoint("
            f'method="{self.method}", '
            f'endpoint="{self.endpoint}", '
            f"{params_str}"
            f"{path_params_str}"
            f"{body_str}"
            f"{headers_str}"
            f"{auth_str}"
            f"{timeout_str}"
            f"{stream_str}"
            f"{cert_str}"
            f")"
        ).replace(", )", ")")

    def _set_path_params(self) -> dict:
        """
        Extract path parameters from the endpoint and store them in self.path_params.
        To obtain path parameters values this method takes self.params as the first precedence, and self.path_params as the second.
        It will also remove path parameters from self.params if they are found in the endpoint.
        Example:
            endpoint = "/users/{user_id}/posts/{post_id}"
            endpoint.params = {"user_id": 2, "post_id": None, "format": "json"}
            endpoint.path_params = {"user_id": 1, "post_id": 1}
            endpoint._set_path_params()
        Will result in:
            endpoint.params = {"format": "json"}
            endpoint.path_params = {"user_id": 2, "post_id": 1}
        """
        # List all path parameters in the endpoint
        path_params_list = re.findall(r"\{([^{}]+)\}", self.endpoint)
        # Initialize path parameters dictionary
        path_params = {param: None for param in path_params_list}
        # Merge with current self.path_params, if any
        if hasattr(self, "path_params"):
            path_params = _merge_setting(self.path_params, path_params)
        # Merge with current self.params, if any
        if self.params:
            path_params = _merge_setting(self.params, path_params)
        # Trim to only path parameters
        path_params = {param: path_params[param] for param in path_params_list}
        # Remove path parameters from self.params, if any
        if self.params:
            for param in path_params:
                try:
                    self.params.pop(param)
                except KeyError:
                    pass
        self.path_params = path_params

    def set_params(self, params: dict) -> None:
        """
        Replace Endpoint 'params' with new parameters.
        This method overwrites default parameters defined at Endpoint instantiation.

        Args:
            params (dict): New parameters to be set.
        """
        self.params = params
        self._set_path_params()

    def set_body(self, body: dict) -> None:
        """
        Update the body for the Endpoint.

        Args:
            body (dict): New body to be set.
        """
        self.body = body

    def merge_params(self, params: dict) -> None:
        """
        Merge Endpoint 'params' with new parameters.
        This method replaces existing parameter values with new ones, and preserves the rest.

        Args:
            params (dict): New parameters to be merged.
        """
        self.params = _merge_setting(params, self.params)
        self._set_path_params()

    def merge_headers(self, headers: dict) -> None:
        """
        Merge Endpoint 'headers' with new headers.
        This method replaces existing header values with new ones, and preserves the rest.
        It is preferred over manual assignment to avoid losing default headers.

        Args:
            headers (dict): New headers to be merged.
        """
        self.headers = _merge_setting(headers, self.headers)

    def request(
        self,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        files: Optional[dict] = None,
        timeout: Optional[int] = None,
        stream: Optional[bool] = None,
    ) -> Response:
        """Sends an HTTP request with the current Endpoint configuration or with the provided parameters.
        Explicit parameters passed to this method takes precedence over default attributes at the Endpoint level.

        Args:
            params (Optional[dict], optional): Path and/or Query parameters. Defaults to None.
            body (Optional[dict], optional): Body payload for PUT and POST methods. Defaults to None.
            headers (Optional[dict], optional): Headers. Defaults to None.
            files (Optional[dict], optional): Files to pass as payload. Defaults to None.
            timeout (Optional[int], optional): Timeout parameter. Defaults to None.
            stream (Optional[bool], optional): Stream flag. Defaults to None.

        Returns:
            Response: Response object from the request.

        To learn more, please refer to the [requests.Session.request documentation](https://requests.readthedocs.io/en/latest/api/#requests.Session.request).
        """
        if params:
            # Retrieve path parameters passed explicitly in the request
            path_params = {
                param: value
                for param, value in params.items()
                if param in self.path_params
            }
            # And remove them from explicitly passed parameters
            for param in path_params:
                params.pop(param)
            # Merge with default path parameters, if any
            path_params = _merge_setting(path_params, self.path_params)
        else:
            path_params = self.path_params
        # Format endpoint
        endpoint = self.endpoint.format(**path_params)
        resp = super().request(
            endpoint=endpoint,
            params=params,
            body=body,
            headers=headers,
            files=files,
            timeout=timeout,
            stream=stream,
        )
        return resp

    def to_pandas(
        self,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        stream=False,
        **kwargs,
    ):
        """
        Returns a pandas DataFrame from the response.
        This method sends a request and attempts to parse the response as a pandas DataFrame.

        Args:
            params (Optional[dict], optional): Path and/or Query parameters. Defaults to None.
            body (Optional[dict], optional): Body payload for PUT and POST methods. Defaults to None.
            stream (bool, optional): Stream flag. Defaults to False.
        """
        try:
            resp = self.request(params=params, body=body, stream=stream, **kwargs)
        except Exception as e:
            raise ValueError(f"An error occurred while sending the request: {e}")
        return json_response_to_pandas(resp)
