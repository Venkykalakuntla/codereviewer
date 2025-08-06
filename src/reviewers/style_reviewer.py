#!/usr/bin/env python3

import logging
import os
import subprocess
from typing import List, Dict, Any

from utils.file_utils import get_file_extension

class StyleReviewer:
    """Reviewer for code style and formatting issues."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Style Reviewer.
        
        Args:
            config (Dict[str, Any]): Configuration for style checking
        """
        self.logger = logging.getLogger('pr_review.style')
        self.config = config
        self.severity_map = {
            'error': 'high',
            'warning': 'medium',
            'convention': 'low',
            'refactor': 'info'
        }
    
    def review(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review files for style issues.
        
        Args:
            files (List[Dict[str, Any]]): List of files to review
            
        Returns:
            Dict[str, Any]: Review results
        """
        self.logger.info(f"Reviewing {len(files)} files for style issues")
        
        issues = []
        
        for file in files:
            filename = file['local_path']  # Path to downloaded file
            if not os.path.exists(filename):
                self.logger.warning(f"File not found for style review: {filename}")
                continue
                
            # Get file extension
            ext = get_file_extension(filename)
            
            # Review based on file type
            if ext.lower() in ['.py']:
                issues.extend(self._review_python_file(filename, file['filename']))
            elif ext.lower() in ['.js', '.jsx', '.ts', '.tsx']:
                issues.extend(self._review_javascript_file(filename, file['filename']))
            elif ext.lower() in ['.java']:
                issues.extend(self._review_java_file(filename, file['filename']))
            elif ext.lower() in ['.go']:
                issues.extend(self._review_go_file(filename, file['filename']))
            elif ext.lower() in ['.rb']:
                issues.extend(self._review_ruby_file(filename, file['filename']))
            elif ext.lower() in ['.php']:
                issues.extend(self._review_php_file(filename, file['filename']))
            elif ext.lower() in ['.c', '.cpp', '.h', '.hpp']:
                issues.extend(self._review_cpp_file(filename, file['filename']))
        
        return {
            'issues': issues,
            'count': len(issues)
        }
    
    def _review_python_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a Python file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        issues = []
        
        # Run flake8
        try:
            result = subprocess.run(
                ['flake8', '--format=%(path)s:%(row)d:%(col)d:%(code)s:%(text)s', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse flake8 output
            for line in result.stdout.splitlines():
                parts = line.split(':', 4)
                if len(parts) < 5:
                    continue
                    
                _, line_num, col, code, message = parts
                
                # Determine severity based on error code
                severity = 'low'  # Default severity
                if code.startswith('E'):
                    severity = 'medium'
                elif code.startswith('F'):
                    severity = 'high'
                
                issues.append({
                    'file': repo_path,
                    'line': int(line_num),
                    'column': int(col),
                    'code': code,
                    'message': f"Style issue: {message.strip()}",
                    'severity': severity,
                    'type': 'style'
                })
        except Exception as e:
            self.logger.error(f"Error running flake8 on {local_path}: {str(e)}")
        
        # Run pylint
        try:
            result = subprocess.run(
                ['pylint', '--output-format=text', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse pylint output
            for line in result.stdout.splitlines():
                if ':' not in line or 'Your code has been rated at' in line:
                    continue
                    
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue
                    
                file_line, code, message = parts
                
                # Extract line number
                line_parts = file_line.split(':')
                if len(line_parts) < 2:
                    continue
                    
                line_num = line_parts[-1]
                
                # Determine severity based on message type
                severity = 'low'  # Default severity
                if '[E' in code:
                    severity = 'high'
                elif '[W' in code:
                    severity = 'medium'
                elif '[C' in code:
                    severity = 'low'
                elif '[R' in code:
                    severity = 'info'
                
                issues.append({
                    'file': repo_path,
                    'line': int(line_num),
                    'code': code.strip(),
                    'message': f"Lint issue: {message.strip()}",
                    'severity': severity,
                    'type': 'lint'
                })
        except Exception as e:
            self.logger.error(f"Error running pylint on {local_path}: {str(e)}")
        
        return issues
    
    def _review_javascript_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a JavaScript/TypeScript file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        issues = []
        
        # Check if ESLint is available
        try:
            result = subprocess.run(
                ['eslint', '--format=json', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse ESLint output (JSON format)
            import json
            eslint_results = json.loads(result.stdout)
            
            for file_result in eslint_results:
                for message in file_result.get('messages', []):
                    severity = 'low'  # Default severity
                    if message.get('severity') == 2:  # Error
                        severity = 'medium'
                    elif message.get('severity') == 1:  # Warning
                        severity = 'low'
                    
                    issues.append({
                        'file': repo_path,
                        'line': message.get('line', 0),
                        'column': message.get('column', 0),
                        'code': message.get('ruleId', 'unknown'),
                        'message': f"Style issue: {message.get('message', '')}",
                        'severity': severity,
                        'type': 'style'
                    })
        except Exception as e:
            self.logger.error(f"Error running ESLint on {local_path}: {str(e)}")
        
        return issues
    
    def _review_java_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a Java file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        # Placeholder for Java style checking
        # In a real implementation, you would use a tool like Checkstyle
        return []
    
    def _review_go_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a Go file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        issues = []
        
        # Run gofmt to check formatting
        try:
            result = subprocess.run(
                ['gofmt', '-d', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.stdout.strip():
                issues.append({
                    'file': repo_path,
                    'message': "Code is not properly formatted according to gofmt",
                    'severity': 'low',
                    'type': 'style',
                    'suggestion': "Run 'gofmt -w' to format the file"
                })
        except Exception as e:
            self.logger.error(f"Error running gofmt on {local_path}: {str(e)}")
        
        # Run golint
        try:
            result = subprocess.run(
                ['golint', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            for line in result.stdout.splitlines():
                if ':' not in line:
                    continue
                    
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue
                    
                _, line_num, message = parts
                
                issues.append({
                    'file': repo_path,
                    'line': int(line_num),
                    'message': f"Lint issue: {message.strip()}",
                    'severity': 'low',
                    'type': 'lint'
                })
        except Exception as e:
            self.logger.error(f"Error running golint on {local_path}: {str(e)}")
        
        return issues
    
    def _review_ruby_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a Ruby file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        # Placeholder for Ruby style checking
        # In a real implementation, you would use a tool like RuboCop
        return []
    
    def _review_php_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a PHP file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        # Placeholder for PHP style checking
        # In a real implementation, you would use a tool like PHP_CodeSniffer
        return []
    
    def _review_cpp_file(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Review a C/C++ file for style issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of style issues
        """
        # Placeholder for C/C++ style checking
        # In a real implementation, you would use a tool like clang-format
        return []