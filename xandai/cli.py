"""
Interface CLI principal do XandAI
"""

import sys
import re
from typing import Optional, List, Dict, Any
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

console = Console()


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
        self.task_manager = TaskManager()
        self.git_manager = GitManager(self.user_initial_dir)
        self.selected_model = None
        self.history_file = Path.home() / ".xandai_history"
        self.auto_execute_shell = True  # Flag for automatic command execution
        self.enhance_prompts = True     # Flag para melhorar prompts automaticamente
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
            '/context': self.show_context_status,
            '/debug': self.toggle_debug_mode,
            '/better': self.toggle_better_prompting
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
        status = "ativada" if self.auto_execute_shell else "desativada"
        console.print(f"[green]✓ Automatic shell command execution {status}[/green]")
    
    def toggle_prompt_enhancement(self):
        """Toggles automatic prompt enhancement"""
        self.enhance_prompts = not self.enhance_prompts
        status = "ativada" if self.enhance_prompts else "desativada"
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
                    role = msg['role']
                    role_counts[role] = role_counts.get(role, 0) + 1
                
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
        else:
            console.print("[dim]Prompts will be sent directly to the LLM[/dim]")
    
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
            for chunk in self.api.generate(self.selected_model, analysis_prompt, stream=True):
                response += chunk
            
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
        console.print("[dim]Analisando arquivos existentes e preparando melhorias...[/dim]\n")
        
        # Salva flag indicando que estamos em modo enhancement
        self._enhancement_mode = True
        
        try:
            # Processa o prompt melhorado
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
                    
                    # Detecta linguagem
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
        
        # Para outras linguagens, usa nome da linguagem
        return f'main{ext}'
    
    def _resolve_file_path(self, filepath: str, current_dir: Path) -> Path:
        """
        Resolve caminho de arquivo relativo ao diretório atual com limpeza de duplicações
        
        Args:
            filepath: Caminho do arquivo (pode ser relativo ou absoluto)
            current_dir: Diretório atual
            
        Returns:
            Caminho absoluto resolvido e limpo
        """
        if Path(filepath).is_absolute():
            resolved_path = Path(filepath)
        else:
            resolved_path = current_dir / filepath
        
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
                        
                        # Check if the directory name already exists in the current path
                        if dir_name.lower() in current_path.lower():
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
        
        # Processa outros blocos de código
        if other_blocks:
            # Agrupa por linguagem
            by_lang = {}
            for lang, code in other_blocks:
                lang_key = lang or 'text'
                if lang_key not in by_lang:
                    by_lang[lang_key] = []
                by_lang[lang_key].append(code)
            
            # Mostra resumo sutil
            total_blocks = sum(len(codes) for codes in by_lang.values())
            if total_blocks == 1:
                console.print(f"\n[dim]💾 1 code file available[/dim]")
            else:
                console.print(f"\n[dim]💾 {total_blocks} code files available[/dim]")
            
            # Pergunta se quer salvar
            save = console.input("[cyan]Salvar código? (s/N): [/cyan]")
            if save.lower() == 's':
                saved_count = 0
                for lang, codes in by_lang.items():
                    for i, code in enumerate(codes):
                        # Gera nome automaticamente
                        filename = self._generate_filename(lang, code, original_prompt)
                        
                        # Se houver múltiplos arquivos da mesma linguagem, adiciona índice
                        if len(codes) > 1:
                            base, ext = filename.rsplit('.', 1)
                            filename = f"{base}_{i+1}.{ext}"
                        
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
                            console.print(f"[red]Erro ao salvar {filename}: {e}[/red]")
                
                if saved_count > 0:
                    console.print(f"[green]✓ {saved_count} arquivo(s) salvo(s)[/green]")
    
    def _process_special_tags(self, response: str, original_prompt: str):
        """
        Processa tags especiais na resposta: <actions>, <read>, <code>
        
        Args:
            response: Resposta completa do modelo
            original_prompt: Prompt original do usuário
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
                    # Verifica se é um comando shell válido
                    if self.shell_exec.is_shell_command(line) or any(line.startswith(cmd) for cmd in ['cd ', 'mkdir ', 'touch ', 'pip ', 'npm ', 'git ']):
                        commands.append(line)
                    else:
                        # Se não é comando, pode ser descrição - ignora
                        if self.debug_mode:
                            console.print(f"[dim]Ignoring description: {line}[/dim]")
                
                for cmd in commands:
                    # Converte comando para o OS apropriado
                    converted_cmd = self.shell_exec.convert_command(cmd)
                    
                    # Check for directory duplication in mkdir commands
                    if converted_cmd.strip().startswith('mkdir '):
                        dir_name = converted_cmd.strip()[6:].strip().strip('"').strip("'")
                        current_path = self.shell_exec.get_current_directory()
                        
                        # Check if the directory name already exists in the current path
                        if dir_name.lower() in current_path.lower():
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
        
        # Processa tags <read>
        read_blocks = re.findall(r'<read>(.*?)</read>', response, re.DOTALL | re.IGNORECASE)
        if read_blocks:
            console.print("\n[bold blue]📖 Lendo arquivos...[/bold blue]")
            processed_something = True
            for reads in read_blocks:
                # Remove comentários e linhas vazias
                lines = [line.strip() for line in reads.strip().split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
                
                # Filtra apenas comandos válidos (ignora descrições em linguagem natural)
                commands = []
                for line in lines:
                    # Verifica se é um comando de leitura válido
                    if self.shell_exec.is_shell_command(line) or any(line.startswith(cmd) for cmd in ['cat ', 'type ', 'ls ', 'dir ', 'head ', 'tail ']):
                        commands.append(line)
                    else:
                        # Se não é comando, pode ser descrição - ignora
                        if self.debug_mode:
                            console.print(f"[dim]Ignoring description: {line}[/dim]")
                
                for cmd in commands:
                    # Converte comando para o OS apropriado
                    converted_cmd = self.shell_exec.convert_command(cmd)
                    
                    # Check for directory duplication in mkdir commands
                    if converted_cmd.strip().startswith('mkdir '):
                        dir_name = converted_cmd.strip()[6:].strip().strip('"').strip("'")
                        current_path = self.shell_exec.get_current_directory()
                        
                        # Check if the directory name already exists in the current path
                        if dir_name.lower() in current_path.lower():
                            console.print(f"[yellow]⚠️  Warning: Directory '{dir_name}' already exists in path![/yellow]")
                            console.print(f"[yellow]Current path: {current_path}[/yellow]")
                            console.print(f"[yellow]Consider using a unique name instead[/yellow]")
                    
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
        
        # Processa tags <code>
        code_matches = re.findall(r'<code\s+filename=["\']([^"\']+)["\']>(.*?)</code>', response, re.DOTALL | re.IGNORECASE)
        if code_matches:
            console.print(f"\n[bold green]💾 Criando {len(code_matches)} arquivo(s)...[/bold green]")
            processed_something = True
            
            created_count = 0
            current_dir = Path(self.shell_exec.get_current_directory())
            
            for filename, code_content in code_matches:
                try:
                    # Remove espaços em branco desnecessários
                    clean_code = code_content.strip()
                    
                    # Resolve caminho do arquivo relativo ao diretório atual
                    file_path = self._resolve_file_path(filename, current_dir)
                    
                    # Verifica se arquivo já existe e decide entre criar ou editar
                    if file_path.exists():
                        console.print(f"[yellow]📝 Editando: {file_path.name}[/yellow]")
                        self.file_ops.edit_file(file_path, clean_code)
                        # Git commit automático
                        self.git_manager.commit_file_operation("edited", file_path)
                    else:
                        console.print(f"[green]📄 Criando: {file_path.name}[/green]")
                        self.file_ops.create_file(file_path, clean_code)
                        # Git commit automático
                        self.git_manager.commit_file_operation("created", file_path)
                    created_count += 1
                    
                except FileOperationError as e:
                    console.print(f"[red]❌ Erro ao processar {filename}: {e}[/red]")
            
            if created_count > 0:
                console.print(f"[bold green]✅ {created_count} arquivo(s) criado(s) com sucesso![/bold green]")
        
        # Debug: informa se nenhuma tag especial foi processada
        if not processed_something:
            console.print("[dim]⚠️  Nenhuma tag especial encontrada na resposta[/dim]")
            console.print("[dim]💡 The model should use <actions>, <read> or <code> for actions[/dim]")
        
        return processed_something
    
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
        
        console.print("\n[bold blue]🎯 Modo de Tarefa Complexa Ativado[/bold blue]")
        console.print(f"[dim]Analisando: {args}[/dim]\n")
        
        # Detecta linguagem e framework na requisição inicial
        self.task_manager.detect_and_update_context(args)
        
        # Passo 1: Pedir ao modelo para quebrar em sub-tarefas
        breakdown_prompt = self.task_manager.get_breakdown_prompt(args)
        
        try:
            # Gera breakdown sem mostrar todo o processo
            with console.status("[bold yellow]Analisando e dividindo em sub-tarefas...", spinner="dots"):
                breakdown_response = ""
                for chunk in self.api.generate(self.selected_model, breakdown_prompt):
                    breakdown_response += chunk
            
            # Extrai tarefas da resposta
            tasks = self.task_manager.parse_task_breakdown(breakdown_response)
            
            # Detecta linguagem e framework no breakdown também
            self.task_manager.detect_and_update_context(breakdown_response)
            
            if not tasks:
                console.print("[red]Could not extract sub-tasks. Try to be more specific.[/red]")
                return
            
            # Salva tarefas no manager
            self.task_manager.current_tasks = tasks
            self.task_manager.completed_tasks = []
            
            # Mostra plano de execução
            console.print("[bold green]✅ Execution Plan Created![/bold green]\n")
            self.task_manager.display_task_progress()
            
            # Conta tarefas essenciais e opcionais
            essential_count = sum(1 for t in tasks if t.get('priority', 'essential') == 'essential')
            optional_count = sum(1 for t in tasks if t.get('priority') == 'optional')
            
            console.print(f"\n[bold]📊 Resumo:[/bold]")
            console.print(f"   [green]Essenciais: {essential_count} tarefas[/green]")
            console.print(f"   [yellow]Opcionais: {optional_count} tarefas[/yellow]")
            
            # Menu de escolha
            console.print("\n[bold cyan]Choose an option:[/bold cyan]")
            console.print("  1. Executar apenas tarefas ESSENCIAIS")
            console.print("  2. Executar TODAS as tarefas (essenciais + opcionais)")
            console.print("  3. Cancelar")
            
            choice = console.input("\n[cyan]Sua escolha (1/2/3): [/cyan]")
            
            if choice == '1':
                # Filtra apenas tarefas essenciais
                tasks_to_execute = [t for t in tasks if t.get('priority', 'essential') == 'essential']
                console.print(f"\n[green]✓ Executando {len(tasks_to_execute)} tarefas essenciais[/green]")
            elif choice == '2':
                # Executa todas as tarefas
                tasks_to_execute = tasks
                console.print(f"\n[green]✓ Executando todas as {len(tasks_to_execute)} tarefas[/green]")
            else:
                console.print("[yellow]Execution cancelled.[/yellow]")
                return
            
            console.print("\n[bold blue]🚀 Starting task execution...[/bold blue]\n")
            
            # Passo 2: Executar cada tarefa
            for i, task in enumerate(tasks_to_execute):
                priority_indicator = "[ESSENCIAL]" if task.get('priority', 'essential') == 'essential' else "[OPCIONAL]"
                console.print(f"\n[bold yellow]━━━ Tarefa {i+1}/{len(tasks_to_execute)} {priority_indicator} ━━━[/bold yellow]")
                console.print(f"[cyan]{task['description']}[/cyan]")
                console.print(f"[dim]Tipo detectado: {task['type']}[/dim]\n")
                
                # Atualiza status
                task['status'] = 'in_progress'
                self.task_manager.display_task_progress()
                
                # Cria prompt específico para a tarefa
                task_prompt = self.task_manager.format_task_prompt(task, context=args)
                
                # Executa a tarefa
                console.print("\n[dim]Executando tarefa...[/dim]")
                self._execute_task(task_prompt, task)
                
                # Marca como completa
                task['status'] = 'completed'
                self.task_manager.completed_tasks.append(task)
                
                # Pequena pausa entre tarefas
                if i < len(tasks) - 1:
                    console.print("\n[dim]Preparing next task...[/dim]")
            
            # Mostra resumo final
            console.print("\n[bold green]🎉 All tasks completed![/bold green]")
            self.task_manager.display_task_progress()
            
        except Exception as e:
            console.print(f"[red]Erro ao processar tarefas: {e}[/red]")
    
    def _execute_task(self, task_prompt: str, task_info: Dict):
        """
        Executa uma tarefa individual
        
        Args:
            task_prompt: Prompt formatado para a tarefa
            task_info: Informações da tarefa
        """
        try:
            # Se melhorias estão ativadas, aplica ao task prompt também
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
                with console.status("[bold green]Generating explanation...", spinner="dots") as status:
                    for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                        full_response += chunk
                
                # Exibe como texto formatado
                console.print("\n[bold cyan]Resposta:[/bold cyan]\n")
                console.print(Panel(Markdown(full_response), border_style="cyan"))
            else:
                # Para código/shell, usa processamento normal
                with console.status("[bold green]Generating solution...", spinner="dots") as status:
                    for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                        full_response += chunk
                
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
            console.print(f"[red]Erro ao executar tarefa: {e}[/red]")
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

## File Commands

- `/file create <path> [content]` - Creates a file
- `/file edit <path> <content>` - Edits a file
- `/file append <path> <content>` - Adds content to file
- `/file read <path>` - Reads a file
- `/file delete <path>` - Deletes a file
- `/file list [directory] [pattern] [-r]` - Lists files (use -r for recursive search)
- `/file search <filename>` - Searches for file in parent and subdirectories

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
                    console.print("[red]Uso: /file read <caminho>[/red]")
                    return
                filepath = self._resolve_file_path(parts[1], current_dir)
                content = self.file_ops.read_file(filepath)
                
                # Detecta linguagem pela extensão
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
                    console.print(f"[yellow]Nenhum arquivo encontrado em {directory}[/yellow]")
                    
            elif subcommand == "search":
                if len(parts) < 2:
                    console.print("[red]Uso: /file search <nome_arquivo>[/red]")
                    return
                
                filename = parts[1]
                
                # Primeiro tenta buscar arquivo normalmente
                found_path = self.file_ops.search_file(filename, current_dir)
                
                if found_path:
                    # Pergunta se quer ler o arquivo
                    from rich.prompt import Confirm
                    if Confirm.ask(f"Deseja ler o arquivo {found_path}?"):
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
                        console.print("\n[bold cyan]📄 Arquivos similares encontrados:[/bold cyan]")
                        for i, file_path in enumerate(results['files'][:5], 1):
                            console.print(f"  {i}. {file_path}")
                        
                        # Pergunta se quer abrir algum arquivo similar
                        if len(results['files']) == 1:
                            from rich.prompt import Confirm
                            if Confirm.ask(f"\nDeseja ler {results['files'][0]}?"):
                                content = self.file_ops.read_file(results['files'][0])
                                console.print(Panel(
                                    Syntax(content, "auto", theme="monokai", line_numbers=True),
                                    title=f"📄 {results['files'][0]}",
                                    border_style="green"
                                ))
                        else:
                            try:
                                choice = console.input("\n[cyan]Digite o número do arquivo para ler (ou Enter para cancelar): [/cyan]")
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
                console.print(f"[red]Comando de arquivo desconhecido: {subcommand}[/red]")
                
        except FileOperationError as e:
            console.print(f"[red]Erro: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Erro inesperado: {e}[/red]")
    
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
        Verifica se o prompt deve ser executado como comando ao invés de enviado ao modelo
        
        Args:
            prompt_text: Texto do prompt
            
        Returns:
            Comando a executar ou None
        """
        prompt_lower = prompt_text.lower()
        
        # Padrões que indicam comandos diretos
        list_patterns = [
            # Listagem de arquivos
            (r'list.*files?.*directory', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'show.*files?', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'what.*files?.*here', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'ls\s*$', 'ls'),
            (r'dir\s*$', 'dir'),
            (r'list.*current.*directory', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            (r'list.*files?', 'dir' if self.shell_exec.is_windows else 'ls'),
            (r'show.*directory.*content', 'dir' if self.shell_exec.is_windows else 'ls -la'),
            # Diretório atual
            (r'where.*am.*i', 'cd' if self.shell_exec.is_windows else 'pwd'),
            (r'current.*directory', 'cd' if self.shell_exec.is_windows else 'pwd'),
            (r'pwd\s*$', 'pwd'),
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
        if not self.selected_model:
            console.print("[red]No model selected. Use /models to select one.[/red]")
            return
        
        # Only execute if it's an EXACT shell command (no interpretation)
        if self.auto_execute_shell and self.shell_exec.is_shell_command(prompt_text.strip()):
            console.print(f"\n[dim]Executing: {prompt_text.strip()}[/dim]\n")
            with console.status(f"[dim]$ {prompt_text.strip()}[/dim]", spinner="dots"):
                success, output = self.shell_exec.execute_command(prompt_text.strip())
            
            if success:
                if output.strip():
                    console.print(output)
                else:
                    console.print("[green]✓ Command executed[/green]")
            else:
                console.print(f"[red]❌ {output}[/red]")
                # If command failed, send error back to LLM for automatic fix
                console.print("[yellow]🤖 Sending error to AI for automatic fix...[/yellow]")
                error_prompt = f"The command '{prompt_text.strip()}' failed with error: {output}. Please provide the correct command to fix this issue."
                # Process the error through LLM but don't auto-execute the fix
                temp_auto_execute = self.auto_execute_shell
                self.auto_execute_shell = False
                self.process_prompt(error_prompt)
                self.auto_execute_shell = temp_auto_execute
            return
        
        try:
            # Step 1: Better prompting - analyze and enhance user request
            working_prompt = prompt_text
            if self.better_prompting:
                working_prompt = self.analyze_and_enhance_prompt(prompt_text)
            
            # Step 2: Apply regular prompt enhancements if enabled  
            if self.enhance_prompts:
                enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                    working_prompt, 
                    self.shell_exec.get_current_directory(),
                    self.shell_exec.get_os_info()
                )
            else:
                enhanced_prompt = working_prompt
                # Still track context even without enhancement
                if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                    self.prompt_enhancer.add_to_context_history("user", working_prompt)
            
            # Buffer para acumular resposta completa
            full_response = ""
            code_count = 0
            line_count = 0
            
            # Gera resposta com status dinâmico
            with console.status("[bold green]Thinking...", spinner="dots") as status:
                for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                    full_response += chunk
                    line_count += chunk.count('\n')
                    
                    # Atualiza status baseado no conteúdo
                    if '```' in chunk:
                        code_count += 1
                        if code_count % 2 == 1:
                            status.update("[bold yellow]Escrevendo código...", spinner="dots2")
                        else:
                            status.update("[bold green]Analisando...", spinner="dots")
                    elif len(full_response) > 100 and line_count % 5 == 0:
                        # Alterna status periodicamente
                        if 'código' in full_response.lower() or 'function' in full_response or 'def ' in full_response:
                            status.update("[bold yellow]Escrevendo código...", spinner="dots2")
                        elif 'erro' in full_response.lower() or 'bug' in full_response.lower():
                            status.update("[bold red]Analisando erro...", spinner="dots3")
                        elif 'test' in full_response.lower():
                            status.update("[bold blue]Preparando testes...", spinner="dots")
                        else:
                            status.update("[bold green]Processando...", spinner="dots")
            
            # Exibe resposta completa formatada
            console.print("\n[bold cyan]Assistente:[/bold cyan]\n")
            
            # Debug: Mostra se há tags especiais na resposta
            has_actions = '<actions>' in full_response.lower()
            has_read = '<read>' in full_response.lower()
            has_code = '<code' in full_response.lower()
            has_traditional_code = '```' in full_response
            
            if not (has_actions or has_read or has_code or has_traditional_code):
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
                console.print("[dim]💡 Tip: Use commands like 'create a Python file' or 'install flask' for automatic actions[/dim]")
            
            # Verifica se estamos em modo enhancement e se o AI usou as tags corretamente
            if hasattr(self, '_enhancement_mode') and self._enhancement_mode:
                if not has_code:
                    console.print("\n[bold red]⚠️  ERROR: The AI did not follow the correct format![/bold red]")
                    console.print("[yellow]O AI deveria ter usado tags <code filename=\"...\"> para editar os arquivos.[/yellow]")
                    console.print("[yellow]Try again with a more specific description or use a different model.[/yellow]")
                    console.print("\n[dim]💡 Example: /enhance_code transform into professional SAAS landing page[/dim]")
            
        except OllamaAPIError as e:
            console.print(f"[red]Erro ao gerar resposta: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Resposta interrompida.[/yellow]")
    
    def run(self):
        """Executa a CLI principal"""
        # Banner de boas-vindas
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
        
        # Seleciona modelo
        self.selected_model = self.list_models()
        if not self.selected_model:
            console.print("[yellow]No model selected. Exiting...[/yellow]")
            return
        
        # Prepara autocompletar
        # Create custom completer that handles both commands and file paths
        custom_completer = XandAICompleter(self.commands, self.shell_exec)
        
        # Loop principal
        console.print("\n[dim]Type /help to see available commands.[/dim]\n")
        
        try:
            while True:
                try:
                    # Prompt com histórico e autocompletar
                    user_input = prompt(
                        f"[{self.selected_model}] > ",
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
                                # Não mostra mensagem de sucesso se não houver output
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
                    console.print("\n[yellow]Use /exit para sair.[/yellow]")
                except EOFError:
                    self.exit_cli()
                    
        except Exception as e:
            console.print(f"\n[red]Erro fatal: {e}[/red]")
            console.print("[dim]Saindo...[/dim]")
