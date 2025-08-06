#!/usr/bin/env python3

import logging
import os
from typing import List, Dict, Any, Optional
import openai

from utils.file_utils import get_file_extension
from reviewers.base_reviewer import BaseReviewer

class LLMReviewer(BaseReviewer):
    """Reviewer that uses LLM to provide intelligent code review."""
    
    def _init_(self, config: Dict[str, Any]):
        """Initialize the LLM Reviewer.
        
        Args:
            config (Dict[str, Any]): Configuration for LLM-based reviewing
        """
        super()._init_(config)
        self.logger = logging.getLogger('pr_review.llm')
        self.config = config
        
        # Get API key from environment variable
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key and not config.get('api_key'):
            self.logger.warning("No OpenAI API key found. LLM reviewer will be disabled.")
        elif config.get('api_key'):
            self.api_key = config.get('api_key')
            
        # Set up OpenAI client if API key is available
        if self.api_key:
            openai.api_key = self.api_key
        
        # Default model to use
        self.model = config.get('model', 'gpt-3.5-turbo')
        
        # Maximum tokens to use in requests
        self.max_tokens = config.get('max_tokens', 1000)
        
        # Temperature for generation
        self.temperature = config.get('temperature', 0.3)
        
        # Supported file extensions
        self.supported_extensions = config.get('supported_extensions', [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.html', '.css', '.scss', '.md'
        ])
    
    def review(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review files using LLM.
        
        Args:
            files (List[Dict[str, Any]]): List of files to review
            
        Returns:
            Dict[str, Any]: Review results
        """
        self.logger.info(f"Reviewing {len(files)} files using LLM")
        
        # Clear previous issues
        self.clear_issues()
        
        # Skip review if no API key is available
        if not self.api_key:
            self.logger.warning("Skipping LLM review due to missing API key")
            return {
                'issues': [],
                'count': 0
            }
        
        for file in files:
            filename = file['local_path']  # Path to downloaded file
            if not os.path.exists(filename):
                self.logger.warning(f"File not found for LLM review: {filename}")
                continue
                
            # Get file extension
            ext = get_file_extension(filename)
            
            # Skip unsupported file types
            if ext.lower() not in self.supported_extensions:
                self.logger.debug(f"Skipping unsupported file type: {filename}")
                continue
            
            # Read file content
            try:
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Review file with LLM
                file_issues = self.review_file(file['filename'], content)
                
                # Add issues to the list
                for issue in file_issues:
                    self.add_issue(
                        file_path=file['filename'],
                        line=issue.get('line'),
                        message=issue.get('message'),
                        severity=issue.get('severity', 'medium'),
                        suggestion=issue.get('suggestion')
                    )
                    
            except Exception as e:
                self.logger.error(f"Error reviewing file {filename}: {str(e)}")
        
        return {
            'issues': self.get_issues(),
            'count': len(self.get_issues())
        }
    
    def review_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Review a single file using LLM and return a list of issues.
        
        Args:
            file_path (str): Path to the file being reviewed
            content (str): Content of the file
            
        Returns:
            List[Dict[str, Any]]: List of issues found in the file
        """
        issues = []
        
        # Skip if content is too large
        if len(content) > 10000:  # Limit to ~10KB to avoid token limits
            self.logger.warning(f"File {file_path} is too large for LLM review, truncating")
            content = content[:10000] + "\n... (truncated)"
        
        # Prepare prompt for the LLM
        prompt = self._create_review_prompt(file_path, content)
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer. Analyze the code and provide specific, actionable feedback on bugs, security issues, performance problems, and code quality issues. Format each issue as a JSON object with 'line', 'message', 'severity', and 'suggestion' fields."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            result = response.choices[0].message.content.strip()
            
            # Extract issues from the response
            extracted_issues = self._extract_issues_from_response(result)
            issues.extend(extracted_issues)
            
        except Exception as e:
            self.logger.error(f"Error calling LLM API for {file_path}: {str(e)}")
        
        return issues
    
    def _create_review_prompt(self, file_path: str, content: str) -> str:
        """Create a prompt for the LLM to review the code.
        
        Args:
            file_path (str): Path to the file
            content (str): Content of the file
            
        Returns:
            str: Prompt for the LLM
        """
        # Get file extension
        ext = get_file_extension(file_path)
        
        # Create prompt
        prompt = f"""Please review the following {ext} code file: {file_path}

{ext}
{content}


Provide a detailed code review focusing on:
1. Bugs and logical errors
2. Security vulnerabilities
3. Performance issues
4. Code quality and maintainability problems
5. Best practices violations

For each issue, provide:
- The line number where the issue occurs
- A clear description of the problem
- The severity (critical, high, medium, low, or info)
- A specific suggestion for how to fix it

Format your response as a list of JSON objects, one per issue, with the following structure:
{{
  "line": <line_number>,
  "message": "<description of the issue>",
  "severity": "<severity level>",
  "suggestion": "<how to fix it>"
}}

If no issues are found, return an empty list: []
"""
        
        return prompt
    
    def _extract_issues_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extract issues from the LLM response.
        
        Args:
            response (str): Response from the LLM
            
        Returns:
            List[Dict[str, Any]]: Extracted issues
        """
        issues = []
        
        try:
            # Try to find JSON in the response
            import json
            import re
            
            # Look for JSON arrays in the response
            json_pattern = r'\[\s*{.}\s\]'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                parsed_issues = json.loads(json_str)
                
                # Validate and clean up issues
                for issue in parsed_issues:
                    if 'message' in issue and 'severity' in issue:
                        # Ensure severity is valid
                        if issue['severity'] not in ['critical', 'high', 'medium', 'low', 'info']:
                            issue['severity'] = 'medium'
                        
                        # Add to issues list
                        issues.append(issue)
            else:
                # Fallback: try to extract structured information from text
                lines = response.split('\n')
                current_issue = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for line number indicators
                    line_match = re.search(r'line\s*(\d+)', line, re.IGNORECASE)
                    if line_match and 'line' not in current_issue:
                        current_issue['line'] = int(line_match.group(1))
                    
                    # Look for severity indicators
                    for severity in ['critical', 'high', 'medium', 'low', 'info']:
                        if severity in line.lower() and 'severity' not in current_issue:
                            current_issue['severity'] = severity
                            break
                    
                    # If we have enough info, create an issue
                    if len(current_issue) >= 2 and 'message' not in current_issue:
                        current_issue['message'] = line
                        current_issue['suggestion'] = "Review and fix the identified issue."
                        issues.append(current_issue)
                        current_issue = {}
        
        except Exception as e:
            self.logger.error(f"Error extracting issues from LLM response: {str(e)}")
        
        return issues