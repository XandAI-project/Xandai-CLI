# Pre-Commit Setup Guide for XandAI CLI

This guide explains how to set up and use the pre-commit hooks for the XandAI CLI project.

## 📋 What Pre-Commit Does

The pre-commit hooks automatically run before each commit to ensure:

1. **🧪 All tests pass** - Multi-language execution system tests
2. **📊 Code quality** - Python syntax and import checks  
3. **🎨 Code formatting** - Black formatting and isort import sorting
4. **🔍 Linting** - Flake8 code analysis
5. **📄 File checks** - Trailing whitespace, line endings, JSON/YAML syntax

## 🚀 Initial Setup

### 1. Install Pre-Commit

```bash
# Using pip
pip install pre-commit

# Or using conda
conda install -c conda-forge pre-commit

# Or using homebrew (macOS)
brew install pre-commit
```

### 2. Install Code Quality Tools

```bash
# Install required formatting and linting tools
pip install black isort flake8

# Or install all development dependencies
pip install -r requirements-dev.txt  # If you create one
```

### 3. Install Pre-Commit Hooks

```bash
# Navigate to project root
cd "C:\Users\keyce\XandNet Project\XandAI-CLI"

# Install the git hooks
pre-commit install

# Verify installation
pre-commit --version
```

## 🔧 Configuration Files

### `.pre-commit-config.yaml`
Main configuration file that defines all hooks and their settings.

### `scripts/run_precommit_tests.py`
Custom test runner that:
- Tries pytest first
- Falls back to direct verification if pytest has IO buffer issues
- Runs code quality checks
- Provides detailed feedback

## 💻 Usage

### Automatic (Recommended)
Pre-commit hooks run automatically on every `git commit`:

```bash
git add .
git commit -m "Your commit message"
# Hooks run automatically here
```

### Manual Testing
Test the hooks without committing:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run xandai-tests
pre-commit run black
pre-commit run flake8

# Run just the test script directly
python scripts/run_precommit_tests.py
```

## 📊 Hook Details

### 1. XandAI Multi-Language Tests (`xandai-tests`)
- **Purpose**: Ensures the multi-language execution system works
- **Strategy**:
  - Tries pytest with multiple configurations
  - Falls back to direct functionality verification
  - Handles Windows IO buffer issues gracefully
- **Files**: Triggers on changes to `xandai/` or `tests/` Python files

### 2. Code Formatting (`black`, `isort`)
- **Black**: Formats Python code consistently (100 char line length)
- **isort**: Sorts Python imports alphabetically
- **Auto-fix**: These tools automatically fix issues

### 3. Code Quality (`flake8`)
- **Purpose**: Catches common Python issues
- **Configuration**: 100 char line length, ignores E203 and W503
- **Scope**: All Python files

### 4. File Checks (pre-commit-hooks)
- **Syntax**: Checks JSON, YAML, and Python AST
- **Content**: Removes trailing whitespace, ensures file endings
- **Conflicts**: Detects merge conflicts and case conflicts
- **Size**: Prevents large files (>500KB)

## 🛠️ Troubleshooting

### Tests Pass Individually But Fail in Pre-Commit
This is usually due to the pytest IO buffer issue on Windows:

```bash
# Test the fallback system directly
python scripts/run_precommit_tests.py

# Run Windows tests specifically (these work reliably)
python -m pytest tests/windows/ -v
```

### Pre-Commit Hook Fails
```bash
# Skip hooks for emergency commits (use sparingly)
git commit --no-verify -m "Emergency fix"

# Debug specific hook
pre-commit run xandai-tests --verbose

# Update hook versions
pre-commit autoupdate
```

### Code Formatting Issues
```bash
# Auto-fix formatting issues
black . --line-length=100
isort . --profile=black

# Check what would change without applying
black . --line-length=100 --diff
```

## 🎯 Expected Output

### Successful Commit
```
🚀 XandAI CLI Pre-Commit Test Runner
==================================================
📊 Checking code quality...
✅ Code quality checks passed (4/4)
🧪 Running pytest tests...
  Attempt 1: python -m pytest tests/ -v --tb=short --no-header -q
✅ Pytest tests passed!

==================================================
📋 Pre-commit Results (took 12.3s):
  ✅ Code Quality: PASSED
  ✅ Pytest Tests: PASSED

🎉 All checks passed! Commit allowed.
```

### Failed Commit with Fallback
```
🚀 XandAI CLI Pre-Commit Test Runner
==================================================
📊 Checking code quality...
✅ Code quality checks passed (4/4)
🧪 Running pytest tests...
  Attempt 1: python -m pytest tests/ -v --tb=short --no-header -q
⚠️  Attempt 1 failed with IO buffer issue, trying next config...
🔧 Running direct functionality verification...
✅ Direct verification passed (11/11 tests)

==================================================
📋 Pre-commit Results (took 8.7s):
  ✅ Code Quality: PASSED
  ⚠️  Pytest Tests: SKIPPED (IO buffer issues)
  ✅ Direct Verification: PASSED

🎉 All checks passed! Commit allowed.
```

## 📚 Best Practices

1. **Run tests locally** before committing large changes
2. **Fix formatting issues** by running `black` and `isort` manually
3. **Don't skip hooks** unless absolutely necessary (emergency fixes)
4. **Update pre-commit** occasionally: `pre-commit autoupdate`
5. **Check hook performance** if commits become slow

## 🔄 Updating

```bash
# Update hook versions
pre-commit autoupdate

# Re-install hooks after updates
pre-commit install

# Test updated configuration
pre-commit run --all-files
```

## 🚫 Disabling (Not Recommended)

```bash
# Temporary disable for one commit
git commit --no-verify -m "Emergency fix"

# Permanently uninstall (not recommended)
pre-commit uninstall
```

## 📞 Support

If you encounter issues:
1. Run `python scripts/run_precommit_tests.py` manually to debug
2. Check that all dependencies are installed
3. Verify Python path and virtual environment
4. Review the detailed output for specific error messages

The pre-commit system is designed to be robust and handle the specific challenges of the XandAI CLI project, including the pytest IO buffer issues on Windows.
