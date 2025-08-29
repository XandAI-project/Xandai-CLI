# LLM Prompt Encoding System - Technical Specification

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tag-Based Encoding System](#tag-based-encoding-system)
4. [Prompt Enhancement Engine](#prompt-enhancement-engine)
5. [Response Processing Pipeline](#response-processing-pipeline)
6. [Error Handling and Recovery](#error-handling-and-recovery)
7. [Performance Optimizations](#performance-optimizations)
8. [Future Improvements](#future-improvements)

---

## Overview

The XandAI CLI implements a sophisticated prompt encoding system that structures communication between users and Large Language Models (LLMs) through a standardized tag-based protocol. This system enables automatic execution of shell commands, file operations, and code generation while maintaining strict control over the interaction flow.

### Key Features
- **Structured Response Format**: XML-like tags for different operation types
- **Automatic Execution**: Direct execution of tagged operations without user intervention
- **Context Enhancement**: Intelligent prompt augmentation with system and project context
- **Error Recovery**: Automatic error handling with LLM-assisted correction
- **Security Controls**: Dangerous command detection and confirmation prompts

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    XandAI CLI Architecture                   │
├─────────────────────────────────────────────────────────────┤
│  User Input                                                 │
│       ↓                                                     │
│  PromptEnhancer  ──→  Context Detection & Enhancement       │
│       ↓                                                     │
│  LLM API Call   ──→  OLLAMA Integration                     │
│       ↓                                                     │
│  Response Parser ──→  Tag Extraction & Validation          │
│       ↓                                                     │
│  ┌─────────────┬─────────────┬─────────────┐                │
│  │ <actions>   │ <read>      │ <code>      │                │
│  │ Shell Exec  │ File Reader │ File Writer │                │
│  └─────────────┴─────────────┴─────────────┘                │
│       ↓                                                     │
│  Output Display & Error Handling                           │
└─────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

- **`PromptEnhancer`**: Context detection, prompt augmentation, and instruction injection
- **`ShellExecutor`**: Cross-platform command execution and path management
- **`FileOperations`**: Safe file creation, editing, and validation
- **`TaskManager`**: Complex task decomposition and execution orchestration
- **`XandAICLI`**: Main coordination and response processing

---

## Tag-Based Encoding System

### Tag Specifications

#### 1. `<actions>` Tag - Shell Command Execution
**Purpose**: Execute shell/terminal commands automatically
**Syntax**: `<actions>command1\ncommand2\n...</actions>`

**Processing Rules**:
- Commands are extracted line by line
- Empty lines and comments are filtered out
- Cross-platform command conversion is applied
- Dangerous commands trigger confirmation prompts
- Failed commands trigger automatic LLM error recovery

**Example**:
```xml
<actions>
mkdir project_folder
cd project_folder
pip install flask
git init
</actions>
```

**Implementation Details**:
```python
actions_blocks = re.findall(r'<actions>(.*?)</actions>', response, re.DOTALL | re.IGNORECASE)
for actions in actions_blocks:
    lines = [line.strip() for line in actions.strip().split('\n') if line.strip()]
    commands = [line for line in lines if not line.startswith('#')]
    
    for cmd in commands:
        converted_cmd = self.shell_exec.convert_command(cmd)
        success, output = self.shell_exec.execute_command(converted_cmd)
```

#### 2. `<read>` Tag - File Examination
**Purpose**: Read and examine existing files or directories
**Syntax**: `<read>command1\ncommand2\n...</read>`

**Processing Rules**:
- Commands for reading/listing files only
- Automatic execution without confirmation
- Results displayed to user and fed back to LLM context
- Support for cross-platform file listing commands

**Example**:
```xml
<read>
cat app.py
ls -la
dir src/
head -20 config.json
</read>
```

#### 3. `<code filename="...">` Tag - File Creation/Editing
**Purpose**: Create new files or edit existing ones
**Syntax**: `<code filename="path/to/file.ext">file_content</code>`

**Processing Rules**:
- **Complete File Content Required**: Never partial content
- **Filename Validation**: Must include valid filename with extension
- **Overwrite Protection**: Confirms before overwriting existing files
- **Directory Creation**: Automatically creates parent directories
- **Content Validation**: Syntax checking for known file types

**Example**:
```xml
<code filename="app.py">
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
</code>
```

### Tag Validation and Security

#### Security Measures
1. **Dangerous Command Detection**: Pattern matching for potentially harmful operations
2. **Path Traversal Prevention**: Validation of file paths and directory access
3. **Confirmation Prompts**: User confirmation for destructive operations
4. **Execution Isolation**: Commands run in controlled environment

#### Dangerous Command Patterns
```python
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bdel\s+.*\*',
    r'\bformat\b',
    r'\bfdisk\b',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bsudo\s+rm',
    r'\bchmod\s+777',
]
```

---

## Prompt Enhancement Engine

### Context Detection System

The `PromptEnhancer` class implements intelligent context detection to automatically augment user prompts with relevant information.

#### Detection Patterns

**File Pattern Recognition**:
```python
FILE_PATTERNS = [
    r'(?:file|script|code|arquivo|código)\s+(?:called\s+|chamado\s+)?([^\s,.:;]+\.[\w]+)',
    r'(?:em|in|no|na)\s+([^\s,.:;]+\.[\w]+)',
    r'([^\s,.:;]+\.(?:py|js|ts|java|c|cpp|rs|go|rb|php|html|css|json|xml|yaml|yml|md|txt|sh|bat))\b',
    r'`([^`]+\.[\w]+)`',
    r'"([^"]+\.[\w]+)"',
    r'\'([^\']+\.[\w]+)\'',
]
```

**Task Type Classification**:
- **Code Tasks**: Create, implement, develop, write code
- **Shell Tasks**: Install, run, execute, deploy, build
- **Analysis Tasks**: Review, analyze, debug, test
- **File Tasks**: Read, edit, modify, update files

### Enhancement Process

#### 1. Context Gathering
```python
def enhance_prompt(self, original_prompt: str, current_dir: str = None, os_info: str = None) -> str:
    # Extract mentioned files
    mentioned_files = self.extract_mentioned_files(original_prompt)
    
    # Detect task type
    task_type = self.detect_task_type(original_prompt)
    
    # Build context information
    context = self.build_context(current_dir, os_info, mentioned_files)
    
    # Apply enhancement strategy
    return self.apply_enhancement_strategy(original_prompt, context, task_type)
```

#### 2. Context Information Structure
```
[SYSTEM CONTEXT]
- Current Directory: /path/to/project
- Operating System: Windows/Linux/macOS
- Available Files: [list of relevant files]
- Project Structure: [directory tree if applicable]

[TASK CONTEXT]
- Detected Task Type: code/shell/analysis/file
- Mentioned Files: [extracted file references]
- Coding Keywords: [detected programming intentions]

[RESPONSE INSTRUCTIONS]
- Mandatory tag usage rules
- File handling requirements
- Error prevention guidelines
```

#### 3. Dynamic Instruction Injection

The system automatically injects task-specific instructions based on detected context:

**For Code Tasks**:
```
[MANDATORY: Use <code filename="appropriate_name.ext"> tags for file creation]
[CRITICAL: Include COMPLETE file content, never partial updates]
[RULE: Edit existing files instead of creating duplicates]
```

**For Shell Tasks**:
```
[MANDATORY: Use <actions> tags for shell commands]
[RULE: One command per line, no descriptions inside tags]
[SECURITY: Dangerous commands will require confirmation]
```

---

## Response Processing Pipeline

### Multi-Stage Processing

#### Stage 1: Tag Extraction
```python
def _process_special_tags(self, response: str, original_prompt: str):
    # Extract and process in order
    actions_blocks = re.findall(r'<actions>(.*?)</actions>', response, re.DOTALL | re.IGNORECASE)
    read_blocks = re.findall(r'<read>(.*?)</read>', response, re.DOTALL | re.IGNORECASE)
    code_matches = re.findall(r'<code\s+filename=["\']([^"\']+)["\']>(.*?)</code>', response, re.DOTALL | re.IGNORECASE)
```

#### Stage 2: Validation and Sanitization
- **Command Validation**: Check for malformed or dangerous commands
- **Path Validation**: Ensure safe file paths and prevent directory traversal
- **Content Validation**: Verify file content integrity and syntax

#### Stage 3: Execution with Error Handling
```python
for cmd in commands:
    converted_cmd = self.shell_exec.convert_command(cmd)
    
    if self._is_dangerous_command(converted_cmd):
        if not self._confirm_dangerous_command(converted_cmd):
            continue
    
    success, output = self.shell_exec.execute_command(converted_cmd)
    
    if not success:
        self._handle_command_error(cmd, output, original_prompt)
```

### Cross-Platform Command Conversion

The system automatically converts commands between different operating systems:

```python
def convert_command(self, command: str) -> str:
    if self.is_windows:
        # Convert Unix-style commands to Windows
        conversions = {
            r'^ls\b': 'dir',
            r'^cat\b': 'type',
            r'^rm\b': 'del',
            r'^cp\b': 'copy',
            r'^mv\b': 'move',
            r'^mkdir -p\b': 'mkdir',
            r'^grep\b': 'findstr',
        }
    else:
        # Convert Windows commands to Unix
        conversions = {
            r'^dir\b': 'ls -la',
            r'^type\b': 'cat',
            r'^del\b': 'rm',
            r'^copy\b': 'cp',
            r'^move\b': 'mv',
        }
```

---

## Error Handling and Recovery

### Automatic Error Recovery System

When a command fails, the system automatically engages the LLM for error analysis and correction:

```python
def _handle_command_error(self, failed_command: str, error_output: str, original_prompt: str):
    console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
    
    error_prompt = f"""
    The command '{failed_command}' failed with error: {error_output}
    Original context: {original_prompt}
    Please provide the correct command to fix this issue.
    """
    
    # Temporarily disable auto-execution to prevent loops
    temp_auto_execute = self.auto_execute_shell
    self.auto_execute_shell = False
    
    self.process_prompt(error_prompt)
    
    self.auto_execute_shell = temp_auto_execute
```

### Error Classification

**Common Error Types**:
1. **Path Errors**: Directory not found, permission denied
2. **Syntax Errors**: Malformed commands, invalid options
3. **Dependency Errors**: Missing packages, tools not installed
4. **Permission Errors**: Insufficient privileges, file locks

### Recovery Strategies

**Path Error Recovery**:
- Automatic directory creation suggestions
- Path normalization and cleaning
- Alternative path recommendations

**Dependency Error Recovery**:
- Package installation suggestions
- Alternative tool recommendations
- Environment setup guidance

---

## Performance Optimizations

### Caching and Memoization

#### Context Caching
```python
class PromptEnhancer:
    def __init__(self):
        self._context_cache = {}
        self._file_structure_cache = {}
        self._last_cache_update = None
```

#### Response Parsing Optimization
- **Compiled Regex Patterns**: Pre-compiled regex for tag extraction
- **Lazy Loading**: Context information loaded only when needed
- **Incremental Processing**: Process tags as they're found

### Memory Management

#### Stream Processing
Large responses are processed in streams to prevent memory overflow:

```python
def process_large_response(self, response_stream):
    buffer = ""
    for chunk in response_stream:
        buffer += chunk
        
        # Process complete tags as they arrive
        while self._has_complete_tag(buffer):
            tag, buffer = self._extract_next_tag(buffer)
            self._process_tag_immediately(tag)
```

### Execution Parallelization

#### Concurrent Tag Processing
- **Actions**: Sequential execution (order matters)
- **Read Operations**: Can be parallelized safely
- **File Operations**: Batched for efficiency

---

## Future Improvements

### Planned Enhancements

#### 1. Enhanced Context Awareness
- **Git Integration**: Automatic detection of Git repositories and branch information
- **Project Type Detection**: Framework-specific context (Flask, React, Django)
- **Dependency Analysis**: Automatic requirements.txt/package.json parsing

#### 2. Advanced Error Recovery
- **Learning System**: Learn from previous error resolutions
- **Confidence Scoring**: Rate the likelihood of fix success
- **Multi-Step Recovery**: Complex error resolution workflows

#### 3. Security Enhancements
- **Sandboxed Execution**: Isolated command execution environment
- **Permission System**: Granular control over operation types
- **Audit Logging**: Complete log of all automated operations

#### 4. Performance Improvements
- **Predictive Caching**: Pre-load likely-needed context
- **Background Processing**: Asynchronous context preparation
- **Response Streaming**: Real-time tag processing during LLM response

### Research Directions

#### 1. Semantic Tag Understanding
Moving beyond pattern matching to semantic understanding of tag content:
- **Intent Recognition**: Understanding the purpose behind commands
- **Context Validation**: Ensuring commands make sense in current context
- **Intelligent Suggestions**: Proactive improvement suggestions

#### 2. Multi-Modal Integration
- **Visual Context**: Screenshot analysis for GUI applications
- **Audio Instructions**: Voice command integration
- **Diagram Generation**: Automatic architecture diagrams from code

#### 3. Collaborative Features
- **Multi-User Sessions**: Shared development environments
- **Code Review Integration**: Automatic PR creation and review
- **Team Context**: Project-wide context sharing

---

## Conclusion

The XandAI CLI prompt encoding system represents a sophisticated approach to structuring human-LLM interaction for development tasks. By implementing a standardized tag-based protocol with automatic execution capabilities, it bridges the gap between natural language instructions and concrete system operations.

The system's strength lies in its balance of automation and safety, providing powerful execution capabilities while maintaining user control and security. The enhancement engine ensures that LLMs receive rich context for better decision-making, while the error recovery system provides resilience against common failure modes.

Future developments will focus on increasing intelligence and context awareness while maintaining the system's core principles of safety, reliability, and user empowerment.

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Authors**: XandAI Development Team  
**License**: Technical Specification - Internal Use
