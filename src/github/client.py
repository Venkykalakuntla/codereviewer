#!/usr/bin/env python3

import logging
import os
import requests
import tempfile
from typing import List, Dict, Any, Optional

class GitHubClient:
    """Client for interacting with the GitHub API."""
    
    def __init__(self, token: str, owner: str, repo: str):
        """Initialize the GitHub client.
        
        Args:
            token (str): GitHub personal access token
            owner (str): Repository owner/organization
            repo (str): Repository name
        """
        self.logger = logging.getLogger('pr_review.github')
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.logger.debug(f"Initialized GitHub client for {owner}/{repo}")
    
    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Get a specific pull request.
        
        Args:
            pr_number (int): Pull request number
            
        Returns:
            Dict[str, Any]: The pull request data
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            pr_data = response.json()
            self.logger.debug(f"Retrieved PR #{pr_number}: {pr_data.get('title', 'Unknown')}")
            return pr_data
        except Exception as e:
            self.logger.error(f"Error retrieving PR #{pr_number}: {str(e)}")
            raise
    
    def list_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """Get all open pull requests for the repository.
        
        Args:
            state (str, optional): State of PRs to retrieve. Defaults to "open".
            
        Returns:
            List[Dict[str, Any]]: List of pull requests
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/pulls"
            params = {"state": state}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            prs = response.json()
            self.logger.debug(f"Retrieved {len(prs)} {state} pull requests")
            return prs
        except Exception as e:
            self.logger.error(f"Error retrieving {state} PRs: {str(e)}")
            raise
    
    def get_pull_request_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get the files changed in a pull request.
        
        Args:
            pr_number (int): Pull request number
            
        Returns:
            List[Dict[str, Any]]: List of files changed in the PR
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            files = response.json()
            self.logger.debug(f"Retrieved {len(files)} files from PR #{pr_number}")
            return files
        except Exception as e:
            self.logger.error(f"Error retrieving files for PR #{pr_number}: {str(e)}")
            raise
    
    def get_file_content(self, file_path: str, ref: Optional[str] = None) -> str:
        """Get the content of a file from the repository.
        
        Args:
            file_path (str): Path to the file
            ref (str, optional): Git reference (branch, commit, tag). Defaults to None (main branch).
            
        Returns:
            ref (Optional[str], optional): Git reference (branch, tag, commit). Defaults to None.
            
        Returns:
            str: Content of the file
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/contents/{file_path}"
            params = {}
            if ref:
                params["ref"] = ref
                
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            content_data = response.json()
            
            # GitHub API returns base64 encoded content
            import base64
            content = base64.b64decode(content_data["content"]).decode("utf-8")
            
            self.logger.debug(f"Retrieved content for {file_path} at {ref or 'default branch'}")
            return content
        except Exception as e:
            self.logger.error(f"Error retrieving content for {file_path}: {str(e)}")
            raise
    
    def post_review_comment(self, pr_number: int, comment: str) -> None:
        """Post a review comment on a pull request.
        
        Args:
            pr_number (int): Pull request number
            comment (str): Comment text
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"
            data = {"body": comment}
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            self.logger.debug(f"Posted review comment on PR #{pr_number}")
        except Exception as e:
            self.logger.error(f"Error posting review comment on PR #{pr_number}: {str(e)}")
            raise
    
    def post_review(self, pr_number: int, comments: List[Dict[str, Any]], body: str, event: str = 'COMMENT') -> None:
        """Post a review with inline comments on a pull request.
        
        Args:
            pr_number (int): Pull request number
            comments (List[Dict[str, Any]]): List of review comments
                Each comment should have: path, position, body
            body (str): Overall review comment
            event (str, optional): Review event. Defaults to 'COMMENT'.
                Can be 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
        """
        try:
            url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}/reviews"
            data = {
                "comments": comments,
                "body": body,
                "event": event
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            self.logger.debug(f"Posted review with {len(comments)} comments on PR #{pr_number}")
        except Exception as e:
            self.logger.error(f"Error posting review on PR #{pr_number}: {str(e)}")
            raise
    
    def download_file(self, file_path: str, pr_number: int, output_dir: str) -> str:
        """Download a file from a pull request to a local directory.
        
        Args:
            file_path (str): Path to the file in the repository
            pr_number (int): Pull request number
            output_dir (str): Directory to save the file to
            
        Returns:
            str: Path to the downloaded file
        """
        try:
            # Get the PR to determine the head ref
            pr_data = self.get_pull_request(pr_number)
            ref = pr_data.get('head', {}).get('ref')
            
            if not ref:
                self.logger.error(f"Could not determine head ref for PR #{pr_number}")
                raise ValueError(f"Could not determine head ref for PR #{pr_number}")
            
            # Get the file content
            content = self.get_file_content(file_path, ref=ref)
            
            # Create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create the directory structure for the file
            file_dir = os.path.dirname(file_path)
            if file_dir:
                os.makedirs(os.path.join(output_dir, file_dir), exist_ok=True)
            
            # Write the file
            output_path = os.path.join(output_dir, file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Downloaded {file_path} from PR #{pr_number} to {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error downloading {file_path} from PR #{pr_number}: {str(e)}")
            raise