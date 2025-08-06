#!/usr/bin/env python3

import logging
import os
import subprocess
import re
from typing import List, Dict, Any

from utils.file_utils import get_file_extension

class SecurityReviewer:
    """Reviewer for security vulnerabilities and issues."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Security Reviewer.
        
        Args:
            config (Dict[str, Any]): Configuration for security checking
        """
        self.logger = logging.getLogger('pr_review.security')
        self.config = config
        
        # Common security patterns to check for
        self.security_patterns = {
            'hardcoded_secrets': {
                'pattern': r'(?i)(password|secret|key|token|credential)s?["\s]*[:=]["\s]*[\'"](\w+)[\'"]',
                'message': "Potential hardcoded secret or credential",
                'severity': 'critical'
            },
            'sql_injection': {
                'pattern': r'(?i)execute\s*\(.*\+\s*.*\)|.*\.raw\(.*\+\s*.*\)',
                'message': "Potential SQL injection vulnerability",
                'severity': 'critical'
            },
            'command_injection': {
                'pattern': r'(?i)(os\.system|subprocess\.call|exec|eval)\s*\(.*\+\s*.*\)',
                'message': "Potential command injection vulnerability",
                'severity': 'critical'
            },
            'xss': {
                'pattern': r'(?i)innerHTML|document\.write\s*\(.*\+\s*.*\)',
                'message': "Potential XSS vulnerability",
                'severity': 'high'
            },
            'insecure_random': {
                'pattern': r'(?i)Math\.random\(\)|random\.random\(\)',
                'message': "Use of insecure random number generator",
                'severity': 'medium'
            },
            'debug_code': {
                'pattern': r'(?i)(console\.log|print|debug|todo|fixme)',
                'message': "Debug code or comment found",
                'severity': 'low'
            }
        }
    
    def review(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review files for security issues.
        
        Args:
            files (List[Dict[str, Any]]): List of files to review
            
        Returns:
            Dict[str, Any]: Review results
        """
        self.logger.info(f"Reviewing {len(files)} files for security issues")
        
        issues = []
        
        for file in files:
            filename = file['local_path']  # Path to downloaded file
            if not os.path.exists(filename):
                self.logger.warning(f"File not found for security review: {filename}")
                continue
                
            # Get file extension
            ext = get_file_extension(filename)
            
            # Run pattern-based checks on all files
            pattern_issues = self._check_security_patterns(filename, file['filename'])
            issues.extend(pattern_issues)
            
            # Run tool-based checks based on file type
            if ext.lower() in ['.py']:
                issues.extend(self._check_python_security(filename, file['filename']))
            elif ext.lower() in ['.js', '.jsx', '.ts', '.tsx']:
                issues.extend(self._check_javascript_security(filename, file['filename']))
            elif ext.lower() in ['.java']:
                issues.extend(self._check_java_security(filename, file['filename']))
        
        return {
            'issues': issues,
            'count': len(issues)
        }
    
    def _check_security_patterns(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check file for common security patterns.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of security issues
        """
        issues = []
        
        try:
            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
                for check_name, check_info in self.security_patterns.items():
                    pattern = check_info['pattern']
                    message = check_info['message']
                    severity = check_info['severity']
                    
                    # Check each line for the pattern
                    for i, line in enumerate(lines):
                        matches = re.findall(pattern, line)
                        if matches:
                            issues.append({
                                'file': repo_path,
                                'line': i + 1,
                                'message': message,
                                'severity': severity,
                                'type': 'security',
                                'code': check_name,
                                'suggestion': self._get_suggestion(check_name)
                            })
        except Exception as e:
            self.logger.error(f"Error checking security patterns in {local_path}: {str(e)}")
        
        return issues
    
    def _check_python_security(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check Python file for security issues using bandit.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of security issues
        """
        issues = []
        
        try:
            result = subprocess.run(
                ['bandit', '-f', 'json', '-o', '-', local_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse bandit output (JSON format)
            import json
            bandit_results = json.loads(result.stdout)
            
            for result in bandit_results.get('results', []):
                severity = 'low'  # Default severity
                if result.get('issue_severity') == 'HIGH':
                    severity = 'high'
                elif result.get('issue_severity') == 'MEDIUM':
                    severity = 'medium'
                elif result.get('issue_severity') == 'LOW':
                    severity = 'low'
                
                issues.append({
                    'file': repo_path,
                    'line': result.get('line_number', 0),
                    'message': f"Security issue: {result.get('issue_text', '')}",
                    'severity': severity,
                    'type': 'security',
                    'code': result.get('test_id', 'unknown'),
                    'suggestion': result.get('more_info', '')
                })
        except Exception as e:
            self.logger.error(f"Error running bandit on {local_path}: {str(e)}")
        
        return issues
    
    def _check_javascript_security(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check JavaScript/TypeScript file for security issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of security issues
        """
        # Placeholder for JavaScript security checking
        # In a real implementation, you would use a tool like npm audit or eslint-plugin-security
        return []
    
    def _check_java_security(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check Java file for security issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of security issues
        """
        # Placeholder for Java security checking
        # In a real implementation, you would use a tool like SpotBugs or FindSecBugs
        return []
    
    def _get_suggestion(self, check_name: str) -> str:
        """Get a suggestion for fixing a security issue.
        
        Args:
            check_name (str): Name of the security check
            
        Returns:
            str: Suggestion for fixing the issue
        """
        suggestions = {
            'hardcoded_secrets': "Store secrets in environment variables or a secure vault",
            'sql_injection': "Use parameterized queries or an ORM instead of string concatenation",
            'command_injection': "Use safe APIs or validate and sanitize user input before using it in commands",
            'xss': "Use safe APIs or sanitize user input before inserting it into HTML",
            'insecure_random': "Use a cryptographically secure random number generator",
            'debug_code': "Remove debug code before production deployment"
        }
        
        return suggestions.get(check_name, "Review and fix the security issue")