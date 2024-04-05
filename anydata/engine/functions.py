from typing import Optional
import guidance
from guidance import gen, system, user, assistant, select
from ..parsers.openapi import OpenAPI
from ..engine.prompts.system_prompts import (
    RELATIVE_URL_FETCHER,
    REST_API_OPERATION_FETCHER,
    REST_API_PARAMETERS_FETCHER,
)
from ..engine.prompts.user_prompts import (
    relative_url_user_prompt,
    rest_api_operation_user_prompt,
    rest_api_parameters_user_prompt,
)


# %% Chaining guidance operations
@guidance
def dataapi_from_prompt(
    lm: guidance.models.Model, prompt: str, openapi: OpenAPI
) -> guidance.models.Model:
    """
    Chain guidance operations to:
        1. Retrieve the relative URL for an endpoint from the 'openapi' to fulfill the 'prompt'.
        2. Retrieve the REST API operation for the endpoint from the 'openapi' to fulfill the 'prompt'.
        3. Retrieve the REST API parameters for the endpoint from the 'openapi' to fulfill the 'prompt'.
    """
    assert isinstance(openapi, OpenAPI), "openapi must be a valid OpenAPI object."
    lm += relative_url_from_openapi(prompt, openapi)
    lm += rest_api_operation_from_openapi(prompt, openapi)
    lm += rest_api_parameters_from_openapi(prompt, openapi)
    return lm


@guidance
def retry_dataapi_from_prompt(
    lm: guidance.models.Model, prompt: str, openapi: OpenAPI
) -> guidance.models.Model:
    """
    Retries a failed dataapi_from_prompt operation with instructions from a failed response.
    """
    assert isinstance(openapi, OpenAPI), "openapi must be a valid OpenAPI object."


# %% Base guidance operations
@guidance
def relative_url_from_openapi(
    lm: guidance.models.Model, prompt: str, openapi: OpenAPI
) -> guidance.models.Model:
    """
    Returns a guidance lm model carrying a relative URL for the endpoint at the 'endpoint' variable.
    """
    endpoints = list(openapi.paths)
    # endpoints_summary = yaml.dump(openapi.summary())
    endpoints_summary = openapi.summary()
    with system():
        lm += RELATIVE_URL_FETCHER
    with user():
        lm += relative_url_user_prompt(prompt, endpoints_summary, endpoints)
    with assistant():
        lm += select(endpoints, name="endpoint")
    return lm


@guidance
def rest_api_operation_from_openapi(
    lm: guidance.models.Model,
    prompt: str,
    openapi: OpenAPI,
    endpoint: Optional[str] = None,
) -> guidance.models.Model:
    """
    Returns a guidance lm model carrying a REST API operation for the endpoint at the 'method' variable.
    """
    if not endpoint:
        assert (
            "endpoint" in lm
        ), "If 'endpoint' is not provided, it must be captured at the 'endpoint' variable in the lm model."
        endpoint = lm["endpoint"]
    # endpoint_summary = yaml.dump(openapi.paths_summary()[endpoint])
    endpoint_summary = openapi.paths_summary()[endpoint]
    endpoint_methods = dict(openapi.endpoint_methods)[endpoint]
    with system():
        lm += REST_API_OPERATION_FETCHER
    with user():
        lm += rest_api_operation_user_prompt(prompt, endpoint, endpoint_summary)
    with assistant():
        lm += select(endpoint_methods, name="method")
    return lm


@guidance
def rest_api_parameters_from_openapi(
    lm: guidance.models.Model,
    prompt: str,
    openapi: OpenAPI,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    temperature: Optional[float] = 0.0,
) -> guidance.models.Model:
    """
    Returns a guidance lm model carrying a JSON object with key value pairs for the parameters needed to call the endpoint.
    """
    if not endpoint:
        assert (
            "endpoint" in lm
        ), "If 'endpoint' is not provided, it must be captured at the 'endpoint' variable in the lm model."
        endpoint = lm["endpoint"]
    if not method:
        assert (
            "method" in lm
        ), "If 'method' is not provided, it must be captured at the 'method' variable in the lm model."
        method = lm["method"]
    # method_openapi = yaml.dump(openapi.paths_summary(resolve_parameter_references=True)[endpoint][method])
    method_openapi = openapi.paths_summary(resolve_parameter_references=True)[endpoint][
        method
    ]
    with system():
        lm += REST_API_PARAMETERS_FETCHER
    with user():
        lm += rest_api_parameters_user_prompt(prompt, endpoint, method_openapi)
    with assistant():
        lm += gen(name="parameters", temperature=temperature)
    return lm


@guidance
def evaluate_unsuccessful_response(
    lm: guidance.models.Model,
    prompt: str,
    response: dict,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    parameters: Optional[dict] = None,
) -> guidance.models.Model:
    """
    Evaluates the response from a REST API call and raises an error if the response is unsuccessful.
    """
    if not endpoint:
        assert (
            "endpoint" in lm
        ), "If 'endpoint' is not provided, it must be captured at the 'endpoint' variable in the lm model."
        endpoint = lm["endpoint"]
    if not method:
        assert (
            "method" in lm
        ), "If 'method' is not provided, it must be captured at the 'method' variable in the lm model."
        method = lm["method"]
    if not parameters:
        assert (
            "parameters" in lm
        ), "If 'parameters' is not provided, it must be captured at the 'parameters' variable in the lm model."
        parameters = lm["parameters"]
    with system():
        lm += """
You only reply with a number corresponding to one of the following options:
    1. The parameters provided are incorrect.
    2. The REST API operation is incorrect.
    3. The endpoint is incorrect.
        """
    with user():
        lm += f"""
When attempting to retrieve data for the prompt '{prompt}', a '{method}' request was made to the endpoint '{endpoint}' with the following parameters:
{parameters}
The request receive an unsuccessful response with status code '{response.status_code}' and the following content:
{response.text}
What do you think is the reason for the unsuccessful response?
        """
    with assistant():
        lm += select([1, 2, 3], name="reason")
    return lm
