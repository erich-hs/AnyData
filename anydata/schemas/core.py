import copy
from typing import Optional
from requests.sessions import Session
from collections.abc import MutableMapping
from requests.sessions import Session, merge_setting

class ABCDataAPI(MutableMapping):
    '''
    Abstract Base Class for DataAPI
    '''
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            raise KeyError(f"Endpoint '{key}' not found")

    def __delitem__(self, key):
        try:
            del self.__dict__[key]
        except KeyError:
            raise KeyError(f"Endpoint '{key}' not found")

    def __iter__(self):
        raise NotImplementedError("Object of type DataAPI is not iterable")

    def __len__(self):
        raise TypeError("Object of type DataAPI has no len()")

class EndpointSession(Session):
    '''
    Base Class for Endpoint.

    Wrapper around requests.Session with a fixed endpoint (relative URL) and list of
    available methods.
    '''
    def __init__(
            self,
            base_url: str,
            endpoint: str,
            method: str,
            params: Optional[dict] = None,  # super: {}
            body: Optional[dict] = None,    # renaming from Session.data
            headers: Optional[dict] = None, # super: default_headers()
            cookies: Optional[dict] = None, # super: cookiejar_from_dict({})
            files: Optional[dict] = None,
            auth: Optional[dict] = None,    # super: None
            timeout: Optional[int] = None,
            allow_redirects: Optional[bool] = True,
            proxies: Optional[dict] = None, # super: {}
            stream: Optional[bool] = False, # super: False
            verify: Optional[bool] = True,  # super: True
            cert: Optional[str] = None,     # super: None
    ):
        self.base_url = base_url
        self.endpoint = endpoint
        self.method = method
        self.body = body
        self.files = files
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        # Holding custom cookies, and proxies to be merged at request time
        self._cookies = cookies
        self._proxies = proxies
        # Session.__init__() sets default headers, default hooks,
        # max_redirects, and initialize an empty cookie jar
        # It also initialize and mount adapters
        super().__init__()
        # Override defaults from Session.__init__()
        # Update default headers with user defined headers
        self.headers = merge_setting(headers, self.headers)
        self.params = copy.deepcopy(params)
        self.auth = auth
        self.stream = stream
        self.verify = verify
        self.cert = cert

    def request(
            self,
            endpoint: Optional[str] = None,
            params: Optional[dict] = None,
            body: Optional[dict] = None,
            headers: Optional[dict] = None,
            files: Optional[dict] = None,
            timeout: Optional[int] = None,
            stream: Optional[bool] = False
    ):
        '''
        At request time, you can redefine:
        - endpoint: relative URL
        - params: query string parameters
        - body: request body
        - headers: request headers
        - files: files to be sent with the request
        - timeout: request timeout
        - stream: flag to set stream mode
        All other parameters are set at session creation time.
        '''

        # If 'endpoint' is not explicitly defined, use the default endpoint
        if not endpoint:
            endpoint = self.endpoint

        # Submits user defined 'params', 'body', 'headers', 'files',
        # and 'timeout' settings to Session.request().
        # Session.request() handles a merge of explict settings on request time
        # and settings defined at Session via merge_setting() function.
        resp = super().request(
            method=self.method,
            url=self.base_url+endpoint,
            params=params or self.params,
            data=body or self.body,
            headers=headers or self.headers,
            cookies=self._cookies,
            files=files or self.files,
            auth=self.auth,
            timeout=timeout or self.timeout,
            allow_redirects=self.allow_redirects,
            proxies=self._proxies,
            hooks=self.hooks,
            stream=stream or self.stream,
            verify=self.verify,
            cert=self.cert
        )
        return resp