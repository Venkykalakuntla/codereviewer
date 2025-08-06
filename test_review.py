#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the necessary modules
from utils.logger import setup_logger
from utils.config import ConfigLoader
from github.client import GitHubClient
from reviewers.review_manager import ReviewManager

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up logging
    logger = setup_logger('pr_review', logging.INFO)
    logger.info('Starting PR code review test')
    
    # Check for required environment variables
    required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in a .env file or in your environment")
        sys.exit(1)
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config_loader = ConfigLoader(config_path)
    config = config_loader.load_config()
    
    # Initialize GitHub client
    github_client = GitHubClient(
        token=os.getenv('GITHUB_TOKEN'),
        owner=os.getenv('GITHUB_OWNER'),
        repo=os.getenv('GITHUB_REPO')
    )
    
    # Get PR number from command line arguments or use a default
    pr_number = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    if pr_number is None:
        # If no PR number is provided, list open PRs
        prs = github_client.list_pull_requests()
        if not prs:
            logger.info("No open pull requests found")
            sys.exit(0)
            
        logger.info(f"Found {len(prs)} open pull requests:")
        for pr in prs:
            logger.info(f"PR #{pr['number']}: {pr['title']}")
            
        # Use the first PR for testing
        pr_number = prs[0]['number']
        logger.info(f"Using PR #{pr_number} for testing")
    
    # Initialize review manager
    review_manager = ReviewManager(github_client, config)
    
    # Review the PR
    result = review_manager.review_pull_request(pr_number, output_mode='console')
    
    # Print the result
    logger.info(f"Review completed with score: {result['score']}/100")
    logger.info(f"Verdict: {result['verdict']}")
    
    # Print issue counts by severity
    for severity, count in result['issue_counts'].items():
        logger.info(f"{severity.capitalize()} issues: {count}")
    
    logger.info('PR code review test completed')

if __name__ == '__main__':
    main()