"""
XandAI - Task Mode Processor
Enhanced task processing with robust parsing and streaming progress
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from xandai.ollama_client import OllamaClient, OllamaResponse
from xandai.history import HistoryManager


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
    
    def __init__(self, ollama_client: OllamaClient, history_manager: HistoryManager):
        """Initialize task processor"""
        self.ollama_client = ollama_client
        self.history_manager = history_manager
        
        self.system_prompt = self._build_system_prompt()
        
        # Vague request patterns to trigger clarifying questions
        self.vague_patterns = [
            r'^(create|make|build)\s+(an?\s+)?(app|website|api|tool|system)$',
            r'^help\s+(me|with).*$',
            r'^(do|fix|improve)\s+something$',
            r'^\w{1,10}$',  # Single word requests
            r'^.{1,15}$',   # Very short requests
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
            metadata={"mode": "task", "step_count": len(steps)}
        )
        
        self.history_manager.add_conversation(
            role="assistant", 
            content=response.content,
            context_usage=str(response.context_usage),
            metadata={"mode": "task", "steps_generated": len(steps)}
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
        tech_keywords = ['python', 'javascript', 'html', 'css', 'react', 'flask', 'django', 
                        'api', 'database', 'web', 'cli', 'gui', 'mobile', 'frontend', 'backend']
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
            "Please provide a more specific request and I'll create a detailed plan! 🚀"
        ]
        
        return "\\n".join(questions)
    
    def _get_llm_response_with_progress(self, prompt: str, console=None) -> OllamaResponse:
        """Get LLM response with streaming progress indicators"""
        # Prepare messages for streaming
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
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
                                status.update(f"[bold blue]Planning tasks... ({current_chunks} chunks received)[/bold blue]")
                            except:
                                status.update(f"[bold blue]Planning tasks... ({message})[/bold blue]")
                        else:
                            status.update(f"[bold blue]{message}[/bold blue]")
                    
                    return self.ollama_client.chat(
                        messages=messages,
                        temperature=0.3,
                        stream=True,
                        progress_callback=progress_callback
                    )
            except Exception:
                # Fallback to non-streaming
                console.print("[dim]⚠️ Streaming not available, using standard mode...[/dim]")
                return self.ollama_client.chat(
                    messages=messages,
                    temperature=0.3
                )
        else:
            # Regular non-streaming mode
            return self.ollama_client.chat(
                messages=messages,
                temperature=0.3
            )
    
    def _parse_response_steps_robust(self, response: str) -> List[TaskStep]:
        """Parse LLM response into TaskStep objects with multiple fallback strategies"""
        steps = []
        
        # Strategy 1: Look for formal STEPS: section
        steps_match = re.search(r'STEPS:\s*\n((?:\d+\s*-\s*.+\n?)*)', response, re.MULTILINE)
        if steps_match:
            step_lines = [line.strip() for line in steps_match.group(1).strip().split('\n') if line.strip()]
            for line in step_lines:
                step = self._parse_step_line(line)
                if step:
                    steps.append(step)
        
        # Strategy 2: Look for numbered lists anywhere in response
        if not steps:
            numbered_pattern = r'(\d+)\s*[-.)]\s*(.+?)(?=\n\d+\s*[-.]|\n\n|$)'
            matches = re.findall(numbered_pattern, response, re.MULTILINE | re.DOTALL)
            for i, (num, desc) in enumerate(matches, 1):
                desc = desc.strip()
                if len(desc) > 5:  # Ignore very short descriptions
                    action, target = self._infer_action_from_description(desc)
                    steps.append(TaskStep(
                        step_number=i,
                        action=action,
                        target=target,
                        description=desc
                    ))
        
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
        if any(word in desc_lower for word in ['create', 'new', 'add', 'make', 'build']):
            action = 'create'
        elif any(word in desc_lower for word in ['edit', 'update', 'modify', 'change']):
            action = 'edit'
        elif any(word in desc_lower for word in ['run', 'execute', 'install', 'start']):
            action = 'run'
        else:
            action = 'create'  # default
        
        # Extract filename or command
        # Look for file extensions
        file_match = re.search(r'(\w+\.\w+)', description)
        if file_match:
            target = file_match.group(1)
        else:
            # Extract the main noun/object
            words = description.split()
            target = words[-1] if words else 'task'
        
        return action, target
    
    def _extract_steps_from_content(self, response: str) -> List[TaskStep]:
        """Extract steps from any content that mentions file operations"""
        steps = []
        
        # Look for code edit blocks
        code_blocks = re.findall(r'<code edit filename="([^"]+)">', response)
        for i, filename in enumerate(code_blocks, 1):
            steps.append(TaskStep(
                step_number=i,
                action='create',
                target=filename,
                description=f"Create {filename}"
            ))
        
        # Look for command blocks  
        command_blocks = re.findall(r'<commands>(.*?)</commands>', response, re.DOTALL)
        if command_blocks:
            cmd_content = command_blocks[0].strip()
            cmd_lines = [line.strip() for line in cmd_content.split('\n') if line.strip()]
            if cmd_lines:
                steps.append(TaskStep(
                    step_number=len(steps) + 1,
                    action='run',
                    target='commands',
                    description="Run commands",
                    commands=cmd_lines
                ))
        
        return steps
    
    def _salvage_or_regenerate(self, user_request: str, failed_response: str) -> List[TaskStep]:
        """Attempt to salvage failed parsing or generate minimal steps"""
        
        # Try to create at least one meaningful step from the request
        request_lower = user_request.lower()
        steps = []
        
        # Detect common patterns and create basic steps
        if 'web' in request_lower or 'html' in request_lower:
            steps.append(TaskStep(1, 'create', 'index.html', 'Create main HTML file'))
            if 'css' in request_lower:
                steps.append(TaskStep(2, 'create', 'style.css', 'Create CSS stylesheet'))
        
        if 'python' in request_lower or 'flask' in request_lower:
            steps.append(TaskStep(len(steps) + 1, 'create', 'app.py', 'Create Python application'))
            steps.append(TaskStep(len(steps) + 1, 'create', 'requirements.txt', 'Create dependencies file'))
        
        if 'react' in request_lower or 'javascript' in request_lower:
            steps.append(TaskStep(len(steps) + 1, 'create', 'package.json', 'Create package configuration'))
            steps.append(TaskStep(len(steps) + 1, 'create', 'src/App.js', 'Create main React component'))
        
        # If still no steps, create a generic one
        if not steps:
            steps.append(TaskStep(1, 'create', 'main.py', f'Implement: {user_request}'))
        
        return steps
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for task mode"""
        return """You are XandAI Task Mode - an expert at breaking down complex development requests into structured, executable steps.

CRITICAL RULES:
1. ALWAYS generate at least one step - NEVER return empty responses
2. If request is unclear, ask clarifying questions instead of failing silently
3. Follow the EXACT format below or use numbered lists (1., 2., 3.)
4. Always provide COMPLETE file contents - never use placeholders

CRITICAL OUTPUT FORMAT:
Your response must follow this structure:

```
PROJECT: [Brief project description]
LANGUAGE: [Primary language: python/javascript/etc]
FRAMEWORK: [If applicable: flask/react/express/etc]
ESTIMATED_TIME: [e.g., "2-3 hours"]

STEPS:
1 - create filename.ext
2 - edit another_file.py
3 - run: pip install package

STEP DETAILS:

=== STEP 1: create filename.ext ===
<code edit filename="filename.ext">
Full file content here - never truncate or use placeholders
All necessary imports, functions, classes
Complete, runnable code
</code>

=== STEP 2: edit another_file.py ===
<code edit filename="another_file.py">
Complete updated file content
Full file, not just changes
</code>

=== STEP 3: run commands ===
<commands>
pip install flask
python app.py
</commands>
```

ALTERNATIVE FORMAT (if above fails):
Just use numbered lists:
1. Create app.py - Main application file
2. Create requirements.txt - Dependencies 
3. Run: pip install -r requirements.txt

RESPONSE QUALITY:
- Write clean, well-documented code
- Follow best practices (PEP8 for Python, ESLint for JS)  
- Include proper error handling
- Use meaningful names
- Add helpful comments

Remember: ALWAYS generate executable steps - the user is counting on you!"""
    
    def _build_task_prompt(self, user_request: str) -> str:
        """Build enhanced prompt with project context"""
        context = self.history_manager.get_project_context()
        existing_files = self.history_manager.get_project_files()
        
        prompt_parts = [f"TASK REQUEST: {user_request}"]
        
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
        
        return "\\n".join(prompt_parts)
    
    def _parse_step_line(self, line: str) -> Optional[TaskStep]:
        """Parse a single step line"""
        # Pattern: "1 - create app.py" or "2 - run: pip install flask"
        match = re.match(r'(\d+)\s*-\s*(create|edit|run)(?::\s*)?\s*(.+)', line)
        if not match:
            return None
        
        step_num = int(match.group(1))
        action = match.group(2)
        target = match.group(3).strip()
        
        return TaskStep(
            step_number=step_num,
            action=action,
            target=target,
            description=line
        )
    
    def _associate_step_content(self, steps: List[TaskStep], response: str):
        """Associate detailed content with parsed steps"""
        for step in steps:
            if step.action in ['create', 'edit']:
                # Look for corresponding <code edit> block
                pattern = rf'=== STEP {step.step_number}:.*?===.*?\n<code edit filename="[^"]*">\s*\n(.*?)\n</code>'
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    step.content = match.group(1).strip()
                    
                    # Track the file edit in history
                    action_type = "create" if step.action == "create" else "edit"
                    self.history_manager.track_file_edit(
                        step.target, 
                        step.content, 
                        action_type
                    )
                    
            elif step.action == 'run':
                # Look for corresponding <commands> block
                pattern = rf'=== STEP {step.step_number}:.*?===.*?\n<commands>\s*\n(.*?)\n</commands>'
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    command_text = match.group(1).strip()
                    step.commands = [cmd.strip() for cmd in command_text.split('\n') if cmd.strip()]
    
    def format_steps_for_display(self, steps: List[TaskStep]) -> str:
        """Format steps for clean display to user"""
        if not steps:
            return "❌ No executable steps found. Please try with a more specific request."
        
        output_lines = []
        
        for step in steps:
            # Step header
            output_lines.append(f"{step.step_number} - {step.action} {step.target}")
            
            # Step content
            if step.action in ['create', 'edit'] and step.content:
                output_lines.append(f'<code edit filename="{step.target}">')
                output_lines.append(step.content)
                output_lines.append('</code>')
                output_lines.append("")  # Blank line
                
            elif step.action == 'run' and step.commands:
                output_lines.append('<commands>')
                for cmd in step.commands:
                    output_lines.append(cmd)
                output_lines.append('</commands>')
                output_lines.append("")  # Blank line
        
        return "\\n".join(output_lines)
    
    def get_task_summary(self, steps: List[TaskStep]) -> str:
        """Generate summary of task plan"""
        if not steps:
            return "No tasks to execute."
        
        create_count = sum(1 for s in steps if s.action == 'create')
        edit_count = sum(1 for s in steps if s.action == 'edit')
        run_count = sum(1 for s in steps if s.action == 'run')
        
        summary_parts = []
        if create_count:
            summary_parts.append(f"{create_count} file(s) to create")
        if edit_count:
            summary_parts.append(f"{edit_count} file(s) to edit")
        if run_count:
            summary_parts.append(f"{run_count} command(s) to run")
        
        return f"Task plan: {', '.join(summary_parts)} ({len(steps)} total steps)"