# Development Guide - XandAI

This document contains information for developers who want to contribute to XandAI.

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/xandai.git
cd xandai
```

### 2. Create a Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

## Project Structure

```
xandai/
├── xandai/                 # Main source code
│   ├── __init__.py        # Package metadata
│   ├── __main__.py        # CLI entry point
│   ├── api.py             # OLLAMA API client
│   ├── cli.py             # Interactive CLI interface
│   └── file_operations.py # File operations
├── tests/                  # Unit tests
│   ├── __init__.py
│   ├── test_api.py        # API tests
│   └── test_file_operations.py # File operations tests
├── examples/               # Usage examples
│   └── demo.py            # Demo script
├── README.md              # Main documentation
├── LICENSE                # MIT License
├── requirements.txt       # Production dependencies
├── setup.py              # Traditional package configuration
└── pyproject.toml        # Modern package configuration
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=xandai

# Only a specific file
pytest tests/test_api.py

# With verbose output
pytest -v
```

### Code Verification

```bash
# Formatting with Black
black xandai tests

# Import sorting with isort
isort xandai tests

# Linting with flake8
flake8 xandai tests

# Type checking with mypy
mypy xandai
```

## Style Guide

### Python

- We follow PEP 8 with maximum line length of 100 characters
- Use Black for automatic formatting
- Docstrings in Google/NumPy format
- Type hints whenever possible

### Commits

Recommended format:

```
type: brief description

Detailed description if necessary.

Fixes #123
```

Types:
- `feat`: New functionality
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code refactoring
- `test`: Adding or fixing tests
- `chore`: Maintenance tasks

## Adding New Features

### 1. New CLI Command

To add a new command to the CLI:

```python
# In cli.py
def my_command(self, args: str = ""):
    """Processes my new command"""
    # Implementation here
    pass

# In XandAICLI class __init__
self.commands['/mycommand'] = self.my_command
```

### 2. New File Operation

To add a new file operation:

```python
# In file_operations.py
def my_operation(self, filepath: Union[str, Path]) -> None:
    """My new operation"""
    try:
        # Implementation here
        pass
    except Exception as e:
        raise FileOperationError(f"Error: {e}")
```

### 3. New API Endpoint

To add support for a new OLLAMA endpoint:

```python
# In api.py
def new_endpoint(self, param: str) -> Dict:
    """Calls new endpoint"""
    response = self._make_request('POST', '/api/new', json={'param': param})
    return response.json()
```

## Debugging

### Local Debug Mode

```python
# Run module directly
python -m xandai

# With debugging enabled
python -m pdb -m xandai
```

### Detailed Logs

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing with OLLAMA

### Local Installation

```bash
# Install OLLAMA
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull llama2

# Start the server
ollama serve
```

### Mock for Tests

Use OLLAMA mock in tests:

```python
@patch('xandai.api.OllamaAPI')
def test_com_mock(mock_api):
    mock_api.list_models.return_value = [...]
```

## Build and Distribution

### Local Build

```bash
# Create distribution
python -m build

# Files generated in dist/
ls dist/
```

### Installation Test

```bash
# In a new virtual environment
pip install dist/xandai-0.1.0-py3-none-any.whl

# Test
xandai --help
```

## Common Issues

### ImportError on Windows

```bash
# Add directory to PYTHONPATH
set PYTHONPATH=%PYTHONPATH%;.
```

### OLLAMA Connection Error

```bash
# Check if it's running
curl http://localhost:11434

# Restart the service
ollama serve
```

### UTF-8 Encoding

Always specify encoding:

```python
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()
```

## Useful Resources

- [Documentação OLLAMA API](https://github.com/jmorganca/ollama/blob/main/docs/api.md)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Prompt Toolkit Docs](https://python-prompt-toolkit.readthedocs.io/)

## Contact

For development questions:
- Open an issue on GitHub
- Discussions in the Discussions tab
- Pull requests are welcome!

---

Happy coding! 🚀
