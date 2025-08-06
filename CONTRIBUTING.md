# Contributing to GitHub PR Code Review Agent

Thank you for considering contributing to the GitHub PR Code Review Agent! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any relevant logs or screenshots

### Suggesting Enhancements

If you have an idea for an enhancement, please create an issue with the following information:

- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Submit a pull request

#### Pull Request Guidelines

- Follow the coding style of the project
- Include tests for new features or bugfixes
- Update documentation as needed
- Keep pull requests focused on a single concern

## Development Setup

1. Clone the repository
2. Run `python install.py` to set up the development environment
3. Create a `.env` file with your GitHub credentials (see `.env.example`)

## Running Tests

Run tests using pytest:

```bash
python -m pytest tests/
```

## Code Style

This project follows these coding standards:

- PEP 8 for Python code
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license.