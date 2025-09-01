"""
Interface CLI principal do XandAI
"""

import sys
import os
import re
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
        self.session_manager = SessionManager()
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
            '/context': self.context_command_new,
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
        
        # For other languages, refuse to create generic names
        # Instead, prompt user to provide specific filename
        console.print(f"[yellow]⚠️ Cannot determine appropriate filename for {lang} code[/yellow]")
        console.print(f"[yellow]💡 Please use <code filename=\"your_filename{ext}\"> tags to specify filename[/yellow]")
        console.print(f"[yellow]💡 Or mention the desired filename in your request[/yellow]")
        return None  # Return None to skip file creation
    
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
    
    def _extract_code_blocks(self, response: str) -> List[Tuple[str, str]]:
        """
        Extrai blocos de código da resposta com melhor tratamento de erros
        
        Args:
            response: Resposta do modelo
            
        Returns:
            Lista de tuplas (filename, code_content)
        """
        code_blocks = []
        
        # Padrão mais robusto para tags code
        pattern = r'<code\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)\s*</code>'
        
        # Primeiro, tenta o padrão padrão
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            for filename, content in matches:
                # Valida o filename
                clean_filename = filename.strip()
                if clean_filename and self._is_valid_filename(clean_filename):
                    code_blocks.append((clean_filename, content))
                else:
                    console.print(f"[yellow]⚠️  Invalid filename skipped: {filename}[/yellow]")
        
        # Se não encontrou nada, tenta padrões alternativos para tags mal formatadas
        if not code_blocks:
            # Busca por tags incompletas ou mal fechadas
            alt_pattern = r'<code\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)(?:</code>|$)'
            alt_matches = re.findall(alt_pattern, response, re.DOTALL | re.IGNORECASE)
            
            for filename, content in alt_matches:
                clean_filename = filename.strip()
                if clean_filename and self._is_valid_filename(clean_filename):
                    # Remove possível texto misturado após o código
                    cleaned_content = self._remove_mixed_content(content)
                    code_blocks.append((clean_filename, cleaned_content))
        
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
        
        # Processa tags <code> com melhor tratamento
        code_blocks = self._extract_code_blocks(response)
        if code_blocks:
            console.print(f"\n[bold green]💾 Criando {len(code_blocks)} arquivo(s)...[/bold green]")
            processed_something = True
            
            created_count = 0
            current_dir = Path(self.shell_exec.get_current_directory())
            
            for filename, code_content in code_blocks:
                try:
                    # Remove espaços em branco desnecessários e valida o conteúdo
                    clean_code = self._clean_code_content(code_content)
                    
                    if not clean_code.strip():
                        console.print(f"[yellow]⚠️  Skipping empty file: {filename}[/yellow]")
                        continue
                    
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
                    console.print(f"[red]❌ Error processing {filename}: {e}[/red]")
            
            if created_count > 0:
                console.print(f"[bold green]✅ {created_count} file(s) created successfully![/bold green]")
        
        # Debug: inform if no special tags were processed
        if not processed_something:
            console.print("[dim]⚠️  No special tags found in response[/dim]")
            console.print("[dim]💡 The model should use <actions>, <read> or <code> for actions[/dim]")
        
        return processed_something
    
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
        
        console.print("\n[bold blue]🎯 Modo de Tarefa Complexa Ativado[/bold blue]")
        console.print(f"[dim]Analisando: {args}[/dim]\n")
        
        # Step 1: Apply better prompting to enhance task description
        enhanced_args = args
        if self.better_prompting:
            enhanced_args = self.analyze_and_enhance_prompt(args)
            # Add to context history
            if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                self.prompt_enhancer.add_to_context_history("user", f"Task: {args}")
        
        # Detecta linguagem e framework na requisição melhorada
        self.task_manager.detect_and_update_context(enhanced_args)
        
        # Passo 1: Pedir ao modelo para quebrar em sub-tarefas usando a versão melhorada
        breakdown_prompt = self.task_manager.get_breakdown_prompt(enhanced_args)
        
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
            
            # Save tasks in manager
            self.task_manager.current_tasks = tasks
            self.task_manager.completed_tasks = []
            
            # Show execution plan
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
            console.print(f"[red]Error processing tasks: {e}[/red]")
    
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
                # If command failed, send error back to LLM for automatic fix
                # Only if we have a model selected
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
            # Step 1: Check if input is an error message and create specialized prompt
            error_info = self.prompt_enhancer.detect_error_type(prompt_text)
            if error_info:
                console.print(f"[yellow]🔍 Detected {error_info['type']} error - creating specialized fix prompt[/yellow]")
                enhanced_prompt = self.prompt_enhancer.create_error_fix_prompt(
                    prompt_text, 
                    error_info, 
                    self.shell_exec.get_current_directory()
                )
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
                else:
                    enhanced_prompt = working_prompt
            
            # ALWAYS track context regardless of enhancement settings
            if hasattr(self.prompt_enhancer, 'add_to_context_history'):
                try:
                    self.prompt_enhancer.add_to_context_history("user", working_prompt)
                except Exception as e:
                    if self.debug_mode:
                        console.print(f"[dim]⚠️ Error adding user message to context: {e}[/dim]")
            
            # Buffer para acumular resposta completa
            full_response = ""
            code_count = 0
            line_count = 0
            last_line = ""
            
            # Gera resposta com status dinâmico mostrando sempre a última linha
            with console.status("[bold green]🤔 Thinking...", spinner="dots") as status:
                for chunk in self.api.generate(self.selected_model, enhanced_prompt):
                    full_response += chunk
                    line_count += chunk.count('\n')
                    
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
                console.print("[dim]💡 Tip: Use commands like 'create a Python file' or 'install flask' for automatic actions[/dim]")
            
            # Verifica se estamos em modo enhancement e se o AI usou as tags corretamente
            if hasattr(self, '_enhancement_mode') and self._enhancement_mode:
                if not has_code:
                    console.print("\n[bold red]⚠️  ERROR: The AI did not follow the correct format![/bold red]")
                    console.print("[yellow]O AI deveria ter usado tags <code filename=\"...\"> para editar os arquivos.[/yellow]")
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
