"""
XandAI - Chat REPL Interface
Interactive REPL with terminal command interception and LLM integration
"""

import os
import subprocess
import shlex
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import prompt
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from xandai.ollama_client import OllamaClient, OllamaResponse
from xandai.history import HistoryManager
from xandai.task import TaskProcessor


class ChatREPL:
    """
    Interactive REPL for XandAI
    
    Features:
    - Rich terminal interface with prompt_toolkit
    - Terminal command interception (ls, cd, cat, etc.)
    - LLM conversation with context tracking
    - Task mode integration
    - Command completion and history
    """
    
    def __init__(self, ollama_client: OllamaClient, history_manager: HistoryManager, verbose: bool = False):
        """Initialize Chat REPL"""
        self.ollama_client = ollama_client
        self.history_manager = history_manager
        self.verbose = verbose
        
        # Rich console for pretty output
        self.console = Console()
        
        # Task processor
        self.task_processor = TaskProcessor(ollama_client, history_manager)
        
        # Prompt session with history and completion
        self.session = PromptSession(
            history=InMemoryHistory(),
            completer=self._create_completer(),
            complete_while_typing=False
        )
        
        # Terminal commands we intercept and run locally (Windows + Linux/macOS)
        self.terminal_commands = {
            # Directory/File listing
            'ls', 'dir',
            # Navigation
            'pwd', 'cd',
            # File operations
            'cat', 'type', 'head', 'tail', 'more', 'less',
            'mkdir', 'rmdir', 'rm', 'del', 'erase',
            'cp', 'copy', 'mv', 'move', 'ren', 'rename',
            # Search and text processing
            'find', 'findstr', 'grep', 'wc', 'sort', 'uniq',
            # System info
            'ps', 'tasklist', 'top', 'df', 'du', 'free', 'uname', 'whoami', 'date', 'time',
            'systeminfo', 'ver', 'hostname',
            # Network
            'ping', 'tracert', 'traceroute', 'netstat', 'ipconfig', 'ifconfig',
            # Process management  
            'kill', 'taskkill', 'killall',
            # File attributes
            'chmod', 'chown', 'attrib', 'icacls',
            # Utilities
            'echo', 'which', 'where', 'whereis', 'tree', 'file',
            # Clear screen
            'clear', 'cls',
            # Help
            'help', 'man'
        }
        
        # System prompt for chat mode
        self.system_prompt = self._build_system_prompt()
    
    def run(self):
        """Run the interactive REPL loop"""
        try:
            while True:
                # Show context info in prompt
                context_info = self.history_manager.get_context_summary()
                prompt_text = f"xandai ({context_info})> " if context_info != "No project context" else "xandai> "
                
                # Get user input
                try:
                    user_input = self.session.prompt(prompt_text).strip()
                except (EOFError, KeyboardInterrupt):
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() in ['clear', 'cls']:
                    self._clear_screen()
                    continue
                elif user_input.lower() == 'history':
                    self._show_conversation_history()
                    continue
                elif user_input.lower() == 'context':
                    self._show_project_context()
                    continue
                elif user_input.lower() == 'status':
                    self._show_status()
                    continue
                
                # Process the input
                self._process_input(user_input)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("\\n👋 Goodbye!")
    
    def _process_input(self, user_input: str):
        """Process user input - special commands, terminal commands, task mode, or LLM chat"""
        
        # Check for special slash commands first
        if user_input.startswith('/'):
            if self._handle_slash_command(user_input):
                return  # Command handled, don't process further
        
        # Check for terminal command
        command_parts = shlex.split(user_input) if user_input else []
        if command_parts and command_parts[0].lower() in self.terminal_commands:
            self._handle_terminal_command(user_input)
            return
        
        # Handle as LLM chat
        self._handle_chat(user_input)
    
    def _handle_slash_command(self, user_input: str) -> bool:
        """
        Handle special slash commands
        
        Returns:
            bool: True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        # Exit commands
        if command in ['/exit', '/quit', '/bye']:
            raise KeyboardInterrupt()  # Will be caught by main loop
        
        # Task mode
        if command.startswith('/task '):
            task_request = user_input[6:].strip()
            if task_request:
                self._handle_task_mode(task_request)
            else:
                self.console.print("[yellow]Usage: /task <description>[/yellow]")
            return True
        
        # Help command
        if command in ['/help', '/h']:
            self._show_help()
            return True
        
        # Clear screen
        if command in ['/clear', '/cls']:
            self._clear_screen()
            return True
        
        # History command
        if command in ['/history', '/hist']:
            self._show_conversation_history()
            return True
        
        # Context command
        if command in ['/context', '/ctx']:
            self._show_project_context()
            return True
        
        # Status command
        if command in ['/status', '/stat']:
            self._show_status()
            return True
        
        # Unknown slash command
        self.console.print(f"[red]Unknown command: {command}[/red]")
        self.console.print("[dim]Type 'help' or '/help' for available commands.[/dim]")
        return True
    
    def _handle_terminal_command(self, command: str):
        """Execute terminal command locally and return wrapped output"""
        try:
            # Add to history
            self.history_manager.add_conversation(
                role="user",
                content=command,
                metadata={"type": "terminal_command"}
            )
            
            # Execute command
            self.console.print(f"[dim]$ {command}[/dim]")
            
            # Handle special commands
            command_parts = shlex.split(command)
            command_name = command_parts[0].lower()
            
            if command_name == 'cd':
                self._handle_cd_command(command_parts)
                return
            elif command_name in ['cls', 'clear']:
                self._handle_clear_command(command)
                return
            
            # Execute other commands
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Format output
            if result.returncode == 0:
                output = result.stdout.strip() if result.stdout else "Command completed successfully"
                wrapped_output = f"<commands_output>\\n{output}\\n</commands_output>"
                
                self.console.print(Panel(
                    output if output else "[dim]Command completed[/dim]",
                    title=f"Command: {command}",
                    border_style="green"
                ))
            else:
                error_output = result.stderr.strip() if result.stderr else f"Command failed with code {result.returncode}"
                wrapped_output = f"<commands_output>\\nError: {error_output}\\n</commands_output>"
                
                self.console.print(Panel(
                    f"[red]{error_output}[/red]",
                    title=f"Command Failed: {command}",
                    border_style="red"
                ))
            
            # Add result to history
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_output", "return_code": result.returncode}
            )
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out (30s limit)"
            self.console.print(f"[red]{error_msg}[/red]")
            self.history_manager.add_conversation(
                role="system",
                content=f"<commands_output>\\n{error_msg}\\n</commands_output>",
                metadata={"type": "command_error"}
            )
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self.console.print(f"[red]{error_msg}[/red]")
            self.history_manager.add_conversation(
                role="system", 
                content=f"<commands_output>\\n{error_msg}\\n</commands_output>",
                metadata={"type": "command_error"}
            )
    
    def _handle_cd_command(self, command_parts: List[str]):
        """Handle cd command specially to change working directory"""
        try:
            if len(command_parts) == 1:
                # cd with no args - go to home
                new_dir = str(Path.home())
            else:
                new_dir = command_parts[1]
            
            # Change directory
            old_dir = os.getcwd()
            os.chdir(os.path.expanduser(new_dir))
            new_dir = os.getcwd()
            
            output = f"Changed directory from {old_dir} to {new_dir}"
            wrapped_output = f"<commands_output>\\n{output}\\n</commands_output>"
            
            self.console.print(f"[green]{output}[/green]")
            
            # Add to history
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "cd_command", "old_dir": old_dir, "new_dir": new_dir}
            )
            
        except Exception as e:
            error_msg = f"cd: {e}"
            wrapped_output = f"<commands_output>\\nError: {error_msg}\\n</commands_output>"
            self.console.print(f"[red]{error_msg}[/red]")
            
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_error"}
            )
    
    def _handle_clear_command(self, command: str):
        """Handle clear/cls command to clear screen"""
        try:
            # Clear the screen
            self._clear_screen()
            
            # Add to history
            wrapped_output = "<commands_output>\\nScreen cleared\\n</commands_output>"
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "clear_command"}
            )
            
            self.console.print("[dim]Screen cleared[/dim]")
            
        except Exception as e:
            error_msg = f"Clear command error: {e}"
            wrapped_output = f"<commands_output>\\nError: {error_msg}\\n</commands_output>"
            self.console.print(f"[red]{error_msg}[/red]")
            
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_error"}
            )
    
    def _handle_chat(self, user_input: str):
        """Handle LLM chat conversation"""
        try:
            # Add user message to history
            self.history_manager.add_conversation(
                role="user",
                content=user_input,
                metadata={"type": "chat"}
            )
            
            # Get conversation context
            context_messages = self.history_manager.get_conversation_context(limit=20)
            
            # Add current user input
            context_messages.append({"role": "user", "content": user_input})
            
            # Show thinking indicator
            with self.console.status("[bold green]Thinking..."):
                response = self.ollama_client.chat(
                    messages=context_messages,
                    system_prompt=self.system_prompt
                )
            
            # Display response with syntax highlighting for code
            self._display_response(response.content)
            
            # Display context usage
            self.console.print(f"\\n[dim]{response.context_usage}[/dim]")
            
            # Add response to history
            self.history_manager.add_conversation(
                role="assistant",
                content=response.content,
                context_usage=str(response.context_usage),
                metadata={"type": "chat"}
            )
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())
    
    def _handle_task_mode(self, task_request: str):
        """Handle task mode request with enhanced progress display"""
        try:
            # Process task with progress indicators
            raw_response, steps = self.task_processor.process_task(task_request, console=self.console)
            
            # If no steps but response exists, it might be clarifying questions
            if not steps and raw_response:
                # Check if it's clarifying questions (starts with 🤔)
                if "🤔" in raw_response or "clarify" in raw_response.lower():
                    self.console.print("\\n" + raw_response.split("Context usage:")[0].strip())
                    return
            
            # Display task summary
            if steps:
                summary = self.task_processor.get_task_summary(steps)
                self.console.print(f"\\n[bold green]✅ {summary}[/bold green]")
                
                # Display formatted steps
                formatted_steps = self.task_processor.format_steps_for_display(steps)
                self._display_task_steps(formatted_steps)
            else:
                self.console.print("\\n[yellow]⚠️  No executable steps generated.[/yellow]")
                self.console.print("[dim]Try being more specific about what you want to build.[/dim]")
            
            # Display context usage (from raw_response which includes it)
            if "Context usage:" in raw_response:
                context_line = raw_response.split("Context usage:")[-1].split("\\n")[0]
                self.console.print(f"\\n[dim]Context usage:{context_line}[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Task processing error: {e}[/red]")
            self.console.print("[dim]Please try rephrasing your request.[/dim]")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())
    
    def _display_response(self, content: str):
        """Display LLM response with syntax highlighting"""
        # Check if response contains code blocks
        import re
        code_blocks = re.findall(r'```(\\w+)?\\n(.*?)\\n```', content, re.DOTALL)
        
        if code_blocks:
            # Split content by code blocks and display with syntax highlighting
            parts = re.split(r'```\\w*\\n.*?\\n```', content, flags=re.DOTALL)
            block_index = 0
            
            for i, part in enumerate(parts):
                if part.strip():
                    self.console.print(part.strip())
                
                # Display code block with syntax highlighting
                if block_index < len(code_blocks):
                    lang, code = code_blocks[block_index]
                    if code.strip():
                        try:
                            syntax = Syntax(code.strip(), lang or "text", theme="monokai", line_numbers=True)
                            self.console.print(Panel(syntax, title=f"Code ({lang or 'text'})", border_style="blue"))
                        except:
                            # Fallback to plain text
                            self.console.print(Panel(code.strip(), title="Code", border_style="blue"))
                    block_index += 1
        else:
            # No code blocks, display as is
            self.console.print(content)
    
    def _display_task_steps(self, formatted_steps: str):
        """Display task steps with proper formatting"""
        # Parse and display each step with proper highlighting
        current_step = ""
        in_code_block = False
        in_commands_block = False
        
        for line in formatted_steps.split("\\n"):
            if line.startswith(('<code edit filename=', '</code>', '<commands>', '</commands>')):
                if line.startswith('<code edit filename='):
                    filename = line.split('"')[1]
                    self.console.print(f"\\n[bold green]📝 File: {filename}[/bold green]")
                    in_code_block = True
                elif line == '</code>':
                    in_code_block = False
                elif line == '<commands>':
                    self.console.print(f"\\n[bold yellow]⚡ Commands:[/bold yellow]")
                    in_commands_block = True
                elif line == '</commands>':
                    in_commands_block = False
            elif re.match(r'^\\d+ - (create|edit|run)', line):
                # Step header
                self.console.print(f"\\n[bold cyan]{line}[/bold cyan]")
            elif in_code_block and line.strip():
                # Code content - try to detect language
                try:
                    # Simple language detection based on content
                    if 'import ' in line or 'def ' in line or 'class ' in line:
                        lang = 'python'
                    elif 'function' in line or 'const ' in line or 'let ' in line:
                        lang = 'javascript'
                    else:
                        lang = 'text'
                    
                    syntax = Syntax(line, lang, theme="monokai")
                    self.console.print(syntax)
                except:
                    self.console.print(f"  {line}")
            elif in_commands_block and line.strip():
                # Command content
                self.console.print(f"  [green]$ {line}[/green]")
            elif line.strip():
                # Regular content
                self.console.print(line)
    
    def _show_help(self):
        """Display help information"""
        help_text = """
[bold]XandAI - Interactive CLI Assistant[/bold]

[yellow]Chat Commands:[/yellow]
  • Just type naturally to chat with the AI
  • Terminal commands (ls, cd, cat, etc.) are executed locally
  • Use /task <description> for structured project planning

[yellow]Special Commands (/ prefix):[/yellow]
  • /help, /h       - Show this help
  • /clear, /cls    - Clear screen
  • /history, /hist - Show conversation history  
  • /context, /ctx  - Show project context
  • /status, /stat  - Show system status
  • /exit, /quit, /bye - Exit XandAI

[yellow]Alternative Commands (no prefix):[/yellow]
  • help, clear, history, context, status
  • exit, quit, bye

[yellow]Task Mode:[/yellow]
  • /task create a web app with Python Flask
  • /task add user authentication to my React app
  • /task optimize the database queries in my Django project

[yellow]Terminal Commands:[/yellow]
  Cross-platform terminal commands work (Windows + Linux/macOS):
  • Windows: dir, cls, type, copy, del, tasklist, ipconfig, etc.
  • Linux/macOS: ls, clear, cat, cp, rm, ps, ifconfig, etc.
  • Universal: cd, mkdir, ping, echo, tree, etc.
  Results are wrapped in <commands_output> tags.

[yellow]Tips:[/yellow]
  • Be specific in /task requests for better results
  • Use quotes for complex terminal commands: "ls -la | grep .py"
  • Context is maintained across the session
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_conversation_history(self):
        """Show recent conversation history"""
        recent = self.history_manager.get_recent_conversation(10)
        if not recent:
            self.console.print("[yellow]No conversation history[/yellow]")
            return
        
        self.console.print("\\n[bold]Recent Conversation:[/bold]")
        for msg in recent:
            role_color = {"user": "green", "assistant": "blue", "system": "yellow"}.get(msg["role"], "white")
            timestamp = msg["timestamp"].split("T")[1].split(".")[0]  # HH:MM:SS
            self.console.print(f"[{role_color}][{timestamp}] {msg['role']}:[/{role_color}] {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
    
    def _show_project_context(self):
        """Show current project context and tracked files"""
        context = self.history_manager.get_project_context()
        files = self.history_manager.get_project_files()
        
        # Project info
        info_text = ""
        if context["language"]:
            info_text += f"Language: {context['language']}\\n"
        if context["framework"]:
            info_text += f"Framework: {context['framework']}\\n"
        if context["project_type"]:
            info_text += f"Type: {context['project_type']}\\n"
        
        if not info_text:
            info_text = "No project context detected\\n"
        
        # Files
        if files:
            info_text += f"\\nTracked files ({len(files)}):\\n"
            for f in files[:10]:
                info_text += f"  • {f}\\n"
            if len(files) > 10:
                info_text += f"  ... and {len(files) - 10} more\\n"
        else:
            info_text += "\\nNo files tracked yet\\n"
        
        self.console.print(Panel(info_text.strip(), title="Project Context", border_style="cyan"))
    
    def _show_status(self):
        """Show system status"""
        health = self.ollama_client.health_check()
        
        status_text = f"""
Connected: {'✅ Yes' if health['connected'] else '❌ No'}
Endpoint: {health['endpoint']}
Current Model: {health.get('current_model', 'None')}
Available Models: {health.get('models_available', 0)}

Working Directory: {os.getcwd()}
Conversation Messages: {len(self.history_manager.conversation_history)}
Tracked Files: {len(self.history_manager.get_project_files())}
        """
        
        self.console.print(Panel(status_text.strip(), title="System Status", border_style="green"))
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for chat mode"""
        return """You are XandAI, an intelligent CLI assistant focused on software development and system administration.

CHARACTERISTICS:
- Provide clear, helpful responses to technical questions
- When users show you command outputs (in <commands_output> tags), analyze and explain them
- Offer practical solutions and best practices
- Be concise but thorough in explanations
- Suggest follow-up commands or actions when appropriate

CONTEXT AWARENESS:
- You can see terminal command outputs that users run locally
- Use this context to provide more relevant advice
- Reference specific files, directories, or system state when visible

RESPONSE STYLE:
- Use markdown formatting for code, commands, and structure
- Provide working examples when explaining concepts
- Include relevant terminal commands users can try
- Explain the reasoning behind your suggestions

CAPABILITIES:
- Software development guidance (all languages/frameworks)
- System administration help (Linux, macOS, Windows)
- DevOps and deployment assistance
- Debugging and troubleshooting
- Best practices and code reviews

Remember: Users can run terminal commands directly, and you'll see the results. Use this to provide contextual, actionable advice."""
    
    def _create_completer(self) -> WordCompleter:
        """Create command completer for prompt"""
        words = [
            # Slash commands
            '/task', '/help', '/h', '/clear', '/cls', '/history', '/hist',
            '/context', '/ctx', '/status', '/stat', '/exit', '/quit', '/bye',
            # Cross-platform terminal commands
            'ls', 'dir', 'cd', 'pwd', 'cat', 'type', 'mkdir', 'rmdir',
            'rm', 'del', 'cp', 'copy', 'mv', 'move', 'ren', 'rename',
            'find', 'findstr', 'grep', 'ps', 'tasklist', 'kill', 'taskkill',
            'ping', 'tracert', 'netstat', 'ipconfig', 'ifconfig',
            'echo', 'tree', 'which', 'where', 'date', 'time',
            'cls', 'clear', 'help', 'man',
            # Special commands (no slash)
            'help', 'clear', 'cls', 'history', 'context', 'status', 'exit', 'quit', 'bye',
            # Programming keywords
            'python', 'javascript', 'react', 'flask', 'django', 'nodejs',
            'git', 'docker', 'kubernetes', 'api', 'database', 'sql'
        ]
        
        return WordCompleter(words, ignore_case=True)
