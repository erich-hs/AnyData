import pytest
import json
import requests
import pandas as pd
from hub.parsers.response_parser import json_response_to_pandas, dataframe_from_array_of_dicts

class MockResponse(requests.models.Response):
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.status_code = 200
    
    def json(self):
        return json.loads(self.response_text)

@pytest.fixture
def single_array_response():
    return MockResponse('[{"field1": "value1", "field2": "value2", "field3": "value3"}]')

@pytest.fixture
def dict_of_single_array_response():
    return MockResponse('{"data": [{"field1": "value1", "field2": "value2", "field3": "value3"}]}')

@pytest.fixture
def multi_array_response():
    return MockResponse('''
{"data": [{"field1": "value1", "field2": "value2", "field3": "value3"}, {"field1": "value4", "field2": "value5", "field3": "value6"}],
"sources": [{"field4": "value4", "field5": "value5", "field6": "value6"}]}
''')

@pytest.fixture
def response_with_no_arrays():
    return MockResponse('{"response_text": "No arrays here."}')

def test_single_array_response_to_pandas(single_array_response):
    df = json_response_to_pandas(single_array_response)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 3)

def test_dict_of_single_array_response_to_pandas(dict_of_single_array_response):
    df = json_response_to_pandas(dict_of_single_array_response)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 3)

def test_multiple_arrays_response_to_pandas(multi_array_response):
    dfs = json_response_to_pandas(multi_array_response)
    assert isinstance(dfs, dict)
    assert all([isinstance(df, pd.DataFrame) for df in dfs.values()])
    assert all([dfs['data'].shape == (2, 3), dfs['sources'].shape == (1, 3)])

def test_response_with_no_arrays_to_pandas(response_with_no_arrays):
    assert json_response_to_pandas(response_with_no_arrays) is None

def test_failed_array_conversion():
    with pytest.raises(ValueError):
        dataframe_from_array_of_dicts('Not a list of dictionaries')