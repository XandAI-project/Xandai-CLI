# XandAI CLI - Intelligent Terminal Assistant

[![Tests](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/test.yml/badge.svg)](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/test.yml)
[![Build](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/workflow.yml/badge.svg)](https://github.com/XandAI-project/Xandai-CLI/actions/workflows/workflow.yml)
[![PyPI version](https://img.shields.io/pypi/v/xandai-cli.svg)](https://pypi.org/project/xandai-cli/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/xandai-cli.svg)](https://pypi.org/project/xandai-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**XandAI CLI** is a powerful terminal assistant that seamlessly blends AI conversation with local command execution. Built with Ollama integration, it provides intelligent code assistance, project planning, and command-line automation - all within a beautiful, interactive terminal interface.

## 📸 See It In Action

![XandAI CLI Interface](images/CLI.png)

*XandAI seamlessly switches between AI chat and terminal commands - ask questions, get code help, and execute commands all in one interface*

## ⚡ Quick Start

```bash
# Install XandAI
pip install xandai-cli

# Start the CLI
xandai

# That's it! Start chatting or running commands
xandai> python --version
xandai> How do I optimize this Flask route?
xandai> /task create a REST API with authentication
```

## 🎯 What Makes XandAI Special

### 🧠 **Smart Command Recognition**
XandAI automatically detects whether you're asking an AI question or running a terminal command:
```bash
xandai> ls -la                    # Executes terminal command
xandai> git status               # Executes git command  
xandai> How do I use git rebase?  # Asks AI for help
xandai> python app.py            # Runs your Python script
```

### 💬 **Intelligent Conversations**
- **Context-Aware**: Remembers your conversation and project context
- **Code Analysis**: Understands your codebase and provides relevant suggestions
- **Real-time Help**: Get explanations while you work

### 🛠️ **Project Planning**
Use `/task` mode for structured project planning:
```bash
xandai> /task create a Flask API with JWT authentication

# XandAI responds with:
# 1. Create project structure
# 2. Set up Flask app with blueprints  
# 3. Implement JWT authentication
# 4. Create user registration/login endpoints
# [Complete implementation details follow]
```

### 🎨 **Beautiful Interface**
- **Syntax Highlighting**: Code blocks with proper language detection
- **Smart Autocomplete**: Context-aware command and file suggestions  
- **Rich Formatting**: Clean, readable output with colors and structure
- **Command History**: Navigate through previous commands and conversations

## 🔧 Installation & Setup

```bash
# Install from PyPI
pip install xandai-cli

# Make sure Ollama is running (install from https://ollama.ai)
ollama serve

# Start XandAI with custom options
xandai --model llama3.2 --endpoint http://localhost:11434
```

## 💡 Real-World Examples

### Daily Development Workflow
```bash
# Navigate and explore your project
xandai> cd my-project && ls -la
xandai> git status
xandai> cat app.py

# Get AI help while coding
xandai> This Flask route is slow, how can I optimize it?
[AI analyzes your code and suggests specific improvements]

# Continue working with AI suggestions
xandai> git add . && git commit -m "Optimize Flask routes"
```

### Project Planning & Learning
```bash
# Plan complex projects
xandai> /task create a microservices architecture with Docker
[Detailed project structure with implementation steps]

# Learn new concepts
xandai> Explain async/await vs Promises in JavaScript with examples
[Comprehensive explanation with code samples]

# Get implementation help
xandai> Show me how to implement JWT authentication in Express.js
[Complete implementation with best practices]
```

## 🧠 How XandAI Works

XandAI intelligently combines AI conversation with terminal command execution:

- **Smart Detection**: Automatically recognizes if your input is a command or question
- **Context Memory**: Remembers your conversation, current directory, and project state  
- **Ollama Integration**: Uses local Ollama models for privacy and performance
- **Rich Interface**: Beautiful terminal UI with syntax highlighting and autocompletion

## 🔧 Advanced Features

### Command Integration
Any terminal command works seamlessly:
```bash
xandai> python --version && pip list | grep flask
xandai> find . -name "*.py" | grep -v __pycache__
xandai> docker ps && docker images
```

### Intelligent Autocompletion
XandAI provides smart suggestions based on context:
- **File commands** (`cat`, `vim`) → Shows only files
- **Directory commands** (`cd`, `mkdir`) → Shows only directories  
- **Mixed commands** (`ls`, `cp`) → Shows both files and directories
- **Slash commands** → `/task`, `/help`, `/clear`, `/status`

### Project Awareness
- Tracks file changes to avoid duplicates
- Maintains coding patterns and framework conventions
- Provides context-aware suggestions based on your project type
- Remembers previous conversations for better assistance

## 🎨 Task Planning Example

When you use `/task` mode, XandAI creates detailed project structures:

```bash
xandai> /task create a Flask API with JWT authentication

# XandAI responds with complete project structure:
Flask API Project:
├── app.py              # Main Flask application
├── models/user.py      # User model with authentication
├── routes/auth.py      # Login/register endpoints  
├── config.py           # App configuration
└── requirements.txt    # Dependencies

# Plus complete implementation for each file with:
# - All necessary functions and classes
# - Proper error handling  
# - Security best practices
# - Ready-to-run code
```

## 🛠️ Available Commands

**Slash Commands:**
- `/task <description>` - Generate structured project plans
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/status` - Show system status
- `/history` - View conversation history

**Any Terminal Command:**
```bash
# Development commands
xandai> python app.py
xandai> npm start  
xandai> docker-compose up

# File operations
xandai> ls -la && cat package.json
xandai> git status && git log --oneline

# System commands  
xandai> ps aux | grep python
xandai> df -h && free -m
```

## 🤝 Contributing

We welcome contributions! XandAI is built with Python 3.8+ and uses modern development practices.

```bash
# Get started
git clone https://github.com/XandAI-project/Xandai-CLI.git
cd Xandai-CLI
pip install -e .

# Run XandAI locally
xandai
```

**📦 PyPI Package:** [xandai-cli on PyPI](https://pypi.org/project/xandai-cli/)  
**Found a bug?** [Create an issue](https://github.com/XandAI-project/Xandai-CLI/issues)  
**Have a feature idea?** [Start a discussion](https://github.com/XandAI-project/Xandai-CLI/discussions)

---

**Made with ❤️ by the XandAI team** • Built for developers who love powerful, intelligent tools
