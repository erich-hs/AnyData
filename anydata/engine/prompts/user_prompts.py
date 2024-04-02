def relative_url_user_prompt(prompt: str, openapi: str, endpoints: list):
    return f"""Given the following OpenAPI specification, which endpoint should I use to return data for the prompt '{prompt}'?

{openapi}

Choose one from the following endpoints:
{endpoints}

If the endpoint contains path parameters, do not replace them with the parameter values, return the parameter name within curly braces.
    """

def rest_api_operation_user_prompt(prompt: str, endpoint: str, openapi: str):
    return f'''Given the following OpenAPI specification, which REST API method should I use when calling the endpoint {endpoint} to fulfill the prompt '{prompt}'?

{openapi}
    '''

def rest_api_parameters_user_prompt(prompt: str, endpoint: str, openapi: str):
    return f'''Given the following OpenAPI specification, which parameters should I pass when calling the endpoint {endpoint} to return all available data in json format for the prompt '{prompt}'?
Return only required parameters and optional parameters needed to fulfill the prompt '{prompt}'.

{openapi}

If no parameter is needed to fulfill the prompt '{prompt}', return an empty JSON object.
    '''