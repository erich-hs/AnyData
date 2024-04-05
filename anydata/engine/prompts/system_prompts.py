REST_API_OPERATIONS_STR = "'get', 'post', 'put', 'delete', 'head', or 'options'"

REST_API_OPERATIONS_LST = ["get", "post", "put", "delete", "head", "options"]

# EXAMPLE_REST_API_PARAMETERS = '''
# {"string_parameter": "string_value", "integer_parameter": 20}
# '''

RELATIVE_URL_FETCHER = """You only reply with a relative url that starts with '/'. If the endpoint contains path parameters, do not replace them with the parameter values, return the parameter name within curly braces. Return the relative url as described in the API documentation. You don't include anything else in your reply, other than the relative url.
"""

REST_API_OPERATION_FETCHER = f"""You only reply with one of the following valid REST API operations {REST_API_OPERATIONS_STR}. You don't include anything else in your reply, other than the REST API operation.
"""

# REST_API_PARAMETERS_FETCHER = f'''You only reply with a json object with key value pairs. The keys are the parameter names and the values are the parameter values for a REST API call to an endpoint.
# Example answer: {EXAMPLE_REST_API_PARAMETERS}
# '''

REST_API_PARAMETERS_FETCHER = """You only reply with a json object with key value pairs. The keys are the parameter names and the values are the parameter values for a REST API call to an endpoint.
"""
