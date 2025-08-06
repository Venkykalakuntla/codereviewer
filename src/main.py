#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from github.client import GitHubClient
from reviewers.review_manager import ReviewManager
from utils.config import ConfigLoader
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub PR Code Review Agent')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pr', type=int, help='Pull request number to review')
    group.add_argument('--all', action='store_true', help='Review all open pull requests')
    
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--output', type=str, choices=['console', 'github', 'both'],
                        default='both', help='Where to output review results')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('pr_review', log_level=log_level)
    logger.info('Starting GitHub PR Code Review Agent')
    
    try:
        # Load configuration
        config_loader = ConfigLoader(args.config)
        config = config_loader.load_config()
        logger.info(f'Loaded configuration from {args.config}')
        
        # Initialize GitHub client
        github_token = os.getenv('GITHUB_TOKEN')
        github_owner = os.getenv('GITHUB_OWNER')
        github_repo = os.getenv('GITHUB_REPO')
        
        if not github_token:
            logger.error('GITHUB_TOKEN environment variable is not set')
            sys.exit(1)
            
        if not github_owner or not github_repo:
            logger.error('GITHUB_OWNER and GITHUB_REPO environment variables must be set')
            sys.exit(1)
        
        github_client = GitHubClient(github_token, github_owner, github_repo)
        logger.info(f'Initialized GitHub client for {github_owner}/{github_repo}')
        
        # Initialize Review Manager
        review_manager = ReviewManager(github_client, config)
        logger.info('Initialized Review Manager')
        
        # Run reviews
        if args.pr:
            logger.info(f'Reviewing pull request #{args.pr}')
            review_manager.review_pull_request(args.pr, output_mode=args.output)
        elif args.all:
            logger.info('Reviewing all open pull requests')
            review_manager.review_all_pull_requests(output_mode=args.output)
        
        logger.info('Code review completed successfully')
        
    except Exception as e:
        logger.error(f'Error in main execution: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()