# XandAI CLI

[![Tests](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/test.yml/badge.svg)](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/xandai-cli.svg)](https://pypi.org/project/xandai-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Terminal assistant that combines AI chat with command execution. Supports Ollama and LM Studio.

## Installation

```bash
pip install xandai-cli
xandai --auto-detect
```

## Usage

```bash
# Terminal commands
xandai> ls -la
xandai> git status

# AI questions  
xandai> How do I optimize this code?

# Natural conversation for any task
xandai> create a REST API with authentication
```

## Providers

- **Ollama** - Local models
- **LM Studio** - GUI-based model management

```bash
xandai --provider ollama
xandai --provider lm_studio --endpoint http://localhost:1234
```

## Commands

```bash
/agent <instruction>  # Multi-step LLM orchestrator for complex tasks
/set-agent-limit <n>  # Set max LLM calls (default: 20, max: 100)
/review               # AI-powered code review
/web on               # Enable web content integration
/help                 # Show all commands
/clear                # Clear history
/status               # System status
```

### Agent Mode 🤖

The `/agent` command is a powerful multi-step LLM orchestrator that chains multiple AI calls to handle complex tasks:

```bash
# Fix code with systematic analysis
/agent fix the bug in main.py where the loop never terminates

# Complex refactoring
/agent refactor this monolithic code into modular components

# Detailed explanations
/agent explain how the authentication system works
```

**Pipeline stages:**
1. **Intent Analysis** - Classifies the task type
2. **Context Gathering** - Identifies needed information
3. **Task Execution** - Performs the main work
4. **Validation** - Verifies output quality
5. **Refinement** - Improves based on validation (if needed)

**When to use /agent:**
- Complex multi-step tasks
- Code requiring analysis and validation
- Tasks needing structured reasoning
- When quality matters more than speed

See [example/agent_demo.md](example/agent_demo.md) for detailed examples.

> **Note:** The `/task` command has been deprecated. Use natural conversation instead for better results.

## File Operations

XandAI can intelligently create and edit files with AI assistance:

### Creating Files

Simply ask to create a file with a specific name:

```bash
xandai> create tokens.py with authentication functions
# AI generates complete code
# System detects filename automatically
This looks like a complete python file. Save it? (y/N): y
Filename: tokens.py
File 'tokens.py' created successfully!
```

### Editing Files

Edit existing files by name:

```bash
xandai> edit index.py adding a health endpoint
# AI reads current file content
# Generates complete updated version
Edit file 'index.py'? (y/N): y
File 'index.py' updated successfully!
```

### Smart Detection

The AI automatically:
- Reads files when editing (preserves existing code)
- Extracts filenames from your request
- Provides complete file content (never placeholders)
- Only prompts when you explicitly request file operations

### Supported Formats

Works with any programming language:
```bash
xandai> create app.js with Express server
xandai> edit styles.css adding dark mode
xandai> create config.json with API settings
```

## Code Execution

XandAI can detect and execute code in various languages:

```bash
xandai> create a math.py that will receive two args and sum them
# AI generates complete Python script with argument handling
This looks like a complete python file. Save it? (y/N): y
Filename: math.py
File 'math.py' created successfully!

xandai> python math.py 2 2
$ python math.py 2 2
2.0 + 2.0 = 4.0
Command completed successfully
```

Features:
- Automatic code detection for Python, JavaScript, Bash, and more
- Interactive execution mode for scripts requiring input
- Non-interactive capture mode for automation
- Smart prompts for user choice between modes

## Code Review

AI-powered code review with Git integration. Analyzes your code changes and provides detailed feedback on security, quality, and best practices.

```bash
xandai> /review
# Automatically detects Git changes and provides comprehensive analysis
```

![Code Review Example](images/Review.png)

## Web Integration

Automatically fetches and analyzes web content when you paste links:

```bash
xandai> /web on
xandai> How does this work? https://docs.python.org/tutorial
# Content is automatically fetched and analyzed
```

## Development

```bash
git clone https://github.com/XandAI-project/Xandai-CLI.git
cd Xandai-CLI
pip install -e .
xandai
```

## License

MIT
