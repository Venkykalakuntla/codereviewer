#!/usr/bin/env python3

import os
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger('pr_review.utils')

def get_file_extension(filename: str) -> str:
    """Get the extension of a file.
    
    Args:
        filename (str): File name or path
        
    Returns:
        str: File extension (including the dot)
    """
    _, ext = os.path.splitext(filename)
    return ext

def count_lines(file_path: str) -> int:
    """Count the number of lines in a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: Number of lines
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return sum(1 for _ in f)

def download_files(files: List[Dict[str, Any]], temp_dir: str, github_client) -> List[Dict[str, Any]]:
    """Download files for analysis.
    
    Args:
        files (List[Dict[str, Any]]): List of files to download
        temp_dir (str): Temporary directory to save files
        github_client: GitHub client instance
        
    Returns:
        List[Dict[str, Any]]: List of downloaded files with local paths
    """
    downloaded_files = []
    
    for file in files:
        # Skip deleted files
        if file['status'] == 'removed':
            continue
            
        filename = file['filename']
        raw_url = file.get('raw_url')
        
        # Create directory structure
        file_dir = os.path.dirname(filename)
        if file_dir:
            os.makedirs(os.path.join(temp_dir, file_dir), exist_ok=True)
            
        local_path = os.path.join(temp_dir, filename)
        
        try:
            # Download file content
            if raw_url:
                # Download directly from raw URL
                response = requests.get(raw_url)
                response.raise_for_status()
                content = response.content
            else:
                # Get content from GitHub API
                content = github_client.get_file_content(filename)
                if isinstance(content, str):
                    content = content.encode('utf-8')
            
            # Save file locally
            with open(local_path, 'wb') as f:
                f.write(content)
                
            # Add local path to file info
            file_info = file.copy()
            file_info['local_path'] = local_path
            downloaded_files.append(file_info)
            
            logger.debug(f"Downloaded {filename} to {local_path}")
            
        except Exception as e:
            logger.error(f"Error downloading {filename}: {str(e)}")
    
    return downloaded_files