#!/usr/bin/env python3

import os
import json
import unittest
from unittest.mock import patch, mock_open

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from utils.config import ConfigLoader

class TestConfigLoader(unittest.TestCase):
    """Test cases for the configuration loader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_path = 'test_config.json'
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_from_file(self, mock_file, mock_exists):
        """Test loading configuration from a file."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        test_config = {
            'general': {
                'check_interval': 30
            },
            'style': {
                'max_line_length': 80
            }
        }
        mock_file.return_value.read.return_value = json.dumps(test_config)
        
        # Create config loader and load config
        config_loader = ConfigLoader(self.config_path)
        config = config_loader.load_config()
        
        # Assertions
        self.assertEqual(config['general']['check_interval'], 30)
        self.assertEqual(config['style']['max_line_length'], 80)
        
        # Default values should still be present
        self.assertTrue('security' in config)
        self.assertTrue('quality' in config)
    
    @patch('os.path.exists')
    def test_load_default_config(self, mock_exists):
        """Test loading default configuration when file doesn't exist."""
        # Mock file non-existence
        mock_exists.return_value = False
        
        # Create config loader and load config
        with patch('builtins.open', mock_open()) as mock_file:
            config_loader = ConfigLoader(self.config_path)
            config = config_loader.load_config()
        
        # Assertions
        self.assertEqual(config['general']['check_interval'], 60)
        self.assertEqual(config['style']['max_line_length'], 100)
        self.assertTrue(config['security']['enabled'])
        self.assertEqual(config['quality']['function_length'], 50)
    
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_merge_configs(self, mock_open, mock_exists):
        """Test merging configurations."""
        # Create a config loader
        config_loader = ConfigLoader(self.config_path)
        
        # Test merging
        base_config = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            }
        }
        
        override_config = {
            'b': {
                'c': 4
            },
            'e': 5
        }
        
        # Merge configs
        config_loader._merge_configs(base_config, override_config)
        
        # Assertions
        self.assertEqual(base_config['a'], 1)
        self.assertEqual(base_config['b']['c'], 4)  # Overridden
        self.assertEqual(base_config['b']['d'], 3)  # Preserved
        self.assertEqual(base_config['e'], 5)  # Added

if __name__ == '__main__':
    unittest.main()