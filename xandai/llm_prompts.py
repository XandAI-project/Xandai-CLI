"""
LLM Prompts Library
===================

Central repository for all LLM prompts used throughout the XandAI CLI system.
This file organizes prompts by category to improve maintainability and reduce code size.
"""

from typing import Dict, Optional


class TaskPrompts:
    """Prompts related to task management and execution"""
    
    # Tag usage instructions for different task types
    CODE_TASK_INSTRUCTIONS = """
🏷️ [MANDATORY TAG USAGE FOR CODE TASKS:]

📝 Creating/Editing Files:
- Use <code filename="appropriate_name.ext">your code here</code>
- Example: <code filename="app.py">print("Hello World")</code>
- ALWAYS include the full path if creating in subdirectories
- Include COMPLETE file content, not just snippets

📖 Reading Files First:
- Use <read>cat filename.ext</read> to read existing files before editing
- Example: <read>cat package.json</read>

🔧 Running Commands:
- Use <actions>command here</actions> for any shell/terminal commands
- Example: <actions>pip install flask</actions>

❌ NEVER use markdown ``` blocks for file creation - use <code> tags only!"""

    SHELL_TASK_INSTRUCTIONS = """
🏷️ [MANDATORY TAG USAGE FOR SHELL TASKS:]

🔧 Running Commands:
- Use <actions>command here</actions> for ALL shell commands
- Example: <actions>mkdir project-folder</actions>
- Example: <actions>cd project-folder && npm init -y</actions>

📖 Reading Files:
- Use <read>cat filename.ext</read> to read files
- Use <read>ls -la</read> to list directory contents

📝 Creating Files:
- Use <code filename="name.ext">content</code> if you need to create files
- Example: <code filename="package.json">{"name": "my-app"}</code>

❌ NEVER show bare commands - always wrap in <actions> tags!"""

    TEXT_TASK_INSTRUCTIONS = """
🏷️ [OPTIONAL TAG USAGE FOR TEXT TASKS:]

📖 Reading for Context:
- Use <read>cat filename.ext</read> to read files for analysis
- Example: <read>cat README.md</read>

📝 Creating Documentation:
- Use <code filename="doc.md">content</code> for documentation files
- Example: <code filename="README.md"># Project Title</code>

Most text tasks don't require special tags unless creating files or reading content."""

    COMPREHENSIVE_TAG_GUIDE = """
🏷️ [COMPREHENSIVE TAG USAGE GUIDE:]

📝 Creating/Editing Files (MOST COMMON):
- <code filename="path/to/file.ext">complete file content here</code>
- Example: <code filename="src/app.js">const express = require('express');</code>
- ALWAYS provide COMPLETE file content, not just changes
- Use proper file extensions (.py, .js, .html, .css, etc.)

📖 Reading Files Before Editing:
- <read>cat existing-file.ext</read> - read file content
- <read>ls -la</read> - list directory contents  
- <read>find . -name "*.js"</read> - find specific files
- ALWAYS read existing files before modifying them

🔧 Running Shell Commands:
- <actions>mkdir new-folder</actions> - create directories
- <actions>pip install package</actions> - install dependencies
- <actions>npm start</actions> - run applications
- <actions>git add . && git commit -m "message"</actions> - git operations

🎯 CRITICAL RULES:
❌ NEVER use ``` markdown blocks for file creation
❌ NEVER show bare shell commands without <actions> tags
✅ ALWAYS use <code filename="..."> for files
✅ ALWAYS use <actions> for commands  
✅ ALWAYS use <read> to check existing files first"""

    # Context-specific instructions
    EDIT_FILES_CONTEXT = """
🔄 [EDITING EXISTING FILES DETECTED:]
1. First use <read>cat filename.ext</read> to see current content
2. Then use <code filename="filename.ext">COMPLETE updated content</code>
3. NEVER show just the changes - provide the ENTIRE file content"""

    CREATE_FILES_CONTEXT = """
🆕 [CREATING NEW FILES DETECTED:]
1. Use <code filename="path/to/newfile.ext">complete file content</code>
2. Choose appropriate filename and extension
3. Include all necessary imports, dependencies, and complete implementation"""

    INSTALL_SETUP_CONTEXT = """
⚙️ [INSTALLATION/SETUP DETECTED:]
1. Use <actions>command here</actions> for all installation commands
2. Example: <actions>pip install flask</actions>
3. Example: <actions>npm install express</actions>"""

    TEST_RUN_CONTEXT = """
🚀 [TESTING/RUNNING DETECTED:]
1. Use <actions>command</actions> for running tests or applications  
2. Example: <actions>python app.py</actions>
3. Example: <actions>npm test</actions>"""

    FINAL_TAG_REMINDER = """
🎯 [FINAL REMINDER - MANDATORY TAG USAGE:]
- Every code/file creation MUST use <code filename="...">content</code>
- Every shell command MUST use <actions>command</actions>  
- Reading files MUST use <read>command</read>
- NO exceptions - tags are required for all implementations!
- The system will automatically execute these tags for you"""

    @staticmethod
    def get_task_instructions(task_type: str) -> str:
        """
        Get tag usage instructions for a specific task type
        
        Args:
            task_type: Type of task ('code', 'shell', 'text', 'mixed')
            
        Returns:
            Appropriate instruction string
        """
        if task_type == 'code':
            return TaskPrompts.CODE_TASK_INSTRUCTIONS
        elif task_type == 'shell':
            return TaskPrompts.SHELL_TASK_INSTRUCTIONS
        elif task_type == 'text':
            return TaskPrompts.TEXT_TASK_INSTRUCTIONS
        else:
            return TaskPrompts.COMPREHENSIVE_TAG_GUIDE


class BreakdownPrompts:
    """Prompts for task breakdown and project analysis"""
    
    TASK_BREAKDOWN_TEMPLATE = """[INTELLIGENT TASK BREAKDOWN REQUEST]

Please carefully analyze the following request and break it down into smaller, specific tasks:

<request>
{original_request}
</request>

🎯 **CRITICAL ANALYSIS REQUIREMENTS:**

1. **PROJECT TYPE DETECTION**: First determine what type of project this is:
   - Frontend/Client-side (HTML/CSS/JS, React, Vue, static sites)
   - Backend/Server-side (APIs, databases, server applications)
   - Fullstack (both frontend and backend components)
   - Desktop/Mobile application
   - Data/Script/Tool (utility scripts, data processing)

2. **INTELLIGENT TASK PRIORITIZATION**:
   - [ESSENTIAL]: Core tasks needed for basic functionality
   - [OPTIONAL]: Enhancements, optimizations, extra features

🚨 **AVOID COMMON MISTAKES:**

- Do NOT assume backend frameworks (Flask/Django) unless explicitly mentioned
- Do NOT force documentation files unless specifically requested
- Do NOT suggest irrelevant dependencies or setup steps
- Do NOT create generic backend tasks for frontend-only projects
- CAREFULLY read what the user actually wants
- Do NOT include code snippets, commands, or technical details in task descriptions
- Do NOT include HTML, CSS, JavaScript, or any programming language syntax in tasks

📋 **TASK BREAKDOWN EXAMPLES BY PROJECT TYPE:**

**For Frontend/Client-side projects:**
1. [ESSENTIAL] Create main HTML structure with semantic elements
2. [ESSENTIAL] Implement responsive CSS styling using Bootstrap framework
3. [ESSENTIAL] Add JavaScript functionality for user interactions
4. [ESSENTIAL] Test basic functionality across different browsers
5. [OPTIONAL] Add responsive design improvements

**For Backend/API projects:**
1. [ESSENTIAL] Setup project structure and install dependencies
2. [ESSENTIAL] Create main application file with basic routing
3. [ESSENTIAL] Implement core API endpoints for data operations
4. [ESSENTIAL] Add basic error handling and validation
5. [OPTIONAL] Add comprehensive testing suite

**For Fullstack projects:**
1. [ESSENTIAL] Create frontend interface with user interactions
2. [ESSENTIAL] Setup backend API with data endpoints
3. [ESSENTIAL] Implement data flow between frontend and backend
4. [ESSENTIAL] Test integration between frontend and backend
5. [OPTIONAL] Add advanced features and optimizations

🎯 **CURRENT REQUEST CONTEXT:**
- Detected Language: {language}
- Detected Framework: {framework}
- Working Directory: {working_directory}

📝 **MANDATORY OUTPUT FORMAT:**

You MUST follow this EXACT format:

1. [ESSENTIAL] Create HTML structure for main interface
2. [ESSENTIAL] Implement CSS styling with responsive design
3. [ESSENTIAL] Add JavaScript functionality for user interactions
4. [OPTIONAL] Add additional UI enhancements

🚨 **CRITICAL FORMATTING RULES:**

- Start each line with number and period (1. 2. 3. etc)
- Follow with priority marker [ESSENTIAL] or [OPTIONAL]
- Write clear, descriptive task in plain English
- Do NOT include code, commands, file names, or technical syntax
- Do NOT include HTML tags, CSS properties, JavaScript functions
- Do NOT include shell commands like mkdir, cd, echo
- Keep descriptions between 30-100 characters
- Focus on WHAT to do, not HOW to do it

Generate ONLY the numbered task list. Be precise, clear, and relevant to the actual request."""

    @staticmethod
    def get_breakdown_prompt(original_request: str, context: Dict[str, str]) -> str:
        """
        Generate a task breakdown prompt with context
        
        Args:
            original_request: User's original request
            context: Dictionary with language, framework, working_directory
            
        Returns:
            Formatted breakdown prompt
        """
        return BreakdownPrompts.TASK_BREAKDOWN_TEMPLATE.format(
            original_request=original_request,
            language=context.get('language', 'Not detected'),
            framework=context.get('framework', 'Not detected'),
            working_directory=context.get('working_directory', 'Current folder')
        )


class ContextPrompts:
    """Prompts for contextual instructions and guidance"""
    
    DOCUMENTATION_CONTEXT = """
[Original Project Request: {original_request}]

[IMPORTANT: Create a comprehensive Documentation.md that includes:]
- Project overview and objectives
- Complete feature list based on the original request
- Technical architecture and structure
- Technologies, languages and frameworks to be used
- Development roadmap
- Any other relevant project information"""

    FILE_STRUCTURE_CONTEXT = """
[CURRENT PROJECT STRUCTURE:]
{file_structure}

[IMPORTANT: Always check existing files before creating new ones]
[CRITICAL: Do not overwrite existing files unless explicitly asked]
[Context: Files listed above already exist in the project]"""

    RECENT_TASKS_CONTEXT = """
[RECENTLY COMPLETED TASKS:]
{recent_tasks}
[IMPORTANT: Build upon the work already done above]"""

    CONVERSATION_CONTEXT = """**CONVERSATION CONTEXT:**
{conversation_context}

**CURRENT TASK REQUEST:**
{current_request}

**CONTEXT INTEGRATION INSTRUCTIONS:**
- Consider the conversation history when breaking down this task
- Reference previous work, decisions, and context when relevant
- Maintain consistency with established patterns and preferences
- Build upon existing knowledge and avoid redundant explanations"""

    @staticmethod
    def get_documentation_context(original_request: str) -> str:
        """Get documentation context with original request"""
        return ContextPrompts.DOCUMENTATION_CONTEXT.format(
            original_request=original_request
        )

    @staticmethod
    def get_file_structure_context(file_structure: str) -> str:
        """Get file structure context"""
        return ContextPrompts.FILE_STRUCTURE_CONTEXT.format(
            file_structure=file_structure
        )

    @staticmethod
    def get_recent_tasks_context(recent_tasks: str) -> str:
        """Get recent tasks context"""
        return ContextPrompts.RECENT_TASKS_CONTEXT.format(
            recent_tasks=recent_tasks
        )

    @staticmethod
    def get_conversation_context(conversation_context: str, current_request: str) -> str:
        """Get conversation context wrapper"""
        return ContextPrompts.CONVERSATION_CONTEXT.format(
            conversation_context=conversation_context,
            current_request=current_request
        )


class ModePrompts:
    """Prompts for different operation modes (create/edit)"""
    
    CREATE_MODE_INSTRUCTIONS = """
[CREATE MODE ACTIVATED]
- Focus on creating new files and components
- Build from scratch using best practices
- Consider project structure and organization
- Use appropriate naming conventions"""

    EDIT_MODE_INSTRUCTIONS = """
[EDIT MODE ACTIVATED]
- Read existing files before making changes
- Preserve existing functionality
- Make targeted modifications only
- Maintain code style and patterns"""

    @staticmethod
    def get_mode_instructions(mode: str, confidence: int) -> str:
        """
        Get mode-specific instructions
        
        Args:
            mode: 'create' or 'edit'
            confidence: Confidence level (0-100)
            
        Returns:
            Mode instruction string
        """
        if mode == 'create':
            return ModePrompts.CREATE_MODE_INSTRUCTIONS
        elif mode == 'edit':
            return ModePrompts.EDIT_MODE_INSTRUCTIONS
        else:
            return ""


class ModeInstructions:
    """Mode-specific instructions for edit/create modes"""
    
    EDIT_MODE_INSTRUCTIONS = [
        "\n## EDIT MODE DETECTED",
        "🚨 CRITICAL: The user wants to UPDATE/MODIFY an existing project, NOT create a new one!",
        "",
        "**PRESERVATION-FIRST Edit Mode Instructions:**",
        "- ALWAYS read existing files first using <read> tags (multiple files in ONE <read> block)",
        "- PRESERVE ALL existing code: functions, endpoints, classes, variables, imports",
        "- NEVER delete or remove existing functionality unless explicitly requested",
        "- Make ONLY the specific changes requested - keep everything else identical",
        "- When editing files, provide the COMPLETE file including all existing code",
        "- Use <code edit filename=\"...\"> for modifying existing files (FULL file content required)",
        "- Use <code create filename=\"...\"> ONLY for completely new files",
        "- 🚀 EFFICIENCY: Process multiple files in ONE response - don't stop after editing just one",
        "- Mark new additions with comments like // NEW: or // ADDED: for clarity",
        "- Maintain consistency with existing patterns and conventions",
        "- If you find config files (package.json, requirements.txt), UPDATE instead of creating new ones",
        "",
        "**CLEAN CODE FORMATTING:**",
        "- Provide ONLY executable code in <code> blocks - NO explanations inside files",
        "- NEVER add markdown blocks (```) inside source files",
        "- NEVER add implementation summaries or feature descriptions at end of files",
        "- Keep files in their proper format (HTML=HTML, JS=JS, CSS=CSS, not markdown)",
        "- Code blocks must contain ONLY the file content, no external commentary",
        "",
        "**ENDPOINT/API PRESERVATION:**",
        "- Keep ALL existing API endpoints, routes, and handlers",
        "- When adding new endpoints, integrate them without affecting existing ones",
        "- Preserve all existing middleware, error handlers, and utilities",
        "- Maintain existing database schemas, models, and connections",
        ""
    ]

    CREATE_MODE_INSTRUCTIONS = [
        "\n## CREATE MODE DETECTED", 
        "The user wants to CREATE a new project/functionality.",
        "",
        "**Instructions for Create Mode:**",
        "- Create a new and organized structure",
        "- Use <code create filename=\"...\"> for all new files",
        "- Use best practices for the chosen technology",
        "- Include necessary configuration files (package.json, requirements.txt, etc.)",
        "- Organize code in logical directory structure",
        "- Include basic documentation (README.md)",
        "- 🚀 EFFICIENCY: Create ALL necessary files in ONE response - don't create just one file",
        "- ALWAYS provide complete implementation, not just explanations",
        "- NEVER stop without creating the requested files and code",
        "",
        "**CLEAN CODE FORMATTING:**",
        "- Provide ONLY executable code in <code> blocks - NO explanations inside files",
        "- NEVER add markdown blocks (```) inside source files",
        "- NEVER add implementation summaries or feature descriptions at end of files",
        "- Keep files in their proper format (HTML=HTML, JS=JS, CSS=CSS, not markdown)",
        "- Code blocks must contain ONLY the file content, no external commentary",
        ""
    ]

    @staticmethod
    def get_default_mode_instructions(mode: str, confidence: float) -> list:
        """Get default mode instructions when confidence is low"""
        return [
            "\n## DEFAULT MODE (low detection confidence)",
            f"Detected mode: {mode} (confidence: {confidence:.0f}%)",
            "",
            "**General Instructions:**",
            "- ALWAYS read existing files first if relevant",
            "- If important existing files exist, use <code edit filename=\"...\"> instead of creating new ones",
            "- If no relevant structure exists, use <code create filename=\"...\"> to create a new organized one",
            "- Use good judgment based on the user prompt context",
            "- ALWAYS provide real implementation with functional code",
            "- NEVER stop without completing the requested task",
            ""
        ]

    @staticmethod
    def get_mode_instructions(mode: str, confidence: float) -> str:
        """
        Get mode-specific instructions based on detected mode
        
        Args:
            mode: Detected mode ('edit' or 'create')
            confidence: Confidence level (0-100)
            
        Returns:
            Mode instruction string
        """
        if mode == 'edit':
            return '\n'.join(ModeInstructions.EDIT_MODE_INSTRUCTIONS)
        elif mode == 'create':
            return '\n'.join(ModeInstructions.CREATE_MODE_INSTRUCTIONS)
        else:
            return '\n'.join(ModeInstructions.get_default_mode_instructions(mode, confidence))


class TagInstructions:
    """Basic tag usage instructions for LLM"""
    
    BASIC_TAG_INSTRUCTIONS = """

[MANDATORY TAGS FOR ACTIONS - CLEAN CODE ONLY]

⚡ EFFICIENCY TIP: Process multiple files in ONE response! Don't stop after editing just one file.

1. For shell/terminal commands:
   ✅ RIGHT: <actions>mkdir my-project</actions>
   ✅ RIGHT: <actions>pip install flask</actions>
   ❌ WRONG: ```bash
             mkdir my-project
             ```
   ❌ WRONG: Just describing: "Create a folder called my-project"

2. For editing existing files:
   ✅ RIGHT: <code edit filename="app.py">
             from flask import Flask
             app = Flask(__name__)
             if __name__ == '__main__':
                 app.run(debug=True)
             </code>
   ❌ WRONG: <code filename="app.py"> (missing edit/create)
   ❌ WRONG: Adding explanations at end of file
   
3. For creating new files:
   ✅ RIGHT: <code create filename="config.py">
             DEBUG = True
             SECRET_KEY = 'dev-key'
             </code>
   ❌ WRONG: <code filename="config.py"> (missing edit/create)

4. For reading existing files:
   ✅ RIGHT: <read>cat app.py</read>
   ✅ RIGHT: <read>ls -la</read>
   ❌ WRONG: ```bash
             cat app.py
             ```
   ❌ WRONG: Just describing: "Check the contents of app.py"

🚀 MULTIPLE OPERATIONS EXAMPLES:

✅ EXCELLENT - Process multiple files in ONE response:
   <read>
   cat app.py
   cat config.py
   ls templates/
   </read>
   
   <code edit filename="app.py">
   # Updated app.py content here
   </code>
   
   <code edit filename="config.py">
   # Updated config.py content here
   </code>
   
   <code create filename="templates/base.html">
   # New template content here
   </code>

❌ INEFFICIENT - Don't stop after just one operation:
   "I'll start by reading app.py and then wait for further instructions..."

CRITICAL RULES:
- ALWAYS use <actions> for commands (mkdir, pip, npm, git, etc.)
- ALWAYS use <code edit filename="..."> for editing existing files
- ALWAYS use <code create filename="..."> for creating new files
- ALWAYS use <read> for examining files
- NEVER use ``` blocks for files that should be created/edited
- NEVER just describe actions - use the tags!
- The old <code filename="..."> format is deprecated - always specify edit or create
- 🚀 BATCH OPERATIONS: Do multiple file operations in ONE response for efficiency

🚫 CLEAN CODE FORMATTING RULES:
- Code blocks must contain ONLY the file content - no explanations or summaries
- NEVER add markdown blocks (```) inside source files
- NEVER add implementation descriptions at the end of files
- Keep files in their proper format (HTML files = HTML, JS files = JavaScript, etc.)
- Do NOT mix markdown with other formats (no markdown inside HTML/CSS/JS files)
- Provide clean, executable code without embedded documentation
"""


class HelpText:
    """CLI help documentation"""
    
    HELP_CONTENT = """
# Available Commands

- `/help` - Shows this help message
- `/models` - Lists available models
- `/clear` - Clears the screen
- `/exit` or `/quit` - Exits XandAI
- `/file <command> <file> [content]` - File operations
- `/shell` - Toggles automatic shell command execution
- `/enhance` - Toggles automatic prompt enhancement
- `/enhance_code <description>` - Improves existing code (adds details, fixes bugs)
- `/task <description>` - Executes complex task divided into steps
- `/flush` - Manually flush LLM context history to free up tokens
- `/context` - Show current context usage status and token percentage
- `/better` - Toggle better prompting system (two-stage prompt enhancement)
- `/debug` - Toggles debug mode (shows complete model responses)
- `/session <command>` - Session management commands
- `/history <command>` - Robust conversation history management

## File Commands

- `/file create <path> [content]` - Creates a file
- `/file edit <path> <content>` - Edits a file
- `/file append <path> <content>` - Adds content to file
- `/file read <path>` - Reads a file
- `/file delete <path>` - Deletes a file
- `/file list [directory] [pattern] [-r]` - Lists files (use -r for recursive search)
- `/file search <filename>` - Searches for file in parent and subdirectories

## Session Commands

- `/session info` - Shows information about current/previous session
- `/session clear` - Clears current session and archives it
- `/session backups` - Lists available session backups
- `/session restore <backup_name>` - Restores a session backup
- `/session save` - Manually saves current session

## History Commands

- `/history` - Shows conversation status and statistics
- `/history export [format]` - Exports conversation (json/markdown/txt)
- `/history summarize` - Forces conversation summarization
- `/history optimize` - Forces context optimization
- `/history stats` - Shows detailed conversation statistics
- `/history clear` - Clears conversation history (with confirmation)

## Automatic Shell Command Execution

When enabled, common shell commands are executed automatically:
- `ls`, `dir`, `cd`, `mkdir`, `rm`, `cp`, `mv`, etc.
- `git`, `npm`, `pip`, `python`, etc.
- Comandos com pipes `|` e redirecionamentos `>`, `>>`

## Prompt Enhancement

When enabled, your prompts are enhanced with:
- Context of mentioned files
- `<task>` tags for clear instructions
- Language and framework detection
- Current directory context

## Code Enhancement Mode

Use `/enhance_code` to improve existing code:

```
/enhance_code add error handling and type hints

# XandAI will:
1. Analyze all existing files
2. Identify problems and areas for improvement
3. EDIT existing files (never create new ones)
4. Add: error handling, documentation, type hints
5. Fix: bugs, linting issues, vulnerabilities
6. Improve: performance, structure, readability
```

⚠️ IMPORTANT: This command NEVER creates new files, only improves existing ones!

## Complex Task Mode

Use `/task` for large projects that need to be divided:

```
/task create a REST API with JWT authentication and user CRUD

# XandAI will:
1. Analyze and divide into sub-tasks
2. Show execution plan
3. Execute each task sequentially
4. Code and commands are processed automatically
5. Explanations are shown as formatted text
```

## Examples

```
# Shell commands (executed automatically)
ls -la
cd src
mkdir new_project

# File commands
/file create test.py print("Hello World")
/file read test.py

# Automatically enhanced prompts
"create a server.js file with express"
→ [Files: server.js] [Language: javascript, Framework: Express]
   <task>create a server.js file with express</task>
```
"""


class CLIPrompts:
    """Prompts used in the main CLI operations"""
    
    ANALYSIS_PROMPT_TEMPLATE = """You are a prompt analysis expert. Your job is to analyze user requests and provide a detailed, enhanced version that will get better results from an AI assistant.

ORIGINAL USER REQUEST:
"{original_prompt}"

ANALYSIS TASK:
1. Identify what the user is trying to accomplish
2. Determine what additional context or details would be helpful
3. Suggest specific requirements, constraints, or preferences
4. Consider technical details, best practices, or standards that should be included
5. Think about potential edge cases or considerations

ENHANCEMENT REQUIREMENTS:
- Provide specific technical requirements when relevant
- Suggest appropriate technologies or frameworks if not specified
- Include relevant best practices or standards
- Consider user experience and accessibility
- Think about performance, security, and maintainability
- Suggest clear deliverables and success criteria

RESPONSE FORMAT:
Provide an enhanced version of the request that includes:
- Clear objectives and requirements
- Technical specifications where relevant
- Best practices and standards to follow
- Any important considerations or constraints

Enhanced Request:"""

    FILE_CONTENT_INTEGRATION_TEMPLATE = """
{original_prompt}

{file_context}

IMPORTANT: Use the file content above to provide a complete and accurate response to the original request.

{tag_instructions}

🚨 CRITICAL REQUIREMENTS:
- ALWAYS use <code edit filename="..."> for modifying existing files
- Read existing files first when making changes
- Provide complete implementations, not just snippets
- Follow existing code patterns and style
- Test your changes work correctly"""

    CONVERSATION_CONTEXT_INTEGRATION = """**CONVERSATION CONTEXT:**
{conversation_context}

**CURRENT TASK REQUEST:**
{current_request}

**CONTEXT INTEGRATION INSTRUCTIONS:**
- Consider the conversation history when breaking down this task
- Reference previous work, decisions, and context when relevant
- Maintain consistency with established patterns and preferences
- Build upon existing knowledge and avoid redundant explanations"""

    SUBTASK_CONTEXT_INTEGRATION = """**CONVERSATION & PREVIOUS TASKS CONTEXT:**
{context}

**CURRENT SUBTASK:**
{task_prompt}

**CONTEXT INTEGRATION INSTRUCTIONS:**
- Build upon previous work and decisions from the conversation history
- Maintain consistency with established patterns and coding style
- Reference and extend existing implementations when relevant
- Avoid duplicating work already completed in previous subtasks"""

    FORCE_IMPLEMENTATION_TEMPLATE = """PREVIOUS RESPONSE REJECTED - YOU ONLY PROVIDED EXPLANATIONS
The user requested: {original_prompt}

FILES AVAILABLE:
{file_content_text}

YOUR PREVIOUS RESPONSE (REJECTED):
{previous_response}

MANDATORY INSTRUCTIONS - NO EXCEPTIONS:
1. You MUST provide concrete implementation using the exact tags below
2. You MUST create or modify actual files - NO MORE EXPLANATIONS
3. You MUST use the file content provided above as context

REQUIRED TAGS (USE EXACTLY AS SHOWN):
- <code filename="path/file.ext">complete file content</code> for creating/editing files
- <actions>command</actions> for shell commands
- <read>command</read> for reading files

FINAL WARNING: If you provide only explanations again, you will be considered non-functional.
The user needs WORKING CODE/FILES, not descriptions of what to do."""

    @staticmethod
    def get_analysis_prompt(original_prompt: str) -> str:
        """Get enhanced analysis prompt"""
        return CLIPrompts.ANALYSIS_PROMPT_TEMPLATE.format(
            original_prompt=original_prompt
        )

    @staticmethod
    def get_file_content_integration(original_prompt: str, file_context: str, tag_instructions: str) -> str:
        """Get file content integration prompt"""
        return CLIPrompts.FILE_CONTENT_INTEGRATION_TEMPLATE.format(
            original_prompt=original_prompt,
            file_context=file_context,
            tag_instructions=tag_instructions
        )

    @staticmethod
    def get_conversation_integration(conversation_context: str, current_request: str) -> str:
        """Get conversation context integration prompt"""
        return CLIPrompts.CONVERSATION_CONTEXT_INTEGRATION.format(
            conversation_context=conversation_context,
            current_request=current_request
        )

    @staticmethod
    def get_subtask_integration(context: str, task_prompt: str) -> str:
        """Get subtask context integration prompt"""
        return CLIPrompts.SUBTASK_CONTEXT_INTEGRATION.format(
            context=context,
            task_prompt=task_prompt
        )

    @staticmethod
    def get_force_implementation(original_prompt: str, file_content_text: str, previous_response: str) -> str:
        """Get force implementation prompt"""
        # Truncate previous response if too long
        truncated_response = previous_response[:500] + '...' if len(previous_response) > 500 else previous_response
        
        return CLIPrompts.FORCE_IMPLEMENTATION_TEMPLATE.format(
            original_prompt=original_prompt,
            file_content_text=file_content_text,
            previous_response=truncated_response
        )


# Export the main prompt classes for easy importing
__all__ = [
    'TaskPrompts',
    'BreakdownPrompts', 
    'ContextPrompts',
    'ModePrompts',
    'ModeInstructions',
    'TagInstructions',
    'HelpText',
    'CLIPrompts'
]
