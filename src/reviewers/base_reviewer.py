#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseReviewer(ABC):
    """Base class for all code reviewers.
    
    This abstract class defines the interface that all reviewers must implement.
    It provides common functionality and ensures consistent behavior across
    different types of reviewers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the base reviewer.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f'pr_review.{self.__class__.__name__}')
        self.issues = []
    
    @abstractmethod
    def review_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Review a single file and return a list of issues.
        
        Args:
            file_path (str): Path to the file being reviewed
            content (str): Content of the file
            
        Returns:
            List[Dict[str, Any]]: List of issues found in the file
        """
        pass
    
    def get_issues(self) -> List[Dict[str, Any]]:
        """Get all issues found by this reviewer.
        
        Returns:
            List[Dict[str, Any]]: List of all issues
        """
        return self.issues
    
    def clear_issues(self) -> None:
        """Clear all issues."""
        self.issues = []
    
    def add_issue(self, file_path: str, line: Optional[int], message: str, 
                 severity: str, suggestion: Optional[str] = None) -> None:
        """Add an issue to the list of issues.
        
        Args:
            file_path (str): Path to the file where the issue was found
            line (Optional[int]): Line number where the issue was found, or None for file-level issues
            message (str): Description of the issue
            severity (str): Severity of the issue (critical, high, medium, low, info)
            suggestion (Optional[str]): Suggested fix for the issue
        """
        issue = {
            'file': file_path,
            'line': line,
            'message': message,
            'severity': severity,
            'suggestion': suggestion
        }
        self.issues.append(issue)
        
        # Log the issue
        log_message = f"{severity.upper()} issue in {file_path}"
        if line is not None:
            log_message += f" at line {line}"
        log_message += f": {message}"
        
        if severity == 'critical':
            self.logger.critical(log_message)
        elif severity == 'high':
            self.logger.error(log_message)
        elif severity == 'medium':
            self.logger.warning(log_message)
        else:  # low or info
            self.logger.info(log_message)