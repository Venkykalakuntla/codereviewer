# GitHub PR Code Review Agent

An automated code review agent for GitHub pull requests that analyzes code changes, provides feedback, and suggests improvements.

## Features

- Automated code review for GitHub pull requests
- Static code analysis to identify potential issues
- Code quality assessment based on best practices
- Security vulnerability detection
- Performance improvement suggestions
- Customizable review rules and thresholds
- Integration with GitHub Actions

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd github-pr-review-agent

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your GitHub credentials and configuration:

```
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=repository_owner
GITHUB_REPO=repository_name
```

Or use environment variables when running the agent.

## Usage

### Command Line

```bash
# Review a specific pull request
python src/main.py --pr 123

# Review all open pull requests
python src/main.py --all

# Use a custom configuration file
python src/main.py --pr 123 --config custom_config.json
```

### GitHub Action

Create a workflow file in your repository at `.github/workflows/code-review.yml`:

```yaml
name: Automated Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run code review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python src/main.py --pr ${{ github.event.pull_request.number }}
```

## License

MIT