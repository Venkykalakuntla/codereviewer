#!/usr/bin/env python3

import logging
from typing import List, Dict, Any, Optional
import os
import tempfile
import shutil

from github.client import GitHubClient
from reviewers.style_reviewer import StyleReviewer
from reviewers.security_reviewer import SecurityReviewer
from reviewers.quality_reviewer import QualityReviewer
from utils.file_utils import download_files, get_file_extension

class ReviewManager:
    """Manages the code review process for pull requests."""
    
    def __init__(self, github_client: GitHubClient, config: Dict[str, Any]):
        """Initialize the Review Manager.
        
        Args:
            github_client (GitHubClient): GitHub client instance
            config (Dict[str, Any]): Configuration dictionary
        """
        self.logger = logging.getLogger('pr_review.manager')
        self.github_client = github_client
        self.config = config
        
        # Initialize reviewers
        self.style_reviewer = StyleReviewer(config.get('style', {}))
        self.security_reviewer = SecurityReviewer(config.get('security', {}))
        self.quality_reviewer = QualityReviewer(config.get('quality', {}))
        
        self.logger.debug("Initialized Review Manager with reviewers")
    
    def review_pull_request(self, pr_number: int, output_mode: str = 'both') -> Dict[str, Any]:
        """Review a specific pull request.
        
        Args:
            pr_number (int): Pull request number
            output_mode (str, optional): Where to output results. Defaults to 'both'.
                Can be 'console', 'github', or 'both'.
            
        Returns:
            Dict[str, Any]: Review results
        """
        self.logger.info(f"Starting review of PR #{pr_number}")
        
        # Get pull request details
        pr = self.github_client.get_pull_request(pr_number)
        pr_files = self.github_client.get_pull_request_files(pr_number)
        
        # Create a temporary directory for downloaded files
        temp_dir = tempfile.mkdtemp(prefix='pr_review_')
        try:
            # Download files for analysis
            downloaded_files = download_files(pr_files, temp_dir, self.github_client)
            self.logger.debug(f"Downloaded {len(downloaded_files)} files for analysis")
            
            # Run reviews
            review_results = self._run_reviews(downloaded_files, pr)
            
            # Format and output results
            formatted_results = self._format_results(review_results, pr)
            
            if output_mode in ['console', 'both']:
                self._print_results(formatted_results)
                
            if output_mode in ['github', 'both']:
                self._post_results_to_github(formatted_results, pr_number)
            
            return review_results
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            self.logger.debug("Cleaned up temporary directory")
    
    def review_all_pull_requests(self, output_mode: str = 'both') -> List[Dict[str, Any]]:
        """Review all open pull requests.
        
        Args:
            output_mode (str, optional): Where to output results. Defaults to 'both'.
                Can be 'console', 'github', or 'both'.
            
        Returns:
            List[Dict[str, Any]]: List of review results for each PR
        """
        self.logger.info("Starting review of all open pull requests")
        
        # Get all open pull requests
        open_prs = self.github_client.get_open_pull_requests()
        self.logger.info(f"Found {len(open_prs)} open pull requests")
        
        # Review each pull request
        results = []
        for pr in open_prs:
            try:
                result = self.review_pull_request(pr['number'], output_mode)
                results.append({
                    'pr_number': pr['number'],
                    'title': pr['title'],
                    'results': result
                })
            except Exception as e:
                self.logger.error(f"Error reviewing PR #{pr.number}: {str(e)}")
        
        return results
    
    def _run_reviews(self, files: List[Dict[str, Any]], pr: Any) -> Dict[str, Any]:
        """Run all reviewers on the files.
        
        Args:
            files (List[Dict[str, Any]]): List of files to review
            pr (Any): Pull request object
            
        Returns:
            Dict[str, Any]: Combined review results
        """
        self.logger.debug("Running reviewers on files")
        
        # Filter files by extension and type
        filtered_files = self._filter_files_for_review(files)
        
        # Run each reviewer
        style_results = self.style_reviewer.review(filtered_files)
        security_results = self.security_reviewer.review(filtered_files)
        quality_results = self.quality_reviewer.review(filtered_files)
        
        # Combine results
        return {
            'style': style_results,
            'security': security_results,
            'quality': quality_results,
            'summary': self._generate_summary(style_results, security_results, quality_results)
        }
    
    def _filter_files_for_review(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter files based on extension and other criteria.
        
        Args:
            files (List[Dict[str, Any]]): List of files
            
        Returns:
            List[Dict[str, Any]]: Filtered list of files
        """
        # Get excluded file patterns from config
        excluded_patterns = self.config.get('exclude_patterns', [])
        
        # Filter files
        filtered_files = []
        for file in files:
            filename = file['filename']
            
            # Skip deleted files
            if file['status'] == 'removed':
                continue
                
            # Skip files matching excluded patterns
            if any(pattern in filename for pattern in excluded_patterns):
                self.logger.debug(f"Skipping excluded file: {filename}")
                continue
                
            # Skip binary files and non-code files
            ext = get_file_extension(filename)
            if not ext or ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf']:
                self.logger.debug(f"Skipping non-code file: {filename}")
                continue
                
            filtered_files.append(file)
        
        self.logger.debug(f"Filtered {len(files)} files to {len(filtered_files)} for review")
        return filtered_files
    
    def _generate_summary(self, style_results: Dict[str, Any], security_results: Dict[str, Any], 
                          quality_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of all review results.
        
        Args:
            style_results (Dict[str, Any]): Style review results
            security_results (Dict[str, Any]): Security review results
            quality_results (Dict[str, Any]): Quality review results
            
        Returns:
            Dict[str, Any]: Summary of results
        """
        # Count issues by severity
        issues = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        # Count style issues
        for issue in style_results.get('issues', []):
            severity = issue.get('severity', 'info')
            issues[severity] += 1
        
        # Count security issues
        for issue in security_results.get('issues', []):
            severity = issue.get('severity', 'info')
            issues[severity] += 1
        
        # Count quality issues
        for issue in quality_results.get('issues', []):
            severity = issue.get('severity', 'info')
            issues[severity] += 1
        
        # Calculate total issues
        total_issues = sum(issues.values())
        
        # Generate overall score (0-100)
        score = 100
        if total_issues > 0:
            # Deduct points based on severity
            score -= issues['critical'] * 10
            score -= issues['high'] * 5
            score -= issues['medium'] * 2
            score -= issues['low'] * 1
            # Ensure score is between 0 and 100
            score = max(0, min(100, score))
        
        return {
            'total_issues': total_issues,
            'issues_by_severity': issues,
            'score': score,
            'verdict': self._get_verdict(score)
        }
    
    def _get_verdict(self, score: int) -> str:
        """Get a verdict based on the score.
        
        Args:
            score (int): Review score (0-100)
            
        Returns:
            str: Verdict
        """
        if score >= 90:
            return "Excellent code quality. Approved!"
        elif score >= 80:
            return "Good code quality with minor issues."
        elif score >= 70:
            return "Acceptable code quality but needs improvement."
        elif score >= 50:
            return "Poor code quality. Significant improvements needed."
        else:
            return "Critical issues found. Must be fixed before merging."
    
    def _format_results(self, results: Dict[str, Any], pr: Any) -> Dict[str, Any]:
        """Format review results for output.
        
        Args:
            results (Dict[str, Any]): Review results
            pr (Any): Pull request object
            
        Returns:
            Dict[str, Any]: Formatted results
        """
        summary = results['summary']
        
        # Format header
        header = f"# Code Review: {pr['title']}\n\n"
        header += f"## Summary\n\n"
        header += f"- **Score**: {summary['score']}/100\n"
        header += f"- **Verdict**: {summary['verdict']}\n"
        header += f"- **Total Issues**: {summary['total_issues']}\n"
        header += "  - Critical: {0}, High: {1}, Medium: {2}, Low: {3}, Info: {4}\n\n".format(
            summary['issues_by_severity']['critical'],
            summary['issues_by_severity']['high'],
            summary['issues_by_severity']['medium'],
            summary['issues_by_severity']['low'],
            summary['issues_by_severity']['info']
        )
        
        # Format issues by category
        categories = {
            'style': "## Style Issues\n\n",
            'security': "## Security Issues\n\n",
            'quality': "## Code Quality Issues\n\n"
        }
        
        for category, title in categories.items():
            category_issues = results[category].get('issues', [])
            if not category_issues:
                categories[category] += "No issues found.\n\n"
                continue
                
            for issue in category_issues:
                categories[category] += f"- **{issue['severity'].upper()}**: {issue['message']}\n"
                categories[category] += f"  - File: `{issue['file']}`\n"
                if 'line' in issue:
                    categories[category] += f"  - Line: {issue['line']}\n"
                if 'suggestion' in issue:
                    categories[category] += f"  - Suggestion: {issue['suggestion']}\n"
                categories[category] += "\n"
        
        # Combine all sections
        formatted_results = {
            'header': header,
            'categories': categories,
            'raw_results': results
        }
        
        return formatted_results
    
    def _print_results(self, formatted_results: Dict[str, Any]) -> None:
        """Print formatted results to console.
        
        Args:
            formatted_results (Dict[str, Any]): Formatted results
        """
        print(formatted_results['header'])
        for category, content in formatted_results['categories'].items():
            print(content)
    
    def _post_results_to_github(self, formatted_results: Dict[str, Any], pr_number: int) -> None:
        """Post formatted results to GitHub PR.
        
        Args:
            formatted_results (Dict[str, Any]): Formatted results
            pr_number (int): Pull request number
        """
        # Combine all sections into a single comment
        comment = formatted_results['header']
        for category, content in formatted_results['categories'].items():
            comment += content
        
        # Post comment to GitHub
        self.github_client.post_review_comment(pr_number, comment)
        self.logger.info(f"Posted review results to PR #{pr_number}")