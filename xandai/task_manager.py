"""
Module for complex task management
"""

import re
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()


class TaskManager:
    """Manages execution of complex tasks divided into sub-tasks"""
    
    def __init__(self):
        """Initializes the task manager"""
        self.current_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.task_mode_active = False
        self.global_context = {
            'language': None,
            'framework': None,
            'original_request': None
        }
        
    def parse_task_breakdown(self, response: str) -> List[Dict]:
        """
        Extracts task list from model response
        
        Args:
            response: Response containing task breakdown
            
        Returns:
            List of extracted tasks
        """
        tasks = []
        
        # Patterns to detect tasks with priority markers
        patterns = [
            r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)',  # 1. Tarefa
            r'(?:Tarefa|Task)\s*(\d+):\s*(.+?)(?=(?:Tarefa|Task)\s*\d+:|$)',  # Tarefa 1: 
            r'[-•]\s*(.+?)(?=[-•]|$)',  # - Tarefa ou • Tarefa
            r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)',  # [1] Tarefa
        ]
        
        # Try each pattern
        for pattern in patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            if matches:
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        # Pattern with number
                        task_num, task_desc = match
                        task_desc = task_desc.strip()
                        if task_desc:
                            # Detecta prioridade da tarefa
                            priority = self._detect_task_priority(task_desc)
                            # Remove priority markers from description
                            clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', task_desc, flags=re.IGNORECASE)
                            tasks.append({
                                'number': int(task_num),
                                'description': clean_desc,
                                'status': 'pending',
                                'type': self._detect_task_type(clean_desc),
                                'priority': priority
                            })
                    else:
                        # Pattern without number (bullets)
                        task_desc = match.strip()
                        if task_desc:
                            # Detecta prioridade da tarefa
                            priority = self._detect_task_priority(task_desc)
                            # Remove priority markers from description
                            clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', task_desc, flags=re.IGNORECASE)
                            tasks.append({
                                'number': len(tasks) + 1,
                                'description': clean_desc,
                                'status': 'pending',
                                'type': self._detect_task_type(clean_desc),
                                'priority': priority
                            })
                break
        
        # If no structured patterns found, try non-empty lines
        if not tasks:
            lines = response.strip().split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Remove prefixos comuns
                line = re.sub(r'^(Passo|Step|Etapa)\s*\d*:?\s*', '', line, flags=re.IGNORECASE)
                if line and len(line) > 10:  # Linha significativa
                    # Detecta prioridade da tarefa
                    priority = self._detect_task_priority(line)
                    # Remove priority markers from description
                    clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', line, flags=re.IGNORECASE)
                    tasks.append({
                        'number': i + 1,
                        'description': clean_desc,
                        'status': 'pending',
                        'type': self._detect_task_type(clean_desc),
                        'priority': priority
                    })
        
        return tasks
    
    def _detect_task_type(self, description: str) -> str:
        """
        Detects task type based on description
        
        Args:
            description: Task description
            
        Returns:
            Task type: 'code', 'shell', 'text', 'mixed'
        """
        desc_lower = description.lower()
        
        # Keywords for code
        code_keywords = [
            'create', 'implement', 'write', 'develop', 'program',
            'function', 'class', 'method', 'code', 'script', 'file',
            'api', 'endpoint', 'component', 'module'
        ]
        
        # Keywords for shell/commands
        shell_keywords = [
            'install', 'execute', 'run', 'configure', 'setup',
            'command', 'terminal', 'shell', 'bash', 'create folder',
            'move', 'copy', 'delete', 'list'
        ]
        
        # Keywords for text/documentation
        text_keywords = [
            'explain', 'describe', 'document', 'analyze',
            'review', 'research', 'understand', 'plan',
            'define', 'specify'
        ]
        
        has_code = any(kw in desc_lower for kw in code_keywords)
        has_shell = any(kw in desc_lower for kw in shell_keywords)
        has_text = any(kw in desc_lower for kw in text_keywords)
        
        if has_code and not has_shell and not has_text:
            return 'code'
        elif has_shell and not has_code and not has_text:
            return 'shell'
        elif has_text and not has_code and not has_shell:
            return 'text'
        else:
            return 'mixed'
    
    def _detect_task_priority(self, description: str) -> str:
        """
        Detects task priority based on markers in the text
        
        Args:
            description: Task description
            
        Returns:
            'essential' or 'optional'
        """
        desc_lower = description.lower()
        
        # Explicit markers
        if '[essencial]' in desc_lower or '[essential]' in desc_lower:
            return 'essential'
        elif '[opcional]' in desc_lower or '[optional]' in desc_lower:
            return 'optional'
        
        # Keywords that indicate essential tasks
        essential_keywords = [
            'documentation.md', 'documentation', 'basic structure', 'configure environment',
            'install dependencies', 'create database', 'database', 'models', 'models',
            'authentication', 'security', 'main api', 'main functionality',
            'core', 'essential', 'fundamental', 'basic', 'necessary'
        ]
        
        # Keywords that indicate optional tasks
        optional_keywords = [
            'optional', 'improve', 'optimize', 'refactor', 'unit tests',
            'additional documentation', 'example', 'demo', 'extra', 'advanced',
            'cache', 'monitoring', 'advanced logging', 'analytics'
        ]
        
        # Verifica palavras-chave
        for keyword in essential_keywords:
            if keyword in desc_lower:
                return 'essential'
                
        for keyword in optional_keywords:
            if keyword in desc_lower:
                return 'optional'
        
        # By default, consider essential (especially the first task)
        return 'essential'
    
    def format_task_prompt(self, task: Dict, context: Optional[str] = None) -> str:
        """
        Formats a prompt for a specific task
        
        Args:
            task: Dictionary with task information
            context: Additional context (optional)
            
        Returns:
            Formatted prompt
        """
        prompt_parts = []
        
        # Add global context (language and framework)
        if self.global_context['language']:
            prompt_parts.append(f"[Language: {self.global_context['language']}]")
        if self.global_context['framework']:
            prompt_parts.append(f"[Framework: {self.global_context['framework']}]")
        
        # Add context if provided
        if context:
            prompt_parts.append(f"[Context: {context}]")
        
        # Add task information
        prompt_parts.append(f"[Task {task['number']} of {len(self.current_tasks)}]")
        prompt_parts.append(f"[Type: {task['type']}]")
        
        # If it's the first task (Documentation.md), add special context
        if task['number'] == 1 and 'documentation' in task['description'].lower():
            prompt_parts.append(f"\n[Original Project Request: {self.global_context['original_request']}]")
            prompt_parts.append("\n[IMPORTANT: Create a comprehensive Documentation.md that includes:]")
            prompt_parts.append("- Project overview and objectives")
            prompt_parts.append("- Complete feature list based on the original request")
            prompt_parts.append("- Technical architecture and structure")
            prompt_parts.append("- Technologies, languages and frameworks to be used")
            prompt_parts.append("- Development roadmap")
            prompt_parts.append("- Any other relevant project information")
        
        # Instruction based on type WITH MANDATORY TAGS
        if task['type'] == 'code':
            prompt_parts.append("[Expected: Working code implementation]")
            prompt_parts.append("""
[MANDATORY: Use <code filename="appropriate_name.ext"> tags for file creation]
[Example: <code filename="app.py">your code here</code>]
[DO NOT use ``` for files that should be created - use <code> tags]""")
        elif task['type'] == 'shell':
            prompt_parts.append("[Expected: Shell commands to execute]")
            prompt_parts.append("""
[MANDATORY: Use <actions> tags for shell commands]
[Example: <actions>pip install flask</actions>]
[DO NOT show commands without tags - wrap in <actions>]""")
        elif task['type'] == 'text':
            prompt_parts.append("[Expected: Clear explanation or documentation]")
        else:
            prompt_parts.append("[Expected: Complete solution with code, commands, or explanation as needed]")
            prompt_parts.append("""
[MANDATORY TAGS:]
- Use <code filename="name.ext"> for creating files
- Use <actions> for shell commands
- Use <read> for reading files
[DO NOT use ``` for file creation]""")
        
        # Add the task itself
        prompt_parts.append(f"\n<task>\n{task['description']}\n</task>")
        
        # Additional instructions based on keywords
        task_desc_lower = task['description'].lower()
        if any(word in task_desc_lower for word in ['import', 'import', 'add', 'add', 'edit', 'modify']):
            if 'file' in task_desc_lower or 'file' in task_desc_lower:
                prompt_parts.append("""
[IMPORTANT: This task requires editing/modifying an existing file]
[Use <code filename="existing_file.ext"> with the COMPLETE updated content]
[Do NOT show just the lines to add - show the ENTIRE file content]""")
        
        # Add previous completed tasks as context
        if self.completed_tasks:
            prompt_parts.append("\n[Previous completed tasks:]")
            for completed in self.completed_tasks[-3:]:  # Last 3 tasks
                prompt_parts.append(f"- Task {completed['number']}: {completed['description']} ✓")
        
        return '\n'.join(prompt_parts)
    
    def display_task_progress(self):
        """Displays task progress"""
        if not self.current_tasks:
            return
        
        # Create progress table
        progress_lines = []
        for task in self.current_tasks:
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(task['status'], '❓')
            
            # Color based on status
            if task['status'] == 'completed':
                color = 'green'
            elif task['status'] == 'in_progress':
                color = 'yellow'
            elif task['status'] == 'failed':
                color = 'red'
            else:
                color = 'dim'
            
            # Add priority indicator
            priority_tag = "[E]" if task.get('priority', 'essential') == 'essential' else "[O]"
            
            progress_lines.append(
                f"[{color}]{status_icon} {priority_tag} Tarefa {task['number']}: {task['description'][:45]}{'...' if len(task['description']) > 45 else ''}[/{color}]"
            )
        
        # Display progress panel
        progress_text = '\n'.join(progress_lines)
        console.print(Panel(progress_text, title="[bold blue]Task Progress[/bold blue]", border_style="blue"))
    
    def get_breakdown_prompt(self, original_request: str) -> str:
        """
        Creates prompt to break task into sub-tasks
        
        Args:
            original_request: User's original request
            
        Returns:
            Prompt for breakdown
        """
        # Save original request in global context
        self.global_context['original_request'] = original_request
        
        return f"""[Task Breakdown Request]

Please analyze the following request and break it down into smaller, specific tasks:

<request>
{original_request}
</request>

IMPORTANT: 
1. THE FIRST TASK SHOULD ALWAYS BE:
   1. [ESSENTIAL] Create Documentation.md file with complete project scope

2. MARK EACH TASK AS [ESSENTIAL] or [OPTIONAL]:
   - [ESSENTIAL]: Fundamental tasks for basic functionality
   - [OPTIONAL]: Improvements, optimizations, extra features

CRITERIA FOR ESSENTIAL TASKS:
- Basic project structure
- Environment configuration
- Main functionalities
- Data models
- Basic authentication/security
- Main APIs

CRITERIA FOR OPTIONAL TASKS:
- Unit tests
- Performance optimizations
- Cache
- Advanced logging
- Additional documentation
- Extra/advanced features

Expected format:
1. [ESSENTIAL] Create Documentation.md file with complete project scope
2. [ESSENTIAL] Configure environment and install dependencies
3. [ESSENTIAL] Create basic project structure
4. [OPTIONAL] Add unit tests
5. [OPTIONAL] Implement cache system
...

Be clear and direct. Mark ALL tasks with [ESSENTIAL] or [OPTIONAL]."""
    
    def should_display_as_text(self, response: str) -> bool:
        """
        Checks if response should be displayed as plain text
        
        Args:
            response: Model response
            
        Returns:
            True if should display as text (not code or commands)
        """
        # If it has code blocks, it's not plain text
        if '```' in response:
            return False
        
        # If it looks like shell command
        shell_indicators = ['$', '#', 'mkdir', 'cd ', 'ls ', 'pip ', 'npm ', 'git ']
        first_line = response.strip().split('\n')[0] if response else ''
        if any(indicator in first_line for indicator in shell_indicators):
            return False
        
        # If it has code structure
        code_indicators = ['def ', 'class ', 'function ', 'import ', 'from ', 'const ', 'let ', 'var ']
        if any(indicator in response for indicator in code_indicators):
            return False
        
        # Otherwise, it's text
        return True
    
    def detect_and_update_context(self, text: str):
        """
        Detects language and framework in text and updates global context
        
        Args:
            text: Text to analyze (request or response)
        """
        text_lower = text.lower()
        
        # Detect language if not yet detected
        if not self.global_context['language']:
            languages = {
                'python': ['python', 'py', 'django', 'flask', 'fastapi'],
                'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'express'],
                'typescript': ['typescript', 'ts', 'angular'],
                'java': ['java', 'spring', 'springboot'],
                'csharp': ['c#', 'csharp', '.net', 'dotnet'],
                'go': ['go', 'golang'],
                'rust': ['rust', 'cargo'],
                'cpp': ['c++', 'cpp'],
                'ruby': ['ruby', 'rails'],
                'php': ['php', 'laravel', 'symfony']
            }
            
            for lang, keywords in languages.items():
                if any(kw in text_lower for kw in keywords):
                    self.global_context['language'] = lang
                    console.print(f"[dim]🔍 Language detected: {lang}[/dim]")
                    break
        
        # Detect framework if not yet detected
        if not self.global_context['framework']:
            frameworks = {
                'django': 'Django',
                'flask': 'Flask',
                'fastapi': 'FastAPI',
                'react': 'React',
                'vue': 'Vue',
                'angular': 'Angular',
                'next': 'Next.js',
                'express': 'Express',
                'spring': 'Spring',
                'laravel': 'Laravel',
                'rails': 'Rails',
                '.net': '.NET',
                'symfony': 'Symfony'
            }
            
            for fw_key, fw_name in frameworks.items():
                if fw_key in text_lower:
                    self.global_context['framework'] = fw_name
                    console.print(f"[dim]🔍 Framework detected: {fw_name}[/dim]")
                    break
