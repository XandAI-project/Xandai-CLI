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

# Project planning
xandai> /task create a REST API
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
/task <description>    # Project planning
/web on               # Enable web content integration
/help                 # Show all commands
/clear                # Clear history
/status               # System status
```

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
