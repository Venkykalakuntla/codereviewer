#!/usr/bin/env python3

import logging
import os
import re
from typing import List, Dict, Any

from utils.file_utils import get_file_extension, count_lines

class QualityReviewer:
    """Reviewer for code quality and maintainability issues."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Quality Reviewer.
        
        Args:
            config (Dict[str, Any]): Configuration for quality checking
        """
        self.logger = logging.getLogger('pr_review.quality')
        self.config = config
        
        # Default thresholds
        self.thresholds = {
            'function_length': config.get('function_length', 50),
            'file_length': config.get('file_length', 500),
            'complexity': config.get('complexity', 10),
            'duplication': config.get('duplication', 0.2)  # 20% duplication threshold
        }
    
    def review(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review files for code quality issues.
        
        Args:
            files (List[Dict[str, Any]]): List of files to review
            
        Returns:
            Dict[str, Any]: Review results
        """
        self.logger.info(f"Reviewing {len(files)} files for code quality issues")
        
        issues = []
        
        for file in files:
            filename = file['local_path']  # Path to downloaded file
            if not os.path.exists(filename):
                self.logger.warning(f"File not found for quality review: {filename}")
                continue
                
            # Get file extension
            ext = get_file_extension(filename)
            
            # Check file length
            file_length_issues = self._check_file_length(filename, file['filename'])
            issues.extend(file_length_issues)
            
            # Check function length and complexity based on file type
            if ext.lower() in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.go', '.rb', '.php']:
                function_issues = self._check_functions(filename, file['filename'], ext.lower())
                issues.extend(function_issues)
            
            # Check for code duplication
            # This is a simplified check - in a real implementation, you would use a more sophisticated tool
            duplication_issues = self._check_duplication(filename, file['filename'])
            issues.extend(duplication_issues)
            
            # Check for commented-out code
            commented_code_issues = self._check_commented_code(filename, file['filename'])
            issues.extend(commented_code_issues)
        
        return {
            'issues': issues,
            'count': len(issues)
        }
    
    def _check_file_length(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check if file exceeds length threshold.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of issues
        """
        issues = []
        
        try:
            line_count = count_lines(local_path)
            threshold = self.thresholds['file_length']
            
            if line_count > threshold:
                issues.append({
                    'file': repo_path,
                    'message': f"File is too long ({line_count} lines, threshold: {threshold})",
                    'severity': 'medium',
                    'type': 'quality',
                    'suggestion': "Consider breaking the file into smaller, more focused modules"
                })
        except Exception as e:
            self.logger.error(f"Error checking file length for {local_path}: {str(e)}")
        
        return issues
    
    def _check_functions(self, local_path: str, repo_path: str, file_ext: str) -> List[Dict[str, Any]]:
        """Check functions for length and complexity issues.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            file_ext (str): File extension
            
        Returns:
            List[Dict[str, Any]]: List of issues
        """
        issues = []
        
        try:
            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
                # Define function patterns based on file type
                function_patterns = self._get_function_patterns(file_ext)
                
                # Find functions and check their length
                functions = self._find_functions(lines, function_patterns)
                
                for func in functions:
                    # Check function length
                    if func['length'] > self.thresholds['function_length']:
                        issues.append({
                            'file': repo_path,
                            'line': func['start_line'],
                            'message': f"Function '{func['name']}' is too long ({func['length']} lines, threshold: {self.thresholds['function_length']})",
                            'severity': 'medium',
                            'type': 'quality',
                            'suggestion': "Break down the function into smaller, more focused functions"
                        })
                    
                    # Check function complexity (simplified)
                    complexity = self._estimate_complexity(lines[func['start_line']-1:func['end_line']])
                    if complexity > self.thresholds['complexity']:
                        issues.append({
                            'file': repo_path,
                            'line': func['start_line'],
                            'message': f"Function '{func['name']}' is too complex (estimated complexity: {complexity}, threshold: {self.thresholds['complexity']})",
                            'severity': 'medium',
                            'type': 'quality',
                            'suggestion': "Reduce complexity by extracting logic into helper functions"
                        })
        except Exception as e:
            self.logger.error(f"Error checking functions in {local_path}: {str(e)}")
        
        return issues
    
    def _get_function_patterns(self, file_ext: str) -> Dict[str, Any]:
        """Get function patterns for a specific file type.
        
        Args:
            file_ext (str): File extension
            
        Returns:
            Dict[str, Any]: Function patterns
        """
        patterns = {
            '.py': {
                'function': r'^\s*def\s+([\w_]+)\s*\(',
                'class': r'^\s*class\s+([\w_]+)',
                'method': r'^\s*def\s+([\w_]+)\s*\(',
                'end': r'^\s*$'
            },
            '.js': {
                'function': r'^\s*function\s+([\w_]+)\s*\(',
                'method': r'^\s*([\w_]+)\s*\(.*\)\s*\{',
                'arrow': r'^\s*(?:const|let|var)\s+([\w_]+)\s*=\s*\(.*\)\s*=>',
                'end': r'^\s*\}'
            },
            '.java': {
                'method': r'^\s*(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+([\w_]+)\s*\(',
                'end': r'^\s*\}'
            },
            '.go': {
                'function': r'^\s*func\s+([\w_]+)\s*\(',
                'method': r'^\s*func\s+\(.*\)\s+([\w_]+)\s*\(',
                'end': r'^\s*\}'
            }
        }
        
        # Default to JavaScript patterns for other file types
        return patterns.get(file_ext, patterns['.js'])
    
    def _find_functions(self, lines: List[str], patterns: Dict[str, str]) -> List[Dict[str, Any]]:
        """Find functions in the file and calculate their length.
        
        Args:
            lines (List[str]): File lines
            patterns (Dict[str, str]): Function patterns
            
        Returns:
            List[Dict[str, Any]]: List of functions with their details
        """
        functions = []
        current_function = None
        brace_count = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Check if we're in a function
            if current_function is not None:
                # Count braces for languages that use them
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                
                # Check for end of function
                if (re.match(patterns.get('end', r'^$'), line) and brace_count <= 0) or \
                   (brace_count <= 0 and line.strip() == '}'):
                    current_function['end_line'] = line_num
                    current_function['length'] = current_function['end_line'] - current_function['start_line'] + 1
                    functions.append(current_function)
                    current_function = None
                    brace_count = 0
            
            # Check for start of function
            else:
                for pattern_type, pattern in patterns.items():
                    if pattern_type == 'end':
                        continue
                        
                    match = re.match(pattern, line)
                    if match:
                        current_function = {
                            'name': match.group(1),
                            'type': pattern_type,
                            'start_line': line_num,
                            'end_line': None,
                            'length': None
                        }
                        if '{' in line:
                            brace_count += line.count('{')
                        break
        
        # Handle case where last function doesn't have a clear end
        if current_function is not None:
            current_function['end_line'] = len(lines)
            current_function['length'] = current_function['end_line'] - current_function['start_line'] + 1
            functions.append(current_function)
        
        return functions
    
    def _estimate_complexity(self, lines: List[str]) -> int:
        """Estimate cyclomatic complexity of a function (simplified).
        
        Args:
            lines (List[str]): Function lines
            
        Returns:
            int: Estimated complexity
        """
        # This is a very simplified complexity estimation
        # In a real implementation, you would use a proper complexity analyzer
        
        # Count control flow statements as a simple proxy for complexity
        complexity = 1  # Base complexity
        
        control_flow_patterns = [
            r'\bif\b',
            r'\belse\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bswitch\b',
            r'\bcase\b',
            r'\bcatch\b',
            r'\b\?\b',  # Ternary operator
            r'\band\b',
            r'\bor\b',
            r'\&\&',
            r'\|\|'
        ]
        
        for line in lines:
            for pattern in control_flow_patterns:
                if re.search(pattern, line):
                    complexity += 1
        
        return complexity
    
    def _check_duplication(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check for code duplication within a file (simplified).
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of issues
        """
        issues = []
        
        # This is a very simplified duplication check
        # In a real implementation, you would use a proper duplication detector
        try:
            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
                # Skip files that are too short
                if len(lines) < 10:
                    return []
                
                # Look for repeated blocks of code (at least 5 lines)
                block_size = 5
                blocks = {}
                
                for i in range(len(lines) - block_size + 1):
                    block = '\n'.join(lines[i:i+block_size])
                    # Skip blocks that are mostly whitespace or comments
                    if block.strip() == '' or block.count('#') > block_size / 2:
                        continue
                        
                    if block in blocks:
                        blocks[block].append(i + 1)
                    else:
                        blocks[block] = [i + 1]
                
                # Report duplicated blocks
                for block, line_numbers in blocks.items():
                    if len(line_numbers) > 1:
                        issues.append({
                            'file': repo_path,
                            'line': line_numbers[0],
                            'message': f"Duplicated code block found at lines {', '.join(map(str, line_numbers))}",
                            'severity': 'medium',
                            'type': 'quality',
                            'suggestion': "Extract duplicated code into a reusable function"
                        })
        except Exception as e:
            self.logger.error(f"Error checking duplication in {local_path}: {str(e)}")
        
        return issues
    
    def _check_commented_code(self, local_path: str, repo_path: str) -> List[Dict[str, Any]]:
        """Check for commented-out code.
        
        Args:
            local_path (str): Local path to the file
            repo_path (str): Repository path to the file
            
        Returns:
            List[Dict[str, Any]]: List of issues
        """
        issues = []
        
        try:
            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
                # Get file extension
                ext = get_file_extension(local_path)
                
                # Define comment patterns based on file type
                if ext.lower() in ['.py']:
                    single_line_comment = '#'
                    multi_line_start = '"""'
                    multi_line_end = '"""'
                elif ext.lower() in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.go']:
                    single_line_comment = '//'
                    multi_line_start = '/*'
                    multi_line_end = '*/'
                else:
                    # Skip unsupported file types
                    return []
                
                # Check for commented-out code
                in_multi_line_comment = False
                for i, line in enumerate(lines):
                    line_num = i + 1
                    
                    # Handle multi-line comments
                    if multi_line_start in line and not in_multi_line_comment:
                        in_multi_line_comment = True
                    if multi_line_end in line and in_multi_line_comment:
                        in_multi_line_comment = False
                        continue
                    
                    # Skip lines that are not comments
                    if not in_multi_line_comment and not line.strip().startswith(single_line_comment):
                        continue
                    
                    # Check if the comment looks like code
                    comment_text = line.strip()
                    if in_multi_line_comment:
                        comment_text = comment_text.strip('*')
                    else:
                        comment_text = comment_text[len(single_line_comment):].strip()
                    
                    # Patterns that suggest commented-out code
                    code_patterns = [
                        r'\bif\b.*\:',
                        r'\bfor\b.*\:',
                        r'\bwhile\b.*\:',
                        r'\bdef\b.*\:',
                        r'\bclass\b.*\:',
                        r'\breturn\b',
                        r'\bfunction\b',
                        r'\bvar\b',
                        r'\blet\b',
                        r'\bconst\b',
                        r'\=\s*\w+\(',
                        r'\w+\(.*\)'
                    ]
                    
                    for pattern in code_patterns:
                        if re.search(pattern, comment_text):
                            issues.append({
                                'file': repo_path,
                                'line': line_num,
                                'message': "Commented-out code found",
                                'severity': 'low',
                                'type': 'quality',
                                'suggestion': "Remove commented-out code or add a clear explanation for why it's kept"
                            })
                            break
        except Exception as e:
            self.logger.error(f"Error checking commented code in {local_path}: {str(e)}")
        
        return issues