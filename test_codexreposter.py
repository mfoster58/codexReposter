import unittest
from unittest.mock import patch, Mock
import azure.functions as func
from codexreposter import codexReposter

class TestCodexReposter(unittest.TestCase):
    @patch('codexreposter.requests.post')
    @patch('codexreposter.requests.get')
    def test_codexReposter(self, mock_get, mock_post):
        # Mock the search response
        mock_get.return_value.json.return_value = [
            {'id': 12345},
            {'id': 67890}
        ]
        
        # Mock the repost response
        mock_post.return_value.status_code = 200

        # Create a mock HTTP request
        req = func.HttpRequest(
            method='GET',
            url='/api/codexReposter',
            params={'name': 'TestUser'},
            body=b''
        )

        # Call the function
        resp = codexReposter(req)

        # Check the response
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Hello, TestUser', resp.get_body().decode())

if __name__ == '__main__':
    unittest.main()