"""
Interface CLI principal do XandAI
"""

import sys
import os
import re
import time
from typing import Optional, List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, PathCompleter, Completer, Completion
from pathlib import Path

from .api import OllamaAPI, OllamaAPIError
from .file_operations import FileOperations, FileOperationError
from .shell_executor import ShellExecutor
from .prompt_enhancer import PromptEnhancer
from .task_manager import TaskManager
from .git_manager import GitManager
from .session_manager import SessionManager

from .cli_utils.file_context import FileContextManager
from .cli_utils.read_levels import ReadLevelsManager
from .cli_utils.context_commands import ContextCommands
from .cli_utils.tag_processor import TagProcessor
from .cli_utils.auto_recovery import AutoRecovery
from .cli_utils.auto_read_structure import AutoReadStructure
from .cli_utils.file_editor import FileEditor


console = Console()


class ProjectModeDetector:
    """
    Automatically detects if the user wants to update an existing project 
    or create a new project based on context and prompt
    """
    
    def __init__(self, shell_executor):
        self.shell_executor = shell_executor
        
        # Files that indicate existing projects
        self.project_indicators = {
            'web_frontend': ['package.json', 'yarn.lock', 'package-lock.json', 'index.html', 'src/index.js', 'src/App.js'],
            'web_backend': ['app.py', 'main.py', 'server.js', 'requirements.txt', 'Pipfile', 'poetry.lock'],
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '__init__.py', 'main.py'],
            'node': ['package.json', 'node_modules/', 'yarn.lock', 'package-lock.json'],
            'react': ['package.json', 'src/App.js', 'src/index.js', 'public/index.html'],
            'next': ['next.config.js', 'package.json', 'pages/', 'app/'],
            'django': ['manage.py', 'settings.py', 'urls.py', 'requirements.txt'],
            'flask': ['app.py', 'requirements.txt', 'templates/', 'static/'],
            'go': ['go.mod', 'go.sum', 'main.go'],
            'rust': ['Cargo.toml', 'Cargo.lock', 'src/main.rs'],
            'java': ['pom.xml', 'build.gradle', 'src/main/java/'],
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'git': ['.git/', '.gitignore', 'README.md']
        }
        
        # Keywords that indicate editing/updating
        self.edit_keywords = {
            'explicit_edit': ['atualizar', 'modificar', 'editar', 'alterar', 'corrigir', 'ajustar', 'melhorar', 'otimizar', 'refatorar'],
            'add_features': ['adicionar', 'incluir', 'implementar', 'inserir', 'acrescentar'],
            'fix_issues': ['corrigir', 'consertar', 'resolver', 'debugar', 'reparar', 'solucionar'],
            'update_existing': ['atualizar', 'renovar', 'modernizar', 'migrar', 'upgradar'],
            'modify_behavior': ['modificar', 'alterar', 'mudar', 'adaptar', 'personalizar']
        }
        
        # Keywords that indicate creation
        self.create_keywords = {
            'explicit_create': ['criar', 'gerar', 'construir', 'desenvolver', 'fazer', 'produzir', 'estabelecer'],
            'new_project': ['novo', 'nova', 'from scratch', 'do zero', 'começar', 'iniciar'],
            'project_types': ['aplicação', 'app', 'sistema', 'plataforma', 'website', 'site', 'api', 'microserviço']
        }

    def detect_existing_projects(self, directory: str = None) -> Dict[str, Any]:
        """
        Analyzes the current directory and detects existing project types
        
        Returns:
            Dict with information about detected projects
        """
        if not directory:
            directory = self.shell_executor.get_current_directory()
        
        try:
            # List files in current directory
            success, files_output = self.shell_executor.execute_command('dir /b' if os.name == 'nt' else 'ls -la')
            if not success:
                return {'has_project': False, 'confidence': 0, 'types': [], 'indicators': []}
            
            # List files recursively limited (only 2 levels)
            success2, recursive_output = self.shell_executor.execute_command(
                'dir /s /b' if os.name == 'nt' else 'find . -maxdepth 2 -type f'
            )
            
            all_files = files_output.lower() + '\n' + (recursive_output.lower() if success2 else '')
            
            detected_types = []
            found_indicators = []
            confidence_score = 0
            
            # Analyze each project type
            for project_type, indicators in self.project_indicators.items():
                type_score = 0
                type_indicators = []
                
                for indicator in indicators:
                    if indicator.lower() in all_files or indicator.replace('/', '\\').lower() in all_files:
                        type_indicators.append(indicator)
                        # Main files have higher weight
                        if indicator in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']:
                            type_score += 30
                        else:
                            type_score += 10
                
                if type_score > 0:
                    detected_types.append({
                        'type': project_type,
                        'confidence': min(type_score, 100),
                        'indicators': type_indicators
                    })
                    found_indicators.extend(type_indicators)
                    confidence_score = max(confidence_score, type_score)
            
            # Check if it has typical directory structure
            common_dirs = ['src', 'lib', 'app', 'components', 'utils', 'config', 'static', 'templates']
            for dir_name in common_dirs:
                if dir_name in all_files:
                    confidence_score += 5
            
            has_project = confidence_score > 15  # Threshold to consider there's a project
            
            return {
                'has_project': has_project,
                'confidence': min(confidence_score, 100),
                'types': sorted(detected_types, key=lambda x: x['confidence'], reverse=True),
                'indicators': list(set(found_indicators)),
                'directory': directory
            }
            
        except Exception as e:
            return {'has_project': False, 'confidence': 0, 'types': [], 'indicators': [], 'error': str(e)}

    def analyze_user_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes the user prompt to detect intention of editing vs creating
        
        Returns:
            Dict with user intention analysis
        """
        prompt_lower = prompt.lower()
        
        edit_score = 0
        create_score = 0
        detected_edit_keywords = []
        detected_create_keywords = []
        
        # Analyze edit keywords
        for category, keywords in self.edit_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_edit_keywords.append(keyword)
                    # Explicit edit words have higher weight
                    if category == 'explicit_edit':
                        edit_score += 25
                    else:
                        edit_score += 15
        
        # Analyze creation keywords
        for category, keywords in self.create_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_create_keywords.append(keyword)
                    # Explicit creation words have higher weight
                    if category == 'explicit_create':
                        create_score += 25
                    else:
                        create_score += 15
        
        # Specific patterns that indicate editing
        edit_patterns = [
            r'no\s+(arquivo|código|projeto)\s+atual',
            r'neste\s+(arquivo|código|projeto)',
            r'arquivo\s+existente',
            r'código\s+que\s+já\s+existe'
        ]
        
        for pattern in edit_patterns:
            if re.search(pattern, prompt_lower):
                edit_score += 20
                detected_edit_keywords.append(f"pattern: {pattern}")
        
        # Specific patterns that indicate creation
        create_patterns = [
            r'criar\s+um\s+novo',
            r'fazer\s+uma?\s+nova?',
            r'desenvolver\s+um',
            r'from\s+scratch',
            r'do\s+zero'
        ]
        
        for pattern in create_patterns:
            if re.search(pattern, prompt_lower):
                create_score += 30
                detected_create_keywords.append(f"pattern: {pattern}")
        
        # Determine main intention
        if edit_score > create_score and edit_score > 20:
            intent = 'edit'
            confidence = min(edit_score, 100)
        elif create_score > edit_score and create_score > 20:
            intent = 'create'
            confidence = min(create_score, 100)
        else:
            intent = 'ambiguous'
            confidence = max(edit_score, create_score)
        
        return {
            'intent': intent,
            'confidence': confidence,
            'edit_score': edit_score,
            'create_score': create_score,
            'edit_keywords': detected_edit_keywords,
            'create_keywords': detected_create_keywords
        }

    def make_mode_decision(self, prompt: str, directory: str = None) -> Dict[str, Any]:
        """
        Makes the final decision about mode (edit vs create) based on all factors
        
        Returns:
            Dict with final decision and justification
        """
        # Analyze existing project
        project_info = self.detect_existing_projects(directory)
        
        # Analyze user intention
        intent_info = self.analyze_user_intent(prompt)
        
        # Decision logic
        final_mode = 'create'  # default
        confidence = 0
        reasoning = []
        
        # If there's an existing project with high confidence
        if project_info['has_project'] and project_info['confidence'] > 30:
            reasoning.append(f"Existing project detected (confidence: {project_info['confidence']}%)")
            
            # If intention is ambiguous or explicitly edit, prefer editing
            if intent_info['intent'] in ['ambiguous', 'edit']:
                final_mode = 'edit'
                confidence = project_info['confidence'] + intent_info['confidence']
                reasoning.append(f"User intention favors editing (score: {intent_info['edit_score']})")
            
            # If intention is explicitly creation with high confidence, keep creation
            elif intent_info['intent'] == 'create' and intent_info['confidence'] > 60:
                final_mode = 'create'
                confidence = intent_info['confidence']
                reasoning.append(f"Explicit creation intention overrides existing project")
            
            # Default case: if there's existing project, prefer editing
            else:
                final_mode = 'edit'
                confidence = project_info['confidence'] + (intent_info['confidence'] * 0.5)
                reasoning.append("Default: existing project indicates edit mode")
        
        # If there's no existing project
        else:
            if intent_info['intent'] == 'edit' and intent_info['confidence'] > 40:
                final_mode = 'edit'
                confidence = intent_info['confidence'] * 0.7  # Reduced because no project
                reasoning.append("Edit intention but no existing project detected")
            else:
                final_mode = 'create'
                confidence = max(50, intent_info['confidence'])  # Minimum 50% for creation
                reasoning.append("No existing project detected, creation mode")
        
        return {
            'mode': final_mode,
            'confidence': min(confidence, 100),
            'reasoning': reasoning,
            'project_info': project_info,
            'intent_info': intent_info
        }


class XandAICompleter(Completer):
    """Custom completer for XandAI CLI that handles both commands and file paths"""
    
    def __init__(self, commands, shell_executor):
        self.commands = commands
        self.shell_executor = shell_executor
        self.command_completer = WordCompleter(list(commands.keys()), ignore_case=True)
        self.path_completer = PathCompleter()
        
        # Shell commands that typically need file/directory completion
        self.file_commands = {
            'cd', 'ls', 'dir', 'cat', 'type', 'rm', 'del', 'cp', 'copy', 'mv', 'move',
            'mkdir', 'rmdir', 'touch', 'head', 'tail', 'less', 'more', 'nano', 'vim',
            'code', 'notepad', 'git', 'find', 'grep', 'chmod', 'chown', 'tar', 'zip',
            'unzip', 'python', 'node', 'npm', 'pip', 'cargo', 'go'
        }
    
    def get_completions(self, document, complete_event):
        text = document.text
        
        # If starts with /, complete CLI commands
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
            return
        
        # For shell commands, provide file/path completion
        words = text.split()
        if words:
            first_word = words[0].lower()
            
            # If it's a shell command that typically needs file completion
            if first_word in self.file_commands:
                # Create a new document with just the path part for completion
                if len(words) > 1:
                    # Get the last word (the path being typed)
                    path_part = words[-1]
                    cursor_pos = len(path_part)
                    path_document = document.__class__(path_part, cursor_pos)
                    yield from self.path_completer.get_completions(path_document, complete_event)
                else:
                    # No path started yet, complete from current directory
                    yield from self.path_completer.get_completions(document.__class__('', 0), complete_event)


class XandAICLI:
    """Main CLI interface for XandAI"""
    
    def __init__(self, endpoint: str = "http://localhost:11434"):
        """
        Inicializa a CLI
        
        Args:
            endpoint: Endpoint da API OLLAMA
        """
        self.api = OllamaAPI(endpoint)
        self.file_ops = FileOperations()
        # Save user's initial directory
        self.user_initial_dir = Path.cwd()
        self.shell_exec = ShellExecutor(initial_dir=self.user_initial_dir)
        self.prompt_enhancer = PromptEnhancer()
        self.task_manager = TaskManager(prompt_enhancer=self.prompt_enhancer)
        self.git_manager = GitManager(self.user_initial_dir)
        self.session_manager = SessionManager()
        self.file_context_manager = FileContextManager()
        self.read_levels_manager = ReadLevelsManager(self.shell_exec)
        self.context_commands = ContextCommands(self.file_context_manager)
        # Novos sistemas
        self.auto_read_structure = AutoReadStructure(self.shell_exec)
        self.file_editor = FileEditor(self.file_ops)
        self.project_mode_detector = ProjectModeDetector(self.shell_exec)
        # TagProcessor e AutoRecovery serão inicializados depois que o modelo for selecionado
        self.tag_processor = None
        self.auto_recovery = None
        self.selected_model = None
        self.history_file = Path.home() / ".xandai_history"
        self.auto_execute_shell = True  # Flag for automatic command execution
        self.enhance_prompts = True     # Flag to improve prompts automatically
        self.better_prompting = True    # Flag for better prompting system
        self.commands = {
            '/help': self.show_help,
            '/models': self.list_models,
            '/clear': self.clear_screen,
            '/exit': self.exit_cli,
            '/quit': self.exit_cli,
            '/file': self.file_command,
            '/shell': self.toggle_shell_execution,
            '/enhance': self.toggle_prompt_enhancement,
            '/enhance_code': self.enhance_code_command,
            '/task': self.task_command,
            '/flush': self.flush_context,
            '/context': self.context_commands.show_file_context,
            '/clear-context': self.context_commands.clear_file_context,
            '/refresh-context': self.context_commands.refresh_file_context,
            '/debug': self.toggle_debug_mode,
            '/better': self.toggle_better_prompting,
            '/session': self.session_command
        }
        
        # Modo debug
        self.debug_mode = False
        
        # Flag para modo enhancement
        self._enhancement_mode = False
        
    def clear_screen(self):
        """Limpa a tela do console"""
        console.clear()
        
    def exit_cli(self):
        """Sai da CLI"""
        console.print("\n[yellow]Goodbye! 👋[/yellow]")
        sys.exit(0)
    
    def toggle_shell_execution(self):
        """Toggles automatic shell command execution"""
        self.auto_execute_shell = not self.auto_execute_shell
        status = "enabled" if self.auto_execute_shell else "disabled"
        console.print(f"[green]✓ Automatic shell command execution {status}[/green]")
    
    def toggle_prompt_enhancement(self):
        """Toggles automatic prompt enhancement"""
        self.enhance_prompts = not self.enhance_prompts
        status = "enabled" if self.enhance_prompts else "disabled"
        console.print(f"[green]✓ Automatic prompt enhancement {status}[/green]")
    
    def flush_context(self):
        """Manually flush the LLM context history"""
        if hasattr(self.prompt_enhancer, 'flush_context'):
            old_usage = self.prompt_enhancer.get_context_usage_percentage()
            self.prompt_enhancer.flush_context()
            new_usage = self.prompt_enhancer.get_context_usage_percentage()
            console.print(f"[green]🔄 Context manually flushed: {old_usage:.1f}% → {new_usage:.1f}%[/green]")
        else:
            console.print("[yellow]Context management not available[/yellow]")
    
    def show_context_status(self):
        """Show current context usage status"""
        if hasattr(self.prompt_enhancer, 'get_context_status'):
            status = self.prompt_enhancer.get_context_status()
            console.print(f"[blue]📊 Context Status: {status}[/blue]")
            
            # Show detailed breakdown
            if hasattr(self.prompt_enhancer, 'context_history'):
                history = self.prompt_enhancer.context_history
                console.print(f"[dim]Messages breakdown:[/dim]")
                
                role_counts = {}
                for msg in history:
                    if isinstance(msg, dict) and 'role' in msg:
                        role = msg['role']
                        role_counts[role] = role_counts.get(role, 0) + 1
                    else:
                        role_counts['unknown'] = role_counts.get('unknown', 0) + 1
                
                for role, count in role_counts.items():
                    console.print(f"[dim]  {role}: {count} messages[/dim]")
        else:
            console.print("[yellow]Context status not available[/yellow]")
    
    def toggle_better_prompting(self):
        """Toggles better prompting system"""
        self.better_prompting = not self.better_prompting
        status = "enabled" if self.better_prompting else "disabled"
        console.print(f"[green]✓ Better prompting system {status}[/green]")
        if self.better_prompting:
            console.print("[dim]Your prompts will be analyzed and enhanced for better results[/dim]")
            console.print("[dim]💡 Press Ctrl+C to cancel analysis or use /better to disable[/dim]")
        else:
            console.print("[dim]Prompts will be sent directly to the LLM[/dim]")
            console.print("[dim]💡 Enable with /better for enhanced prompt analysis[/dim]")
    
    def analyze_and_enhance_prompt(self, original_prompt: str) -> str:
        """
        Analyze user prompt and enhance it with better context and details
        
        Args:
            original_prompt: User's original prompt
            
        Returns:
            Enhanced prompt with more context and details
        """
        analysis_prompt = f"""You are a prompt analysis expert. Your job is to analyze user requests and provide a detailed, enhanced version that will get better results from an AI assistant.

ORIGINAL USER REQUEST:
"{original_prompt}"

ANALYSIS TASK:
1. Identify what the user is trying to accomplish
2. Determine what additional context or details would be helpful
3. Suggest specific requirements, constraints, or preferences
4. Consider technical details, best practices, or standards that should be included
5. Think about potential edge cases or considerations

ENHANCED REQUEST FORMAT:
Provide an enhanced version of the request that:
- Maintains the user's original intent
- Adds helpful context and details
- Specifies clear requirements when applicable  
- Includes relevant technical considerations
- Is more likely to produce a comprehensive, useful response

IMPORTANT: 
- Keep the enhanced request focused and practical
- Don't over-complicate simple requests
- Maintain the original tone and style
- Add value without changing the core request

Enhanced Request:"""

        try:
            console.print("[dim]🔍 Analyzing and enhancing your prompt...[/dim]")
            
            # Send to LLM for analysis
            response = ""
            chunk_count = 0
            
            with console.status("[dim]Analyzing prompt...", spinner="dots") as status:
                for chunk in self.api.generate(self.selected_model, analysis_prompt, stream=True):
                    response += chunk
                    chunk_count += 1
                    
                    # Update status periodically
                    if chunk_count % 20 == 0:
                        status.update(f"[dim]Analyzing... ({chunk_count} chunks received)", spinner="dots")
            
            # Check if we got a valid response
            if not response.strip():
                console.print("[yellow]⚠️ Empty response from analysis, using original prompt[/yellow]")
                return original_prompt
            
            # Extract the enhanced request from the response
            enhanced_prompt = response.strip()
            
            # Clean up the response to get just the enhanced prompt
            if "Enhanced Request:" in enhanced_prompt:
                enhanced_prompt = enhanced_prompt.split("Enhanced Request:")[-1].strip()
            elif "enhanced version:" in enhanced_prompt.lower():
                parts = enhanced_prompt.lower().split("enhanced version:")
                if len(parts) > 1:
                    enhanced_prompt = enhanced_prompt[len(parts[0]):].strip()
            
            # Remove any leading/trailing quotes or formatting
            enhanced_prompt = enhanced_prompt.strip('"').strip("'").strip()
            
            # Show the enhancement to the user
            console.print(f"\n[blue]🎯 Enhanced Prompt:[/blue]")
            console.print(f"[dim]{enhanced_prompt}[/dim]\n")
            
            return enhanced_prompt
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ Prompt analysis interrupted by user[/yellow]")
            console.print("[dim]Using original prompt[/dim]")
            return original_prompt
        except Exception as e:
            console.print(f"[yellow]⚠️ Prompt enhancement failed: {e}[/yellow]")
            console.print("[dim]Falling back to original prompt[/dim]")
            return original_prompt
    
    def toggle_debug_mode(self):
        """Alterna modo debug para mostrar respostas completas"""
        self.debug_mode = not self.debug_mode
        status = "ativado" if self.debug_mode else "desativado"
        console.print(f"[green]✓ Modo debug {status}[/green]")
        if self.debug_mode:
            console.print("[dim]In debug mode, complete model responses are displayed[/dim]")
        else:
            console.print("[dim]Normal mode: only text and processed actions are displayed[/dim]")
    
    def enhance_code_command(self, description: str = ""):
        """
        Command to improve existing code
        
        Args:
            description: Optional description of what to improve
        """
        if not description.strip():
            console.print("[yellow]Please describe what you would like to improve.[/yellow]")
            console.print("[dim]Example: /enhance_code add error handling and documentation[/dim]")
            return
        
        # Create specific prompt for enhancement
        enhanced_prompt = self.prompt_enhancer.create_enhance_code_prompt(
            description, 
            str(self.user_initial_dir)
        )
        
        # Show that it's in enhancement mode
        console.print("\n[bold magenta]🔧 CODE ENHANCEMENT MODE[/bold magenta]")
        console.print("[dim]Analyzing existing files and preparing improvements...[/dim]\n")
        
        # Save flag indicating we're in enhancement mode
        self._enhancement_mode = True
        
        try:
            # Process the enhanced prompt
            self.process_prompt(enhanced_prompt)
        finally:
            self._enhancement_mode = False
    
    def _display_formatted_response(self, response: str):
        """
        Exibe a resposta formatada de forma limpa
        
        Args:
            response: Resposta completa do modelo
        """
        # Remove special tags (already processed separately)
        clean_response = response
        clean_response = re.sub(r'<actions>.*?</actions>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        clean_response = re.sub(r'<read>.*?</read>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        clean_response = re.sub(r'<code[^>]*>.*?</code>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        
        # Separate text and code blocks
        parts = re.split(r'(```[\s\S]*?```)', clean_response)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # It's a code block
                lines = part.split('\n')
                if len(lines) > 2:
                    # Extract language and code
                    lang_line = lines[0][3:].strip()
                    code_content = '\n'.join(lines[1:-1])
                    
                    # Detect language
                    lang = lang_line if lang_line else 'text'
                    
                    # Mapeia linguagens comuns
                    lang_map = {
                        'py': 'python', 'python': 'python',
                        'js': 'javascript', 'javascript': 'javascript',
                        'ts': 'typescript', 'typescript': 'typescript',
                        'java': 'java', 'c': 'c', 'cpp': 'cpp',
                        'go': 'go', 'rust': 'rust', 'rb': 'ruby',
                        'php': 'php', 'sql': 'sql', 'bash': 'bash',
                        'sh': 'bash', 'json': 'json', 'xml': 'xml',
                        'yaml': 'yaml', 'yml': 'yaml'
                    }
                    
                    display_lang = lang_map.get(lang.lower(), lang)
                    
                    # Display code with syntax highlighting
                    syntax = Syntax(code_content, display_lang, theme="monokai", line_numbers=True)
                    console.print("\n")
                    console.print(Panel(syntax, title=f"[bold yellow]{display_lang.upper()} Code[/bold yellow]", border_style="yellow"))
                    console.print("\n")
                else:
                    # Empty or malformed code block
                    console.print(part)
            else:
                # It's normal text
                # Remove extra spaces and format paragraphs
                paragraphs = part.strip().split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Formata listas
                        if para.strip().startswith(('- ', '* ', '• ')):
                            lines = para.split('\n')
                            for line in lines:
                                if line.strip():
                                    console.print(f"  {line.strip()}")
                        # Format titles
                        elif para.strip().startswith('#'):
                            console.print(f"\n[bold]{para.strip()}[/bold]\n")
                        else:
                            # Texto normal
                            console.print(para.strip())
                        console.print()  # Blank line between paragraphs
    
    def _generate_filename(self, lang: str, code: str, context: str) -> str:
        """
        Generates an intelligent filename based on context and code
        
        Args:
            lang: Code language
            code: Code content
            context: Original prompt context
            
        Returns:
            Suggested filename
        """
        # Map languages to extensions
        ext_map = {
            'python': '.py', 'py': '.py',
            'javascript': '.js', 'js': '.js', 
            'typescript': '.ts', 'ts': '.ts',
            'java': '.java', 'c': '.c', 'cpp': '.cpp',
            'go': '.go', 'rust': '.rs', 'ruby': '.rb',
            'php': '.php', 'html': '.html', 'css': '.css',
            'sql': '.sql', 'json': '.json', 'xml': '.xml',
            'yaml': '.yml', 'yml': '.yml', 'bash': '.sh',
            'sh': '.sh', 'shell': '.sh'
        }
        
        ext = ext_map.get(lang.lower(), '.txt')
        current_dir = Path(self.shell_exec.get_current_directory())
        
        # 1. First, try to extract specific name from context
        import re
        
        # Search for filename mentions in context
        filename_patterns = [
            r'arquivo\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z]+)?)',
            r'file\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z]+)?)',
            r'create\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z]+)?)',
            r'([a-zA-Z_][a-zA-Z0-9_]*\.py)',
            r'([a-zA-Z_][a-zA-Z0-9_]*\.js)',
            r'([a-zA-Z_][a-zA-Z0-9_]*\.html)',
        ]
        
        for pattern in filename_patterns:
            match = re.search(pattern, context.lower())
            if match:
                suggested_name = match.group(1)
                if not suggested_name.endswith(ext.lower()):
                    suggested_name = suggested_name.split('.')[0] + ext
                
                # Check if file already exists - if so, edit instead of creating new
                suggested_path = current_dir / suggested_name
                if suggested_path.exists():
                    console.print(f"[yellow]📝 File {suggested_name} already exists - will be edited[/yellow]")
                    return suggested_name
                return suggested_name
        
        # 2. Se não encontrou nome específico, analisa o código para extrair nomes
        code_lines = code.strip().split('\n')
        
        # Para Python: procura por classes, funções principais, imports específicos
        if lang.lower() in ['python', 'py']:
            for line in code_lines[:10]:  # Primeiras 10 linhas
                if 'class ' in line:
                    class_match = re.search(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                    if class_match:
                        return class_match.group(1).lower() + ext
                elif 'def ' in line and 'main' not in line:
                    func_match = re.search(r'def\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                    if func_match:
                        return func_match.group(1) + ext
                elif 'from flask' in line or 'import flask' in line:
                    # Verifica se já existe app.py
                    if (current_dir / 'app.py').exists():
                        console.print(f"[yellow]📝 app.py already exists - will be edited[/yellow]")
                        return 'app.py'
                    return 'app.py'
                elif 'fastapi' in line.lower():
                    if (current_dir / 'main.py').exists():
                        console.print(f"[yellow]📝 main.py already exists - will be edited[/yellow]")
                        return 'main.py'
                    return 'main.py'
        
        # Para JavaScript: procura por funções, componentes
        elif lang.lower() in ['javascript', 'js']:
            for line in code_lines[:10]:
                if 'function ' in line:
                    func_match = re.search(r'function\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                    if func_match:
                        return func_match.group(1).lower() + ext
                elif 'const ' in line and '=' in line:
                    const_match = re.search(r'const\s+([A-Za-z_][A-Za-z0-9_]*)', line)
                    if const_match:
                        return const_match.group(1).lower() + ext
        
        # 3. Baseado no contexto/tipo de projeto
        context_lower = context.lower()
        
        # Mapas de prioridade baseados em contexto
        context_names = {
            'flask': 'app.py',
            'fastapi': 'main.py', 
            'django': 'views.py',
            'express': 'server.js',
            'react': 'App.js',
            'vue': 'App.vue',
            'api': 'api.py' if lang.lower() in ['python', 'py'] else 'api.js',
            'server': 'server.py' if lang.lower() in ['python', 'py'] else 'server.js',
            'fibonacci': 'fibonacci' + ext,
            'calculator': 'calculator' + ext,
            'backup': 'backup' + ext,
            'test': 'test' + ext,
            'config': 'config' + ext,
            'auth': 'auth' + ext,
            'database': 'database' + ext,
            'db': 'db' + ext,
            'model': 'models' + ext,
            'util': 'utils' + ext,
            'helper': 'helpers' + ext,
        }
        
        for keyword, filename in context_names.items():
            if keyword in context_lower:
                suggested_path = current_dir / filename
                if suggested_path.exists():
                    console.print(f"[yellow]📝 {filename} already exists - will be edited[/yellow]")
                    return filename
                return filename
        
        # 4. Como último recurso, usa nomes genéricos mas inteligentes
        existing_files = list(current_dir.glob(f'*{ext}'))
        
        # Se existe main.py ou app.py, edita em vez de criar novo
        if lang.lower() in ['python', 'py']:
            for existing in ['main.py', 'app.py', 'script.py']:
                if (current_dir / existing).exists():
                    console.print(f"[yellow]📝 {existing} already exists - will be edited[/yellow]")
                    return existing
            return 'main.py'
        elif lang.lower() in ['javascript', 'js']:
            for existing in ['index.js', 'main.js', 'app.js']:
                if (current_dir / existing).exists():
                    console.print(f"[yellow]📝 {existing} already exists - will be edited[/yellow]")
                    return existing
            return 'index.js'
        elif lang.lower() == 'html':
            for existing in ['index.html', 'main.html']:
                if (current_dir / existing).exists():
                    console.print(f"[yellow]📝 {existing} already exists - will be edited[/yellow]")
                    return existing
            return 'index.html'
        
        # For other languages, refuse to create generic names
        # Instead, prompt user to provide specific filename
        console.print(f"[yellow]⚠️ Cannot determine appropriate filename for {lang} code[/yellow]")
        console.print(f"[yellow]💡 Please use <code filename=\"your_filename{ext}\"> tags to specify filename[/yellow]")
        console.print(f"[yellow]💡 Or mention the desired filename in your request[/yellow]")
        return None  # Return None to skip file creation
    
    def _resolve_file_path(self, filepath: str, current_dir: Path) -> Path:
        """
        Resolve file path relative to current directory with duplication cleaning
        
        Args:
            filepath: File path (can be relative or absolute)
            current_dir: Current directory
            
        Returns:
            Resolved and cleaned absolute path
        """
        if Path(filepath).is_absolute():
            resolved_path = Path(filepath)
        else:
            resolved_path = current_dir / filepath
        
        # Check for self-nesting (creating files inside a directory with the same name)
        current_dir_name = current_dir.name
        file_parts = Path(filepath).parts
        
        # Prevent creating files like "uber-react-app/uber-react-app/file.js"
        if len(file_parts) > 1 and file_parts[0].lower() == current_dir_name.lower():
            console.print(f"[yellow]⚠️  Preventing self-nesting: Removing duplicate '{file_parts[0]}' from path[/yellow]")
            # Remove the duplicate directory part
            cleaned_filepath = Path(*file_parts[1:])
            resolved_path = current_dir / cleaned_filepath
            console.print(f"[dim]🔧 Path adjusted: {filepath} → {cleaned_filepath}[/dim]")
        
        # Apply path cleaning to prevent duplications
        try:
            str_path = str(resolved_path)
            path_parts = str_path.replace('\\', '/').split('/')
            path_parts = [part for part in path_parts if part and part != '.']
            
            # Use the same deduplication logic as ShellExecutor
            if hasattr(self.shell_exec, '_remove_path_duplications'):
                cleaned_parts = self.shell_exec._remove_path_duplications(path_parts)
                
                if len(cleaned_parts) != len(path_parts):
                    # Reconstruct clean path
                    if self.shell_exec.is_windows and len(cleaned_parts) > 0:
                        if ':' not in cleaned_parts[0] and len(cleaned_parts[0]) == 1:
                            cleaned_parts[0] = cleaned_parts[0] + ':'
                        clean_path = Path('\\'.join(cleaned_parts))
                    else:
                        clean_path = Path('/'.join(cleaned_parts))
                    
                    console.print(f"[dim]🔧 File path cleaned: {resolved_path} → {clean_path}[/dim]")
                    return clean_path
        except Exception as e:
            console.print(f"[dim]⚠️ File path cleaning failed: {e}[/dim]")
        
        return resolved_path
    
    def _extract_code_blocks(self, response: str) -> List[Tuple[str, str, str]]:
        """
        Extrai blocos de código da resposta com suporte para <code edit> e <code create>
        
        Args:
            response: Resposta do modelo
            
        Returns:
            Lista de tuplas (action_type, filename, code_content) onde action_type é 'edit' ou 'create'
        """
        code_blocks = []
        
        # Padrão para novas tags específicas: <code edit> e <code create>
        new_pattern = r'<code\s+(edit|create)\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)\s*</code>'
        
        # Primeiro, tenta o novo padrão com edit/create
        new_matches = re.findall(new_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if new_matches:
            for action_type, filename, content in new_matches:
                # Valida o filename
                clean_filename = filename.strip()
                if clean_filename and self._is_valid_filename(clean_filename):
                    code_blocks.append((action_type.lower(), clean_filename, content))
                else:
                    console.print(f"[yellow]⚠️  Invalid filename skipped: {filename}[/yellow]")
        
        # Compatibilidade com padrão antigo (sem edit/create) - assume 'create' como padrão
        old_pattern = r'<code\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)\s*</code>'
        old_matches = re.findall(old_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if old_matches:
            for filename, content in old_matches:
                # Valida o filename
                clean_filename = filename.strip()
                if clean_filename and self._is_valid_filename(clean_filename):
                    # Verifica se o arquivo já existe para decidir o tipo de ação
                    current_dir = Path(self.shell_exec.get_current_directory())
                    file_path = self._resolve_file_path(clean_filename, current_dir)
                    action_type = 'edit' if file_path.exists() else 'create'
                    code_blocks.append((action_type, clean_filename, content))
                else:
                    console.print(f"[yellow]⚠️  Invalid filename skipped: {filename}[/yellow]")
        
        # Se não encontrou nada, tenta padrões alternativos para tags mal formatadas
        if not code_blocks:
            # Busca por tags incompletas ou mal fechadas
            alt_pattern = r'<code\s+(edit|create)?\s*filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)(?:</code>|$)'
            alt_matches = re.findall(alt_pattern, response, re.DOTALL | re.IGNORECASE)
            
            for action_type, filename, content in alt_matches:
                clean_filename = filename.strip()
                if clean_filename and self._is_valid_filename(clean_filename):
                    # Remove possível texto misturado após o código
                    cleaned_content = self._remove_mixed_content(content)
                    # Se action_type está vazio, determina baseado na existência do arquivo
                    if not action_type:
                        current_dir = Path(self.shell_exec.get_current_directory())
                        file_path = self._resolve_file_path(clean_filename, current_dir)
                        action_type = 'edit' if file_path.exists() else 'create'
                    code_blocks.append((action_type.lower(), clean_filename, cleaned_content))
        
        return code_blocks
    
    def _is_valid_filename(self, filename: str) -> bool:
        """
        Verifica se um nome de arquivo é válido
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            True se o filename for válido
        """
        if not filename or len(filename.strip()) == 0:
            return False
        
        # Caracteres inválidos para nomes de arquivo
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in filename:
                return False
        
        # Verifica se tem extensão válida
        if '.' not in filename:
            return False
        
        # Verifica se não é muito longo
        if len(filename) > 255:
            return False
        
        return True
    
    def _remove_mixed_content(self, content: str) -> str:
        """
        Remove conteúdo misturado após o código (como tags HTML ou texto descritivo)
        
        Args:
            content: Conteúdo bruto
            
        Returns:
            Conteúdo limpo
        """
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # Para se encontrar uma tag HTML que não seja código
            if re.match(r'^\s*<[/]?(code|actions|read)\b', line, re.IGNORECASE):
                break
            
            # Para se encontrar texto descritivo típico (frases em inglês)
            if re.match(r'^\s*(Now I\'ll|First|Next|Then|Let me|I\'ll)', line, re.IGNORECASE):
                break
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _clean_code_content(self, content: str) -> str:
        """
        Limpa o conteúdo do código removendo espaços desnecessários e validando
        
        Args:
            content: Conteúdo bruto do código
            
        Returns:
            Código limpo
        """
        if not content:
            return ""
        
        # Remove espaços em branco no início e fim
        cleaned = content.strip()
        
        # Remove possíveis caracteres de controle
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        
        # Verifica se o conteúdo parece ser código válido
        if self._is_likely_code(cleaned):
            return cleaned
        else:
            # Se não parece código, tenta extrair apenas a parte que parece código
            return self._extract_code_portion(cleaned)
    
    def _is_likely_code(self, content: str) -> bool:
        """
        Verifica se o conteúdo parece ser código válido
        
        Args:
            content: Conteúdo a verificar
            
        Returns:
            True se parece ser código
        """
        if not content.strip():
            return False
        
        # Indicadores de código válido
        code_indicators = [
            r'import\s+\w+',  # Python imports
            r'from\s+\w+\s+import',  # Python imports
            r'function\s+\w+',  # JavaScript functions
            r'const\s+\w+',  # JavaScript/TypeScript
            r'let\s+\w+',  # JavaScript/TypeScript
            r'interface\s+\w+',  # TypeScript
            r'class\s+\w+',  # Classes
            r'def\s+\w+',  # Python functions
            r'<\w+[^>]*>',  # HTML/JSX tags
            r'{\s*\w+',  # Object syntax
            r'export\s+(default\s+)?',  # ES6 exports
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def _extract_code_portion(self, content: str) -> str:
        """
        Extrai apenas a porção que parece ser código válido
        
        Args:
            content: Conteúdo misto
            
        Returns:
            Apenas a parte que parece código
        """
        lines = content.split('\n')
        code_lines = []
        found_code_start = False
        
        for line in lines:
            # Se encontrou início de código
            if not found_code_start and self._line_looks_like_code(line):
                found_code_start = True
                code_lines.append(line)
            elif found_code_start:
                # Se já está em código, para quando encontrar texto descritivo
                if self._line_looks_like_description(line):
                    break
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def _line_looks_like_code(self, line: str) -> bool:
        """Verifica se uma linha parece código"""
        line = line.strip()
        if not line:
            return False
        
        # Padrões que indicam código
        code_patterns = [
            r'^import\s+',
            r'^from\s+',
            r'^export\s+',
            r'^const\s+',
            r'^let\s+',
            r'^var\s+',
            r'^function\s+',
            r'^class\s+',
            r'^def\s+',
            r'^interface\s+',
            r'^type\s+',
            r'^\w+\s*=',
            r'^<\w+',
            r'^\/\/',
            r'^\/\*',
            r'^#',
            r'^\s*{',
            r'^\s*}',
        ]
        
        return any(re.match(pattern, line) for pattern in code_patterns)
    
    def _line_looks_like_description(self, line: str) -> bool:
        """Verifica se uma linha parece descrição em texto natural"""
        line = line.strip()
        if not line:
            return False
        
        # Padrões que indicam texto descritivo
        desc_patterns = [
            r'^(Now|First|Next|Then|Finally|Let me|I\'ll|This)',
            r'^<[/]?(actions|read|code)\b',
            r'\w+\s+(will|can|should|might|creates?|updates?|modifies?)',
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in desc_patterns)
    
    def _is_valid_command_syntax(self, command: str) -> bool:
        """
        Verifica se um comando tem sintaxe válida
        
        Args:
            command: Comando a verificar
            
        Returns:
            True se a sintaxe do comando for válida
        """
        if not command or not command.strip():
            return False
            
        # Remove espaços extras
        command = command.strip()
        
        # Verifica se é apenas texto descritivo (frases em linguagem natural)
        descriptive_patterns = [
            r'^(create|make|build|install|setup|configure|add|update|modify)',
            r'(folder|directory|file|project|application|app)',
            r'^(let\'s|we|now|first|then|next|after)',
            r'(and then|followed by|in order to)',
        ]
        
        for pattern in descriptive_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                # Se contém palavras descritivas, verifica se é realmente um comando
                words = command.split()
                if len(words) > 0:
                    first_word = words[0].lower()
                    # Verifica se a primeira palavra é um comando válido conhecido
                    if first_word not in ['mkdir', 'cd', 'pip', 'npm', 'git', 'python', 'node', 'ls', 'dir', 'cat', 'type', 'echo', 'touch']:
                        return False
        
        # Verifica se contém múltiplos comandos em uma linha (&&, ;, |)
        if re.search(r'&&|;\s*\w|^\s*\w.*\|\s*\w', command):
            return False
        
        # Verifica se tem aspas desbalanceadas
        if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
            return False
        
        # Verifica se contém caracteres de controle inválidos
        invalid_chars = ['\t', '\r', '\n', '\x00']
        if any(char in command for char in invalid_chars):
            return False
        
        return True
    
    def _is_dangerous_command(self, code: str) -> bool:
        """
        Verifica se o código contém comandos perigosos
        
        Args:
            code: Código a verificar
            
        Returns:
            True se contém comandos perigosos
        """
        dangerous_patterns = [
            r'\brm\s+-rf\s+/', r'\brm\s+-rf\s+\.\.', r'\brm\s+-rf\s+\*',
            r'\brmdir\s+/s', r'\btaskkill\s+/f',
            r'\bformat\s+', r'\bfdisk\s+',
            r'\bdd\s+if=/dev/zero', r'\bmkfs\.',
            r'>\s*/dev/sd[a-z]', r':\(\)\{\s*:\|\s*:\s*&\s*\}',
            r'\bsudo\s+rm\s+-rf', r'\bdel\s+/f\s+/s\s+/q'
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, code_lower):
                return True
        
        return False
    
    def _process_code_blocks(self, code_blocks: list, original_prompt: str):
        """
        Processa blocos de código encontrados na resposta
        
        Args:
            code_blocks: Lista de tuplas (linguagem, código)
            original_prompt: Prompt original do usuário
        """
        bash_blocks = []
        other_blocks = []
        
        # Separa blocos bash/shell dos outros
        for lang, code in code_blocks:
            if lang.lower() in ['bash', 'sh', 'shell', 'zsh', 'fish']:
                bash_blocks.append((lang, code))
            else:
                other_blocks.append((lang, code))
        
        # Executa blocos bash automaticamente
        if bash_blocks and self.auto_execute_shell:
            for lang, code in bash_blocks:
                # Remove comentários e linhas vazias
                commands = [line.strip() for line in code.strip().split('\n') 
                           if line.strip() and not line.strip().startswith('#')]
                
                for cmd in commands:
                    # Converte comando para o OS apropriado
                    converted_cmd = self.shell_exec.convert_command(cmd)
                    
                    # Check for directory duplication in mkdir commands
                    if converted_cmd.strip().startswith('mkdir '):
                        dir_name = converted_cmd.strip()[6:].strip().strip('"').strip("'")
                        current_path = self.shell_exec.get_current_directory()
                        current_dir_name = Path(current_path).name
                        
                        # Check if trying to create a directory with same name as current directory
                        if dir_name.lower() == current_dir_name.lower():
                            console.print(f"[red]❌ Skipping: Cannot create directory '{dir_name}' - already inside '{current_dir_name}'![/red]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[dim]💡 Tip: Use a different unique name for the new directory[/dim]")
                            continue  # Skip this command
                        
                        # Check if the directory name already exists in the current path components
                        elif dir_name.lower() in current_path.lower():
                            console.print(f"[yellow]⚠️  Warning: Directory '{dir_name}' already exists in path![/yellow]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[yellow]Consider using a unique name instead[/yellow]")
                    
                    if self._is_dangerous_command(converted_cmd):
                        console.print(f"\n[yellow]⚠️  Comando potencialmente perigoso detectado:[/yellow]")
                        console.print(f"[red]{converted_cmd}[/red]")
                        confirm = console.input("[cyan]Executar mesmo assim? (s/N): [/cyan]")
                        if confirm.lower() != 's':
                            console.print("[dim]Comando ignorado[/dim]")
                            continue
                    
                    # Executa o comando convertido
                    with console.status(f"[dim]$ {converted_cmd}[/dim]", spinner="dots"):
                        success, output = self.shell_exec.execute_command(converted_cmd)
                    
                    if success:
                        if output.strip():
                            console.print(output)
                    else:
                        console.print(f"[red]❌ {output}[/red]")
                        # Send error back to LLM for automatic fix
                        console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                        error_prompt = f"The shell command '{converted_cmd}' failed with error: {output}. Please provide the correct command to fix this issue."
                        # Process error through LLM but disable auto-execution temporarily
                        temp_auto_execute = self.auto_execute_shell
                        self.auto_execute_shell = False
                        self.process_prompt(error_prompt)
                        self.auto_execute_shell = temp_auto_execute
        
                        # Process other code blocks
        if other_blocks:
            # Group by language
            by_lang = {}
            for lang, code in other_blocks:
                lang_key = lang or 'text'
                if lang_key not in by_lang:
                    by_lang[lang_key] = []
                by_lang[lang_key].append(code)
            
            # Show subtle summary
            total_blocks = sum(len(codes) for codes in by_lang.values())
            if total_blocks == 1:
                console.print(f"\n[dim]💾 1 code file available[/dim]")
            else:
                console.print(f"\n[dim]💾 {total_blocks} code files available[/dim]")
            
            # Save automatically without asking
            saved_count = 0
            for lang, codes in by_lang.items():
                for i, code in enumerate(codes):
                    # Generate name automatically
                    filename = self._generate_filename(lang, code, original_prompt)
                    
                    # Skip if no valid filename could be generated
                    if filename is None:
                        continue
                    
                    # If there are multiple files of the same language, add index
                    if len(codes) > 1:
                        # Don't create generic indexed files - instead skip or use better naming
                        if filename.startswith('main') or filename in ['index.js', 'index.html', 'main.py']:
                            console.print(f"[yellow]⚠️ Skipping generic file creation: {filename}_{i+1}[/yellow]")
                            console.print(f"[yellow]💡 Hint: Use specific filenames in your request or <code filename=\"...\"> tags[/yellow]")
                            continue
                        base, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
                        filename = f"{base}_{i+1}.{ext}" if ext else f"{base}_{i+1}"
                        
                        try:
                            # Resolve caminho do arquivo relativo ao diretório atual
                            current_dir = Path(self.shell_exec.get_current_directory())
                            file_path = self._resolve_file_path(filename, current_dir)
                            
                            # Verifica se arquivo já existe e decide entre criar ou editar
                            if file_path.exists():
                                console.print(f"[yellow]📝 Editando arquivo existente: {file_path.name}[/yellow]")
                                self.file_ops.edit_file(file_path, code.strip())
                                # Git commit automático
                                self.git_manager.commit_file_operation("edited", file_path)
                            else:
                                console.print(f"[green]📄 Criando novo arquivo: {file_path.name}[/green]")
                                self.file_ops.create_file(file_path, code.strip())
                                # Git commit automático
                                self.git_manager.commit_file_operation("created", file_path)
                            saved_count += 1
                        except FileOperationError as e:
                            console.print(f"[red]Error saving {filename}: {e}[/red]")
                
                if saved_count > 0:
                    console.print(f"[green]✓ {saved_count} file(s) saved[/green]")
    
    def _process_special_tags(self, response: str, original_prompt: str, skip_read_tags: bool = False):
        """
        Processa tags especiais na resposta: <actions>, <read>, <code>
        
        Args:
            response: Resposta completa do modelo
            original_prompt: Prompt original do usuário
            skip_read_tags: Se True, pula processamento de tags <read> para evitar loop infinito
        """
        processed_something = False
        
        # Processa tags <actions>
        actions_blocks = re.findall(r'<actions>(.*?)</actions>', response, re.DOTALL | re.IGNORECASE)
        if actions_blocks:
            console.print("\n[bold yellow]🔧 Executing actions...[/bold yellow]")
            processed_something = True
            for actions in actions_blocks:
                # Remove comentários e linhas vazias
                lines = [line.strip() for line in actions.strip().split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
                
                # Filtra apenas comandos válidos (ignora descrições em linguagem natural)
                commands = []
                for line in lines:
                    # Remove aspas desnecessárias e limpa o comando
                    cleaned_line = line.strip().strip('"').strip("'")
                    
                    # Verifica se contém caracteres inválidos para comandos
                    if self._is_valid_command_syntax(cleaned_line):
                        # Verifica se é um comando shell válido
                        if self.shell_exec.is_shell_command(cleaned_line) or any(cleaned_line.startswith(cmd) for cmd in ['cd ', 'mkdir ', 'touch ', 'pip ', 'npm ', 'git ', 'python ', 'node ']):
                            commands.append(cleaned_line)
                        else:
                            # Se não é comando, pode ser descrição - ignora
                            if self.debug_mode:
                                console.print(f"[dim]Ignoring non-command: {line}[/dim]")
                    else:
                        if self.debug_mode:
                            console.print(f"[dim]Ignoring invalid syntax: {line}[/dim]")
                
                for cmd in commands:
                    # Converte comando para o OS apropriado
                    converted_cmd = self.shell_exec.convert_command(cmd)
                    
                    # Check for directory duplication in mkdir commands
                    if converted_cmd.strip().startswith('mkdir '):
                        dir_name = converted_cmd.strip()[6:].strip().strip('"').strip("'")
                        current_path = self.shell_exec.get_current_directory()
                        current_dir_name = Path(current_path).name
                        
                        # Check if trying to create a directory with same name as current directory
                        if dir_name.lower() == current_dir_name.lower():
                            console.print(f"[red]❌ Skipping: Cannot create directory '{dir_name}' - already inside '{current_dir_name}'![/red]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[dim]💡 Tip: Use a different unique name for the new directory[/dim]")
                            continue  # Skip this command
                        
                        # Check if the directory name already exists in the current path components
                        elif dir_name.lower() in current_path.lower():
                            console.print(f"[yellow]⚠️  Warning: Directory '{dir_name}' already exists in path![/yellow]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[yellow]Consider using a unique name instead[/yellow]")
                    
                    if self._is_dangerous_command(converted_cmd):
                        console.print(f"\n[yellow]⚠️  Comando potencialmente perigoso detectado:[/yellow]")
                        console.print(f"[red]{converted_cmd}[/red]")
                        confirm = console.input("[cyan]Executar mesmo assim? (s/N): [/cyan]")
                        if confirm.lower() != 's':
                            console.print("[dim]Comando ignorado[/dim]")
                            continue
                    
                    # Executa o comando convertido
                    with console.status(f"[dim]$ {converted_cmd}[/dim]", spinner="dots"):
                        success, output = self.shell_exec.execute_command(converted_cmd)
                    
                    if success:
                        if output.strip():
                            console.print(output)
                    else:
                        console.print(f"[red]❌ {output}[/red]")
                        # Send error back to LLM for automatic fix
                        console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                        error_prompt = f"The shell command '{converted_cmd}' failed with error: {output}. Please provide the correct command to fix this issue."
                        # Process error through LLM but disable auto-execution temporarily
                        temp_auto_execute = self.auto_execute_shell
                        self.auto_execute_shell = False
                        self.process_prompt(error_prompt)
                        self.auto_execute_shell = temp_auto_execute
        
        # Processa tags <read> (only if not skipping to avoid infinite loop)
        if not skip_read_tags:
            read_blocks = re.findall(r'<read>(.*?)</read>', response, re.DOTALL | re.IGNORECASE)
            read_content = []  # Acumula conteúdo lido para injetar no contexto
        else:
            read_blocks = []
            read_content = []
            # Check if response contains read tags that we're skipping
            skipped_reads = re.findall(r'<read>(.*?)</read>', response, re.DOTALL | re.IGNORECASE)
            if skipped_reads:
                console.print(f"[dim]🔄 Skipping {len(skipped_reads)} read tag(s) to prevent infinite loop[/dim]")
            
        if read_blocks:
            console.print("\n[bold blue]📖 Reading files...[/bold blue]")
            processed_something = True
            for reads in read_blocks:
                # Remove comentários e linhas vazias
                lines = [line.strip() for line in reads.strip().split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
                
                # Filtra apenas comandos válidos (ignora descrições em linguagem natural)
                commands = []
                for line in lines:
                    # Remove aspas desnecessárias e limpa o comando
                    cleaned_line = line.strip().strip('"').strip("'")
                    
                    # Verifica se contém caracteres inválidos para comandos
                    if self._is_valid_command_syntax(cleaned_line):
                        # Verifica se é um comando de leitura válido
                        if self.shell_exec.is_shell_command(cleaned_line) or any(cleaned_line.startswith(cmd) for cmd in ['cat ', 'type ', 'ls ', 'dir ', 'head ', 'tail ']):
                            commands.append(cleaned_line)
                        else:
                            # Se não é comando, pode ser descrição - ignora
                            if self.debug_mode:
                                console.print(f"[dim]Ignoring non-command: {line}[/dim]")
                    else:
                        if self.debug_mode:
                            console.print(f"[dim]Ignoring invalid syntax: {line}[/dim]")
                
                for cmd in commands:
                    # Converte comando para o OS apropriado
                    converted_cmd = self.shell_exec.convert_command(cmd)
                    
                    # Check for directory duplication in mkdir commands
                    if converted_cmd.strip().startswith('mkdir '):
                        dir_name = converted_cmd.strip()[6:].strip().strip('"').strip("'")
                        current_path = self.shell_exec.get_current_directory()
                        current_dir_name = Path(current_path).name
                        
                        # Check if trying to create a directory with same name as current directory
                        if dir_name.lower() == current_dir_name.lower():
                            console.print(f"[red]❌ Skipping: Cannot create directory '{dir_name}' - already inside '{current_dir_name}'![/red]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[dim]💡 Tip: Use a different unique name for the new directory[/dim]")
                            continue  # Skip this command
                        
                        # Check if the directory name already exists in the current path components
                        elif dir_name.lower() in current_path.lower():
                            console.print(f"[yellow]⚠️  Warning: Directory '{dir_name}' already exists in path![/yellow]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[yellow]Consider using a unique name instead[/yellow]")
                    
                    # Executa o comando convertido
                    with console.status(f"[dim]$ {converted_cmd}[/dim]", spinner="dots"):
                        success, output = self.shell_exec.execute_command(converted_cmd)
                    
                    if success:
                        if output.strip():
                            console.print(output)
                            # Captura conteúdo para injetar no contexto do LLM
                            read_content.append(f"--- Output from: {converted_cmd} ---\n{output.strip()}\n")
                    else:
                        console.print(f"[red]❌ {output}[/red]")
                        # Send error back to LLM for automatic fix
                        console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                        error_prompt = f"The shell command '{converted_cmd}' failed with error: {output}. Please provide the correct command to fix this issue."
                        # Process error through LLM but disable auto-execution temporarily
                        temp_auto_execute = self.auto_execute_shell
                        self.auto_execute_shell = False
                        self.process_prompt(error_prompt)
                        self.auto_execute_shell = temp_auto_execute
        
        # Se houve leitura de arquivos, re-executa o prompt original com o conteúdo
        if read_content:
            console.print(f"\n[bold cyan]🔄 Re-executing prompt with file content...[/bold cyan]")
            self._reprocess_with_file_content(original_prompt, read_content)
        
        # Processa tags <code edit> e <code create> com tratamento específico
        code_blocks = self._extract_code_blocks(response)
        if code_blocks:
            # Separa blocos por tipo de ação
            edit_blocks = [(filename, content) for action_type, filename, content in code_blocks if action_type == 'edit']
            create_blocks = [(filename, content) for action_type, filename, content in code_blocks if action_type == 'create']
            
            total_blocks = len(code_blocks)
            console.print(f"\n[bold green]💾 Processing {total_blocks} file(s): {len(edit_blocks)} edit(s), {len(create_blocks)} create(s)...[/bold green]")
            processed_something = True
            
            processed_count = 0
            current_dir = Path(self.shell_exec.get_current_directory())
            
            # Processa edições primeiro
            for filename, code_content in edit_blocks:
                try:
                    # Remove espaços em branco desnecessários e valida o conteúdo
                    clean_code = self._clean_code_content(code_content)
                    
                    if not clean_code.strip():
                        console.print(f"[yellow]⚠️  Skipping empty edit: {filename}[/yellow]")
                        continue
                    
                    # Resolve caminho do arquivo relativo ao diretório atual
                    file_path = self._resolve_file_path(filename, current_dir)
                    
                    # Verifica se arquivo existe para edição
                    if not file_path.exists():
                        console.print(f"[yellow]⚠️  File does not exist for edit, creating instead: {filename}[/yellow]")
                    
                    console.print(f"[blue]✏️  Editing: {filename}[/blue]")
                    
                    # Preview das mudanças para edições
                    preview = self.file_editor.preview_file_changes(str(file_path), clean_code)
                    console.print(f"[dim]{preview}[/dim]")
                    
                    # Usa modo de edição inteligente
                    success, message = self.file_editor.smart_file_update(
                        str(file_path), 
                        clean_code, 
                        update_mode="smart_merge"  # Modo inteligente para edições
                    )
                    
                    if success:
                        console.print(f"[green]✅ {message}[/green]")
                        # Git commit com mensagem específica de edição
                        self.git_manager.commit_file_operation("edited", file_path)
                    else:
                        console.print(f"[red]❌ Failed to edit {filename}: {message}[/red]")
                        continue
                    processed_count += 1
                    
                except FileOperationError as e:
                    console.print(f"[red]❌ Error editing {filename}: {e}[/red]")
            
            # Processa criações depois
            for filename, code_content in create_blocks:
                try:
                    # Remove espaços em branco desnecessários e valida o conteúdo
                    clean_code = self._clean_code_content(code_content)
                    
                    if not clean_code.strip():
                        console.print(f"[yellow]⚠️  Skipping empty file: {filename}[/yellow]")
                        continue
                    
                    # Resolve caminho do arquivo relativo ao diretório atual
                    file_path = self._resolve_file_path(filename, current_dir)
                    
                    # Avisa se arquivo já existe na criação
                    if file_path.exists():
                        console.print(f"[yellow]⚠️  File already exists, overwriting: {filename}[/yellow]")
                    
                    console.print(f"[green]🆕 Creating: {filename}[/green]")
                    
                    # Preview das mudanças para criações
                    preview = self.file_editor.preview_file_changes(str(file_path), clean_code)
                    console.print(f"[dim]{preview}[/dim]")
                    
                    # Usa modo de substituição para criações
                    success, message = self.file_editor.smart_file_update(
                        str(file_path), 
                        clean_code, 
                        update_mode="replace"  # Modo replace para criações
                    )
                    
                    if success:
                        console.print(f"[green]✅ {message}[/green]")
                        # Git commit com mensagem específica de criação
                        self.git_manager.commit_file_operation("created", file_path)
                    else:
                        console.print(f"[red]❌ Failed to create {filename}: {message}[/red]")
                        continue
                    processed_count += 1
                    
                except FileOperationError as e:
                    console.print(f"[red]❌ Error creating {filename}: {e}[/red]")
            
            if processed_count > 0:
                console.print(f"[bold green]✅ {processed_count} file(s) processed successfully![/bold green]")
        
        # Debug: inform if no special tags were processed
        if not processed_something:
            console.print("[dim]⚠️  No special tags found in response[/dim]")
            console.print("[dim]💡 The model should use <actions>, <read>, <code edit> or <code create> for actions[/dim]")
        
        return processed_something
    
    def _restart_generation_with_content(self, original_prompt: str, enhanced_prompt: str, read_content: list, previous_response: str = ""):
        """
        Reinicia a geração com o conteúdo dos arquivos injetado
        
        Args:
            original_prompt: Prompt original do usuário
            enhanced_prompt: Prompt melhorado (pode ter contexto adicional)
            read_content: Lista de conteúdos lidos
            previous_response: Resposta parcial antes da tag <read>
        """
        try:
            # Constrói contexto com o conteúdo dos arquivos
            file_context_parts = ["\n[FILES READ - INJECTED CONTENT:]"]
            
            for content in read_content:
                file_context_parts.append(content)
            
            file_context = '\n'.join(file_context_parts)
            
            # Inclui resposta parcial anterior se houver
            context_parts = []
            if previous_response:
                context_parts.append(f"[PREVIOUS PARTIAL RESPONSE:]\n{previous_response}\n")
            
            context_parts.append(f"[ORIGINAL REQUEST:]\n{original_prompt}")
            context_parts.append(file_context)
            context_parts.append("\nIMPORTANT: Complete your response using the file content above. Continue from where you left off.")
            
            restart_prompt = '\n'.join(context_parts)
            
            console.print("[dim]🔄 Restarting generation with file content...[/dim]")
            
            # Reinicia a geração
            full_response = ""
            try:
                with console.status("[bold green]🔄 Continuing with file content...", spinner="dots") as status:
                    for chunk in self.api.generate(self.selected_model, restart_prompt):
                        full_response += chunk
            except KeyboardInterrupt:
                console.print("\n[yellow]💡 Restarted generation interrupted by user[/yellow]")
                return
            
            # Exibe a resposta final
            console.print("\n[bold cyan]📋 Complete Response with File Content:[/bold cyan]\n")
            
            # Processa novamente para tags especiais
            self._process_special_tags(full_response, original_prompt)
            
            # Exibe a resposta formatada
            self._display_formatted_response(full_response)
            
        except Exception as e:
            console.print(f"[red]Error restarting generation with file content: {e}[/red]")
            if self.debug_mode:
                import traceback
                console.print(f"[dim]Debug traceback: {traceback.format_exc()}[/dim]")
    
    def _reprocess_with_file_content(self, original_prompt: str, read_content: list):
        """
        Re-executa o prompt original com o conteúdo dos arquivos lidos injetado
        
        Args:
            original_prompt: Prompt original do usuário
            read_content: Lista de strings com conteúdo dos arquivos lidos
        """
        try:
            # Constrói contexto com o conteúdo dos arquivos
            file_context_parts = ["\n[FILES READ - INJECTED CONTENT:]"]
            
            for content in read_content:
                file_context_parts.append(content)
            
            file_context = '\n'.join(file_context_parts)
            
            # Cria prompt expandido com conteúdo dos arquivos
            enhanced_prompt_with_files = f"""
{original_prompt}

{file_context}

IMPORTANT: Use the file content above to provide a complete and accurate response to the original request.
"""
            
            console.print("[dim]Sending enhanced prompt with file content to model...[/dim]")
            
            # Re-executa o prompt com o conteúdo dos arquivos
            try:
                full_response = ""
                with console.status("[bold green]🔄 Processing with file content...", spinner="dots") as status:
                    for chunk in self.api.generate(self.selected_model, enhanced_prompt_with_files):
                        full_response += chunk
            except KeyboardInterrupt:
                console.print("\n[yellow]💡 Reprocessing interrupted by user[/yellow]")
                return
            
            # Exibe a resposta final
            console.print("\n[bold cyan]📋 Response with File Content:[/bold cyan]\n")
            
            # Processa novamente para tags especiais (recursivamente)
            self._process_special_tags(full_response, original_prompt)
            
            # Exibe a resposta formatada
            self._display_formatted_response(full_response)
            
        except Exception as e:
            console.print(f"[red]Error reprocessing with file content: {e}[/red]")
            if self.debug_mode:
                import traceback
                console.print(f"[dim]Debug traceback: {traceback.format_exc()}[/dim]")
    
    def session_command(self, args: str = ""):
        """
        Processes session-related commands
        
        Args:
            args: Session command arguments
        """
        parts = args.split(maxsplit=1) if args.strip() else []
        subcommand = parts[0].lower() if parts else "info"
        
        if subcommand == "info" or subcommand == "status":
            # Show current session information
            summary = self.session_manager.get_session_summary()
            if summary:
                console.print(summary)
                
                # Show detailed statistics
                stats = self.session_manager.get_interaction_stats()
                if stats:
                    console.print(f"\n[bold blue]📈 Session Statistics:[/bold blue]")
                    console.print(f"[dim]• Total interactions: {stats.get('total_interactions', 0)}")
                    console.print(f"• User messages: {stats.get('user_messages', 0)}")
                    console.print(f"• Assistant messages: {stats.get('assistant_messages', 0)}")
                    if stats.get('session_duration'):
                        console.print(f"• Session duration: {stats['session_duration']}[/dim]")
            else:
                console.print("[yellow]No previous session found.[/yellow]")
                
        elif subcommand == "clear":
            # Clear current session
            if self.session_manager.clear_session():
                console.print("[green]✓ Current session cleared and archived[/green]")
                # Also clear prompt enhancer context
                if hasattr(self.prompt_enhancer, 'flush_context'):
                    self.prompt_enhancer.flush_context()
                    console.print("[green]✓ Model context also cleared[/green]")
            else:
                console.print("[red]❌ Error clearing session[/red]")
                
        elif subcommand == "backups":
            # List available backups
            backups = self.session_manager.list_backup_sessions()
            if backups:
                console.print(f"[bold blue]📁 Available Session Backups:[/bold blue]")
                for i, backup in enumerate(backups[:10], 1):  # Show only the 10 most recent
                    from datetime import datetime
                    timestamp = datetime.fromtimestamp(backup.stat().st_mtime)
                    console.print(f"[dim]  {i}. {backup.name} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
                
                if len(backups) > 10:
                    console.print(f"[dim]  ... and {len(backups) - 10} more backup(s)[/dim]")
                    
                console.print(f"\n[dim]💡 Use '/session restore <backup_name>' to restore[/dim]")
            else:
                console.print("[yellow]No session backups found.[/yellow]")
                
        elif subcommand == "restore":
            # Restore a backup
            if len(parts) < 2:
                console.print("[red]Usage: /session restore <backup_name>[/red]")
                console.print("[dim]Use '/session backups' to see available backups[/dim]")
                return
            
            backup_name = parts[1]
            backup_path = self.session_manager.session_dir / backup_name
            
            if not backup_path.exists():
                # Try to find by partial pattern
                backups = self.session_manager.list_backup_sessions()
                matches = [b for b in backups if backup_name in b.name]
                
                if len(matches) == 1:
                    backup_path = matches[0]
                elif len(matches) > 1:
                    console.print(f"[yellow]Multiple backups found with '{backup_name}':[/yellow]")
                    for match in matches[:5]:
                        console.print(f"[dim]  - {match.name}[/dim]")
                    console.print("[dim]Use the complete backup name[/dim]")
                    return
                else:
                    console.print(f"[red]Backup '{backup_name}' not found[/red]")
                    console.print("[dim]Use '/session backups' to see available backups[/dim]")
                    return
            
            if self.session_manager.restore_backup_session(backup_path):
                console.print("[green]✓ Backup restored successfully[/green]")
                console.print("[yellow]💡 Restart XandAI to load the restored session[/yellow]")
            else:
                console.print("[red]❌ Error restoring backup[/red]")
                
        elif subcommand == "save":
            # Force save of current session
            if self.selected_model and hasattr(self.prompt_enhancer, 'context_history'):
                success = self.session_manager.save_session(
                    model_name=self.selected_model,
                    context_history=getattr(self.prompt_enhancer, 'context_history', []),
                    working_directory=str(self.shell_exec.get_current_directory()),
                    shell_settings={
                        'auto_execute_shell': self.auto_execute_shell,
                        'enhance_prompts': self.enhance_prompts,
                        'better_prompting': self.better_prompting
                    }
                )
                
                if success:
                    console.print("[green]✓ Session saved successfully[/green]")
                else:
                    console.print("[red]❌ Error saving session[/red]")
            else:
                console.print("[yellow]⚠️  No active session to save[/yellow]")
                
        else:
            console.print(f"[red]Unknown session command: {subcommand}[/red]")
            console.print("[dim]Available commands: info, clear, backups, restore, save[/dim]")
    
    def task_command(self, args: str = ""):
        """
        Processa comando de tarefa complexa
        
        Args:
            args: Descrição da tarefa complexa
        """
        if not args.strip():
            console.print("[red]Usage: /task <complex task description>[/red]")
            console.print("[dim]Example: /task create a complete REST API with authentication[/dim]")
            return
        
        if not self.selected_model:
            console.print("[red]No model selected. Use /models to select one.[/red]")
            return
        
        console.print("\n[bold blue]🎯 Complex Task Mode Activated[/bold blue]")
        console.print(f"[dim]Analyzing: {args}[/dim]\n")
        
        # *** CRITICAL: Set working directory context for task manager ***
        current_working_dir = str(Path.cwd())
        self.task_manager.set_working_directory(current_working_dir)
        console.print(f"[dim]Working directory: {current_working_dir}[/dim]")
        
        # Step 1: Apply better prompting to enhance task description
        enhanced_args = args
        if self.better_prompting:
            enhanced_args = self.analyze_and_enhance_prompt(args)
            # Add to context history
            if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                self.prompt_enhancer.add_to_context_history("user", f"Task: {args}")
        
        # Detect language and framework in enhanced request
        self.task_manager.detect_and_update_context(enhanced_args)
        
        # Step 1: Ask model to break down into sub-tasks using improved version
        breakdown_prompt = self.task_manager.get_breakdown_prompt(enhanced_args)
        
        try:
            # Generate breakdown without showing the whole process
            try:
                with console.status("[bold yellow]Analyzing and dividing into sub-tasks...", spinner="dots"):
                    breakdown_response = ""
                    for chunk in self.api.generate(self.selected_model, breakdown_prompt):
                        breakdown_response += chunk
            except KeyboardInterrupt:
                console.print("\n[yellow]💡 Task breakdown interrupted by user[/yellow]")
                return
            
            # Extract tasks from response
            tasks = self.task_manager.parse_task_breakdown(breakdown_response)
            
            # Detect language and framework in breakdown too
            self.task_manager.detect_and_update_context(breakdown_response)
            
            if not tasks:
                console.print("[red]Could not extract sub-tasks. Try to be more specific.[/red]")
                return
            
            # Save tasks in manager
            self.task_manager.current_tasks = tasks
            self.task_manager.completed_tasks = []
            
            # Show execution plan
            console.print("[bold green]✅ Execution Plan Created![/bold green]\n")
            self.task_manager.display_task_progress()
            
            # Count essential and optional tasks
            essential_count = sum(1 for t in tasks if t.get('priority', 'essential') == 'essential')
            optional_count = sum(1 for t in tasks if t.get('priority') == 'optional')
            
            console.print(f"\n[bold]📊 Summary:[/bold]")
            console.print(f"   [green]Essential: {essential_count} tasks[/green]")
            console.print(f"   [yellow]Optional: {optional_count} tasks[/yellow]")
            
            # Choice menu
            console.print("\n[bold cyan]Choose an option:[/bold cyan]")
            console.print("  1. Execute ESSENTIAL tasks only")
            console.print("  2. Execute ALL tasks (essential + optional)")
            console.print("  3. Cancel")
            
            choice = console.input("\n[cyan]Your choice (1/2/3): [/cyan]")
            
            if choice == '1':
                # Filter only essential tasks
                tasks_to_execute = [t for t in tasks if t.get('priority', 'essential') == 'essential']
                console.print(f"\n[green]✓ Executing {len(tasks_to_execute)} essential tasks[/green]")
            elif choice == '2':
                # Execute all tasks
                tasks_to_execute = tasks
                console.print(f"\n[green]✓ Executing all {len(tasks_to_execute)} tasks[/green]")
            else:
                console.print("[yellow]Execution cancelled.[/yellow]")
                return
            
            console.print("\n[bold blue]🚀 Starting task execution...[/bold blue]\n")
            
            # Step 2: Execute each task
            for i, task in enumerate(tasks_to_execute):
                priority_indicator = "[ESSENTIAL]" if task.get('priority', 'essential') == 'essential' else "[OPTIONAL]"
                console.print(f"\n[bold yellow]━━━ Task {i+1}/{len(tasks_to_execute)} {priority_indicator} ━━━[/bold yellow]")
                console.print(f"[cyan]{task['description']}[/cyan]")
                console.print(f"[dim]Detected type: {task['type']}[/dim]\n")
                
                # Update status
                task['status'] = 'in_progress'
                self.task_manager.display_task_progress()
                
                # Create specific prompt for the task
                task_prompt = self.task_manager.format_task_prompt(task, context=args)
                
                # Execute the task
                console.print("\n[dim]Executing task...[/dim]")
                self._execute_task(task_prompt, task)
                
                # Mark as completed and refresh context
                task['status'] = 'completed'
                self.task_manager.add_task_completion_info(task)
                
                # Small pause between tasks
                if i < len(tasks) - 1:
                    console.print("\n[dim]Preparing next task...[/dim]")
            
            # Show final summary
            console.print("\n[bold green]🎉 All tasks completed![/bold green]")
            self.task_manager.display_task_progress()
            
        except Exception as e:
            console.print(f"[red]Error processing tasks: {e}[/red]")
    
    def _execute_task(self, task_prompt: str, task_info: Dict):
        """
        Executa uma tarefa individual
        
        Args:
            task_prompt: Prompt formatado para a tarefa
            task_info: Informações da tarefa
        """
        try:
            # If enhancements are enabled, apply to task prompt too
            if self.enhance_prompts:
                enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                    task_prompt,
                    self.shell_exec.get_current_directory(),
                    self.shell_exec.get_os_info()
                )
            else:
                enhanced_prompt = task_prompt
            
            # Gera resposta
            full_response = ""
            
            # Se é tarefa de texto, mostra em tempo real
            if task_info['type'] == 'text':
                try:
                    with console.status("[bold green]Generating explanation...", spinner="dots") as status:
                        for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                            full_response += chunk
                except KeyboardInterrupt:
                    console.print("\n[yellow]💡 Task generation interrupted by user[/yellow]")
                    if full_response.strip():
                        console.print("[dim]Processing partial response...[/dim]")
                    else:
                        return
                
                # Exibe como texto formatado
                console.print("\n[bold cyan]Resposta:[/bold cyan]\n")
                console.print(Panel(Markdown(full_response), border_style="cyan"))
            else:
                # Para código/shell, usa processamento normal
                try:
                    with console.status("[bold green]Generating solution...", spinner="dots") as status:
                        for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                            full_response += chunk
                except KeyboardInterrupt:
                    console.print("\n[yellow]💡 Task generation interrupted by user[/yellow]")
                    if full_response.strip():
                        console.print("[dim]Processing partial response...[/dim]")
                    else:
                        return
                
                # Processa resposta normalmente
                console.print("\n[bold cyan]Solution:[/bold cyan]\n")
                
                # Debug: Mostra se há tags especiais na resposta
                has_actions = '<actions>' in full_response.lower()
                has_read = '<read>' in full_response.lower()
                has_code = '<code' in full_response.lower()
                has_traditional_code = '```' in full_response
                
                if not (has_actions or has_read or has_code or has_traditional_code):
                    if self.debug_mode:
                        console.print(f"[dim]🔍 Response without code/actions detected.[/dim]")
                        console.print(Panel(full_response, title="[dim]DEBUG - Resposta Raw[/dim]", border_style="dim"))
                
                # Processa tags especiais PRIMEIRO
                special_processed = False
                
                # Processa tags especiais
                if has_actions or has_read or has_code:
                    tags_processed = self._process_special_tags(full_response, task_info['description'])
                    if tags_processed:
                        special_processed = True
                
                # Detecta e processa blocos de código tradicionais (compatibilidade)
                if has_traditional_code:
                    code_blocks = re.findall(r'```(\w*)\n(.*?)```', full_response, re.DOTALL)
                    if code_blocks:
                        self._process_code_blocks(code_blocks, task_info['description'])
                        special_processed = True
                
                # Exibe a resposta formatada (texto restante)
                self._display_formatted_response(full_response)
                
                # Se não houve processamento especial, avisa o usuário
                if not special_processed and full_response.strip():
                    console.print("[dim]💡 Dica: O modelo deveria usar tags <code>, <actions> ou <read> para esta tarefa[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error executing task: {e}[/red]")
            task_info['status'] = 'failed'
        
    def show_help(self):
        """Shows CLI help"""
        help_text = """
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
        console.print(Panel(Markdown(help_text), title="[bold blue]Ajuda do XandAI[/bold blue]"))
        
    def file_command(self, args: str = ""):
        """
        Processa comandos de arquivo
        
        Args:
            args: Argumentos do comando
        """
        parts = args.split(maxsplit=2)
        
        if not parts:
            console.print("[red]Usage: /file <command> <file> [content][/red]")
            return
            
        subcommand = parts[0].lower()
        
        try:
            # Obtém diretório atual para resolver caminhos relativos
            current_dir = Path(self.shell_exec.get_current_directory())
            
            if subcommand == "create":
                if len(parts) < 2:
                    console.print("[red]Usage: /file create <path> [content][/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                content = parts[2] if len(parts) > 2 else ""
                self.file_ops.create_file(filepath, content)
                # Git commit automático
                self.git_manager.commit_file_operation("created", filepath)
                
            elif subcommand == "edit":
                if len(parts) < 3:
                    console.print("[red]Usage: /file edit <path> <content>[/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                content = parts[2]
                self.file_ops.edit_file(filepath, content)
                # Git commit automático
                self.git_manager.commit_file_operation("edited", filepath)
                
            elif subcommand == "append":
                if len(parts) < 3:
                    console.print("[red]Usage: /file append <path> <content>[/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                content = parts[2]
                self.file_ops.append_to_file(filepath, content)
                # Git commit automático
                self.git_manager.commit_file_operation("edited", filepath)
                
            elif subcommand == "read":
                if len(parts) < 2:
                    console.print("[red]Usage: /file read <path>[/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                content = self.file_ops.read_file(filepath)
                
                # Detect language by extension
                lang = Path(filepath).suffix.lstrip('.')
                if lang in ['py', 'python']:
                    lang = 'python'
                elif lang in ['js', 'javascript']:
                    lang = 'javascript'
                elif lang in ['ts', 'typescript']:
                    lang = 'typescript'
                elif lang in ['rs', 'rust']:
                    lang = 'rust'
                elif lang in ['go']:
                    lang = 'go'
                elif lang in ['java']:
                    lang = 'java'
                elif lang in ['cpp', 'c++', 'cc']:
                    lang = 'cpp'
                elif lang in ['c']:
                    lang = 'c'
                else:
                    lang = 'text'
                
                syntax = Syntax(content, lang, theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"[bold]{filepath}[/bold]"))
                
            elif subcommand == "delete":
                if len(parts) < 2:
                    console.print("[red]Uso: /file delete <caminho>[/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                self.file_ops.delete_file(filepath)
                # Git commit automático
                self.git_manager.commit_file_operation("deleted", filepath)
                
            elif subcommand == "list":
                # Verifica se deve buscar recursivamente
                recursive = False
                pattern = "*"
                directory = current_dir
                
                # Parse dos argumentos
                remaining_parts = parts[1:]
                for i, part in enumerate(remaining_parts):
                    if part in ["-r", "--recursive"]:
                        recursive = True
                    elif i == 0 and part not in ["-r", "--recursive"]:
                        directory = self._resolve_file_path(part, current_dir)
                    elif part not in ["-r", "--recursive"]:
                        pattern = part
                
                files = self.file_ops.list_files(directory, pattern, recursive=recursive)
                
                if files:
                    title = f"Arquivos em {directory}"
                    if recursive:
                        title += " (busca recursiva)"
                    
                    table = Table(title=title)
                    table.add_column("Path", style="cyan")
                    table.add_column("Size", style="green")
                    table.add_column("Modified", style="yellow")
                    
                    for file in sorted(files):
                        if file.is_file():
                            stat = file.stat()
                            size = f"{stat.st_size:,} bytes"
                            modified = file.stat().st_mtime
                            from datetime import datetime
                            modified_str = datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Mostra caminho relativo se for busca recursiva
                            if recursive:
                                try:
                                    rel_path = file.relative_to(directory)
                                    table.add_row(str(rel_path), size, modified_str)
                                except ValueError:
                                    table.add_row(str(file), size, modified_str)
                            else:
                                table.add_row(file.name, size, modified_str)
                    
                    console.print(table)
                else:
                    console.print(f"[yellow]No files found in {directory}[/yellow]")
                    
            elif subcommand == "search":
                if len(parts) < 2:
                    console.print("[red]Usage: /file search <filename>[/red]")
                    return
                
                filename = parts[1]
                
                # Primeiro tenta buscar arquivo normalmente
                found_path = self.file_ops.search_file(filename, current_dir)
                
                if found_path:
                    # Pergunta se quer ler o arquivo
                    from rich.prompt import Confirm
                    if Confirm.ask(f"Do you want to read the file {found_path}?"):
                        content = self.file_ops.read_file(found_path)
                        console.print(Panel(
                            Syntax(content, "auto", theme="monokai", line_numbers=True),
                            title=f"📄 {found_path}",
                            border_style="green"
                        ))
                else:
                    # Se não encontrou arquivo, busca por diretórios também
                    console.print(f"[yellow]File '{filename}' not found. Searching for directories...[/yellow]\n")
                    
                    results = self.file_ops.search_file_or_directory(filename, current_dir)
                    
                    # Mostra diretórios encontrados
                    if results['directories']:
                        console.print("[bold cyan]📁 Directories found:[/bold cyan]")
                        for i, dir_path in enumerate(results['directories'][:10], 1):
                            console.print(f"  {i}. {dir_path}")
                        
                        console.print("\n[yellow]💡 Tip: Navigate to a directory and search again[/yellow]")
                        
                        # Pergunta se quer navegar para algum diretório
                        if len(results['directories']) == 1:
                            from rich.prompt import Confirm
                            if Confirm.ask(f"\nDeseja navegar para {results['directories'][0]}?"):
                                rel_path = os.path.relpath(results['directories'][0], current_dir)
                                cmd = f"cd \"{rel_path}\""
                                console.print(f"\n[dim]Executando: {cmd}[/dim]")
                                success, output = self.shell_exec.execute_command(cmd)
                                if success:
                                    console.print(f"[green]✓ Navegado para: {results['directories'][0]}[/green]")
                                    console.print("[yellow]💡 Tente buscar o arquivo novamente com /file search[/yellow]")
                        else:
                            try:
                                choice = console.input("\n[cyan]Digite o número do diretório para navegar (ou Enter para cancelar): [/cyan]")
                                if choice.strip():
                                    idx = int(choice) - 1
                                    if 0 <= idx < len(results['directories']):
                                        rel_path = os.path.relpath(results['directories'][idx], current_dir)
                                        cmd = f"cd \"{rel_path}\""
                                        console.print(f"\n[dim]Executando: {cmd}[/dim]")
                                        success, output = self.shell_exec.execute_command(cmd)
                                        if success:
                                            console.print(f"[green]✓ Navegado para: {results['directories'][idx]}[/green]")
                                            console.print("[yellow]💡 Tente buscar o arquivo novamente com /file search[/yellow]")
                            except (ValueError, IndexError):
                                console.print("[red]Invalid choice[/red]")
                    
                    # Mostra arquivos similares encontrados
                    if results['files']:
                        console.print("\n[bold cyan]📄 Similar files found:[/bold cyan]")
                        for i, file_path in enumerate(results['files'][:5], 1):
                            console.print(f"  {i}. {file_path}")
                        
                        # Pergunta se quer abrir algum arquivo similar
                        if len(results['files']) == 1:
                            from rich.prompt import Confirm
                            if Confirm.ask(f"\nDo you want to read {results['files'][0]}?"):
                                content = self.file_ops.read_file(results['files'][0])
                                console.print(Panel(
                                    Syntax(content, "auto", theme="monokai", line_numbers=True),
                                    title=f"📄 {results['files'][0]}",
                                    border_style="green"
                                ))
                        else:
                            try:
                                choice = console.input("\n[cyan]Enter the file number to read (or Enter to cancel): [/cyan]")
                                if choice.strip():
                                    idx = int(choice) - 1
                                    if 0 <= idx < len(results['files']):
                                        content = self.file_ops.read_file(results['files'][idx])
                                        console.print(Panel(
                                            Syntax(content, "auto", theme="monokai", line_numbers=True),
                                            title=f"📄 {results['files'][idx]}",
                                            border_style="green"
                                        ))
                            except (ValueError, IndexError):
                                console.print("[red]Invalid choice[/red]")
                    
                    if not results['files'] and not results['directories']:
                        console.print(f"[red]❌ No file or directory found with name similar to '{filename}'[/red]")
                    
            else:
                console.print(f"[red]Unknown file command: {subcommand}[/red]")
                
        except FileOperationError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
    
    def list_models(self) -> Optional[str]:
        """
        Lista os modelos disponíveis e permite seleção
        
        Returns:
            Nome do modelo selecionado ou None
        """
        try:
            models = self.api.list_models()
            
            if not models:
                console.print("[red]No models available.[/red]")
                return None
            
            # Cria tabela de modelos
            table = Table(title="Available Models")
            table.add_column("Number", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Modified", style="magenta")
            
            for i, model in enumerate(models, 1):
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                modified = model.get('modified_at', 'Unknown')
                
                # Formata data se disponível
                if modified != 'Unknown':
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                        modified = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                table.add_row(
                    str(i),
                    name,
                    f"{size_gb:.1f} GB",
                    modified
                )
            
            console.print(table)
            
            # Seleção de modelo
            while True:
                try:
                    choice = console.input("\n[bold cyan]Select a model by number (or 'q' to exit): [/bold cyan]")
                    
                    if choice.lower() == 'q':
                        return None
                    
                    model_index = int(choice) - 1
                    if 0 <= model_index < len(models):
                        selected = models[model_index]['name']
                        console.print(f"\n[green]✓ Model selected: {selected}[/green]")
                        return selected
                    else:
                        console.print("[red]Invalid number. Try again.[/red]")
                        
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")
                    
        except OllamaAPIError as e:
            console.print(f"[red]Error listing models: {e}[/red]")
            return None
    
    def _should_execute_as_command(self, prompt_text: str) -> Optional[str]:
        """
        Checks if the prompt should be executed as a shell command instead of sent to LLM
        
        Args:
            prompt_text: User input to analyze
            
        Returns:
            Command to execute if it's a shell command, None otherwise
        """
        # Remove leading/trailing whitespace and normalize
        text = prompt_text.strip()
        
        # Skip if it's too long (likely not a simple command)
        if len(text) > 150:
            return None
        
        text_lower = text.lower()
        
        # Skip if it contains question words or complex phrases indicating LLM queries
        question_indicators = ['what', 'how', 'why', 'when', 'where', 'which', 'who', 'can you', 'please', 'help', '?', 'explain', 'show me', 'tell me', 'create', 'make', 'generate', 'write', 'build', 'fix', 'error', 'problema', 'bug', 'issue', 'broken', 'not working']
        if any(indicator in text_lower for indicator in question_indicators):
            return None
        
        # Early return for obviously non-command patterns (error messages, webpack, etc.)
        if any(pattern in text_lower for pattern in ['error', 'compiled with', 'webpack', 'ts2307', 'cannot find module', 'fix this', 'help with', 'module not found']):
            return None
        
        # ONLY basic shell commands that should be executed directly
        shell_commands = [
            'ls', 'dir', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'cat', 'type',
            'echo', 'touch', 'grep', 'find', 'ps', 'kill', 'chmod', 'chown', 'which',
            'whereis', 'date', 'time', 'whoami', 'hostname', 'uname', 'df', 'du',
            'free', 'top', 'htop', 'clear', 'cls', 'exit', 'logout', 'history',
            'tree', 'nano', 'vim', 'vi', 'less', 'more', 'head', 'tail', 'wc',
            'sort', 'uniq', 'cut', 'awk', 'sed', 'tar', 'zip', 'unzip', 'gzip',
            'gunzip', 'wget', 'curl', 'ping', 'traceroute', 'nslookup', 'dig',
            'ifconfig', 'ipconfig', 'netstat', 'ss', 'route', 'arp', 'git',
            'npm', 'pip', 'python', 'python3', 'node', 'java', 'javac', 'gcc',
            'g++', 'make', 'cmake', 'cargo', 'rustc', 'go', 'docker', 'kubectl'
        ]
        
        # Check if the first word is a shell command
        first_word = text.split()[0] if text else ""
        
        # Check exact command match - be very strict
        if first_word.lower() in shell_commands:
            return text
            
        # Pattern matching for common command structures
        command_patterns = [
            r'^cd\s+[\w\-\.\/\\]+$',  # cd path
            r'^ls\s*[\w\-\.\s\/\\]*$',  # ls with optional path/flags
            r'^dir\s*[\w\-\.\s\/\\]*$',  # dir with optional path/flags  
            r'^cat\s+[\w\-\.\/\\]+$',  # cat filename
            r'^mkdir\s+[\w\-\.\/\\]+$',  # mkdir dirname
            r'^rm\s+[\w\-\.\/\\]+$',  # rm filename
            r'^git\s+\w+(\s+[\w\-\.\/\\]*)*$',  # git commands
            r'^npm\s+\w+(\s+[\w\-\.\/\\@]*)*$',  # npm commands
            r'^python\s+[\w\-\.\/\\]+\.py$',  # python script.py
        ]
        
        for pattern in command_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return text
        
        # Legacy patterns for natural language commands
        prompt_lower = text.lower()
        list_patterns = [
            # File listing
            (r'list.*files?.*directory', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'show.*files?', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'what.*files?.*here', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'list.*current.*directory', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'show.*directory.*content', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            # Current directory
            (r'where.*am.*i', 'cd' if self.shell_exec.is_windows else 'pwd'),
            (r'current.*directory', 'cd' if self.shell_exec.is_windows else 'pwd'),
            (r'show.*current.*path', 'cd' if self.shell_exec.is_windows else 'pwd'),
        ]
        
        for pattern, command in list_patterns:
            if re.search(pattern, prompt_lower):
                return command
        
        return None
    
    def process_prompt(self, prompt_text: str):
        """
        Processa um prompt e exibe a resposta
        
        Args:
            prompt_text: Texto do prompt
        """
        # FIRST: Check if it should be executed as a shell command directly
        # This should work even without a model selected
        command_to_execute = self._should_execute_as_command(prompt_text.strip())
        if self.auto_execute_shell and command_to_execute:
            console.print(f"\n[dim]Executing: {command_to_execute}[/dim]\n")
            with console.status(f"[dim]$ {command_to_execute}[/dim]", spinner="dots"):
                success, output = self.shell_exec.execute_command(command_to_execute)
            
            if success:
                if output.strip():
                    console.print(output)
                else:
                    console.print("[green]✓ Command executed[/green]")
            else:
                console.print(f"[red]❌ {output}[/red]")
                
                # *** NEW: Auto-recovery for directory not found errors ***
                if self.auto_recovery and self.auto_recovery.is_directory_not_found_error(output):
                    console.print("[blue]🔄 Initiating auto-recovery for directory error...[/blue]")
                    
                    # Get recovery commands
                    recovery_commands = self.auto_recovery.auto_recover_directory_error(command_to_execute, output)
                    
                    if recovery_commands:
                        console.print(f"[blue]📖 Executing {len(recovery_commands)} recovery commands...[/blue]")
                        
                        # Execute recovery commands and collect results
                        recovery_results = []
                        for cmd in recovery_commands:
                            console.print(f"[dim]$ {cmd}[/dim]")
                            try:
                                rec_success, rec_output = self.shell_exec.execute_command(cmd)
                                if rec_success and rec_output.strip():
                                    console.print(rec_output)
                                    recovery_results.append(rec_output)
                            except Exception as e:
                                console.print(f"[yellow]⚠️ Recovery command failed: {e}[/yellow]")
                        
                        # Suggest correct paths based on findings
                        if recovery_results:
                            failed_path = self.auto_recovery.extract_failed_path(command_to_execute, output)
                            suggestions = self.auto_recovery.suggest_correct_paths(recovery_results, failed_path)
                            
                            if suggestions:
                                console.print(f"[green]💡 Found similar directories:[/green]")
                                for i, suggestion in enumerate(suggestions, 1):
                                    console.print(f"  {i}. {suggestion}")
                                console.print(f"[dim]💡 Try: cd {suggestions[0]}[/dim]")
                            else:
                                console.print("[blue]📋 Directory structure mapped. Check the output above for available paths.[/blue]")
                        
                        return  # Skip normal AI error processing
                
                # Normal AI error fix for non-directory errors
                if self.selected_model:
                    console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                    error_prompt = f"The command '{command_to_execute}' failed with error: {output}. Please provide the correct command to fix this issue."
                    # Process the error through LLM but don't auto-execute the fix
                    temp_auto_execute = self.auto_execute_shell
                    self.auto_execute_shell = False
                    self.process_prompt(error_prompt)
                    self.auto_execute_shell = temp_auto_execute
            return
        
        # SECOND: Check if we have a model for LLM tasks
        if not self.selected_model:
            console.print("[red]No model selected. Use /models to select one.[/red]")
            return
        
        try:
            # *** NEW: ALWAYS read project structure first ***
            console.print("[dim]📁 Reading project structure for context...[/dim]")
            structure_info = self.auto_read_structure.read_current_structure()
            structure_context = self.auto_read_structure.format_structure_for_context(structure_info)
            
            # *** NEW: AUTOMATIC PROJECT MODE DETECTION ***
            console.print("[dim]🤖 Analyzing project context and user intent...[/dim]")
            mode_decision = self.project_mode_detector.make_mode_decision(prompt_text)
            
            # Add mode-specific instructions to the prompt
            mode_instructions = self._generate_mode_instructions(mode_decision)
            if mode_instructions:
                structure_context += "\n\n" + mode_instructions
                
            # Debug mode: show detection details
            if self.debug_mode:
                self._show_mode_detection_debug(mode_decision)
            else:
                # Show brief mode indication
                mode_emoji = "✏️" if mode_decision['mode'] == 'edit' else "🆕"
                console.print(f"[dim]{mode_emoji} Mode: {mode_decision['mode']} (confidence: {mode_decision['confidence']:.0f}%)[/dim]")
            
            # Step 1: Check if input is an error message and create specialized prompt
            error_info = self.prompt_enhancer.detect_error_type(prompt_text)
            if error_info:
                console.print(f"[yellow]🔍 Detected {error_info['type']} error - creating specialized fix prompt[/yellow]")
                enhanced_prompt = self.prompt_enhancer.create_error_fix_prompt(
                    prompt_text, 
                    error_info, 
                    self.shell_exec.get_current_directory()
                )
                # Inject structure context into error fix prompt
                enhanced_prompt = structure_context + "\n\n" + enhanced_prompt
            else:
                # Step 2: Better prompting - analyze and enhance user request
                working_prompt = prompt_text
                if self.better_prompting:
                    working_prompt = self.analyze_and_enhance_prompt(prompt_text)
                
                # Step 3: Apply regular prompt enhancements if enabled  
                if self.enhance_prompts:
                    enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                        working_prompt, 
                        self.shell_exec.get_current_directory(),
                        self.shell_exec.get_os_info()
                    )
                    # Inject structure context AFTER enhancement
                    enhanced_prompt = structure_context + "\n\n" + enhanced_prompt
                else:
                    # *** CRITICAL FIX: Even if enhancement is disabled, add basic tag instructions ***
                    # for prompts that suggest code/file creation or shell commands
                    needs_tag_instructions = self._prompt_needs_special_tags(working_prompt)
                    if needs_tag_instructions:
                        enhanced_prompt = working_prompt + self._get_basic_tag_instructions()
                        console.print("[dim]💡 Added basic tag instructions (enhancement disabled)[/dim]")
                    else:
                        enhanced_prompt = working_prompt
                    # Inject structure context even when enhancement is disabled
                    enhanced_prompt = structure_context + "\n\n" + enhanced_prompt
                
                # *** NEW FEATURE: Always suggest reading files first (unless file content already provided)
                # *** SIMPLE FIX: Force read-first for edit mode ***
                if mode_decision['mode'] == 'edit':
                    console.print("[blue]🔧 Edit mode detected - FORCING file reading first[/blue]")
                    enhanced_prompt, needs_read_first = self._add_read_first_instruction(enhanced_prompt, force_read=True)
                else:
                    enhanced_prompt, needs_read_first = self._add_read_first_instruction(enhanced_prompt)
            
            # ALWAYS track context regardless of enhancement settings
            if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                try:
                    self.prompt_enhancer.add_to_context_history("user", working_prompt)
                except Exception as e:
                    if self.debug_mode:
                        console.print(f"[dim]⚠️ Error adding user message to context: {e}[/dim]")
            
            # *** NEW LOGIC: Handle read-first flow ***
            if needs_read_first:
                console.print("[blue]📖 Read-first flow: Requesting file examination...[/blue]")
                
                # Step 1: Send prompt with read instruction and capture read response
                read_response = ""
                read_content = None
                try:
                    with console.status("[bold blue]📖 Waiting for read commands...", spinner="dots") as status:
                        chunk_count = 0
                        for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                            read_response += chunk
                            chunk_count += 1
                            
                            # Update status every 5 chunks
                            if chunk_count % 5 == 0:
                                status.update(f"[bold blue]📖 Analyzing response... ({chunk_count} chunks)", spinner="dots")
                            
                            # Check if we have a complete read tag
                            read_match = re.search(r'<read>(.*?)</read>', read_response, re.DOTALL)
                            if read_match:
                                status.update("[bold blue]📖 Read commands detected, executing...", spinner="dots3")
                                
                                # Execute read commands and get content
                                read_content = self.tag_processor.execute_read_tags_only(read_response)
                                break  # Exit the loop to end the status context
                    
                    # Step 2: Re-send ORIGINAL prompt with file content (outside status context)
                    if read_content is not None:
                        console.print(f"[green]📖 Read commands executed successfully[/green]")
                        self._send_original_with_file_content(
                            prompt_text,  # Original user prompt  
                            working_prompt,  # Enhanced prompt without read instruction
                            read_content
                        )
                        return
                            
                except KeyboardInterrupt:
                    console.print(f"\n[yellow]⚠️ Read-first generation interrupted by user[/yellow]")
                    return
                    
                # If we get here, no read tag was found - show warning and continue with normal processing
                console.print(f"\n[yellow]⚠️ No read tag found in read-first response, proceeding with normal flow[/yellow]")
                # Use the response we got as the final response
                if read_response.strip():
                    console.print("\n[bold cyan]Response:[/bold cyan]\n")
                    self._display_formatted_response(read_response)
                    self._process_special_tags(read_response, prompt_text, skip_read_tags=True)
                    return
            
            # Normal flow: Generate response without read-first requirement
            full_response = ""
            code_count = 0
            line_count = 0
            last_line = ""
            
            # Gera resposta com status dinâmico mostrando sempre a última linha
            try:
                with console.status("[bold green]🤔 Thinking...", spinner="dots") as status:
                    for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                        full_response += chunk
                        line_count += chunk.count('\n')
                        
                        # *** FALLBACK: Check for complete <read> tags in normal flow ***
                        read_match = re.search(r'<read>(.*?)</read>', full_response, re.DOTALL | re.IGNORECASE)
                        if read_match:
                            console.print(f"\n[bold blue]📖 Read tag detected - stopping generation and executing reads...[/bold blue]")
                            # Stop the generation loop immediately
                            break
                        
                        # Extrai a última linha completa para mostrar no status
                        lines = full_response.split('\n')
                        if len(lines) > 1:
                            # Pega a penúltima linha se ela for mais substancial
                            last_line = lines[-2].strip() if lines[-2].strip() else lines[-1].strip()
                        else:
                            last_line = lines[0].strip()
                        
                        # Limita o tamanho da linha mostrada no status
                        if len(last_line) > 80:
                            display_line = last_line[:77] + "..."
                        else:
                            display_line = last_line
                        
                        # Atualiza status baseado no conteúdo com a última linha
                        base_status = ""
                        spinner_type = "dots"
                        
                        if '```' in chunk:
                            code_count += 1
                            if code_count % 2 == 1:
                                base_status = "[bold yellow]💻 Writing code"
                                spinner_type = "dots2"
                            else:
                                base_status = "[bold green]📝 Analyzing"
                        elif len(full_response) > 100:
                            # Determina status baseado no conteúdo
                            if 'code' in full_response.lower() or 'function' in full_response or 'def ' in full_response:
                                base_status = "[bold yellow]💻 Writing code"
                                spinner_type = "dots2"
                            elif 'error' in full_response.lower() or 'bug' in full_response.lower():
                                base_status = "[bold red]🔍 Analyzing error"
                                spinner_type = "dots3"
                            elif 'test' in full_response.lower():
                                base_status = "[bold blue]🧪 Preparing tests"
                                spinner_type = "dots"
                            elif '<read>' in full_response.lower():
                                base_status = "[bold blue]📖 Preparing to read files"
                                spinner_type = "dots3"
                            elif '<actions>' in full_response.lower():
                                base_status = "[bold cyan]⚡ Preparing commands"
                                spinner_type = "dots2"
                            elif '<code' in full_response.lower():
                                base_status = "[bold yellow]📄 Creating files"
                                spinner_type = "dots2"
                            else:
                                base_status = "[bold green]🤔 Processing"
                        else:
                            base_status = "[bold green]🤔 Thinking"
                        
                        # Monta status completo com a última linha
                        if display_line:
                            status_text = f"{base_status}...\n[dim]💬 {display_line}[/dim]"
                        else:
                            status_text = f"{base_status}..."
                        
                        status.update(status_text, spinner=spinner_type)
            except KeyboardInterrupt:
                console.print("\n[yellow]💡 Response generation interrupted by user[/yellow]")
                # Use any partial response received so far
                if full_response.strip():
                    console.print("[dim]Processing partial response...[/dim]")
                else:
                    console.print("[dim]No response generated[/dim]")
                    return
            
            # *** FALLBACK: Check if generation was stopped due to <read> tag ***
            read_match = re.search(r'<read>(.*?)</read>', full_response, re.DOTALL | re.IGNORECASE)
            if read_match:
                # Display partial response first
                console.print("\n[bold cyan]Partial Response:[/bold cyan]")
                response_before_read = full_response.split('<read>')[0].strip()
                if response_before_read:
                    self._display_formatted_response(response_before_read)
                
                # Process the read tags immediately
                console.print(f"\n[bold blue]📖 Processing read tags and restarting generation...[/bold blue]")
                read_content = self.tag_processor.execute_read_tags_only(full_response)
                
                if read_content:
                    # Restart generation with file content injected
                    self._restart_generation_with_content(prompt_text, enhanced_prompt, read_content, response_before_read)
                    return
            
            # Exibe resposta completa formatada
            console.print("\n[bold cyan]Assistente:[/bold cyan]\n")
            
            # Debug: Mostra se há tags especiais na resposta
            has_actions = '<actions>' in full_response.lower()
            has_read = '<read>' in full_response.lower()
            has_code = '<code' in full_response.lower()
            has_traditional_code = '```' in full_response
            
            if not (has_actions or has_read or has_code or has_traditional_code):
                # Check if the user's prompt expected actions but model didn't provide tags
                expected_tags = self._prompt_needs_special_tags(prompt_text)
                if expected_tags:
                    console.print(f"[yellow]⚠️  Model response missing expected action tags[/yellow]")
                    console.print(f"[dim]💡 The model should have used <actions>, <read>, or <code> tags[/dim]")
                    if not self.enhance_prompts:
                        console.print(f"[dim]💡 Try enabling enhancements with /enhance for better tag compliance[/dim]")
                
                # Debug: mostra parte da resposta para diagnóstico
                if self.debug_mode:
                    console.print(f"[dim]🔍 Response without code/actions detected.[/dim]")
                    console.print(f"[dim]📝 Resposta completa do modelo:[/dim]")
                    console.print(Panel(full_response, title="[dim]DEBUG - Resposta Raw[/dim]", border_style="dim"))
                else:
                    response_preview = full_response[:200] + "..." if len(full_response) > 200 else full_response
                    console.print(f"[dim]🔍 Response without code/actions detected.[/dim]")
                    console.print(f"[dim]📝 Preview da resposta: {response_preview}[/dim]")
                    console.print(f"[dim]💡 Use /debug para ver resposta completa[/dim]\n")
            
            # ALWAYS add assistant response to context at the end
            if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                try:
                    self.prompt_enhancer.add_to_context_history("assistant", full_response)
                except Exception as e:
                    if self.debug_mode:
                        console.print(f"[dim]⚠️ Error adding assistant message to context: {e}[/dim]")
            
            # Processa tags especiais e blocos de código PRIMEIRO
            special_processed = False
            
            # Processa tags especiais
            if has_actions or has_read or has_code:
                tags_processed = self._process_special_tags(full_response, prompt_text)
                if tags_processed:
                    special_processed = True
            
            # Detecta e processa blocos de código tradicionais (para compatibilidade)
            if has_traditional_code:
                code_blocks = re.findall(r'```(\w*)\n(.*?)```', full_response, re.DOTALL)
                if code_blocks:
                    self._process_code_blocks(code_blocks, prompt_text)
                    special_processed = True
            
            # Processa e exibe a resposta com formatação (texto restante)
            self._display_formatted_response(full_response)
            
            # Se não houve processamento especial, avisa o usuário
            if not special_processed and not full_response.strip():
                console.print("[yellow]⚠️  Resposta vazia recebida do modelo[/yellow]")
            elif not special_processed and full_response.strip():
                # Check if this was a prompt that should have generated actions
                expected_tags = self._prompt_needs_special_tags(prompt_text)
                if expected_tags:
                    console.print("[yellow]💡 The model provided text instead of actionable code/commands[/yellow]")
                    console.print("[dim]Tip: The model should have used <actions>, <code>, or <read> tags for automatic execution[/dim]")
                    if not self.enhance_prompts:
                        console.print("[dim]Try enabling enhancements with '/enhance' for better results[/dim]")
                else:
                    console.print("[dim]💡 Tip: Use commands like 'create a Python file' or 'install flask' for automatic actions[/dim]")
            
            # Verifica se estamos em modo enhancement e se o AI usou as tags corretamente
            if hasattr(self, '_enhancement_mode') and self._enhancement_mode:
                if not has_code:
                    console.print("\n[bold red]⚠️  ERROR: The AI did not follow the correct format![/bold red]")
                    console.print("[yellow]The AI should have used <code filename=\"...\"> tags to edit the files.[/yellow]")
                    console.print("[yellow]Try again with a more specific description or use a different model.[/yellow]")
                    console.print("\n[dim]💡 Example: /enhance_code transform into professional SAAS landing page[/dim]")
            
            # Automatically save interaction
            try:
                self.auto_save_session({
                    'prompt': prompt_text,
                    'enhanced_prompt': enhanced_prompt if enhanced_prompt != prompt_text else None,
                    'response': full_response,
                    'model': self.selected_model,
                    'directory': str(self.shell_exec.get_current_directory()),
                    'had_special_processing': special_processed
                })
            except Exception as e:
                if self.debug_mode:
                    console.print(f"[dim]⚠️ Error auto-saving session: {e}[/dim]")
            
        except OllamaAPIError as e:
            console.print(f"[red]Error generating response: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Response interrupted.[/yellow]")
    
    def _prompt_needs_special_tags(self, prompt: str) -> bool:
        """
        Detecta se um prompt precisa de instruções de tags especiais
        
        Args:
            prompt: Prompt do usuário
            
        Returns:
            True se o prompt indica criação de código/arquivos ou comandos
        """
        prompt_lower = prompt.lower()
        
        # Keywords que indicam necessidade de tags especiais
        code_creation_keywords = [
            'create', 'make', 'write', 'build', 'implement', 'generate',
            'file', 'script', 'code', 'function', 'class', 'app',
            'project', 'website', 'api', 'database', 'html', 'css', 'js',
            'python', 'flask', 'django', 'react', 'node'
        ]
        
        command_keywords = [
            'install', 'run', 'execute', 'setup', 'configure', 'mkdir',
            'cd', 'pip', 'npm', 'git', 'docker', 'start', 'stop'
        ]
        
        return (
            any(keyword in prompt_lower for keyword in code_creation_keywords) or
            any(keyword in prompt_lower for keyword in command_keywords) or
            'app.py' in prompt_lower or
            'requirements.txt' in prompt_lower or
            'package.json' in prompt_lower
        )
    
    def _get_basic_tag_instructions(self) -> str:
        """
        Retorna instruções básicas sobre tags especiais
        
        Returns:
            String com instruções básicas sobre tags
        """
        return """

[MANDATORY TAGS FOR ACTIONS]

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

CRITICAL RULES:
- ALWAYS use <actions> for commands (mkdir, pip, npm, git, etc.)
- ALWAYS use <code edit filename="..."> for editing existing files
- ALWAYS use <code create filename="..."> for creating new files
- ALWAYS use <read> for examining files
- NEVER use ``` blocks for files that should be created/edited
- NEVER just describe actions - use the tags!
- The old <code filename="..."> format is deprecated - always specify edit or create
"""
    
    def _add_read_first_instruction(self, prompt: str, force_read: bool = False) -> tuple[str, bool]:
        """
        Adds instruction to always start with <read> except when there's already file context
        """
        return self.tag_processor.add_read_first_instruction(prompt, self.read_levels_manager, force_read)
    
    def _get_suggested_read_commands(self, prompt: str) -> str:
        """
        Sugere comandos de leitura baseados no contexto do prompt usando sistema de níveis
        """
        return self.read_levels_manager.get_suggested_read_commands(prompt)
    
    def _determine_read_level(self, prompt_lower: str) -> int:
        """
        Determina qual nível de read é necessário baseado no contexto
        """
        return self.read_levels_manager.determine_read_level(prompt_lower)
    
    def _send_original_with_file_content(self, original_prompt: str, working_prompt: str, read_content: list):
        """
        Re-envia o prompt original (sem instrução read) mas com conteúdo dos arquivos injetado
        """
        full_response = self.tag_processor.send_original_with_file_content(
            original_prompt, working_prompt, read_content, self.api, self.selected_model
        )
        
        if full_response:
            # Verifica se a resposta contém implementação real (tags de ação)
            has_implementation = self._check_if_response_has_implementation(full_response)
            
            if not has_implementation:
                console.print("\n[yellow]⚠️  AI response lacks implementation. Requesting explicit implementation...[/yellow]")
                # Força uma nova tentativa com instruções mais explícitas
                full_response = self._force_implementation_request(original_prompt, working_prompt, read_content, full_response)
            
            # Exibe a resposta final
            console.print("\n[bold cyan]Response:[/bold cyan]\n")
            
            # Processa resposta para tags especiais (skip read tags to avoid infinite loop)
            implementation_found = self._process_special_tags(full_response, original_prompt, skip_read_tags=True)
            
            # Se ainda não há implementação, avisa o usuário
            if not implementation_found:
                console.print("\n[red]⚠️  Warning: The AI provided explanations but no actual implementation.[/red]")
                console.print("[yellow]💡 Try being more specific about what files/code you want created or modified.[/yellow]")
            
            # Exibe a resposta formatada
            self._display_formatted_response(full_response)
    
    def _check_if_response_has_implementation(self, response: str) -> bool:
        """
        Verifica se a resposta contém implementação real (tags de ação)
        
        Args:
            response: Resposta do AI
            
        Returns:
            True se contém implementação, False se apenas texto explicativo
        """
        # Verifica por tags de implementação
        implementation_patterns = [
            r'<code\s+(edit|create)\s+filename=',  # Novas tags específicas
            r'<code\s+filename=',  # Tag tradicional
            r'<actions>.*</actions>',  # Comandos shell
        ]
        
        for pattern in implementation_patterns:
            if re.search(pattern, response, re.DOTALL | re.IGNORECASE):
                return True
        
        return False
    
    def _force_implementation_request(self, original_prompt: str, working_prompt: str, read_content: list, previous_response: str) -> str:
        """
        Força uma nova tentativa quando o AI não implementou a solução
        
        Args:
            original_prompt: Prompt original do usuário
            working_prompt: Prompt melhorado
            read_content: Conteúdo dos arquivos lidos
            previous_response: Resposta anterior que não tinha implementação
            
        Returns:
            Nova resposta do AI com implementação forçada
        """
        console.print("[blue]🔄 Forcing implementation with more explicit instructions...[/blue]")
        
        # Cria um prompt muito mais direto e específico
        file_content_text = "\n\n".join(read_content) if read_content else ""
        
        force_prompt = f"""PREVIOUS RESPONSE REJECTED - YOU ONLY PROVIDED EXPLANATIONS
The user requested: {original_prompt}

FILES AVAILABLE:
{file_content_text}

YOUR PREVIOUS RESPONSE (REJECTED):
{previous_response[:500]}{'...' if len(previous_response) > 500 else ''}

MANDATORY INSTRUCTIONS - NO EXCEPTIONS:
1. You MUST provide concrete implementation using the exact tags below
2. For existing files: <code edit filename="filename.ext">COMPLETE_CODE_HERE</code>
3. For new files: <code create filename="filename.ext">COMPLETE_CODE_HERE</code>
4. For shell commands: <actions>command_here</actions>
5. NO explanations without implementation
6. NO "here's how you could do it" - ACTUALLY DO IT
7. Provide complete, working code that implements: {original_prompt}

IMPLEMENT NOW - NO MORE EXPLANATIONS:"""
        
        try:
            with console.status("[bold red]🔄 Forcing implementation...", spinner="dots") as status:
                forced_response = ""
                for chunk in self.api.generate(self.selected_model, force_prompt):
                    forced_response += chunk
                
                return forced_response
        except Exception as e:
            console.print(f"[red]❌ Error forcing implementation: {e}[/red]")
            return previous_response  # Retorna resposta original se falhar
    
    def load_previous_session(self):
        """
        Loads previous session if it exists and asks user if they want to continue
        """
        previous_session = self.session_manager.load_session()
        if not previous_session:
            return False
        
        # Show previous session summary
        summary = self.session_manager.get_session_summary()
        if summary:
            console.print(summary)
            
            # Ask if user wants to continue session
            from rich.prompt import Confirm
            continue_session = Confirm.ask("\n[cyan]Do you want to continue the previous session?[/cyan]", default=True)
            
            if continue_session:
                # Restore settings
                self.selected_model = previous_session.get('model_name')
                self.auto_execute_shell = previous_session.get('shell_settings', {}).get('auto_execute_shell', True)
                self.enhance_prompts = previous_session.get('shell_settings', {}).get('enhance_prompts', True)
                self.better_prompting = previous_session.get('shell_settings', {}).get('better_prompting', True)
                
                # Verify model is available
                if self.selected_model:
                    try:
                        available_models = [model['name'] for model in self.api.list_models()]
                        if self.selected_model not in available_models:
                            console.print(f"[yellow]⚠️ Previously selected model '{self.selected_model}' is not available[/yellow]")
                            console.print(f"[yellow]Available models: {', '.join(available_models[:3])}{'...' if len(available_models) > 3 else ''}[/yellow]")
                            self.selected_model = None
                    except Exception as e:
                        if self.debug_mode:
                            console.print(f"[yellow]Could not verify model availability: {e}[/yellow]")
                        self.selected_model = None
                
                # Restore context if available
                if hasattr(self.prompt_enhancer, 'context_history') and previous_session.get('context_history'):
                    # Validate context history format before restoring
                    context_history = previous_session['context_history']
                    valid_messages = []
                    for msg in context_history:
                        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                            valid_messages.append(msg)
                        elif self.debug_mode:
                            console.print(f"[dim]⚠️ Skipping invalid message in context: {msg}[/dim]")
                    
                    self.prompt_enhancer.context_history = valid_messages
                    console.print(f"[green]✓ Context restored with {len(valid_messages)} messages[/green]")
                
                # Try to navigate to previous directory
                previous_dir = previous_session.get('working_directory')
                if previous_dir and Path(previous_dir).exists():
                    try:
                        rel_path = os.path.relpath(previous_dir, self.user_initial_dir)
                        if rel_path != ".":
                            success, _ = self.shell_exec.execute_command(f'cd "{rel_path}"')
                            if success:
                                console.print(f"[green]✓ Directory restored: {previous_dir}[/green]")
                    except Exception:
                        pass
                
                console.print("[green]✓ Previous session loaded successfully![/green]\n")
                return True
            else:
                # Archive previous session
                self.session_manager.clear_session()
                console.print("[yellow]📦 Previous session archived[/yellow]\n")
        
        return False
    
    def auto_save_session(self, last_interaction=None):
        """
        Automatically saves current session state
        
        Args:
            last_interaction: Last interaction (prompt + response)
        """
        if not self.selected_model:
            return
            
        try:
            context_history = []
            if hasattr(self.prompt_enhancer, 'context_history'):
                # Get context history and ensure it's valid
                raw_context = getattr(self.prompt_enhancer, 'context_history', [])
                # Filter out invalid entries that don't have proper message format
                context_history = [msg for msg in raw_context if isinstance(msg, dict) and 'role' in msg and 'content' in msg]
            
            self.session_manager.save_session(
                model_name=self.selected_model,
                context_history=context_history,
                working_directory=str(self.shell_exec.get_current_directory()),
                shell_settings={
                    'auto_execute_shell': self.auto_execute_shell,
                    'enhance_prompts': self.enhance_prompts,
                    'better_prompting': self.better_prompting
                },
                last_interaction=last_interaction
            )
        except Exception as e:
            # Silent failure to not interrupt flow
            if self.debug_mode:
                console.print(f"[dim]⚠️ Error auto-saving session: {e}[/dim]")

    def run(self):
        """Executa a CLI principal"""
        # Welcome banner
        os_info = self.shell_exec.get_os_info()
        dir_display = str(self.user_initial_dir)
        if len(dir_display) > 30:
            dir_display = "..." + dir_display[-27:]
        
        # Create beautiful ASCII art logo in purple
        ascii_logo = """[bold magenta]
 _  _   __   __ _  ____   __   __       ___  __    __  
( \/ ) / _\ (  ( \(    \ / _\ (  )___  / __)(  )  (  ) 
 )  ( /    \/    / ) D (/    \ )((___)( (__ / (_/\ )(  
(_/\_)\_/\_/\_)__)(____/\_/\_/(__)     \___)\____/(__) [/bold magenta]"""
        
        # Dynamic status indicators with colors
        shell_status = "[green]ENABLED[/green]" if self.auto_execute_shell else "[red]DISABLED[/red]"
        prompt_status = "[green]ENABLED[/green]" if self.enhance_prompts else "[red]DISABLED[/red]"
        
        # Get context status and better prompting status
        context_status = ""
        if hasattr(self.prompt_enhancer, 'get_context_status'):
            context_status = f"\n[bold blue]🧠 Context:[/bold blue] {self.prompt_enhancer.get_context_status()}"
        
        better_status = f"\n[bold blue]🎯 Better Prompting:[/bold blue] {'[green]ENABLED[/green]' if self.better_prompting else '[red]DISABLED[/red]'}"
        
        # Create the complete banner
        banner = f"""{ascii_logo}

[dim cyan]                    AI Assistant with OLLAMA[/dim cyan]

[bold yellow]⚡ Automatic shell:[/bold yellow] {shell_status}
[bold yellow]🎯 Enhanced prompts:[/bold yellow] {prompt_status}{better_status}{context_status}

[bold blue]💻 System:[/bold blue] [white]{os_info}[/white]
[bold blue]📁 Directory:[/bold blue] [white]{dir_display}[/white]
        """
        console.print(Panel(banner, style="bright_white", border_style="bright_blue", padding=(1, 2)))
        
        # Test connection
        console.print("[dim]Connecting to OLLAMA API...[/dim]")
        if not self.api.test_connection():
            console.print(f"[red]❌ Could not connect to OLLAMA API at {self.api.endpoint}[/red]")
            console.print("[yellow]Make sure OLLAMA is running.[/yellow]")
            console.print("[dim]Example: ollama serve[/dim]")
            return
        
        console.print("[green]✓ Connected to OLLAMA API[/green]\n")
        
        # Try to load previous session
        session_loaded = self.load_previous_session()
        
        # Select model (if not loaded from previous session)
        if not self.selected_model:
            self.selected_model = self.list_models()
            if not self.selected_model:
                console.print("[yellow]No model selected. Exiting...[/yellow]")
                return
                
        # Initialize TagProcessor and AutoRecovery with AI decision system after model selection
        if not self.tag_processor:
            self.tag_processor = TagProcessor(
                self.shell_exec, 
                self.file_ops, 
                self.file_context_manager,
                self.api,
                self.selected_model
            )
            
        if not self.auto_recovery:
            self.auto_recovery = AutoRecovery(
                self.shell_exec,
                self.tag_processor.ai_read_decision if self.tag_processor else None
            )
        elif session_loaded:
            # If loaded from session, confirm model is still available
            try:
                models = self.api.list_models()
                available_models = [m['name'] for m in models]
                if self.selected_model not in available_models:
                    console.print(f"[yellow]⚠️  Model from previous session '{self.selected_model}' is no longer available[/yellow]")
                    console.print("[cyan]Selecting new model...[/cyan]")
                    self.selected_model = self.list_models()
                    if not self.selected_model:
                        console.print("[yellow]No model selected. Exiting...[/yellow]")
                        return
                        
                else:
                    console.print(f"[green]✓ Using model from session: {self.selected_model}[/green]")
            except Exception:
                # If verification fails, allow continuing with session model
                pass
                
        # Re-initialize TagProcessor and AutoRecovery if model changed
        if not self.tag_processor or session_loaded:
            self.tag_processor = TagProcessor(
                self.shell_exec, 
                self.file_ops, 
                self.file_context_manager,
                self.api,
                self.selected_model
            )
            
            self.auto_recovery = AutoRecovery(
                self.shell_exec,
                self.tag_processor.ai_read_decision if self.tag_processor else None
            )
        
        # Prepare autocompletion
        # Create custom completer that handles both commands and file paths
        custom_completer = XandAICompleter(self.commands, self.shell_exec)
        
        # Loop principal
        console.print("\n[dim]Type /help to see available commands.[/dim]\n")
        
        try:
            while True:
                try:
                    # Build dynamic prompt with model name and context percentage
                    context_percentage = ""
                    if self.selected_model and hasattr(self.prompt_enhancer, 'get_context_usage_percentage'):
                        percentage = self.prompt_enhancer.get_context_usage_percentage()
                        context_percentage = f" ({percentage:.0f}% context)"
                    
                    model_name = self.selected_model or "No model"
                    prompt_text = f"[{model_name}{context_percentage}] > "
                    
                    # Prompt com histórico e autocompletar
                    user_input = prompt(
                        prompt_text,
                        history=FileHistory(str(self.history_file)),
                        auto_suggest=AutoSuggestFromHistory(),
                        completer=custom_completer,
                        multiline=False,
                        complete_while_typing=True
                    )
                    
                    if not user_input.strip():
                        continue
                    
                    # Processa comandos
                    if user_input.startswith('/'):
                        parts = user_input.split(maxsplit=1)
                        command = parts[0].lower()
                        args = parts[1] if len(parts) > 1 else ""
                        
                        if command in self.commands:
                            if command in ['/file', '/task', '/enhance_code']:
                                self.commands[command](args)
                            else:
                                self.commands[command]()
                        else:
                            console.print(f"[red]Unknown command: {command}[/red]")
                            console.print("[dim]Type /help to see available commands.[/dim]")
                    else:
                        # Verifica se é um comando shell
                        if self.auto_execute_shell and self.shell_exec.is_shell_command(user_input):
                            # Mostra apenas um indicador sutil de execução
                            with console.status(f"[dim]$ {user_input}[/dim]", spinner="dots"):
                                success, output = self.shell_exec.execute_command(user_input)
                            
                            if success:
                                if output.strip():
                                    console.print(output)
                                # Don't show success message if no output
                            else:
                                console.print(f"[red]❌ {output}[/red]")
                                # If command failed, send error back to LLM for automatic fix
                                console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                                error_prompt = f"The command '{user_input}' failed with error: {output}. Please provide the correct command to fix this issue."
                                self.process_prompt(error_prompt)
                        else:
                            # Processa prompt normal
                            self.process_prompt(user_input)
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Use /exit to quit.[/yellow]")
                except EOFError:
                    self.exit_cli()
                    
        except Exception as e:
            console.print(f"\n[red]Fatal error: {str(e)}[/red]")
            if self.debug_mode:
                import traceback
                console.print(f"[dim]Debug traceback:[/dim]")
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            console.print("[dim]Exiting...[/dim]")
    
    def context_command_new(self, args: List[str] = None):
        """
        Gerencia contexto de arquivos e estrutura do projeto
        
        Subcomandos:
        - status: Mostra status atual do contexto
        - show: Mostra estrutura completa do projeto
        - settings: Mostra configurações atuais
        - clear: Limpa cache de estrutura de arquivos
        - config: Configura opções de contexto
        """
        if not args:
            args = []
        
        if len(args) == 0 or args[0] == 'status':
            # Mostra status do contexto
            if hasattr(self.prompt_enhancer, 'get_context_status'):
                status = self.prompt_enhancer.get_context_status()
                console.print(f"[cyan]📊 Context Usage: {status}[/cyan]")
                
                # Mostra também settings de arquivo
                if hasattr(self.prompt_enhancer, 'get_current_settings'):
                    settings = self.prompt_enhancer.get_current_settings()
                    console.print(f"[cyan]📁 File Context: {'Full' if settings['full_context_mode'] else 'Limited'} mode[/cyan]")
                    console.print(f"[dim]   Max files: {settings['max_files_threshold']}, Cache: {settings['cache_size']} entries[/dim]")
            else:
                console.print("[yellow]Context status not available[/yellow]")
        
        elif args[0] == 'show':
            # Mostra estrutura completa forçada
            try:
                current_dir = self.shell_exec.get_current_directory()
                if hasattr(self.prompt_enhancer, 'get_full_project_context'):
                    full_context = self.prompt_enhancer.get_full_project_context(current_dir)
                    console.print("[bold green]🌳 Complete Project Structure:[/bold green]")
                    console.print(full_context)
                else:
                    console.print("[yellow]Full project context not available[/yellow]")
            except Exception as e:
                console.print(f"[red]Error generating project context: {e}[/red]")
        
        elif args[0] == 'settings':
            # Mostra configurações atuais
            if hasattr(self.prompt_enhancer, 'get_current_settings'):
                settings = self.prompt_enhancer.get_current_settings()
                
                table = Table(title="File Context Settings")
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Full Context Mode", str(settings['full_context_mode']))
                table.add_row("Max Files Threshold", str(settings['max_files_threshold']))
                table.add_row("Max Depth", str(settings['max_depth_default']))
                table.add_row("Cache Expiry (seconds)", str(settings['cache_expiry_time']))
                table.add_row("Show File Sizes", str(settings['show_file_sizes']))
                table.add_row("Cache Size", str(settings['cache_size']))
                table.add_row("Custom Ignore Dirs", str(len(settings['custom_ignore_dirs'])))
                table.add_row("Custom Include Ext", str(len(settings['custom_include_extensions'])))
                table.add_row("Custom Exclude Ext", str(len(settings['custom_exclude_extensions'])))
                
                console.print(table)
            else:
                console.print("[yellow]Settings not available[/yellow]")
        
        elif args[0] == 'clear':
            # Limpa cache
            if hasattr(self.prompt_enhancer, 'clear_cache'):
                self.prompt_enhancer.clear_cache()
            else:
                console.print("[yellow]Cache clearing not available[/yellow]")
        
        elif args[0] == 'config':
            # Configura opções
            if len(args) < 2:
                console.print("[yellow]Usage: /context config <option> <value>[/yellow]")
                console.print("[dim]Options: full_context, max_files, max_depth, cache_expiry[/dim]")
                return
            
            option = args[1]
            
            if len(args) < 3:
                if hasattr(self.prompt_enhancer, 'get_current_settings'):
                    settings = self.prompt_enhancer.get_current_settings()
                    if option == 'full_context':
                        console.print(f"[yellow]Current {option}: {settings['full_context_mode']}[/yellow]")
                    elif option in settings:
                        console.print(f"[yellow]Current {option}: {settings[option]}[/yellow]")
                    else:
                        console.print(f"[red]Unknown option: {option}[/red]")
                return
            
            value = args[2]
            
            if hasattr(self.prompt_enhancer, 'configure_file_context'):
                try:
                    if option == 'full_context':
                        bool_value = value.lower() in ['true', '1', 'yes', 'on']
                        self.prompt_enhancer.configure_file_context(full_context=bool_value)
                    elif option == 'max_files':
                        self.prompt_enhancer.configure_file_context(max_files_threshold=int(value))
                    elif option == 'max_depth':
                        depth_value = None if value.lower() in ['none', 'null', 'unlimited'] else int(value)
                        self.prompt_enhancer.configure_file_context(max_depth=depth_value)
                    elif option == 'cache_expiry':
                        self.prompt_enhancer.configure_file_context(cache_expiry=int(value))
                    else:
                        console.print(f"[red]Unknown option: {option}[/red]")
                except ValueError as e:
                    console.print(f"[red]Invalid value for {option}: {value} ({e})[/red]")
            else:
                console.print("[yellow]Configuration not available[/yellow]")
        
        else:
            console.print(f"[red]Unknown context command: {args[0]}[/red]")
            console.print("[yellow]Available commands: status, show, settings, clear, config[/yellow]")
    
    def _generate_mode_instructions(self, mode_decision: Dict[str, Any]) -> str:
        """
        Gera instruções específicas baseadas no modo detectado (edit vs create)
        
        Args:
            mode_decision: Resultado da detecção automática de modo
            
        Returns:
            String com instruções específicas para o modo
        """
        mode = mode_decision['mode']
        confidence = mode_decision['confidence']
        project_info = mode_decision['project_info']
        
        if mode == 'edit' and confidence > 30:
            instructions = [
                "\n## EDIT MODE DETECTED",
                "🚨 CRITICAL: The user wants to UPDATE/MODIFY an existing project, NOT create a new one!",
                "",
                "**PRESERVATION-FIRST Edit Mode Instructions:**",
                "- ALWAYS read existing files first using <read> tags",
                "- PRESERVE ALL existing code: functions, endpoints, classes, variables, imports",
                "- NEVER delete or remove existing functionality unless explicitly requested",
                "- Make ONLY the specific changes requested - keep everything else identical",
                "- When editing files, provide the COMPLETE file including all existing code",
                "- Use <code edit filename=\"...\"> for modifying existing files (FULL file content required)",
                "- Use <code create filename=\"...\"> ONLY for completely new files",
                "- Mark new additions with comments like // NEW: or // ADDED: for clarity",
                "- Maintain consistency with existing patterns and conventions",
                "- If you find config files (package.json, requirements.txt), UPDATE instead of creating new ones",
                "",
                "**ENDPOINT/API PRESERVATION:**",
                "- Keep ALL existing API endpoints, routes, and handlers",
                "- When adding new endpoints, integrate them without affecting existing ones",
                "- Preserve all existing middleware, error handlers, and utilities",
                "- Maintain existing database schemas, models, and connections",
                ""
            ]
            
            # Add information about detected project types
            if project_info['types']:
                instructions.append("**Detected Project(s):**")
                for proj_type in project_info['types'][:3]:  # Top 3
                    instructions.append(f"- {proj_type['type']} (confidence: {proj_type['confidence']}%)")
                    if proj_type['indicators']:
                        instructions.append(f"  Indicators: {', '.join(proj_type['indicators'][:5])}")
                instructions.append("")
            
            instructions.extend([
                "**NEVER:**",
                "- Delete or remove existing endpoints, functions, or features",
                "- Create new projects or structures from scratch when editing",
                "- Overwrite files without preserving existing functionality",
                "- Ignore or remove existing API routes, handlers, or middleware",
                "- Remove existing imports, dependencies, or configurations",
                "- Provide partial code that excludes existing functionality",
                "- Drastically change architecture without understanding current context",
                "- Provide only explanations - ALWAYS implement with real code",
                "- Stop without providing the complete requested implementation"
            ])
            
        elif mode == 'create' and confidence > 30:
            instructions = [
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
                "- ALWAYS provide complete implementation, not just explanations",
                "- NEVER stop without creating the requested files and code",
                ""
            ]
            
            # If there's an existing project but intention is to create
            if project_info['has_project']:
                instructions.extend([
                    "**ATTENTION:** Existing project detected, but user wants to create something new.",
                    "- Create in subdirectory or use unique names to avoid conflicts",
                    "- Consider integration with existing project if relevant",
                    ""
                ])
        else:
            # Ambiguous mode or low confidence
            instructions = [
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
        
        return "\n".join(instructions)
    
    def _show_mode_detection_debug(self, mode_decision: Dict[str, Any]) -> None:
        """
        Shows detailed mode detection information for debugging
        
        Args:
            mode_decision: Result from automatic mode detection
        """
        console.print("\n[bold blue]🔍 DEBUG: Automatic Mode Detection[/bold blue]")
        
        # General information
        mode = mode_decision['mode']
        confidence = mode_decision['confidence']
        console.print(f"[green]📋 Final Decision: {mode.upper()} (confidence: {confidence:.1f}%)[/green]")
        
        # Existing project
        project_info = mode_decision['project_info']
        console.print(f"\n[cyan]📁 Project Analysis:[/cyan]")
        console.print(f"  • Project detected: {project_info['has_project']}")
        console.print(f"  • Confidence: {project_info['confidence']}%")
        console.print(f"  • Directory: {project_info['directory']}")
        
        if project_info['types']:
            console.print("  • Detected types:")
            for proj_type in project_info['types'][:3]:
                console.print(f"    - {proj_type['type']} ({proj_type['confidence']}%)")
                console.print(f"      Indicators: {', '.join(proj_type['indicators'])}")
        
        # User intention
        intent_info = mode_decision['intent_info']
        console.print(f"\n[yellow]🎯 Intent Analysis:[/yellow]")
        console.print(f"  • Intent: {intent_info['intent']}")
        console.print(f"  • Confidence: {intent_info['confidence']}%")
        console.print(f"  • Edit Score: {intent_info['edit_score']}")
        console.print(f"  • Create Score: {intent_info['create_score']}")
        
        if intent_info['edit_keywords']:
            console.print(f"  • Edit keywords: {', '.join(intent_info['edit_keywords'][:5])}")
        
        if intent_info['create_keywords']:
            console.print(f"  • Create keywords: {', '.join(intent_info['create_keywords'][:5])}")
        
        # Reasoning
        console.print(f"\n[magenta]🧠 Reasoning:[/magenta]")
        for i, reason in enumerate(mode_decision['reasoning'], 1):
            console.print(f"  {i}. {reason}")
        
        console.print("")  # Empty line
