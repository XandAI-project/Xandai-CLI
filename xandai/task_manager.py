"""
Module for complex task management
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()


class TaskManager:
    """Manages execution of complex tasks divided into sub-tasks"""
    
    def __init__(self, prompt_enhancer=None):
        """Initializes the task manager
        
        Args:
            prompt_enhancer: PromptEnhancer instance for file structure context
        """
        self.current_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.task_mode_active = False
        self.prompt_enhancer = prompt_enhancer
        self.global_context = {
            'language': None,
            'framework': None,
            'original_request': None,
            'working_directory': None
        }
        
    def parse_task_breakdown(self, response: str) -> List[Dict]:
        """
        Extracts task list from model response with improved validation
        
        Args:
            response: Response containing task breakdown
            
        Returns:
            List of extracted tasks
        """
        tasks = []
        
        # *** NEW: Validate and clean response first ***
        response = self._validate_and_clean_response(response)
        if not response:
            return tasks
        
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
                        
                        # *** NEW: Validate task content ***
                        if self._is_valid_task(task_num, task_desc):
                            # Detecta prioridade da tarefa
                            priority = self._detect_task_priority(task_desc)
                            # Remove priority markers from description
                            clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', task_desc, flags=re.IGNORECASE)
                            tasks.append({
                                'number': int(task_num),
                                'description': clean_desc[:200],  # Limit description length
                                'status': 'pending',
                                'type': self._detect_task_type(clean_desc),
                                'priority': priority
                            })
                    else:
                        # Pattern without number (bullets)
                        task_desc = match.strip()
                        if self._is_valid_task_description(task_desc):
                            # Detecta prioridade da tarefa
                            priority = self._detect_task_priority(task_desc)
                            # Remove priority markers from description
                            clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', task_desc, flags=re.IGNORECASE)
                            tasks.append({
                                'number': len(tasks) + 1,
                                'description': clean_desc[:200],  # Limit description length
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
                
                if self._is_valid_task_description(line):
                    # Detecta prioridade da tarefa
                    priority = self._detect_task_priority(line)
                    # Remove priority markers from description
                    clean_desc = re.sub(r'\s*\[(ESSENCIAL|OPCIONAL|ESSENTIAL|OPTIONAL)\]\s*', '', line, flags=re.IGNORECASE)
                    tasks.append({
                        'number': i + 1,
                        'description': clean_desc[:200],  # Limit description length
                        'status': 'pending',
                        'type': self._detect_task_type(clean_desc),
                        'priority': priority
                    })
        
        # *** NEW: Validate final task list ***
        validated_tasks = self._validate_task_list(tasks)
        return validated_tasks
    
    def _validate_and_clean_response(self, response: str) -> str:
        """
        Validates and cleans the LLM response to prevent malformed parsing
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response or empty string if invalid
        """
        if not response or not isinstance(response, str):
            return ""
        
        # Remove excessive HTML/CSS/JS content that might be mixed in
        # This prevents fragmented code from being parsed as tasks
        response = re.sub(r'<[^>]+>', ' ', response)  # Remove HTML tags
        response = re.sub(r'\{[^}]*\}', ' ', response)  # Remove CSS/JS blocks
        response = re.sub(r'http[s]?://[^\s]+', '[URL]', response)  # Replace URLs
        response = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', response)  # Replace IPs
        
        # Remove excessively long lines that are likely code
        lines = response.split('\n')
        clean_lines = []
        for line in lines:
            if len(line.strip()) < 300:  # Skip very long lines
                clean_lines.append(line)
        
        response = '\n'.join(clean_lines)
        
        # If response is too short or too long, it's probably malformed
        if len(response.strip()) < 50 or len(response) > 10000:
            return ""
        
        return response
    
    def _is_valid_task(self, task_num: str, task_desc: str) -> bool:
        """
        Validates if a task number and description are legitimate
        
        Args:
            task_num: Task number string
            task_desc: Task description
            
        Returns:
            True if valid task, False otherwise
        """
        try:
            num = int(task_num)
            # Reject unreasonable task numbers
            if num < 1 or num > 50:
                return False
        except (ValueError, TypeError):
            return False
        
        return self._is_valid_task_description(task_desc)
    
    def _is_valid_task_description(self, description: str) -> bool:
        """
        Validates if a task description is legitimate
        
        Args:
            description: Task description to validate
            
        Returns:
            True if valid description, False otherwise
        """
        if not description or not isinstance(description, str):
            return False
        
        description = description.strip()
        
        # Too short or too long
        if len(description) < 15 or len(description) > 500:
            return False
        
        # *** ENHANCED: Reject obvious code patterns ***
        
        # Contains function/method declarations
        if re.search(r'\b(function|def|class|var|let|const)\s*\w*\s*[\(\{]', description, re.IGNORECASE):
            return False
        
        # Contains programming keywords
        code_keywords = ['console\.log', 'return\s', 'import\s', 'export\s', 'require\(', 'alert\(']
        if any(re.search(keyword, description, re.IGNORECASE) for keyword in code_keywords):
            return False
        
        # Contains too many special characters (likely code fragments)
        special_char_ratio = sum(1 for c in description if c in '{}[]()<>/\\|@#$%^&*=+') / len(description)
        if special_char_ratio > 0.2:  # More restrictive
            return False
        
        # Contains HTML-like content
        if re.search(r'<[^>]+>', description):
            return False
        
        # Contains CSS-like content
        if re.search(r'[a-zA-Z-]+\s*:\s*[^;]+;', description):
            return False
        
        # Contains IP addresses or URLs (likely fragmented) - including our [IP] replacement
        if re.search(r'(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|\[IP\]|\[URL\])', description):
            return False
        
        # Contains file extensions mixed in weird ways
        if re.search(r'\.[a-z]{2,4}["\'>]', description):
            return False
        
        # *** NEW: Reject descriptions that are mostly numbers or single values ***
        # Check if description is mostly numbers or single short values
        words = description.split()
        if len(words) <= 2:
            # If it's very short, check if it looks like a value/number
            if re.match(r'^[a-zA-Z]*\s*\d+[\.:]\d*$', description.strip()):
                return False
        
        # *** NEW: Must contain at least one action verb ***
        action_verbs = [
            'create', 'build', 'implement', 'develop', 'design', 'write', 'add', 'remove',
            'update', 'modify', 'configure', 'setup', 'install', 'test', 'validate', 
            'check', 'verify', 'ensure', 'optimize', 'improve', 'fix', 'debug',
            'integrate', 'connect', 'deploy', 'run', 'execute', 'analyze', 'review',
            'prepare', 'organize', 'structure', 'plan', 'define', 'specify'
        ]
        
        description_lower = description.lower()
        has_action_verb = any(verb in description_lower for verb in action_verbs)
        
        # *** NEW: Or must contain task-like indicators ***
        task_indicators = [
            'file', 'component', 'interface', 'api', 'endpoint', 'service', 'system',
            'page', 'template', 'layout', 'style', 'script', 'function', 'method',
            'database', 'model', 'view', 'controller', 'form', 'button', 'menu'
        ]
        
        has_task_indicator = any(indicator in description_lower for indicator in task_indicators)
        
        # Must have either an action verb OR task indicator
        if not (has_action_verb or has_task_indicator):
            return False
        
        # *** NEW: Reject if it looks like a "Tarefa X:" pattern with just numbers/IPs ***
        if re.match(r'^tarefa\s*\d+:\s*[\d\.\:\s]+$', description_lower):
            return False
        
        return True
    
    def _validate_task_list(self, tasks: List[Dict]) -> List[Dict]:
        """
        Final validation and cleaning of the task list
        
        Args:
            tasks: List of parsed tasks
            
        Returns:
            Validated and cleaned task list
        """
        if not tasks:
            return []
        
        # Remove duplicates based on description similarity
        unique_tasks = []
        seen_descriptions = set()
        
        for task in tasks:
            # Normalize description for comparison
            normalized = re.sub(r'\s+', ' ', task['description'].lower().strip())
            
            # Check if similar description already exists
            is_duplicate = False
            for seen in seen_descriptions:
                if self._descriptions_similar(normalized, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_descriptions.add(normalized)
                unique_tasks.append(task)
        
        # Renumber tasks to ensure sequential numbering
        for i, task in enumerate(unique_tasks):
            task['number'] = i + 1
        
        # Limit to reasonable number of tasks
        if len(unique_tasks) > 20:
            unique_tasks = unique_tasks[:20]
        
        return unique_tasks
    
    def _descriptions_similar(self, desc1: str, desc2: str, threshold: float = 0.8) -> bool:
        """
        Check if two task descriptions are similar
        
        Args:
            desc1: First description
            desc2: Second description  
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if descriptions are similar
        """
        # Simple similarity based on common words
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
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
    
    def _get_file_structure_context(self, current_dir: str = None) -> str:
        """
        Get file structure context using PromptEnhancer
        
        Args:
            current_dir: Current working directory
            
        Returns:
            File structure context string
        """
        if not self.prompt_enhancer:
            return ""
        
        try:
            # Use current directory or stored working directory
            directory = current_dir or self.global_context.get('working_directory') or str(Path.cwd())
            
            # Get file structure using PromptEnhancer
            file_structure = self.prompt_enhancer._get_file_structure(directory)
            
            if file_structure:
                context_parts = [
                    "\n[CURRENT PROJECT STRUCTURE:]",
                    file_structure,
                    "\n[IMPORTANT: Always check existing files before creating new ones]",
                    "[CRITICAL: Do not overwrite existing files unless explicitly asked]",
                    "[Context: Files listed above already exist in the project]"
                ]
                return '\n'.join(context_parts)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get file structure: {e}[/yellow]")
        
        return ""
    
    def _get_recent_files_context(self) -> str:
        """
        Get context about recently created files from completed tasks
        
        Returns:
            Context string about recently created files
        """
        if not self.completed_tasks:
            return ""
        
        recent_files = []
        for task in self.completed_tasks[-5:]:  # Last 5 tasks
            # Extract file patterns from task description
            if any(keyword in task['description'].lower() for keyword in ['create', 'file', 'implement', 'write']):
                recent_files.append(f"- Task {task['number']}: {task['description']}")
        
        if recent_files:
            context_parts = [
                "\n[RECENTLY COMPLETED TASKS:]"
            ]
            context_parts.extend(recent_files)
            context_parts.append("[IMPORTANT: Build upon the work already done above]")
            return '\n'.join(context_parts)
        
        return ""
    
    def set_working_directory(self, directory: str):
        """
        Set the working directory for context
        
        Args:
            directory: Working directory path
        """
        self.global_context['working_directory'] = str(Path(directory).resolve())
    
    def refresh_file_context(self):
        """
        Refresh the file structure context after task execution
        This ensures the next task sees any newly created files
        """
        if self.prompt_enhancer and hasattr(self.prompt_enhancer, 'file_structure_cache'):
            # Clear cache to force refresh
            self.prompt_enhancer.file_structure_cache.clear()
    
    def add_task_completion_info(self, task: Dict, files_created: List[str] = None):
        """
        Add information about completed task including files created
        
        Args:
            task: Completed task dictionary
            files_created: List of files created/modified during task
        """
        # Store additional info about files created
        if files_created:
            task['files_created'] = files_created
            console.print(f"[dim]✓ Task {task['number']} created/modified: {', '.join(files_created)}[/dim]")
        
        # Add to completed tasks
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)
        
        # Refresh file context for next task
        self.refresh_file_context()
    
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
        
        # Add working directory context
        if self.global_context.get('working_directory'):
            prompt_parts.append(f"[Working Directory: {self.global_context['working_directory']}]")
        
        # Add context if provided
        if context:
            prompt_parts.append(f"[Context: {context}]")
        
        # Add task information
        prompt_parts.append(f"[Task {task['number']} of {len(self.current_tasks)}]")
        prompt_parts.append(f"[Type: {task['type']}]")
        
        # *** CRITICAL ADDITION: Add file structure context ***
        file_structure_context = self._get_file_structure_context()
        if file_structure_context:
            prompt_parts.append(file_structure_context)
        
        # Add recent files context from completed tasks
        recent_files_context = self._get_recent_files_context()
        if recent_files_context:
            prompt_parts.append(recent_files_context)
        
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
