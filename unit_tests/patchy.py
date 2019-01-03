import requests
import unittest
from unittest import mock


# This is the class we want to test
class MyGreatClass:
    def post_json(self, endpoint, data):
        response = requests.post(endpoint, json=data)
        return response.json()


# This method will be used by the mock to replace requests.get
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse({'results': [
        {
            'columns': ['key'],
            'data': [
                {'row': ['value']}
            ]
        }
    ]}, 200)


# Our test case class
class MyGreatClassTestCase(unittest.TestCase):

    # We patch 'requests.get' with our own method. The mock object is passed in to our test case method.
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_fetch(self, mock_get):
        # Assert requests.get calls
        mgc = MyGreatClass()
        json_data = mgc.post_json('http://someurl.com/', {'data': ['a', 'b']})
        self.assertEqual(json_data, {"key": [0, 1]})
        json_data = mgc.post_json('http://someurl.com/', {'data': ['a']})
        self.assertEqual(json_data, {"key": [0]})

        # We can even assert that our mocked method was called with the right parameters
        # self.assertIn(mock.call('http://someurl.com/test.json'), mock_get.call_args_list)
        # self.assertIn(mock.call('http://someotherurl.com/anothertest.json'), mock_get.call_args_list)

        # self.assertEqual(len(mock_get.call_args_list), 3)


if __name__ == '__main__':
    unittest.main()
