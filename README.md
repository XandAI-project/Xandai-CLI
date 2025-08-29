# XandAI CLI

An interactive command-line tool for interacting with language models through the OLLAMA API, with extended capabilities for file manipulation.

## Features

- 🤖 Interactive and user-friendly CLI interface
- 🔌 Complete integration with OLLAMA API
- 📝 File creation, editing, and deletion
- 🎨 Syntax highlighting for code
- 📊 Visual listing of available models
- 💾 Persistent command history
- 🛡️ Security confirmations for destructive operations
- 🎯 Command autocompletion
- ⚡ **Automatic shell command execution**
- 🧠 **Intelligent prompt enhancement with context**
- 🤖 **v0.2.1**: Automatic bash/shell code execution
- 📝 **v0.2.1**: Intelligent automatic file naming
- 🎯 **v0.2.1**: Cleaner and more responsive interface
- 💻 **v0.3.0**: Multi-platform support (Windows, macOS, Linux)
- 🔄 **v0.3.0**: Automatic command conversion between systems
- 🎯 **NEW v0.4.0**: Complex Task Mode for large projects
- 📋 **NEW v0.4.0**: Automatic breakdown into sub-tasks
- 🔄 **NEW v0.4.0**: Context maintained between tasks
- 🔧 **NEW v0.4.9**: /enhance_code command to improve existing code
- 📝 **NEW v0.4.9**: Specialized prompt for code enhancement
- 🚫 **NEW v0.4.9**: Mode that NEVER creates new files, only improves existing ones
- 🔍 **NEW v0.4.11**: Advanced file search in parent and subdirectories
- 📁 **NEW v0.4.11**: Recursive listing with -r flag
- 🎯 **NEW v0.4.11**: AI sees expanded context including parent directory
- 📄 **NEW v0.5.0**: AI always generates complete files, never partial outputs
- 📖 **NEW v0.5.0**: Existing files are automatically read for context
- 🔀 **NEW v0.5.0**: Automatic Git commits after each file operation
- 🌐 **NEW v0.5.1**: Language/framework context maintained across all tasks
- 📝 **NEW v0.5.1**: First task always creates Documentation.md with complete scope
- 🎯 **NEW v0.5.2**: Tasks categorized as ESSENTIAL and OPTIONAL
- 🎮 **NEW v0.5.2**: Interactive menu to choose which tasks to execute
- 🔍 **NEW v0.5.3**: Intelligent search that suggests directories when file is not found
- 📁 **NEW v0.5.3**: Automatic navigation to directories found during search

## Installation

### Prerequisites

- Python 3.10 or higher
- OLLAMA installed and running

### Installing OLLAMA

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or visit https://ollama.ai for other options
```

### Installing XandAI

```bash
# Clone the repository
git clone https://github.com/yourusername/xandai
cd xandai

# Install the tool
pip install .

# Or for development
pip install -e .
```

## Usage

### Starting XandAI

```bash
# Using default endpoint (http://localhost:11434)
xandai

# Specifying custom endpoint
xandai --endpoint http://192.168.1.100:11434
```

### Available Commands

#### Basic Commands

- `/help` - Shows detailed help message
- `/models` - Lists and allows selecting available models
- `/clear` - Clears the screen
- `/exit` or `/quit` - Exits XandAI
- `/shell` - Enables/disables automatic shell command execution
- `/enhance` - Enables/disables automatic prompt enhancement
- `/enhance_code <description>` - **NEW v0.4.9**: Improves existing code without creating new files
- `/task <description>` - Executes complex task divided into steps
- `/debug` - Enables/disables debug mode

#### File Commands

- `/file create <path> [content]` - Creates a new file
- `/file edit <path> <content>` - Edits an existing file
- `/file append <path> <content>` - Adds content to the end of a file
- `/file read <path>` - Reads and displays file content
- `/file delete <path>` - Deletes a file (with confirmation)
- `/file list [directory] [pattern]` - Lists files in a directory

### Usage Examples

#### Basic Conversation

```bash
[llama2:latest] > Hello! How are you?
# The model responds...

[llama2:latest] > Write a hello world in Python
# The model generates code...
```

#### Automatic Shell Command Execution (NEW!)

```bash
# Shell commands are executed automatically
[llama2:latest] > ls -la
# Lists files in current directory

[llama2:latest] > cd src
# Changes to src directory

[llama2:latest] > git status
# Shows git status

[llama2:latest] > pip install requests
# Installs Python package

# Disable automatic execution
[llama2:latest] > /shell
✓ Automatic shell command execution disabled
```

#### Automatically Enhanced Prompts (NEW!)

```bash
# Your original prompt:
[llama2:latest] > create a server.js file with express

# Is automatically enhanced to:
[Working Directory: /home/user/project]
[Files Referenced: server.js]
[Language: javascript, Framework: Express]

<task>
create a server.js file with express
</task>

[Instructions: Create complete, working code with proper error handling and comments]
```

#### 🏷️ Structured Action Tags (v0.4.2+)

XandAI now instructs the LLM to use special tags to organize and execute actions automatically:

```bash
# The LLM now structures responses with tags:

# For shell/terminal commands (executed automatically):
<actions>
mkdir api_project
cd api_project  
touch app.py requirements.txt
</actions>

# For examining files (executed automatically):
<read>
cat app.py
ls -la
dir /w
</read>

# For creating files (created automatically):
<code filename="app.py">
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)
</code>
```

**Advantages:**
- ⚡ **Automatic execution** of commands and scripts
- 📁 **Automatic creation** of files with correct names  
- 🔍 **Automatic reading** of files for analysis
- 🧹 **Clean interface** (tags don't appear in response)
- 🔄 **Compatibility** with traditional ``` blocks

#### Working with Files

```bash
# Create a Python file
[llama2:latest] > /file create hello.py print("Hello, World!")

# Read the file
[llama2:latest] > /file read hello.py

# Add more code
[llama2:latest] > /file append hello.py \nprint("Welcome to XandAI!")

# List Python files in current directory
[llama2:latest] > /file list . *.py

# List ALL Python files recursively
[llama2:latest] > /file list . *.py -r

# Search for file in parent and subdirectories
[llama2:latest] > /file search config.json
🔍 Searching for 'config.json' in C:\project and subdirectories...
🔍 Searching in parent directory: C:\Users
✓ Found: C:\Users\project_root\config.json
Do you want to read the file? (y/N)
```

#### Advanced File Search (v0.4.11 / Enhanced v0.5.3)

**New v0.5.3 feature - Intelligent Search with Directories:**

```bash
# When file is not found, suggests directories!
[llama2:latest] > /file search Documentation.md

🔍 Searching for 'Documentation.md' in C:\project...
⚠️  File 'Documentation.md' not found
File 'Documentation.md' not found. Searching for directories...

📁 Directories found:
  1. C:\project\youtube-clone\youtube-clone
  2. C:\project\docs

💡 Tip: Navigate to a directory and search again

Enter directory number to navigate (or Enter to cancel): 1

Executing: cd "youtube-clone\youtube-clone"
✓ Navigated to: C:\project\youtube-clone\youtube-clone
💡 Try searching for the file again with /file search

# Also shows similar files if found:
📄 Similar files found:
  1. documentation.txt
  2. Documentation.pdf
  3. docs/README.md

Enter file number to read (or Enter to cancel): _
```

**Traditional search (v0.4.11):**

```bash
# Search for file anywhere (parent directories and all subdirectories)
[llama2:latest] > /file search package.json
🔍 Searching in subdirectories...
🔍 Searching in parent directory...
✓ Found: ../package.json

# List recursively with pattern
[llama2:latest] > /file list src *.test.js -r
# Lists all test files in src/ and subdirectories

# List all files recursively
[llama2:latest] > /file list -r
# Shows ENTIRE project file structure
```

#### Saving Generated Code (v0.2.1)

When the assistant generates code, XandAI automatically names and saves:

```bash
[llama2:latest] > Create a function to calculate factorial

# Assistant generates code...

💾 1 code file available
Save code? (y/N): y
✓ 1 file(s) saved
# Automatically saved as: main.py (or factorial.py if mentioned)
```

## What's New in v0.2.1

### Cleaner Interface

- No longer prints each chunk during generation
- Shows only status: "Thinking...", "Writing code...", etc.
- Response formatted with inline syntax highlighting
- Fewer interruptions and unnecessary questions

### Automatic Bash Code Execution

When the assistant generates bash/shell code in code blocks, it is executed automatically:

```bash
# Assistente responde com:
```bash
mkdir novo_projeto
cd novo_projeto
echo "# Meu Projeto" > README.md
```

# XandAI executes automatically without asking!
```

### Intelligent File Naming

XandAI now automatically names files based on context:

- `"create a server"` → `server.py` or `server.js`
- `"make tests"` → `test.py` or `test_1.py`
- `"configuration"` → `config.json` or `config.yml`
- `"authentication"` → `auth.js` or `auth.py`

Only asks: "Save code? (y/N)" - no name required!

### Dangerous Command Detection

Destructive commands ask for confirmation:
- `rm -rf /`
- `rmdir /s`
- `taskkill /f`
- `format`
- E outros...

## Code Enhancement Mode (v0.4.9) 🔧

Use the `/enhance_code` command to improve existing code without creating new files:

```bash
[llama2:latest] > /enhance_code add error handling and documentation

# XandAI will:
# 1. Analyze all existing files
# 2. Identify problems and areas for improvement  
# 3. EDIT existing files (never create new ones)
# 4. Add: error handling, documentation, type hints
# 5. Fix: bugs, linting, vulnerabilities
# 6. Improve: performance, structure, readability
```

### What the command does:

**✅ Adds:**
- Error and exception handling
- Documentation (docstrings, comments)
- Type hints and proper typing
- Input validations
- Appropriate logging

**🔧 Fixes:**
- Bugs and syntax errors
- Linting issues
- Security vulnerabilities
- Code smells

**📈 Improves:**
- Performance and optimizations
- Structure and organization
- Variable and function names
- Overall readability

### Usage examples:

```bash
# Add error handling
/enhance_code add try/except and validations

# Improve documentation
/enhance_code add docstrings and type hints

# Fix issues
/enhance_code fix bugs and linting issues

# Optimize code
/enhance_code optimize performance and security

# General improvement
/enhance_code improve overall code quality
```

**⚠️ IMPORTANT:** This command NEVER creates new files, only improves existing ones!

## Automatic Git (v0.5.0) 🔀

XandAI now manages Git automatically for you:

### Features

**1. Automatic Initialization**
```bash
# If .git doesn't exist in directory:
🔧 Initializing Git repository...
✓ Git repository initialized
✓ Git commit: Initial commit - XandAI project initialized
```

**2. Automatic Commits**
Every file operation generates a commit:
```bash
# When creating file
✓ Git commit: XandAI: created app.py

# When editing file
✓ Git commit: XandAI: edited app.py

# When deleting file
✓ Git commit: XandAI: deleted old_file.py
```

**3. Complete History**
```bash
git log --oneline
# d4f5a6b XandAI: edited server.js
# c3d2e1f XandAI: created server.js
# b2a1c0d XandAI: created package.json
# a1b2c3d Initial commit - XandAI project initialized
```

### Enhanced AI (v0.5.0) 📄

**1. Always Generates Complete Files**
- AI now ALWAYS includes the entire file in `<code>` tags
- Forbidden to use "..." or omit parts of the code
- Ensures you never accidentally lose code

**2. Automatic File Reading**
When you mention an existing file, the AI receives:
```
[EXISTING FILE CONTENT - app.py]:
```
# All file content here
```
[END OF app.py]
⚠️ IMPORTANT: When editing this file, include the COMPLETE updated content!
```

### Benefits
- 🔒 **Automatic backup** of all changes
- 📝 **Complete traceability** of development
- 🚀 **No code loss** with always complete files
- ⏱️ **Temporal history** of entire project evolution

## Complex Task Mode (v0.4.0 / Enhanced v0.5.2)

Perfect for creating complete projects from scratch:

### New Enhancements (v0.5.2)

**1. Essential vs Optional Tasks** 🎯
- Each task is marked as [ESSENTIAL] or [OPTIONAL]
- Interactive menu allows choosing:
  - Execute only essentials (quick MVP)
  - Execute all (complete project)
  - Cancel execution

**2. Persistent Context** 🌐 (v0.5.1)
- Language and framework automatically detected
- Context maintained across ALL tasks
- Each task knows which technology is being used

**3. Mandatory Documentation.md** 📝 (v0.5.1)
The first task ALWAYS creates Documentation.md with:
- Project overview and objectives
- Complete feature list  
- Technical architecture and structure
- Technologies, languages and frameworks
- Development roadmap

### Complete Example

```bash
[llama2:latest] > /task create a blog system with React and Django

🔍 Language detected: python
🔍 Framework detected: Django

✅ Execution Plan Created!

┌─── Task Progress ───┐
│ ⏳ [E] Task 1: Create Documentation.md file with complete scope │
│ ⏳ [E] Task 2: Configure Django backend environment                 │
│ ⏳ [E] Task 3: Create data models for posts and users      │
│ ⏳ [E] Task 4: Implement REST API with Django REST Framework     │
│ ⏳ [E] Task 5: Configure React frontend environment                 │
│ ⏳ [E] Task 6: Create basic UI components                   │
│ ⏳ [E] Task 7: Integrate frontend with API                         │
│ ⏳ [E] Task 8: Add JWT authentication                        │
│ ⏳ [O] Task 9: Add unit tests                        │
│ ⏳ [O] Task 10: Implement Redis cache system               │
│ ⏳ [O] Task 11: Add pagination and advanced filters         │
│ ⏳ [O] Task 12: Configure CI/CD pipeline                        │
└──────────────────────────────────────────────────────────────────┘

📊 Resumo:
   Essential: 8 tasks
   Optional: 4 tasks

Choose an option:
  1. Execute only ESSENTIAL tasks
  2. Execute ALL tasks (essential + optional)
  3. Cancel

Your choice (1/2/3): _

━━━ Tarefa 1/8 ━━━
Create Documentation.md file with complete scope

[Language: python]
[Framework: Django]
[Task 1 of 8]
[Original Project Request: create a blog system with React and Django]

# AI cria Documentation.md com todo o escopo do projeto...
✓ Git commit: XandAI: created Documentation.md

━━━ Tarefa 2/8 ━━━  
Configure Django backend environment

[Language: python]    # ← Contexto mantido!
[Framework: Django]   # ← Contexto mantido!
[Task 2 of 8]

# AI configures Django knowing it's Python/Django...
```

### Como era antes vs Agora

**Antes (v0.4.x):**
```bash
[llama2:latest] > /task create a REST API with authentication and product CRUD

# XandAI will:
# 1. Analyze and divide into smaller sub-tasks
# 2. Show execution plan for approval
# 3. Execute each task sequentially:
#    - Shell commands are executed automatically
#    - Code is generated and saved to files
#    - Explanations are formatted elegantly
# 4. Maintain context between tasks
# 5. Show visual progress

✅ Execution Plan Created!
┌─── Task Progress ───┐
│ ⏳ Task 1: Configure project...        │
│ ⏳ Task 2: Install dependencies...     │
│ ⏳ Task 3: Create models...              │
│ ⏳ Task 4: Implement authentication...  │
│ ⏳ Task 5: Create CRUD endpoints...      │
└──────────────────────────────────────────┘
```

### Task Mode Usage Examples

```bash
# Create complete application
/task create a blog with React frontend and Node.js backend

# Configure development environment
/task configure Python environment with Docker and automated tests

# Implement complex feature
/task add real-time notification system with WebSockets

# Refactor existing code
/task refactor architecture to microservices
```

## Advanced Features

### Persistent History

XandAI automatically saves command history to `~/.xandai_history`. Use ↑↓ arrows to navigate through history.

### Autocompletion

Start typing a command and press TAB to autocomplete.

### Syntax Highlighting

When reading code files, XandAI automatically detects the language and applies appropriate syntax highlighting.

### Multiline Mode

For longer prompts, paste multi-line text directly into the prompt.

## Development

### Project Structure

```
xandai/
├── __init__.py          # Metadados do pacote
├── __main__.py          # Ponto de entrada
├── api.py               # Cliente da API OLLAMA
├── cli.py               # Interface CLI principal
└── file_operations.py   # File operations
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Com cobertura
pytest --cov=xandai
```

### Contributing

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Troubleshooting

### OLLAMA not running

```bash
# Check if OLLAMA is installed
ollama --version

# Start OLLAMA server
ollama serve

# Test connection
curl http://localhost:11434
```

### Model not available

```bash
# List installed models
ollama list

# Download a model
ollama pull llama2
```

### File permissions

If you encounter permission errors when creating/editing files, check directory permissions:

```bash
# Linux/macOS
chmod 755 .
```

## Security

- **Confirmations**: Destructive operations (like deleting files) always ask for confirmation
- **Backups**: When editing files, a temporary backup is created
- **Validation**: All file paths are validated before operations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OLLAMA team for the excellent local model server
- Python community for the amazing packages
- Inspired by tools like claude-code and qwen-CLI

## Roadmap

- [ ] Support for multiple simultaneous sessions
- [ ] Integration with version control (Git)
- [ ] Project templates
- [ ] Interactive file editing mode
- [ ] Support for other backends besides OLLAMA
- [ ] Optional web interface
- [ ] Plugins and extensions

## Contact

For questions, suggestions or contributions, open an issue on GitHub.
