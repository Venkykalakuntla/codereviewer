#!/usr/bin/env python3

import os
import json
import logging
from typing import Dict, Any

class ConfigLoader:
    """Loads and validates configuration for the PR review agent."""
    
    def __init__(self, config_path: str):
        """Initialize the Config Loader.
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.logger = logging.getLogger('pr_review.config')
        self.config_path = config_path
        
        # Default configuration
        self.default_config = {
            'general': {
                'check_interval': 60,  # Seconds between checks
                'max_prs_per_run': 10  # Maximum PRs to review in one run
            },
            'style': {
                'enabled': True,
                'max_line_length': 100,
                'indent_size': 4
            },
            'security': {
                'enabled': True,
                'severity_threshold': 'low'  # 'critical', 'high', 'medium', 'low', 'info'
            },
            'quality': {
                'enabled': True,
                'function_length': 50,  # Maximum function length in lines
                'file_length': 500,     # Maximum file length in lines
                'complexity': 10        # Maximum cyclomatic complexity
            },
            'exclude_patterns': [
                'node_modules/',
                'venv/',
                '.git/',
                '__pycache__/',
                '*.min.js',
                '*.min.css',
                '*.svg',
                '*.png',
                '*.jpg',
                '*.jpeg',
                '*.gif',
                '*.pdf',
                '*.lock',
                'package-lock.json'
            ]
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        config = self.default_config.copy()
        
        # Try to load configuration from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    
                # Merge file configuration with defaults
                self._merge_configs(config, file_config)
                self.logger.info(f"Loaded configuration from {self.config_path}")
                
            except Exception as e:
                self.logger.error(f"Error loading configuration from {self.config_path}: {str(e)}")
                self.logger.info("Using default configuration")
        else:
            self.logger.info(f"Configuration file {self.config_path} not found, using defaults")
            
            # Create default configuration file
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                self.logger.info(f"Created default configuration file at {self.config_path}")
            except Exception as e:
                self.logger.error(f"Error creating default configuration file: {str(e)}")
        
        return config
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """Recursively merge override_config into base_config.
        
        Args:
            base_config (Dict[str, Any]): Base configuration to merge into
            override_config (Dict[str, Any]): Configuration to merge from
        """
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_configs(base_config[key], value)
            else:
                # Override or add value
                base_config[key] = value