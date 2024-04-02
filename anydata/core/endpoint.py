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

def _merge_setting(new_setting: dict, base_setting: Optional[dict]=None) -> dict:
    assert isinstance(new_setting, Mapping), f"New setting to be merged must be a valid mapping. 'new_setting' provided is of type {type(new_setting)}."
    if base_setting:
        assert isinstance(base_setting, Mapping), f"Base setting to be merged must be a valid mapping. 'base_setting' provided is of type {type(base_setting)}."
        new_setting = copy.deepcopy(new_setting)
        try:
            for key, value in base_setting.items():
                new_setting.setdefault(key, value)
        except AttributeError:
            pass
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
            **kwargs
    ) -> None:
        '''
        Allows for Session-level states such as cookies or custom authentication mechanisms.
        '''
        # Storing custom headers for __repr__ method
        self._custom_headers = headers
        super().__init__(
            base_url=base_url,
            endpoint=endpoint,
            method=method,
            params=params,
            body=body,
            headers=headers,
            **kwargs
        )
        if raise_unsuccessful:
            self.hooks['response'].append(_handle_response_status_code)
        self.alias = alias
        self._set_path_params()

    def __repr__(self) -> str:
        params_str = f'params={self.params}, ' if self.params else ""
        path_params_str = f'path_params={self.path_params}, ' if self.path_params else ""
        body_str = f'body={self.body}, ' if self.body else ""
        headers_str = f'headers={self._custom_headers}, ' if self._custom_headers else ""
        auth_str = f'auth={self.auth}, ' if self.auth else ""
        timeout_str = f'timeout={self.timeout}, ' if self.timeout else ""
        stream_str = f'stream={self.stream}, ' if self.stream else ""
        cert_str = f'cert={self.cert}, ' if self.cert else ""
        return (
            f'Endpoint('
            f'method="{self.method}", '
            f'endpoint="{self.endpoint}", '
            f'{params_str}'
            f'{path_params_str}'
            f'{body_str}'
            f'{headers_str}'
            f'{auth_str}'
            f'{timeout_str}'
            f'{stream_str}'
            f'{cert_str}'
            f')'
        ).replace(", )", ")")

    def _set_path_params(self) -> dict:
        '''
        Sets path parameters from the endpoint URL as a dictionary with parameter names as values.
        If self.params is defined, attempts to assign path parameters values from self.params, deleting them from self.params.
        If self.params is not defined, returns None for each path parameter found in the endpoint relative URL.
        Will match any string between curly braces {} at the endpoint relative URL.
        '''
        path_params = re.findall(r'\{([^{}]+)\}', self.endpoint)
        if self.params:
            path_params_dict = {}
            for parameter in path_params:
                try:
                    path_params_dict[parameter] = self.params[parameter]
                    self.params.pop(parameter)
                except KeyError:
                    path_params_dict[parameter] = None
        else:
            path_params_dict = {param: None for param in path_params}
        if hasattr(self, 'path_params'):
            self.path_params = _merge_setting(path_params_dict, self.path_params)
        else:
            self.path_params = path_params_dict

    def set_params(self, params: dict, reset_path_params: bool=True) -> None:
        '''
        Replace Endpoint 'params' with new parameters.
        This method overwrites default parameters defined at Endpoint instantiation,
        '''
        self.params = params
        if reset_path_params:
            self._set_path_params()
    
    def set_body(self, body: dict) -> None:
        '''
        Update the body for the Endpoint.
        '''
        self.body = body
    
    def merge_params(self, params: dict, reset_path_params: bool=True) -> None:
        '''
        Merge Endpoint 'params' with new parameters.
        This method replaces existing parameter values with new ones, and preserves the rest.
        '''
        self.params = _merge_setting(params, self.params)
        if reset_path_params:
            self._set_path_params()

    def merge_headers(self, headers: dict) -> None:
        '''
        Merge Endpoint 'headers' with new headers.
        This method replaces existing header values with new ones, and preserves the rest.
        It is preferred over manual assignment to avoid losing default headers.
        '''
        self.headers = _merge_setting(headers, self.headers)

    def request(
            self,
            params: Optional[dict] = None,
            path_params: Optional[dict] = None,
            body: Optional[dict] = None,
            headers: Optional[dict] = None,
            files: Optional[dict] = None,
            timeout: Optional[int] = None,
            stream: Optional[bool] = None
    ) -> Response:
        path_params = path_params or {}
        path_params = _merge_setting(path_params, self.path_params)
        endpoint = self.endpoint.format(**path_params)
        resp = super().request(
            endpoint=endpoint,
            params=params,
            body=body,
            headers=headers,
            files=files,
            timeout=timeout,
            stream=stream
        )
        return resp
    
    def to_pandas(
            self,
            params: Optional[dict] = None,
            body: Optional[dict] = None,
            stream=False,
            **kwargs
    ):
        '''
        Returns a pandas DataFrame from the response.
        '''
        try:
            resp = self.request(params=params, body=body, stream=stream, **kwargs)
        except Exception as e:
            raise ValueError(f"An error occurred while sending the request: {e}")
        return json_response_to_pandas(resp)