# Python Development Rules

## Code Style
- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length of 88 characters (Black formatter)
- Use meaningful variable and function names
- Use snake_case for variables and functions
- Use PascalCase for classes

## Project Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
├── requirements.txt
├── README.md
└── .gitignore
```

## Dependencies
- Use virtual environments (venv or pipenv)
- Pin dependency versions in requirements.txt
- Separate dev dependencies from production
- Use requirements-dev.txt for development dependencies

## Error Handling
- Use specific exception types
- Always handle exceptions gracefully
- Log errors with appropriate context
- Use try-catch blocks judiciously

## Documentation
- Use docstrings for all functions and classes
- Follow Google or NumPy docstring style
- Include type hints for function parameters and returns
- Write comprehensive README.md

## Testing
- Use pytest for testing
- Aim for 80%+ test coverage
- Write unit tests for all functions
- Use fixtures for test data
- Name test functions descriptively

## Type Hints
- Use type hints for all function signatures
- Import types from typing module
- Use Optional for nullable parameters
- Use Union for multiple possible types

## File Organization
- One class per file (when classes are large)
- Group related functions in modules
- Use __init__.py for package initialization
- Keep main execution in if __name__ == "__main__"

## Performance
- Use list comprehensions over loops when appropriate
- Use generators for large datasets
- Profile code before optimizing
- Consider using dataclasses for data structures
