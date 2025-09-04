# XandAI-CLI Usage Guide

XandAI-CLI is a powerful AI-assisted development tool that integrates with Ollama to provide intelligent code generation, project planning, and execution capabilities. This guide shows practical examples of what you can accomplish.

## 🚀 Getting Started

```bash
# Install XandAI-CLI
pip install -e .

# Run with default Ollama endpoint
xandai

# Run with custom endpoint and model
xandai --endpoint http://192.168.3.70:11434 --model "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:IQ4_XS"
```

## 💬 Chat Mode vs Task Mode

### Chat Mode
Interactive conversation for code assistance, debugging, and quick tasks.

### Task Mode
Structured project planning and generation with step-by-step execution.

```bash
xandai> /task create a REST API for video management
```

## 📁 Real Examples from Our Projects

### 1. Video Management API (Express.js)

**What it does:** A complete REST API for managing video content with CRUD operations.

**Generated with:**
```bash
xandai> /task create a video management API with Express.js, including validation and error handling
```

**Result:** Complete project structure:
```
simple-api/
├── server.js              # Main Express server
├── package.json           # Dependencies and scripts
├── routes/
│   └── videos.js          # Video CRUD endpoints
├── models/
│   └── video.js           # Video data model
├── middleware/
│   └── validation.js      # Request validation
└── config/
    └── database.js        # Database connection
```

**API Endpoints:**
- `GET /api/videos` - List all videos
- `GET /api/videos/:id` - Get specific video
- `POST /api/videos` - Create new video
- `PUT /api/videos/:id` - Update video
- `DELETE /api/videos/:id` - Delete video

### 2. Todo Application (Full Stack)

**What it does:** Complete web application with frontend and backend for task management.

**Generated with:**
```bash
xandai> /task create a todo application with HTML frontend and Node.js backend
```

**Result:**
```
todo-app/
├── server.js              # Express server
├── database.js            # SQLite database setup
├── routes/
│   └── todos.js           # Todo API routes
├── public/
│   ├── index.html         # Frontend interface
│   ├── css/style.css      # Styling
│   └── js/main.js         # Frontend logic
└── package.json           # Project configuration
```

**Features:**
- Add/edit/delete todos
- Mark todos as complete
- Persistent storage with SQLite
- Responsive web interface

### 3. Ollama Integration Testing

**What it does:** Python script for testing Ollama API connectivity and model responses.

**Generated with:**
```bash
xandai> create a Python script to test Ollama API connection and generate responses
```

**Result:** `script-testing/ollama_testing.py`
- Connection testing
- Model response generation
- Error handling
- Configurable endpoints

## 🎯 Common Use Cases

### 1. Quick Scripts and Automation

**Ask for scripts in chat mode:**

```bash
xandai> create a PowerShell script to find the 50 largest files on Windows
```

**AI Response:**
```powershell
# PowerShell script here...
```

**System prompts:** `⚡ Detected executable powershell code. Execute it? (y/N):`

### 2. Code Analysis and Debugging

```bash
xandai> read my server.js and explain what it does
```

**AI analyzes your code and provides:**
- Function explanations
- Potential improvements
- Bug identification
- Security considerations

### 3. File Operations in Chat Mode

The AI can suggest file operations that you can approve:

```html
<code create filename="utils/helper.js">
// Helper functions
const formatDate = (date) => {
    return date.toLocaleDateString();
};

module.exports = { formatDate };
</code>
```

**System prompts:** `📄 Create file 'utils/helper.js'? (y/N):`

### 4. Multi-language Development

**Python API:**
```bash
xandai> /task create a FastAPI application for user management
```

**JavaScript Frontend:**
```bash
xandai> /task create a React app that consumes my Python API
```

**Go Microservice:**
```bash
xandai> /task create a Go microservice for file processing
```

## 🔧 Advanced Features

### 1. Context-Aware Development

XandAI remembers your project context:

```bash
xandai> analyze this Express API
# AI reads and understands your API structure

xandai> create a Python version of this API
# AI creates Python equivalent using the same endpoints and logic
```

### 2. Intelligent File Detection

When AI generates code, it automatically:
- **Detects complete files** and offers to save them
- **Suggests appropriate filenames** based on content
- **Infers file types** from code structure
- **Creates directory structure** automatically

### 3. Command Execution

Multiple ways to execute code:

**Markdown blocks:**
```bash
ls -la
```

**Code tags:**
```html
<code type="bash">dir /s</code>
```

**Command blocks:**
```html
<commands>
npm install
npm start
</commands>
```

### 4. Debug Mode

Enable verbose logging:
```bash
xandai --debug
```

Or toggle in chat:
```bash
xandai> /debug true
```

## 🛠️ Development Workflow Examples

### Starting a New Project

```bash
# 1. Plan the project
xandai> /task create a blog system with user authentication

# 2. Review the generated structure
# 3. Execute the planned steps
# 4. Test and iterate in chat mode

xandai> add JWT authentication to the login endpoint
xandai> create unit tests for the user controller
```

### Analyzing Existing Code

```bash
# 1. Read existing code
xandai> read my entire project structure

# 2. Get suggestions
xandai> how can I improve the security of this API?

# 3. Generate improvements
xandai> create middleware for rate limiting
```

### Learning and Documentation

```bash
# Understand complex code
xandai> explain this React component step by step

# Generate documentation
xandai> create API documentation for my Express routes

# Learn new technologies
xandai> show me how to use Docker with this Node.js app
```

## 📊 Project Statistics

Based on our example projects:

| Project | Files Generated | Lines of Code | Features |
|---------|----------------|---------------|----------|
| Video API | 8 files | ~400 lines | CRUD, Validation, Middleware |
| Todo App | 7 files | ~350 lines | Frontend, Backend, Database |
| Ollama Testing | 1 file | ~65 lines | API Testing, Error Handling |

## 🎨 Customization

### Custom Endpoints
```bash
xandai --endpoint http://your-ollama-server:11434
```

### Custom Models
```bash
xandai --model "your-preferred-model"
```

### Configuration Files
Create `.xandai-config.json` for persistent settings.

## 🔍 Tips and Best Practices

1. **Be Specific:** More detailed requests yield better results
2. **Use Context:** Reference existing files for consistency
3. **Iterate:** Start simple and add complexity gradually
4. **Test Execution:** Always verify AI-generated scripts before running
5. **Save Important Code:** Use the file save feature for generated code
6. **Debug Mode:** Use verbose mode when troubleshooting

## 🚨 Safety Features

- **Execution Confirmation:** Always asks before running code
- **File Overwrite Protection:** Confirms before overwriting existing files
- **Backup Creation:** Creates `.backup` files when editing
- **Timeout Protection:** Commands timeout after 60 seconds
- **Error Handling:** Graceful error reporting and recovery

## 📚 Further Learning

- Explore the `/help` command for available features
- Use `/debug info` to see system information  
- Check the `example/` folder for more project templates
- Visit our documentation for advanced configuration

---

**XandAI-CLI: Where AI meets productivity in software development** 🚀
