from requests.models import Response
from typing import Union

try:
    import pandas as pd

    is_pandas = True
except ImportError:
    is_pandas = False


def dataframe_from_array_of_dicts(array: list) -> "pd.DataFrame":
    """
    Returns a pandas DataFrame from an array of dictionaries.
    """
    if not is_pandas:
        raise ImportError(
            "Please install the 'pandas' package using `pip install pandas` to use this function."
        )
    try:
        return pd.DataFrame.from_dict(array, orient="columns")
    except Exception as e:
        print(
            f"An error occurred while converting the array of type {type(array)} into a DataFrame: {e}"
        )
        raise


def json_response_to_pandas(response: Response) -> Union["pd.DataFrame", dict]:
    """
    Returns a pandas DataFrame from the response.
    If the response contains more than one array that can be converted into a DataFrame, it returns a dictionary of DataFrames.
    """
    assert isinstance(
        response, Response
    ), "response should be a requests.models.Response object"
    response = response.json()
    # Some APIs return a list of json at the top level. In this case, pass the list to the DataFrame constructor.
    if isinstance(response, list):
        return dataframe_from_array_of_dicts(response)

    # In most cases, the response will be a dictionary. Look for arrays in the response and pass to the DataFrame constructor.
    array_keys = [key for key in response.keys() if isinstance(response[key], list)]
    # Single array found in response
    if len(array_keys) == 1:
        return dataframe_from_array_of_dicts(response[array_keys[0]])
    # Multiple arrays found in response
    elif len(array_keys) > 1:
        dfs = {}
        for key in array_keys:
            dfs[key] = dataframe_from_array_of_dicts(response[key])
        print(
            f"Parser retrieved multiple DataFrames. Returning a dictionary of DataFrames with keys:\n{list(dfs.keys())}"
        )
        return dfs
    else:
        print(f"No arrays found in response with {response.keys()}.")
        return
