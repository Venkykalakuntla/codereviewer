#!/usr/bin/env python3

import os
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from github.client import GitHubClient

class TestGitHubClient(unittest.TestCase):
    """Test cases for the GitHub client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.token = 'test_token'
        self.owner = 'test_owner'
        self.repo = 'test_repo'
        self.client = GitHubClient(self.token, self.owner, self.repo)
    
    @patch('github.client.requests.get')
    def test_list_pull_requests(self, mock_get):
        """Test listing pull requests."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'number': 1, 'title': 'Test PR 1'},
            {'number': 2, 'title': 'Test PR 2'}
        ]
        mock_get.return_value = mock_response
        
        # Call the method
        prs = self.client.list_pull_requests()
        
        # Assertions
        self.assertEqual(len(prs), 2)
        self.assertEqual(prs[0]['number'], 1)
        self.assertEqual(prs[0]['title'], 'Test PR 1')
        self.assertEqual(prs[1]['number'], 2)
        self.assertEqual(prs[1]['title'], 'Test PR 2')
        
        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(f'https://api.github.com/repos/{self.owner}/{self.repo}/pulls', args[0])
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['headers']['Authorization'], f'token {self.token}')
    
    @patch('github.client.requests.get')
    def test_get_pull_request(self, mock_get):
        """Test getting a single pull request."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'number': 1,
            'title': 'Test PR',
            'user': {'login': 'test_user'},
            'body': 'Test PR description'
        }
        mock_get.return_value = mock_response
        
        # Call the method
        pr = self.client.get_pull_request(1)
        
        # Assertions
        self.assertEqual(pr['number'], 1)
        self.assertEqual(pr['title'], 'Test PR')
        self.assertEqual(pr['user']['login'], 'test_user')
        
        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(f'https://api.github.com/repos/{self.owner}/{self.repo}/pulls/1', args[0])
    
    @patch('github.client.requests.get')
    def test_get_pull_request_files(self, mock_get):
        """Test getting files from a pull request."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'filename': 'test_file.py',
                'status': 'modified',
                'additions': 10,
                'deletions': 5,
                'changes': 15
            }
        ]
        mock_get.return_value = mock_response
        
        # Call the method
        files = self.client.get_pull_request_files(1)
        
        # Assertions
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['filename'], 'test_file.py')
        self.assertEqual(files[0]['status'], 'modified')
        
        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(f'https://api.github.com/repos/{self.owner}/{self.repo}/pulls/1/files', args[0])

if __name__ == '__main__':
    unittest.main()