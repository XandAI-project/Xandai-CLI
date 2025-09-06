"""
XandAI - Task Mode Processor
Enhanced task processing with robust parsing and streaming progress
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from xandai.history import HistoryManager
from xandai.integrations.base_provider import LLMProvider, LLMResponse


@dataclass
class TaskStep:
    """Represents a single task step"""

    step_number: int
    action: str  # 'create', 'edit', 'run'
    target: str  # filename or command
    description: str
    content: Optional[str] = None  # file content for create/edit
    commands: Optional[List[str]] = None  # commands for run


class TaskProcessor:
    """
    Enhanced task mode processor for structured project planning

    Features:
    - Converts high-level requests into ordered steps
    - Robust parsing with multiple fallback strategies
    - Clarifying questions for vague requests
    - Streaming progress indicators
    - Prevents duplicate file creation
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        history_manager: HistoryManager,
        verbose: bool = False,
    ):
        """Initialize task processor"""
        self.llm_provider = llm_provider
        self.history_manager = history_manager
        self.verbose = verbose

        self.system_prompt = self._build_system_prompt()

        # Vague request patterns to trigger clarifying questions
        self.vague_patterns = [
            r"^(create|make|build)\s+(an?\s+)?(app|website|api|tool|system)$",
            r"^help\s+(me|with).*$",
            r"^(do|fix|improve)\s+something$",
            r"^\w{1,10}$",  # Single word requests
            r"^.{1,15}$",  # Very short requests
        ]

    def process_task(self, user_request: str, console=None) -> Tuple[str, List[TaskStep]]:
        """
        Process task request and return structured plan

        Args:
            user_request: High-level task description
            console: Rich console for progress display (optional)

        Returns:
            Tuple of (raw_response, parsed_steps)
        """
        # Check if request is too vague and needs clarification
        if self._is_request_too_vague(user_request):
            clarifying_response = self._generate_clarifying_questions(user_request)
            return clarifying_response, []

        # Build enhanced prompt with context
        enhanced_prompt = self._build_task_prompt(user_request)

        # Get LLM response with streaming progress
        if console:
            console.print("[dim]🧠 Analyzing request...[/dim]")

        response = self._get_llm_response_with_progress(enhanced_prompt, console)

        # Parse response into steps with multiple fallback strategies
        if console:
            console.print("[dim]📋 Parsing task steps...[/dim]")

        steps = self._parse_response_steps_robust(response.content)

        # If parsing failed, try to salvage or regenerate
        if not steps:
            if console:
                console.print("[dim]🔧 Attempting recovery...[/dim]")
            steps = self._salvage_or_regenerate(user_request, response.content)

        # Add to conversation history
        self.history_manager.add_conversation(
            role="user",
            content=f"/task {user_request}",
            metadata={"mode": "task", "step_count": len(steps)},
        )

        self.history_manager.add_conversation(
            role="assistant",
            content=response.content,
            context_usage=str(response.context_usage),
            metadata={"mode": "task", "steps_generated": len(steps)},
        )

        return response.print_with_context(), steps

    def _is_request_too_vague(self, user_request: str) -> bool:
        """Check if request is too vague and needs clarification"""
        request_lower = user_request.lower().strip()

        # Check against vague patterns
        for pattern in self.vague_patterns:
            if re.match(pattern, request_lower, re.IGNORECASE):
                return True

        # Check for lack of technical detail
        tech_keywords = [
            "python",
            "javascript",
            "html",
            "css",
            "react",
            "flask",
            "django",
            "api",
            "database",
            "web",
            "cli",
            "gui",
            "mobile",
            "frontend",
            "backend",
        ]
        has_tech_keywords = any(keyword in request_lower for keyword in tech_keywords)

        # If no tech keywords and very short, consider vague
        if not has_tech_keywords and len(user_request.split()) < 4:
            return True

        return False

    def _generate_clarifying_questions(self, user_request: str) -> str:
        """Generate clarifying questions for vague requests"""
        questions = [
            "🤔 I need more details to create a proper plan. Could you clarify:",
            "",
            "• **What type of application?** (web app, mobile app, CLI tool, API, etc.)",
            "• **What technology stack?** (Python/Flask, JavaScript/React, HTML/CSS, etc.)",
            "• **What's the main functionality?** (what should it do?)",
            "• **Who's the target user?** (developers, end users, etc.)",
            "",
            "**Example requests:**",
            "- `/task create a web chat app with Python Flask and HTML/CSS`",
            "- `/task build a React todo app with local storage`",
            "- `/task create a Python CLI tool that processes CSV files`",
            "",
            "Please provide a more specific request and I'll create a detailed plan! 🚀",
        ]

        return "\\n".join(questions)

    def _get_llm_response_with_progress(self, prompt: str, console=None) -> LLMResponse:
        """Get LLM response with streaming progress indicators"""
        # Get conversation context to maintain continuity between chat and task modes
        context_messages = self.history_manager.get_conversation_context(limit=15)

        # Debug output for context sharing
        if self.verbose:
            from xandai.utils.os_utils import OSUtils

            OSUtils.debug_print(
                f"Task mode using {len(context_messages)} context messages from chat history",
                True,
            )
            OSUtils.debug_print(
                "🧠 Context-aware task processing: analyzing conversation for specific requirements",
                True,
            )

        # Prepare messages with context for unified experience
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation context (excluding system messages to avoid conflicts)
        context_without_system = [msg for msg in context_messages if msg.get("role") != "system"]
        messages.extend(context_without_system)

        # Debug output for final message count
        if self.verbose:
            from xandai.utils.os_utils import OSUtils

            OSUtils.debug_print(
                f"Task mode sending {len(messages)} total messages (including context)",
                True,
            )

        # Add current task request
        messages.append({"role": "user", "content": prompt})

        # Use streaming with in-place progress if console is available
        if console:
            try:
                # Use status context that updates in-place
                with console.status("[bold blue]Planning tasks...") as status:
                    current_chunks = 0

                    def progress_callback(message: str):
                        nonlocal current_chunks
                        if "chunks received" in message:
                            # Extract chunk count and update status
                            try:
                                current_chunks = int(message.split()[1])
                                status.update(
                                    f"[bold blue]Planning tasks... ({current_chunks} chunks received)[/bold blue]"
                                )
                            except:
                                status.update(
                                    f"[bold blue]Planning tasks... ({message})[/bold blue]"
                                )
                        else:
                            status.update(f"[bold blue]{message}[/bold blue]")

                    return self.llm_provider.chat(
                        messages=messages,
                        temperature=0.3,
                        stream=False,  # Tasks use non-streaming mode as requested
                    )
            except Exception:
                # Fallback to non-streaming
                console.print("[dim]⚠️ Streaming not available, using standard mode...[/dim]")
                return self.llm_provider.chat(
                    messages=messages,
                    temperature=0.3,
                    stream=False,  # Tasks use non-streaming mode
                )
        else:
            # Regular non-streaming mode for tasks
            return self.llm_provider.chat(
                messages=messages,
                temperature=0.3,
                stream=False,  # Tasks use non-streaming mode
            )

    def _parse_response_steps_robust(self, response: str) -> List[TaskStep]:
        """Parse LLM response into TaskStep objects with multiple fallback strategies"""
        steps = []

        # Extract and display folder structure if present
        folder_structure_match = re.search(
            r"FOLDER_STRUCTURE:\s*\n((?:.+\n)*?)(?=\n[A-Z]+:|\nSTEPS:|$)",
            response,
            re.MULTILINE,
        )
        if folder_structure_match:
            folder_structure = folder_structure_match.group(1).strip()
            if folder_structure:
                print(f"\\n[dim]Detected project structure:\\n{folder_structure}[/dim]")

        # Strategy 1: Look for formal STEPS: section
        steps_match = re.search(r"STEPS:\s*\n((?:\d+\s*-\s*.+\n?)*)", response, re.MULTILINE)
        if steps_match:
            step_lines = [
                line.strip() for line in steps_match.group(1).strip().split("\n") if line.strip()
            ]
            for line in step_lines:
                step = self._parse_step_line(line)
                if step:
                    steps.append(step)

        # Strategy 2: Look for numbered lists anywhere in response
        if not steps:
            numbered_pattern = r"(\d+)\s*[-.)]\s*(.+?)(?=\n\d+\s*[-.]|\n\n|$)"
            matches = re.findall(numbered_pattern, response, re.MULTILINE | re.DOTALL)
            for i, (num, desc) in enumerate(matches, 1):
                desc = desc.strip()
                if len(desc) > 5:  # Ignore very short descriptions
                    action, target = self._infer_action_from_description(desc)
                    steps.append(
                        TaskStep(
                            step_number=i,
                            action=action,
                            target=target,
                            description=desc,
                        )
                    )

        # Strategy 3: Look for action verbs and file references
        if not steps:
            steps = self._extract_steps_from_content(response)

        # Associate detailed content with steps
        if steps:
            self._associate_step_content(steps, response)

        return steps

    def _infer_action_from_description(self, description: str) -> Tuple[str, str]:
        """Infer action and target from description text"""
        desc_lower = description.lower()

        # Look for action keywords
        if any(word in desc_lower for word in ["create", "new", "add", "make", "build"]):
            action = "create"
        elif any(word in desc_lower for word in ["edit", "update", "modify", "change"]):
            action = "edit"
        elif any(word in desc_lower for word in ["run", "execute", "install", "start"]):
            action = "run"
        else:
            action = "create"  # default

        # Extract filename or command
        # Look for file extensions
        file_match = re.search(r"(\w+\.\w+)", description)
        if file_match:
            target = file_match.group(1)
        else:
            # Extract the main noun/object
            words = description.split()
            target = words[-1] if words else "task"

        return action, target

    def _extract_steps_from_content(self, response: str) -> List[TaskStep]:
        """Extract steps from any content that mentions file operations"""
        steps = []

        # Look for code edit blocks
        code_blocks = re.findall(r'<code edit filename="([^"]+)">', response)
        for i, filename in enumerate(code_blocks, 1):
            steps.append(
                TaskStep(
                    step_number=i,
                    action="create",
                    target=filename,
                    description=f"Create {filename}",
                )
            )

        # Look for command blocks
        command_blocks = re.findall(r"<commands>(.*?)</commands>", response, re.DOTALL)
        if command_blocks:
            cmd_content = command_blocks[0].strip()
            cmd_lines = [line.strip() for line in cmd_content.split("\n") if line.strip()]
            if cmd_lines:
                steps.append(
                    TaskStep(
                        step_number=len(steps) + 1,
                        action="run",
                        target="commands",
                        description="Run commands",
                        commands=cmd_lines,
                    )
                )

        return steps

    def _salvage_or_regenerate(self, user_request: str, failed_response: str) -> List[TaskStep]:
        """Attempt to salvage failed parsing or generate minimal steps"""

        # Try to create at least one meaningful step from the request
        request_lower = user_request.lower()
        steps = []

        # Detect common patterns and create basic steps
        if "web" in request_lower or "html" in request_lower:
            steps.append(TaskStep(1, "create", "index.html", "Create main HTML file"))
            if "css" in request_lower:
                steps.append(TaskStep(2, "create", "style.css", "Create CSS stylesheet"))

        if "python" in request_lower or "flask" in request_lower:
            steps.append(TaskStep(len(steps) + 1, "create", "app.py", "Create Python application"))
            steps.append(
                TaskStep(
                    len(steps) + 1,
                    "create",
                    "requirements.txt",
                    "Create dependencies file",
                )
            )

        if "react" in request_lower or "javascript" in request_lower:
            steps.append(
                TaskStep(
                    len(steps) + 1,
                    "create",
                    "package.json",
                    "Create package configuration",
                )
            )
            steps.append(
                TaskStep(
                    len(steps) + 1,
                    "create",
                    "src/App.js",
                    "Create main React component",
                )
            )

        # If still no steps, create a generic one
        if not steps:
            steps.append(TaskStep(1, "create", "main.py", f"Implement: {user_request}"))

        return steps

    def _build_system_prompt(self) -> str:
        """Build system prompt for task mode"""
        return """You are XandAI Task Mode - an expert at breaking down complex development requests into COMPLETE, structured project plans.

🧠 CONTEXT-AWARE PLANNING - CRITICAL:
1. ALWAYS analyze the PREVIOUS CONVERSATION CONTEXT first
2. If code was analyzed or discussed, use THAT SPECIFIC functionality
3. When user says "create a version of that API" or "write that in Python", they mean the SPECIFIC API/code discussed previously
4. DO NOT create generic examples - replicate the EXACT functionality, endpoints, features discussed
5. Use conversation context to understand specific requirements, endpoints, data models, business logic

CRITICAL PLANNING RULES:
6. Analyze the FULL project scope - don't miss any files
7. Plan the COMPLETE folder structure with ALL necessary files
8. Ensure imports only reference files that will be created
9. Include ALL configuration files, dependencies, and assets
10. Plan for proper separation of concerns (models, views, controllers, etc.)

PROJECT STRUCTURE REQUIREMENTS:
- List EVERY file needed for a complete, working project
- Include proper folder structure (src/, public/, templates/, static/, etc.)
- Add configuration files (package.json, requirements.txt, .env examples, etc.)
- Include database/model files if needed
- Add static assets (CSS, JS, images) if it's a web project
- Include test files if appropriate
- Add documentation files (README.md) when needed

IMPORT CONSISTENCY RULES:
- NEVER import from files that won't be created
- If you reference a module/file in imports, it MUST be in your step list
- Use relative imports correctly based on folder structure
- Verify all dependencies are installable

CRITICAL OUTPUT FORMAT:
```
PROJECT: [Brief project description]
LANGUAGE: [Primary language: python/javascript/etc]
FRAMEWORK: [If applicable: flask/react/express/etc]
ESTIMATED_TIME: [e.g., "2-3 hours"]

FOLDER_STRUCTURE:
project_name/
├── folder1/
│   ├── file1.ext          # Brief description of what this file does
│   │                      # Functions: main_function(), helper_function()
│   │                      # Exports: MainClass, utility_functions
│   └── file2.ext          # Brief description of what this file does
│                          # Functions: process_data(), validate_input()
│                          # Exports: DataProcessor, validators
├── folder2/
│   └── file3.ext          # Brief description of what this file does
│                          # Functions: api_handler(), error_handler()
│                          # Exports: router, middleware
└── file4.ext              # Main application entry point
                           # Functions: main(), initialize_app()
                           # Exports: app instance

STEPS:
1 - create folder1/file1.ext
2 - create folder1/file2.ext
3 - create folder2/file3.ext
4 - create file4.ext
5 - run: command here
```

🔍 CONTEXT ANALYSIS PRIORITY:
Before using generic examples, FIRST analyze the conversation context for:
- Specific API endpoints mentioned (GET /videos, POST /users, etc.)
- Data models discussed (Video, User, Product with specific fields)
- Business logic requirements (validation rules, authentication, etc.)
- Technology stack preferences mentioned in conversation
- Specific features or functionality that was analyzed or requested

If previous conversation contains code analysis or specific requirements,
REPLICATE THAT EXACT FUNCTIONALITY rather than creating generic examples.

EXAMPLES OF COMPLETE PROJECTS (use ONLY if no specific context exists):

Flask API:
```
api_project/
├── app.py              # Main Flask application entry point
│                       # Functions: create_app(), register_blueprints(), init_extensions()
│                       # Exports: app (Flask instance)
├── models.py           # Database models using SQLAlchemy
│                       # Classes: User, Product, Order (all inherit db.Model)
│                       # Functions: init_db(), create_tables()
│                       # Exports: db, User, Product, Order
├── routes.py           # API route definitions
│                       # Functions: register_routes(), get_all_users(), create_user()
│                       # Exports: api_bp (Blueprint)
├── config.py           # Application configuration settings
│                       # Classes: Config, DevelopmentConfig, ProductionConfig
│                       # Exports: config dictionary, get_config()
├── requirements.txt    # Python dependencies list
│                       # Content: flask, sqlalchemy, bcrypt, python-dotenv, pytest
├── .env.example        # Environment variables template
│                       # Variables: DATABASE_URL, SECRET_KEY, DEBUG
└── README.md           # Project documentation and setup instructions
                        # Sections: Installation, Usage, API Endpoints, Testing
```

Express API:
```
api_project/
├── server.js           # Main Express server entry point
│                       # Functions: startServer(), setupMiddleware(), setupRoutes()
│                       # Exports: app (Express instance)
├── package.json        # NPM configuration and dependencies
│                       # Scripts: start, dev, test, build
│                       # Dependencies: express, mongoose, bcryptjs, jsonwebtoken, cors
├── routes/
│   └── api.js          # API route definitions (/api/users, /api/auth)
│                       # Functions: getUsers(), createUser(), updateUser(), deleteUser()
│                       # Exports: router (Express Router instance)
├── models/
│   └── model.js        # Data models using Mongoose
│                       # Classes: User, Product (Mongoose schemas)
│                       # Functions: hashPassword(), comparePassword(), toJSON()
│                       # Exports: User, Product models
├── middleware/
│   └── auth.js         # Authentication middleware functions
│                       # Functions: verifyToken(), requireAuth(), checkPermissions()
│                       # Exports: auth middleware functions
├── config/
│   └── database.js     # Database connection configuration
│                       # Functions: connectDB(), closeDB(), getConnection()
│                       # Exports: connection instance
└── .env.example        # Environment variables template
                        # Variables: PORT, DB_URI, JWT_SECRET, NODE_ENV
```

React App:
```
react_app/
├── package.json        # NPM configuration and dependencies
│                       # Scripts: start, build, test, eject
│                       # Dependencies: react, react-dom, react-router-dom, axios
├── public/
│   └── index.html      # HTML template with React root element
│                       # Contains: <div id="root"></div>, meta tags
├── src/
│   ├── App.js          # Main React application component
│   │                   # Component: App (default export)
│   │                   # Functions: handleRouting(), initializeApp()
│   ├── App.css         # Main application styles
│   │                   # Styles: global styles, component classes
│   ├── index.js        # React DOM render entry point
│   │                   # Functions: render()
│   │                   # Exports: none (entry point)
│   └── components/
│       └── Component.js # Reusable UI components
│                        # Components: Header, Footer, Button (named exports)
│                        # Props: onClick, children, className, variant
│                        # Functions: handleClick(), validateProps()
```

QUALITY STANDARDS:
- Production-ready, complete projects
- No missing dependencies or broken imports
- Proper error handling and logging
- Security best practices
- Clean, well-documented code
- Immediate runnable state after completion

🎯 FINAL REMINDER:
1. Use CONVERSATION CONTEXT FIRST - if specific API/code was discussed, replicate it exactly
2. Plan the ENTIRE project structure - missing files break everything!
3. When in doubt, ask "What specific functionality was mentioned in the conversation?"

ALWAYS RESPOND IN ENGLISH."""

    def _build_task_prompt(self, user_request: str) -> str:
        """Build enhanced prompt with project context and conversation awareness"""
        context = self.history_manager.get_project_context()
        existing_files = self.history_manager.get_project_files()
        conversation_context = self.history_manager.get_conversation_context(limit=10)

        prompt_parts = [f"TASK REQUEST: {user_request}"]

        # Emphasize conversation context analysis
        if conversation_context:
            prompt_parts.append("\\n🧠 CRITICAL: Analyze the PREVIOUS CONVERSATION above for:")
            prompt_parts.append("- Specific code that was read/analyzed")
            prompt_parts.append("- Exact API endpoints mentioned (GET /videos, POST /users, etc.)")
            prompt_parts.append("- Data models with specific fields")
            prompt_parts.append("- Business logic and validation rules")
            prompt_parts.append("- Any specific functionality discussed")
            prompt_parts.append(
                "\\n❗ If the conversation contains specific code analysis, REPLICATE THAT EXACT functionality!"
            )
            prompt_parts.append(
                "❗ Do NOT create generic examples when specific requirements exist in conversation!"
            )

        # Add project context if available
        if context["framework"] or context["language"] or context["project_type"]:
            prompt_parts.append("\\nCURRENT PROJECT CONTEXT:")
            if context["language"]:
                prompt_parts.append(f"- Language: {context['language']}")
            if context["framework"]:
                prompt_parts.append(f"- Framework: {context['framework']}")
            if context["project_type"]:
                prompt_parts.append(f"- Type: {context['project_type']}")

        # Add existing files info
        if existing_files:
            prompt_parts.append(f"\\nEXISTING FILES ({len(existing_files)}):")
            for filepath in existing_files[:10]:
                prompt_parts.append(f"- {filepath}")
            if len(existing_files) > 10:
                prompt_parts.append(f"- ... and {len(existing_files) - 10} more")

            prompt_parts.append("\\n⚠️  IMPORTANT: Use 'edit' for existing files, not 'create'!")

        prompt_parts.append("\\n🚀 Generate a complete, executable plan with working code!")
        prompt_parts.append("🎯 REMEMBER: Use conversation context FIRST, generic examples LAST!")

        # Add mode-specific instruction
        project_mode = self._detect_project_mode()
        if project_mode == "edit":
            prompt_parts.append("\\n⚠️  EDIT MODE DETECTED:")
            prompt_parts.append("- You're modifying an existing project")
            prompt_parts.append("- Preserve existing functionality unless explicitly changing")
            prompt_parts.append("- Use 'edit' for existing files, 'create' for new files")
            prompt_parts.append("- Maintain consistency with existing code style and patterns")
        else:
            prompt_parts.append("\\n🆕 CREATE MODE:")
            prompt_parts.append("- You're creating a new project from scratch")
            prompt_parts.append("- Design a clean, well-structured project")

        return "\\n".join(prompt_parts)

    def _detect_project_mode(self) -> str:
        """Detect if we're in create or edit mode"""
        import os
        from pathlib import Path

        # Check for common project indicators
        project_indicators = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "composer.json",
            "go.mod",
            "Gemfile",
        ]

        cwd = Path.cwd()

        # Check for project files in current directory
        for indicator in project_indicators:
            if (cwd / indicator).exists():
                return "edit"

        # Check for multiple code files
        code_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
        code_files = []
        for ext in code_extensions:
            code_files.extend(list(cwd.glob(f"*{ext}")))
            code_files.extend(list(cwd.glob(f"**/*{ext}")))

        if len(code_files) >= 3:
            return "edit"

        return "create"

    def _parse_step_line(self, line: str) -> Optional[TaskStep]:
        """Parse a single step line"""
        # Pattern: "1 - create app.py" or "2 - run: pip install flask"
        match = re.match(r"(\d+)\s*-\s*(create|edit|run)(?::\s*)?\s*(.+)", line)
        if not match:
            return None

        step_num = int(match.group(1))
        action = match.group(2)
        target = match.group(3).strip()

        return TaskStep(step_number=step_num, action=action, target=target, description=line)

    def _associate_step_content(self, steps: List[TaskStep], response: str):
        """Associate detailed content with parsed steps"""
        for step in steps:
            if step.action in ["create", "edit"]:
                # Look for corresponding <code edit> block
                pattern = rf'=== STEP {step.step_number}:.*?===.*?\n<code edit filename="[^"]*">\s*\n(.*?)\n</code>'
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    step.content = match.group(1).strip()

                    # Track the file edit in history
                    action_type = "create" if step.action == "create" else "edit"
                    self.history_manager.track_file_edit(step.target, step.content, action_type)

            elif step.action == "run":
                # Look for corresponding <commands> block
                pattern = (
                    rf"=== STEP {step.step_number}:.*?===.*?\n<commands>\s*\n(.*?)\n</commands>"
                )
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    command_text = match.group(1).strip()
                    step.commands = [cmd.strip() for cmd in command_text.split("\n") if cmd.strip()]

    def format_steps_for_display(self, steps: List[TaskStep]) -> str:
        """Format steps for clean display to user"""
        if not steps:
            return "❌ No executable steps found. Please try with a more specific request."

        output_lines = []

        for step in steps:
            # Step header
            output_lines.append(f"{step.step_number} - {step.action} {step.target}")

            # Step content
            if step.action in ["create", "edit"] and step.content:
                output_lines.append(f'<code edit filename="{step.target}">')
                output_lines.append(step.content)
                output_lines.append("</code>")
                output_lines.append("")  # Blank line

            elif step.action == "run" and step.commands:
                output_lines.append("<commands>")
                for cmd in step.commands:
                    output_lines.append(cmd)
                output_lines.append("</commands>")
                output_lines.append("")  # Blank line

        return "\\n".join(output_lines)

    def get_task_summary(self, steps: List[TaskStep]) -> str:
        """Generate summary of task plan"""
        if not steps:
            return "No tasks to execute."

        create_count = sum(1 for s in steps if s.action == "create")
        edit_count = sum(1 for s in steps if s.action == "edit")
        run_count = sum(1 for s in steps if s.action == "run")

        summary_parts = []
        if create_count:
            summary_parts.append(f"{create_count} file(s) to create")
        if edit_count:
            summary_parts.append(f"{edit_count} file(s) to edit")
        if run_count:
            summary_parts.append(f"{run_count} command(s) to run")

        return f"Task plan: {', '.join(summary_parts)} ({len(steps)} total steps)"
