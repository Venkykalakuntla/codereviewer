# Makefile for GitHub PR Code Review Agent

.PHONY: install test lint clean run

# Default Python interpreter
PYTHON = python

# Installation
install:
	$(PYTHON) -m pip install -r requirements.txt

# Install in development mode
develop:
	$(PYTHON) -m pip install -e .

# Run tests
test:
	$(PYTHON) -m pytest tests/

# Run linting
lint:
	$(PYTHON) -m flake8 src/
	$(PYTHON) -m mypy src/
	$(PYTHON) -m isort --check-only src/
	$(PYTHON) -m black --check src/

# Format code
format:
	$(PYTHON) -m isort src/
	$(PYTHON) -m black src/

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the code review agent
run:
	$(PYTHON) src/main.py $(ARGS)

# Run the test script
test-review:
	$(PYTHON) test_review.py $(PR)