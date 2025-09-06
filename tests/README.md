# XandAI CLI Tests

This directory contains comprehensive tests for the XandAI CLI multi-language code execution system.

## Test Structure

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Shared fixtures and configuration
├── README.md                       # This file
├── test_basic.py                   # Basic CLI functionality tests
├── test_python_execution.py        # Python code execution tests
├── test_javascript_execution.py    # JavaScript/Node.js execution tests
├── test_multi_language_integration.py  # Cross-language integration tests
└── windows/                        # Windows-specific tests
    ├── __init__.py
    ├── test_powershell_execution.py    # PowerShell execution tests
    └── test_batch_execution.py         # Batch/CMD execution tests
```

## Test Categories

### Unit Tests
- **Language Configuration**: Tests for language-specific configurations
- **Code Detection Logic**: Tests for detecting when to use temp files vs inline execution
- **Command Generation**: Tests for proper command generation for each language
- **Error Handling**: Tests for graceful error handling across all languages

### Integration Tests
- **Cross-Language Consistency**: Tests ensuring consistent behavior across languages
- **Resource Management**: Tests for proper cleanup of temporary files and executables
- **Fallback Behavior**: Tests for unknown language handling

### Platform-Specific Tests
- **Windows Tests** (`tests/windows/`): PowerShell and Batch script execution
- **Cross-Platform Tests**: Bash, Python, JavaScript execution

## Supported Languages Tested

| Language | Simple Execution | Complex Execution | Compilation | Platform |
|----------|------------------|-------------------|-------------|----------|
| **Python** | Inline (`python -c`) | Temp file | No | All |
| **JavaScript** | Inline (`node -e`) | Temp file | No | All |
| **PowerShell** | Inline (`powershell -Command`) | Temp file | No | Windows |
| **Batch** | Inline (`cmd /c`) | Temp file | No | Windows |
| **C** | N/A | Temp file + GCC | Yes | All |
| **C++** | N/A | Temp file + G++ | Yes | All |
| **Go** | N/A | Temp file + `go run` | No* | All |
| **Bash** | Inline (`bash -c`) | Temp file | No | Unix/Linux |

*Go uses `go run` which handles compilation internally.

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/ -m unit -v

# Integration tests only
python -m pytest tests/ -m integration -v

# Windows-specific tests (only on Windows)
python -m pytest tests/windows/ -v

# Specific language tests
python -m pytest tests/test_python_execution.py -v
python -m pytest tests/test_javascript_execution.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=xandai --cov-report=html -v
```

### Run Specific Test Functions
```bash
# Test specific functionality
python -m pytest tests/test_python_execution.py::TestPythonExecution::test_simple_python_should_use_inline -v
```

## Test Fixtures

### Common Fixtures (in `conftest.py`)
- `chat_repl`: Mock ChatREPL instance for testing
- `mock_llm_provider`: Mock LLM provider
- `temp_directory`: Temporary directory for test files
- `mock_file_operations`: Mock file operations (temp files, cleanup)
- `multi_lang_assertions`: Custom assertions for multi-language testing

### Platform-Specific Fixtures
- Windows tests include Windows-specific path and command mocking
- Unix tests include bash-specific environment mocking

## Test Data and Scenarios

### Simple Code Examples (Inline Execution)
- Single-line print/echo statements
- Basic variable assignments
- Simple function calls

### Complex Code Examples (Temp File Execution)
- Multi-line functions and classes
- Control flow structures (if, for, while)
- Complex string handling with nested quotes
- Import/require statements
- Long scripts (>200 characters)

### Edge Cases
- Empty code
- Code with special characters and escaping
- Very long single-line scripts
- Nested quotes and string interpolation

## Continuous Integration

These tests are designed to run in CI environments:

- **Cross-platform**: Tests run on Windows, Linux, and macOS
- **Isolated**: Each test runs in isolation with clean state
- **Fast**: Most tests use mocking to avoid actual code execution
- **Comprehensive**: High test coverage of all major functionality

## Adding New Tests

### For New Languages
1. Create `test_{language}_execution.py` in appropriate directory
2. Follow the pattern established by existing language tests
3. Include tests for:
   - Language configuration
   - Simple vs complex code detection
   - Inline vs temp file execution
   - Error handling
   - Language-specific keywords/features

### For New Features
1. Add unit tests for the specific feature
2. Add integration tests if the feature affects multiple components
3. Update existing tests if the feature changes existing behavior
4. Add platform-specific tests if needed

## Debugging Tests

### Running with Debug Output
```bash
# Run with verbose output and print statements
python -m pytest tests/ -v -s

# Run single test with debugging
python -m pytest tests/test_python_execution.py::TestPythonExecution::test_simple_python_should_use_inline -v -s --pdb
```

### Common Issues
- **Import Errors**: Ensure project root is in Python path
- **Mock Failures**: Check that mocks are properly configured
- **Platform Issues**: Use appropriate platform markers
- **Fixture Issues**: Verify fixture dependencies and scope

## Test Quality Guidelines

1. **Descriptive Names**: Test functions should clearly describe what they test
2. **Single Responsibility**: Each test should test one specific behavior
3. **Comprehensive Coverage**: Test both success and failure cases
4. **Proper Mocking**: Mock external dependencies (file system, commands)
5. **Platform Awareness**: Use appropriate platform-specific tests
6. **Clear Assertions**: Assertions should be specific and informative
7. **Resource Cleanup**: Tests should not leave temporary files or state

## Performance Considerations

- Tests use mocking to avoid actual code execution for speed
- Temp file operations are mocked to prevent I/O overhead
- Integration tests focus on component interaction, not performance
- Real execution tests are minimal and focused on critical paths
