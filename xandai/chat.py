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
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.shortcuts import prompt
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import re

from xandai.ollama_client import OllamaClient, OllamaResponse
from xandai.history import HistoryManager
from xandai.task import TaskProcessor, TaskStep
from xandai.utils.os_utils import OSUtils
from xandai.utils.prompt_manager import PromptManager


class IntelligentCompleter(Completer):
    """Smart completer that provides context-aware suggestions"""
    
    def __init__(self):
        self.slash_commands = [
            '/task', '/help', '/h', '/clear', '/cls', '/history', '/hist',
            '/context', '/ctx', '/status', '/stat', '/scan', '/structure', 
            '/exit', '/quit', '/bye'
        ]
        
        # Commands that need directory suggestions
        self.dir_commands = ['cd', 'mkdir', 'rmdir', 'pushd', 'popd']
        
        # Commands that need file suggestions  
        self.file_commands = ['cat', 'type', 'nano', 'vim', 'edit', 'open', 'head', 'tail', 'less', 'more']
        
        # Commands that need both files and directories
        self.path_commands = ['ls', 'dir', 'cp', 'copy', 'mv', 'move', 'rm', 'del', 'find', 'grep', 'findstr', 'tree', 'du', 'chmod', 'chown', 'stat']
        
        # All terminal commands
        self.terminal_commands = [
            'ls', 'dir', 'cd', 'pwd', 'cat', 'type', 'mkdir', 'rmdir',
            'rm', 'del', 'cp', 'copy', 'mv', 'move', 'ren', 'rename',
            'find', 'findstr', 'grep', 'ps', 'tasklist', 'kill', 'taskkill',
            'ping', 'tracert', 'netstat', 'ipconfig', 'ifconfig',
            'echo', 'tree', 'which', 'where', 'date', 'time',
            'cls', 'clear', 'help', 'man'
        ]
    
    def get_completions(self, document, complete_event):
        """Provide intelligent completions based on context"""
        try:
            text = document.text
            cursor_position = document.cursor_position
            
            # Get current line up to cursor
            current_line = document.current_line_before_cursor
            words = current_line.split()
            
            # If nothing typed yet, suggest slash commands and basic commands
            if not words:
                yield from self._get_basic_completions("")
                return
            
            # If typing a slash command
            if current_line.startswith('/'):
                yield from self._get_slash_completions(current_line)
                return
            
            # If typing a terminal command with arguments
            if len(words) >= 1:
                command = words[0].lower()
                
                # Get the current word being typed
                current_word = ""
                if current_line.endswith(' '):
                    # Starting a new word
                    current_word = ""
                else:
                    # Completing current word
                    current_word = words[-1] if words else ""
                
                # Provide path suggestions for commands that need them
                if len(words) > 1 and command in self.dir_commands:
                    yield from self._get_directory_completions(current_word)
                elif len(words) > 1 and command in self.file_commands:
                    yield from self._get_file_completions(current_word)
                elif len(words) > 1 and command in self.path_commands:
                    yield from self._get_path_completions(current_word)
                elif len(words) == 1 and not current_line.endswith(' '):
                    # Still typing the command itself
                    yield from self._get_command_completions(current_word)
                elif len(words) == 1 and current_line.endswith(' '):
                    # Command typed, ready for arguments
                    if command in self.dir_commands:
                        yield from self._get_directory_completions("")
                    elif command in self.file_commands:
                        yield from self._get_file_completions("")
                    elif command in self.path_commands:
                        yield from self._get_path_completions("")
            else:
                # Single word, suggest commands
                yield from self._get_command_completions(current_line)
                
        except Exception:
            # Fallback to basic completions if anything fails
            yield from self._get_basic_completions("")
    
    def _get_basic_completions(self, prefix: str):
        """Basic completions for slash commands and common words"""
        suggestions = self.slash_commands + ['help', 'clear', 'exit', 'quit']
        for suggestion in suggestions:
            if suggestion.lower().startswith(prefix.lower()):
                yield Completion(suggestion, start_position=-len(prefix))
    
    def _get_slash_completions(self, text: str):
        """Get completions for slash commands"""
        for cmd in self.slash_commands:
            if cmd.lower().startswith(text.lower()):
                yield Completion(cmd, start_position=-len(text))
    
    def _get_command_completions(self, prefix: str):
        """Get completions for terminal commands"""
        all_commands = self.terminal_commands + self.slash_commands + ['help', 'clear', 'exit']
        for cmd in all_commands:
            if cmd.lower().startswith(prefix.lower()):
                yield Completion(cmd, start_position=-len(prefix))
    
    def _get_directory_completions(self, prefix: str):
        """Get directory completions"""
        try:
            current_dir = Path.cwd()
            
            # Handle relative paths
            if '/' in prefix or '\\' in prefix:
                # Extract directory part
                path_parts = prefix.replace('\\', '/').split('/')
                dir_part = '/'.join(path_parts[:-1])
                file_prefix = path_parts[-1]
                
                if dir_part:
                    try:
                        search_dir = current_dir / dir_part
                        if not search_dir.exists():
                            return
                    except:
                        return
                else:
                    search_dir = current_dir
                    file_prefix = prefix
            else:
                search_dir = current_dir
                file_prefix = prefix
            
            # Get directories
            try:
                for item in search_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        item_name = item.name
                        if item_name.lower().startswith(file_prefix.lower()):
                            # Add trailing slash for directories
                            suggestion = item_name + "/"
                            yield Completion(suggestion, start_position=-len(file_prefix))
            except (PermissionError, OSError):
                pass
        except Exception:
            pass
    
    def _get_file_completions(self, prefix: str):
        """Get file completions"""
        try:
            current_dir = Path.cwd()
            
            # Handle relative paths
            if '/' in prefix or '\\' in prefix:
                path_parts = prefix.replace('\\', '/').split('/')
                dir_part = '/'.join(path_parts[:-1])
                file_prefix = path_parts[-1]
                
                if dir_part:
                    try:
                        search_dir = current_dir / dir_part
                        if not search_dir.exists():
                            return
                    except:
                        return
                else:
                    search_dir = current_dir
                    file_prefix = prefix
            else:
                search_dir = current_dir
                file_prefix = prefix
            
            # Get files
            try:
                for item in search_dir.iterdir():
                    if item.is_file() and not item.name.startswith('.'):
                        item_name = item.name
                        if item_name.lower().startswith(file_prefix.lower()):
                            yield Completion(item_name, start_position=-len(file_prefix))
            except (PermissionError, OSError):
                pass
        except Exception:
            pass
    
    def _get_path_completions(self, prefix: str):
        """Get both file and directory completions"""
        # Combine both file and directory completions
        yield from self._get_directory_completions(prefix)
        yield from self._get_file_completions(prefix)


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
        
        # Task processor (with shared verbose mode)
        self.task_processor = TaskProcessor(ollama_client, history_manager, verbose)
        
        # Prompt session with history and completion
        self.session = PromptSession(
            history=InMemoryHistory(),
            completer=IntelligentCompleter(),
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
        
        # Track current task session files
        self.current_task_files = []
        self.current_project_structure = None
    
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
        
        if self.verbose:
            OSUtils.debug_print(f"Processing input: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'", True)
        
        # Check for special slash commands first
        if user_input.startswith('/'):
            if self.verbose:
                OSUtils.debug_print("Detected slash command", True)
            if self._handle_slash_command(user_input):
                return  # Command handled, don't process further
        
        # Check for terminal command
        try:
            command_parts = shlex.split(user_input) if user_input else []
        except ValueError as e:
            # Handle shlex parsing errors (e.g., unmatched quotes/apostrophes)
            if self.verbose:
                OSUtils.debug_print(f"Shlex parsing error (treating as regular chat): {e}", True)
            command_parts = []
        
        if command_parts and command_parts[0].lower() in self.terminal_commands:
            if self.verbose:
                OSUtils.debug_print(f"Executing terminal command: {command_parts[0]}", True)
            self._handle_terminal_command(user_input)
            return
        
        # Handle as LLM chat
        if self.verbose:
            context_count = len(self.history_manager.get_conversation_context(limit=20))
            OSUtils.debug_print(f"Sending to LLM for chat processing with {context_count} context messages (includes any recent task history)", True)
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
        
        # Debug command - show OS and platform debug information or toggle debug mode
        if command.startswith('/debug') or command.startswith('/dbg'):
            self._handle_debug_command(user_input)
            return True
        
        # Scan current directory structure
        if command in ['/scan', '/structure']:
            self._show_project_structure()
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
            try:
                command_parts = shlex.split(command)
                command_name = command_parts[0].lower()
            except ValueError as e:
                # Handle shlex parsing errors (e.g., unmatched quotes/apostrophes)
                if self.verbose:
                    OSUtils.debug_print(f"Shlex parsing error in terminal command: {e}", True)
                # Fallback: split by spaces for basic parsing
                command_parts = command.split()
                command_name = command_parts[0].lower() if command_parts else ""
            
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
        """Handle LLM chat conversation with intelligent command generation"""
        try:
            if self.verbose:
                OSUtils.debug_print(f"Starting chat processing for {len(user_input)} character input", True)
            
            # Add user message to history
            self.history_manager.add_conversation(
                role="user",
                content=user_input,
                metadata={"type": "chat"}
            )
            
            # Check if we need to generate commands first (two-stage processing)
            command_output = ""
            if self._should_generate_commands(user_input):
                if self.verbose:
                    OSUtils.debug_print("Detected need for command generation - using two-stage LLM processing", True)
                
                command_output = self._generate_and_execute_commands(user_input)
            
            # Get conversation context
            context_messages = self.history_manager.get_conversation_context(limit=20)
            
            if self.verbose:
                OSUtils.debug_print(f"Retrieved {len(context_messages)} context messages from history", True)
            
            # Add current user input
            context_messages.append({"role": "user", "content": user_input})
            
            # If we have command output, add it as additional context
            if command_output:
                if self.verbose:
                    OSUtils.debug_print(f"Adding command output as context: {len(command_output)} characters", True)
                
                context_messages.append({
                    "role": "system", 
                    "content": f"Command execution results for context:\n\n{command_output}"
                })
            
            if self.verbose:
                OSUtils.debug_print(f"Sending {len(context_messages)} total messages to LLM", True)
            
            # Show thinking indicator with streaming
            response = self._chat_with_streaming_progress(context_messages)
            
            if self.verbose:
                OSUtils.debug_print(f"Received response: {len(response.content)} characters", True)
            
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
    
    def _should_generate_commands(self, user_input: str) -> bool:
        """
        Determine if we should use two-stage LLM processing (command generation + chat)
        Returns True if the user input suggests they want to read/examine files
        """
        # Keywords that suggest file reading/examination
        read_keywords = [
            'read', 'show', 'display', 'examine', 'analyze', 'describe',
            'look at', 'check', 'view', 'see', 'tell me about', 'explain',
            'what is in', 'contents of', 'open', 'cat', 'type'
        ]
        
        # File-related keywords
        file_keywords = [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.php',
            '.rb', '.go', '.rs', '.kt', '.swift', '.css', '.html',
            '.json', '.xml', '.yaml', '.yml', '.md', '.txt', '.log',
            'file', 'script', 'code', 'source', 'app.py', 'main.py',
            'index.js', 'package.json', 'requirements.txt', 'config'
        ]
        
        user_lower = user_input.lower()
        
        # Check if we have both read intent and file references
        has_read_intent = any(keyword in user_lower for keyword in read_keywords)
        has_file_reference = any(keyword in user_lower for keyword in file_keywords)
        
        if self.verbose and (has_read_intent or has_file_reference):
            OSUtils.debug_print(f"Command generation analysis: read_intent={has_read_intent}, file_ref={has_file_reference}", True)
        
        return has_read_intent and has_file_reference
    
    def _generate_and_execute_commands(self, user_input: str) -> str:
        """
        Use LLM to generate OS commands, execute them, and return the output
        """
        try:
            if self.verbose:
                OSUtils.debug_print("Step 1: Generating commands using Command LLM", True)
            
            # Get command generation prompt
            command_prompt = PromptManager.get_file_read_command_for_prompt(user_input)
            
            if self.verbose:
                OSUtils.debug_print(f"Command prompt length: {len(command_prompt)} chars", True)
            
            # Use LLM to generate commands - use the same pattern as chat with system prompt
            command_messages = [{"role": "user", "content": command_prompt}]
            
            if self.verbose:
                OSUtils.debug_print(f"Sending command generation request to LLM", True)
            
            # Get command response from LLM - use non-streaming for command generation to avoid JSON parsing issues
            try:
                if self.verbose:
                    OSUtils.debug_print("Using non-streaming for command generation to ensure reliability", True)
                
                command_response = self.ollama_client.chat(
                    messages=command_messages, 
                    stream=False  # Use non-streaming for command generation to avoid "Extra data" JSON issues
                )
                
                if self.verbose:
                    OSUtils.debug_print(f"Command LLM response: {len(command_response.content)} chars", True)
                
            except Exception as e:
                if self.verbose:
                    OSUtils.debug_print(f"Command generation LLM error: {e}", True)
                    OSUtils.debug_print("Trying with minimal system prompt as final fallback", True)
                
                # Try with simpler system prompt as final fallback
                try:
                    simple_command_messages = [{
                        "role": "user", 
                        "content": f"Generate a Windows command to read the file mentioned in: {user_input}"
                    }]
                    
                    command_response = self.ollama_client.chat(
                        messages=simple_command_messages, 
                        stream=False
                    )
                    if self.verbose:
                        OSUtils.debug_print("Command generation succeeded with simple fallback", True)
                except Exception as fallback_error:
                    if self.verbose:
                        OSUtils.debug_print(f"All command generation methods failed: {fallback_error}", True)
                    return ""
            
            # Extract commands from response
            commands = self._extract_commands_from_response(command_response.content)
            
            if not commands:
                if self.verbose:
                    OSUtils.debug_print("No commands extracted from LLM response", True)
                    OSUtils.debug_print("Trying direct command generation fallback", True)
                
                # Fallback: Generate simple command directly based on user input
                fallback_command = self._generate_fallback_command(user_input)
                if fallback_command:
                    commands = [fallback_command]
                    if self.verbose:
                        OSUtils.debug_print(f"Using fallback command: {fallback_command}", True)
                else:
                    return ""
            
            if self.verbose:
                OSUtils.debug_print(f"Step 2: Executing {len(commands)} generated commands", True)
            
            # Execute commands and collect output
            all_output = []
            for i, command in enumerate(commands, 1):
                if self.verbose:
                    OSUtils.debug_print(f"Executing command {i}/{len(commands)}: {command[:50]}...", True)
                
                try:
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        cwd=os.getcwd(),
                        timeout=30
                    )
                    
                    if result.stdout:
                        all_output.append(f"Command: {command}\n{result.stdout}\n")
                    
                    if result.stderr and self.verbose:
                        OSUtils.debug_print(f"Command stderr: {result.stderr[:100]}...", True)
                        
                except subprocess.TimeoutExpired:
                    if self.verbose:
                        OSUtils.debug_print(f"Command timed out: {command}", True)
                except Exception as e:
                    if self.verbose:
                        OSUtils.debug_print(f"Command execution error: {e}", True)
            
            output = "\n".join(all_output)
            
            if self.verbose:
                OSUtils.debug_print(f"Step 3: Collected {len(output)} characters of command output", True)
            
            return output
            
        except Exception as e:
            if self.verbose:
                OSUtils.debug_print(f"Error in command generation/execution: {e}", True)
            return ""
    
    def _extract_commands_from_response(self, response_content: str) -> list:
        """Extract commands from LLM response that are in <commands> blocks"""
        import re
        
        if self.verbose:
            OSUtils.debug_print(f"Extracting commands from response: {response_content[:200]}...", True)
        
        # Find all <commands>...</commands> blocks
        pattern = r'<commands>\s*(.*?)\s*</commands>'
        matches = re.findall(pattern, response_content, re.DOTALL | re.IGNORECASE)
        
        commands = []
        for match in matches:
            # Split by newlines and filter empty lines
            lines = [line.strip() for line in match.split('\n') if line.strip()]
            # Filter out comments and empty lines
            filtered_lines = [line for line in lines if not line.startswith('#') and not line.startswith('//')]
            commands.extend(filtered_lines)
        
        # If no commands found, try alternative patterns (fallback)
        if not commands:
            if self.verbose:
                OSUtils.debug_print("No <commands> blocks found, trying alternative extraction", True)
            
            # Try to find single command patterns like "type filename" or "cat filename"
            common_commands = ['type', 'cat', 'dir', 'ls', 'head', 'tail', 'grep', 'findstr']
            lines = response_content.split('\n')
            
            for line in lines:
                line = line.strip()
                # Check if line starts with common file commands
                if any(line.lower().startswith(cmd) for cmd in common_commands):
                    # Remove markdown code block markers if present
                    line = line.replace('```', '').strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        commands.append(line)
        
        if self.verbose and commands:
            OSUtils.debug_print(f"Extracted {len(commands)} commands: {commands}", True)
        elif self.verbose:
            OSUtils.debug_print("No commands found in LLM response", True)
        
        return commands
    
    def _generate_fallback_command(self, user_input: str) -> str:
        """Generate a simple fallback command when LLM fails to generate commands"""
        import re
        
        user_lower = user_input.lower()
        
        # Look for file mentions in the user input
        file_patterns = [
            r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]{1,4})\b',  # filename.ext
            r'\b(app\.py|main\.py|index\.js|package\.json|requirements\.txt|config\.py)\b'  # common files
        ]
        
        found_files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            found_files.extend(matches)
        
        if found_files:
            # Use the first file found
            target_file = found_files[0]
            
            # Generate OS-appropriate read command
            if 'read' in user_lower or 'show' in user_lower or 'display' in user_lower:
                command = OSUtils.get_file_read_command(target_file)
                return command
            elif 'head' in user_lower or 'first' in user_lower:
                command = OSUtils.get_file_head_command(target_file, 20)
                return command
            elif 'tail' in user_lower or 'last' in user_lower:
                command = OSUtils.get_file_tail_command(target_file, 20)
                return command
            else:
                # Default to reading the file
                command = OSUtils.get_file_read_command(target_file)
                return command
        
        # No files found, try directory listing
        if 'list' in user_lower or 'show' in user_lower or 'files' in user_lower:
            return OSUtils.get_directory_list_command('.')
        
        return None
    
    def _handle_task_mode(self, task_request: str):
        """Handle task mode request with enhanced progress display and shared context"""
        try:
            if self.verbose:
                # Show context sharing information
                context_count = len(self.history_manager.get_conversation_context(limit=15))
                OSUtils.debug_print(f"Switching to task mode with {context_count} context messages available", True)
            
            # Detect project mode and read existing structure if needed
            project_mode = self._detect_project_mode()
            
            if project_mode == 'edit':
                self.console.print("[dim]📁 Detected existing project - reading current structure...[/dim]")
                self.current_project_structure = self._read_current_directory_structure()
                
                # Display current project structure
                if self.current_project_structure:
                    structure_display = self._format_directory_structure(self.current_project_structure)
                    if structure_display.strip():
                        self.console.print(f"\\n[dim]Current project structure:\\n{structure_display}[/dim]")
                
                # Add existing files to history for context
                existing_files = self._flatten_file_list(self.current_project_structure)
                for file_info in existing_files:
                    self.history_manager.track_file_edit(
                        file_info['full_path'], 
                        "", 
                        "existing"
                    )
                
                self.console.print(f"[dim]🔍 Found {len(existing_files)} existing files[/dim]")
            else:
                self.console.print("[dim]🆕 Creating new project...[/dim]")
                self.current_project_structure = None
            
            # Process task with progress indicators
            raw_response, steps = self.task_processor.process_task(task_request, console=self.console)
            
            # If no steps but response exists, it might be clarifying questions
            if not steps and raw_response:
                # Check if it's clarifying questions (starts with 🤔)
                if "🤔" in raw_response or "clarify" in raw_response.lower():
                    self.console.print("\\n" + raw_response.split("Context usage:")[0].strip())
                    return
            
            # Display task summary and steps
            if steps:
                # Store planned files for this session
                self.current_task_files = [step.target for step in steps if step.action in ['create', 'edit']]
                
                summary = self.task_processor.get_task_summary(steps)
                mode_indicator = "🔧 Editing" if project_mode == 'edit' else "🆕 Creating"
                self.console.print(f"\\n[bold green]✅ {mode_indicator} - {summary}[/bold green]")
                
                # First, show simple step list (required format)
                self.console.print("\\n[bold cyan]Steps:[/bold cyan]")
                for step in steps:
                    if step.action == 'run':
                        self.console.print(f"{step.step_number} - run: {step.target}")
                    else:
                        self.console.print(f"{step.step_number} - {step.action} {step.target}")
                
                # Execute the steps (create files, etc.)
                self.console.print("\\n[bold yellow]Executing steps...[/bold yellow]")
                self._execute_task_steps(steps)
                
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
    
    def _execute_task_steps(self, steps: List[TaskStep]):
        """Execute task steps one by one, calling LLM for each file generation"""
        import os
        import subprocess
        from pathlib import Path
        
        for step in steps:
            try:
                if step.action in ['create', 'edit']:
                    # Generate file content with individual LLM call
                    self.console.print(f"[blue]🧠 Generating {step.target}...[/blue]")
                    
                    file_content = self._generate_file_content(step)
                    
                    if file_content:
                        # Create/edit file
                        file_path = Path(step.target)
                        
                        # Create directory if needed
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write file content
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(file_content)
                        
                        # Show success with preview
                        action_text = "Created" if step.action == "create" else "Updated"
                        self.console.print(f"[green]✅ {action_text} {step.target}[/green]")
                        
                        # Show file preview (first few lines)
                        lines = file_content.split('\\n')[:3]
                        preview = '\\n'.join(lines)
                        if len(lines) >= 3:
                            preview += '\\n...'
                        self.console.print(f"[dim]{preview}[/dim]")
                        
                        # Track in history
                        self.history_manager.track_file_edit(step.target, file_content, step.action)
                        
                    else:
                        self.console.print(f"[red]❌ Failed to generate content for {step.target}[/red]")
                    
                elif step.action == 'run':
                    # Execute commands directly (no LLM needed)
                    if hasattr(step, 'commands') and step.commands:
                        commands = step.commands
                    else:
                        # Extract command from target if commands not set
                        commands = [step.target] if step.target else []
                    
                    for cmd in commands:
                        self.console.print(f"[blue]🔧 Running: {cmd}[/blue]")
                        try:
                            result = subprocess.run(
                                cmd,
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            
                            if result.returncode == 0:
                                self.console.print(f"[green]✅ Command completed successfully[/green]")
                                if result.stdout.strip():
                                    self.console.print(f"[dim]{result.stdout.strip()}[/dim]")
                            else:
                                self.console.print(f"[yellow]⚠️  Command completed with warnings[/yellow]")
                                if result.stderr.strip():
                                    self.console.print(f"[dim]{result.stderr.strip()}[/dim]")
                                    
                        except subprocess.TimeoutExpired:
                            self.console.print(f"[red]❌ Command timed out after 60s[/red]")
                        except Exception as cmd_error:
                            self.console.print(f"[red]❌ Command failed: {cmd_error}[/red]")
                            
            except Exception as e:
                self.console.print(f"[red]❌ Failed to execute step {step.step_number}: {e}[/red]")
        
        self.console.print(f"\\n[bold green]🎉 Task execution completed![/bold green]")
    
    def _generate_file_content(self, step: TaskStep) -> str:
        """Generate file content for a specific step using LLM with conversation context"""
        try:
            # Get project context
            context = self.history_manager.get_project_context()
            existing_files = self.history_manager.get_project_files()
            
            # CRITICAL: Get conversation context for context-aware file generation
            conversation_context = self.history_manager.get_conversation_context(limit=15)
            
            if self.verbose:
                OSUtils.debug_print(f"🔍 File generation using {len(conversation_context)} context messages for {step.target}", True)
            
            # Build specific prompt for this file
            file_prompt = self._build_file_generation_prompt(step, context, existing_files, conversation_context)
            
            # Prepare messages with conversation context
            messages = [
                {"role": "system", "content": self._get_file_generation_system_prompt()}
            ]
            
            # Add conversation context (excluding system messages to avoid conflicts)
            context_without_system = [msg for msg in conversation_context if msg.get("role") != "system"]
            messages.extend(context_without_system)
            
            # Add file generation request
            messages.append({"role": "user", "content": file_prompt})
            
            if self.verbose:
                OSUtils.debug_print(f"🧠 File generation sending {len(messages)} total messages (with conversation context)", True)
            
            # Call LLM using chat() instead of generate() to include conversation context
            with self.console.status(f"[bold blue]Generating {step.target}..."):
                response = self.ollama_client.chat(
                    messages=messages,
                    stream=False,  # Use non-streaming for file generation
                    temperature=0.3
                )
            
            # Extract file content from response
            content = self._extract_file_content_from_response(response.content)
            return content
            
        except Exception as e:
            self.console.print(f"[red]Error generating {step.target}: {e}[/red]")
            return ""
    
    def _build_file_generation_prompt(self, step: TaskStep, context: dict, existing_files: list, conversation_context: list = None) -> str:
        """Build specific prompt for generating a single file with conversation context"""
        prompt_parts = [
            f"GENERATE FILE: {step.target}",
            f"PURPOSE: {step.description}",
            f"ACTION: {step.action.upper()}"
        ]
        
        # CRITICAL: Add conversation context analysis instructions
        if conversation_context:
            prompt_parts.append("\\n🧠 CRITICAL - ANALYZE CONVERSATION CONTEXT ABOVE:")
            prompt_parts.append("- Look for SPECIFIC API endpoints that were analyzed (GET /videos, POST /videos, etc.)")
            prompt_parts.append("- Find EXACT data models and fields mentioned")
            prompt_parts.append("- Identify SPECIFIC business logic and validation rules discussed") 
            prompt_parts.append("- Use EXACT functionality from conversation, NOT generic examples!")
            prompt_parts.append("\\n❗ IMPORTANT: If specific API/code was analyzed in conversation, REPLICATE IT EXACTLY!")
        
        # Add project context (safely handle None context)
        if context and context.get("framework"):
            prompt_parts.append(f"FRAMEWORK: {context['framework']}")
        if context and context.get("language"):
            prompt_parts.append(f"LANGUAGE: {context['language']}")
        if context and context.get("project_type"):
            prompt_parts.append(f"PROJECT_TYPE: {context['project_type']}")
        
        # Add existing project structure if in edit mode
        if self.current_project_structure:
            prompt_parts.append(f"\\nCURRENT PROJECT STRUCTURE (edit mode):")
            structure_display = self._format_directory_structure(self.current_project_structure)
            prompt_parts.append(structure_display)
            
            # List existing files for import context
            existing_project_files = self._flatten_file_list(self.current_project_structure)
            if existing_project_files:
                prompt_parts.append(f"\\nEXISTING FILES (available for import):")
                for file_info in existing_project_files[:20]:  # Limit to first 20
                    prompt_parts.append(f"- {file_info['full_path']}")
                if len(existing_project_files) > 20:
                    prompt_parts.append(f"- ... and {len(existing_project_files) - 20} more files")
        
        # Add existing tracked files
        if existing_files:
            prompt_parts.append(f"\\nTRACKED FILES:")
            for file in existing_files:
                prompt_parts.append(f"- {file}")
        
        # Get all planned files from current task session
        planned_files = self._get_planned_files_from_session()
        if planned_files:
            prompt_parts.append(f"\\nPLANNED PROJECT FILES (use these for imports):")
            for file in planned_files:
                prompt_parts.append(f"- {file}")
        
        # Add expected functions and exports for this file
        expected_info = self._get_expected_file_info(step.target, context, step.description)
        if expected_info:
            prompt_parts.append(f"\\nEXPECTED FILE DETAILS:")
            prompt_parts.append(expected_info)

        # Add folder structure context for new files
        if not self.current_project_structure:
            folder_structure = self._infer_folder_structure(step.target, planned_files)
            if folder_structure:
                prompt_parts.append(f"\\nPLANNED PROJECT STRUCTURE:")
                prompt_parts.append(folder_structure)
        
        # Add file-specific instructions based on extension
        file_ext = step.target.split('.')[-1].lower() if step.target and '.' in step.target else ''
        
        if file_ext in ['py']:
            prompt_parts.append("\\nPYTHON REQUIREMENTS:")
            prompt_parts.append("- Follow PEP8 style")
            prompt_parts.append("- ONLY import from files listed in EXISTING or PLANNED files above")
            prompt_parts.append("- Use relative imports correctly based on folder structure")
            prompt_parts.append("- Add docstrings and comments")
            prompt_parts.append("- Handle errors gracefully")
        elif file_ext in ['js']:
            prompt_parts.append("\\nJAVASCRIPT REQUIREMENTS:")
            prompt_parts.append("- Use modern ES6+ syntax")
            prompt_parts.append("- ONLY require/import files that exist in the project structure")
            prompt_parts.append("- Use proper module syntax (CommonJS or ES6)")
            prompt_parts.append("- Add proper error handling")
            prompt_parts.append("- Include JSDoc comments")
        elif file_ext in ['html']:
            prompt_parts.append("\\nHTML REQUIREMENTS:")
            prompt_parts.append("- Use semantic HTML5")
            prompt_parts.append("- Link only to CSS/JS files that will exist")
            prompt_parts.append("- Include meta tags")
            prompt_parts.append("- Make it responsive")
        elif file_ext in ['css']:
            prompt_parts.append("\\nCSS REQUIREMENTS:")
            prompt_parts.append("- Use modern CSS3")
            prompt_parts.append("- Make it responsive")
            prompt_parts.append("- Include comments")
        elif file_ext in ['json']:
            prompt_parts.append("\\nJSON REQUIREMENTS:")
            prompt_parts.append("- Valid JSON format")
            prompt_parts.append("- Include all necessary fields")
        elif file_ext in ['md']:
            prompt_parts.append("\\nMARKDOWN REQUIREMENTS:")
            prompt_parts.append("- Clear structure with headers")
            prompt_parts.append("- Include examples where relevant")
        
        prompt_parts.append(f"\\nIMPORT CONSISTENCY RULE:")
        prompt_parts.append(f"- Do NOT import/require any files not listed above")
        prompt_parts.append(f"- Use only standard library imports or dependencies from requirements/package.json")
        prompt_parts.append(f"\\nGenerate complete, production-ready content for {step.target}")
        
        return "\\n".join(prompt_parts)
    
    def _get_file_generation_system_prompt(self) -> str:
        """Get system prompt for individual file generation"""
        return """You are an expert software developer generating individual project files with CONTEXT-AWARE implementation.

🧠 CONTEXT-FIRST IMPLEMENTATION - CRITICAL:
1. FIRST: Analyze the CONVERSATION CONTEXT above for specific code/API that was discussed
2. If specific functionality was analyzed (e.g. API endpoints, data models), REPLICATE IT EXACTLY
3. When user analyzed an API with specific endpoints (GET /videos, POST /videos), use THOSE endpoints
4. When specific data models were mentioned, use THOSE exact field names and structures
5. DO NOT create generic examples if specific requirements exist in conversation

CRITICAL RULES:
6. Generate ONLY the file content - no explanations or markdown
7. Write complete, production-ready code
8. Follow best practices for the language/framework
9. ONLY import/require files that are explicitly listed in the context
10. IMPLEMENT ALL functions and exports specified in "EXPECTED FILE DETAILS"
11. Make the code immediately runnable/usable
12. Do NOT include any wrapper text or explanations

IMPORT/DEPENDENCY RULES (CRITICAL):
- NEVER import from files that don't exist in the project structure
- ONLY use imports that are:
  * Standard library modules (os, sys, json, etc.)
  * Dependencies listed in requirements.txt or package.json
  * Files explicitly mentioned in EXISTING or PLANNED files
- Use correct relative imports based on folder structure
- For missing functionality, implement it within the file or use standard libraries

EXPECTED FILE DETAILS COMPLIANCE:
- If "EXPECTED FILE DETAILS" section is provided, follow it exactly
- Implement ALL functions listed in "Functions:" with proper signatures
- Create ALL exports listed in "Exports:" with correct naming
- Include ALL imports listed in "Imports:" (only if they exist in project)
- Follow the architectural pattern and purpose described
- Maintain consistency with expected API and interface

OUTPUT FORMAT:
- Return ONLY the raw file content
- No code blocks, no markdown, no explanations
- The response should be exactly what goes in the file
- Start immediately with file content (no introductory text)

QUALITY STANDARDS:
- Clean, readable code with proper indentation
- Meaningful variable and function names
- Appropriate comments and documentation
- Error handling where necessary
- Security best practices
- Self-contained functionality when external files don't exist

EXAMPLE VIOLATIONS TO AVOID:
- DON'T: from utils import helper (unless utils.py is in project files)
- DON'T: require('./config/database') (unless config/database.js exists)
- DON'T: import custom_module (unless it's explicitly listed)

DO INSTEAD:
- Use standard library: import os, import json, import sqlite3
- Inline simple functions instead of importing non-existent modules
- Use only the files you can see in the project structure

Remember: Your response will be written directly to the file! NO explanatory text!"""
    
    def _extract_file_content_from_response(self, response: str) -> str:
        """Extract clean file content from LLM response"""
        import re
        
        # Handle None or empty response
        if not response:
            return ""
        
        # Remove any markdown code blocks if present
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        code_match = re.search(code_block_pattern, response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Remove any explanatory text before/after code
        lines = response.strip().split('\\n')
        
        # Find the start of actual content (skip explanatory lines)
        start_idx = 0
        for i, line in enumerate(lines):
            # Skip lines that look like explanations
            if (line and (line.startswith(('Here', 'This', 'The file', 'Below', 'I will', 'Let me')) or
                'generate' in line.lower() or 'create' in line.lower())):
                continue
            # Start from first line that looks like code/content
            if line.strip() and not line.startswith('#'):
                start_idx = i
                break
        
        # Find the end of actual content (skip explanatory lines at end)
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if (line and (line.startswith(('That', 'This', 'The above', 'Hope this')) or
                'complete' in line.lower() or 'should work' in line.lower())):
                end_idx = i
            elif line.strip():
                break
        
        # Return the cleaned content
        content_lines = lines[start_idx:end_idx]
        return '\\n'.join(content_lines).strip()
    
    def _get_planned_files_from_session(self) -> list:
        """Get all files planned in the current task session"""
        return self.current_task_files
    
    def _get_expected_file_info(self, filename: str, context: dict, description: str) -> str:
        """Generate expected functions and exports for a specific file"""
        info_parts = []
        
        # Validate inputs to prevent None errors
        if not filename:
            return None
        if not isinstance(context, dict):
            context = {}
        if not description:
            description = ""
        
        # Extract file extension and basename safely
        try:
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            basename = filename.split('/')[-1].split('.')[0].lower()
        except (AttributeError, IndexError):
            return None
        
        # Determine framework and language safely
        framework = (context.get("framework") or "").lower()
        language = (context.get("language") or "").lower()
        
        # Generate expectations based on file type and context
        if framework == "flask" and file_ext == "py":
            if "app.py" in filename or "main.py" in filename:
                info_parts.append("# Main Flask application file")
                info_parts.append("Functions: create_app(), register_blueprints(), init_extensions()")
                info_parts.append("Exports: app (Flask instance)")
                info_parts.append("Imports: Flask, blueprints, database, config")
            elif "models" in filename or "model" in filename:
                info_parts.append("# Database model definitions")
                info_parts.append("Classes: User, Product, Order (inherit from db.Model)")
                info_parts.append("Functions: __init__(), __repr__(), serialize(), validate()")
                info_parts.append("Exports: model classes, db instance")
                info_parts.append("Imports: SQLAlchemy, datetime, bcrypt")
            elif "routes" in filename or "views" in filename:
                info_parts.append("# API route definitions")
                info_parts.append("Functions: route handlers (GET, POST, PUT, DELETE)")
                info_parts.append("Exports: blueprint instance")
                info_parts.append("Imports: Flask Blueprint, models, request, jsonify")
            elif "config" in filename:
                info_parts.append("# Application configuration")
                info_parts.append("Classes: Config, DevelopmentConfig, ProductionConfig")
                info_parts.append("Functions: get_config()")
                info_parts.append("Exports: config classes and variables")
        
        elif framework == "express" and file_ext == "js":
            if "server.js" in filename or "app.js" in filename:
                info_parts.append("# Main Express server file")
                info_parts.append("Functions: startServer(), setupMiddleware(), setupRoutes()")
                info_parts.append("Exports: app (Express instance)")
                info_parts.append("Imports: express, routes, middleware, database config")
            elif "routes" in filename:
                info_parts.append("# Express route definitions")
                info_parts.append("Functions: route handlers (router.get, router.post, etc.)")
                info_parts.append("Exports: router (Express Router)")
                info_parts.append("Imports: express.Router, models, middleware")
            elif "models" in filename or "model" in filename:
                info_parts.append("# Data model definitions")
                info_parts.append("Classes: Mongoose schemas")
                info_parts.append("Functions: schema methods, static methods, instance methods")
                info_parts.append("Exports: model instances")
                info_parts.append("Imports: mongoose")
            elif "middleware" in filename:
                info_parts.append("# Middleware functions")
                info_parts.append("Functions: authentication, validation, error handling")
                info_parts.append("Exports: middleware functions")
                info_parts.append("Imports: jsonwebtoken, bcrypt")
            elif "config" in filename:
                info_parts.append("# Configuration and environment settings")
                info_parts.append("Functions: connection functions, config getters")
                info_parts.append("Exports: configuration objects")
                info_parts.append("Imports: mongoose, dotenv")
        
        elif framework == "react" and file_ext in ["js", "jsx"]:
            if "App.js" in filename:
                info_parts.append("# Main React application component")
                info_parts.append("Component: App (functional component)")
                info_parts.append("Functions: handleNavigation(), useEffect hooks")
                info_parts.append("Exports: App (default export)")
                info_parts.append("Imports: React, components, react-router-dom")
            elif "index.js" in filename and "src" in filename:
                info_parts.append("# React DOM entry point")
                info_parts.append("Functions: render()")
                info_parts.append("Exports: none (entry point)")
                info_parts.append("Imports: React, ReactDOM, App component")
            elif "components" in filename:
                info_parts.append("# Reusable React component")
                info_parts.append(f"Component: {basename.title()} (functional component)")
                info_parts.append("Functions: event handlers, useEffect, useState")
                info_parts.append(f"Exports: {basename.title()} (default export)")
                info_parts.append("Imports: React, hooks, prop-types")
            elif "hooks" in filename:
                info_parts.append("# Custom React hook")
                info_parts.append(f"Hook: use{basename.title()}")
                info_parts.append("Functions: custom hook logic, state management")
                info_parts.append(f"Exports: use{basename.title()} (default export)")
                info_parts.append("Imports: React hooks (useState, useEffect)")
            elif "services" in filename or "api" in filename:
                info_parts.append("# API service functions")
                info_parts.append("Functions: HTTP methods (get, post, put, delete)")
                info_parts.append("Exports: API client object or functions")
                info_parts.append("Imports: axios or fetch")
        
        elif file_ext == "json":
            if "package.json" in filename:
                info_parts.append("# NPM package configuration")
                info_parts.append("Scripts: start, build, test, dev")
                info_parts.append("Dependencies: framework and utility packages")
            elif "config" in filename or "settings" in filename:
                info_parts.append("# JSON configuration file")
                info_parts.append("Structure: nested configuration objects")
        
        elif file_ext in ["html", "htm"]:
            info_parts.append("# HTML template file")
            info_parts.append("Structure: semantic HTML5 elements")
            info_parts.append("Contains: meta tags, scripts, styles")
        
        elif file_ext == "css":
            info_parts.append("# CSS stylesheet")
            info_parts.append("Contains: component styles, responsive design")
            info_parts.append("Structure: organized by components or pages")
        
        elif file_ext == "md":
            info_parts.append("# Markdown documentation")
            info_parts.append("Sections: Installation, Usage, API, Examples")
        
        elif file_ext == "txt" and "requirements" in filename:
            info_parts.append("# Python dependencies list")
            info_parts.append("Format: package==version")
            info_parts.append("Categories: web framework, database, utilities, testing")
        
        # Add generic expectations based on description
        description_lower = description.lower() if description else ""
        if "auth" in description_lower:
            info_parts.append("Authentication focus: login, register, token management")
        if "database" in description_lower or "db" in description_lower:
            info_parts.append("Database focus: connections, models, migrations")
        if "api" in description_lower:
            info_parts.append("API focus: endpoints, validation, responses")
        if "test" in description_lower:
            info_parts.append("Testing focus: unit tests, integration tests, mocks")
        
        return "\\n".join(info_parts) if info_parts else None
    
    def _chat_with_streaming_progress(self, messages: list):
        """Handle normal chat with streaming progress"""
        try:
            # Create progress callback for streaming
            with self.console.status("[bold green]Thinking...") as status:
                current_chunks = 0
                
                def progress_callback(message: str):
                    nonlocal current_chunks
                    if "chunks received" in message:
                        try:
                            current_chunks = int(message.split()[1])
                            status.update(f"[bold green]Thinking... ({current_chunks} chunks)[/bold green]")
                        except:
                            status.update(f"[bold green]Thinking... ({message})[/bold green]")
                    else:
                        status.update(f"[bold green]{message}[/bold green]")
                
                # Try streaming first
                try:
                    return self.ollama_client.chat(
                        messages=messages,
                        system_prompt=self.system_prompt,
                        stream=True,
                        progress_callback=progress_callback
                    )
                except Exception:
                    # Fallback but still use streaming
                    status.update("[bold green]Thinking... (streaming fallback)[/bold green]")
                    return self.ollama_client.chat(
                        messages=messages,
                        system_prompt=self.system_prompt,
                        stream=True
                    )
                    
        except Exception as e:
            self.console.print(f"[red]Error in chat: {e}[/red]")
            # Final fallback - still use streaming
            return self.ollama_client.chat(
                messages=messages,
                system_prompt=self.system_prompt,
                stream=True
            )
    
    def _infer_folder_structure(self, current_file: str, all_files: list) -> str:
        """Infer and display project folder structure"""
        if not all_files:
            return ""
        
        # Build folder tree
        folders = {}
        for file_path in all_files:
            parts = file_path.split('/')
            current_level = folders
            
            # Navigate/create folder structure
            for part in parts[:-1]:  # All except filename
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            
            # Add file to final folder
            filename = parts[-1]
            if '___files___' not in current_level:
                current_level['___files___'] = []
            current_level['___files___'].append(filename)
        
        # Add root level files
        root_files = [f for f in all_files if '/' not in f]
        if root_files:
            folders['___files___'] = root_files
        
        # Generate tree representation
        return self._format_folder_tree(folders, "", True)
    
    def _format_folder_tree(self, folder_dict: dict, prefix: str = "", is_root: bool = False) -> str:
        """Format folder dictionary into tree structure"""
        lines = []
        
        # Get folders and files separately
        subfolders = {k: v for k, v in folder_dict.items() if k != '___files___' and isinstance(v, dict)}
        files = folder_dict.get('___files___', [])
        
        # Add folders first
        folder_items = list(subfolders.items())
        for i, (folder_name, folder_contents) in enumerate(folder_items):
            is_last_folder = (i == len(folder_items) - 1) and not files
            
            # Folder line
            connector = "└── " if is_last_folder else "├── "
            lines.append(f"{prefix}{connector}{folder_name}/")
            
            # Recurse into folder
            extension = "    " if is_last_folder else "│   "
            subfolder_lines = self._format_folder_tree(folder_contents, prefix + extension, False)
            if subfolder_lines:
                lines.append(subfolder_lines)
        
        # Add files
        for i, filename in enumerate(files):
            is_last_file = (i == len(files) - 1)
            connector = "└── " if is_last_file else "├── "
            lines.append(f"{prefix}{connector}{filename}")
        
        return "\\n".join(lines)
    
    def _read_current_directory_structure(self, max_depth: int = 3) -> dict:
        """Read current directory structure including files and folders"""
        import os
        from pathlib import Path
        
        def should_ignore(path: str) -> bool:
            """Check if path should be ignored"""
            ignore_patterns = [
                '.git', '.gitignore', '__pycache__', '.pytest_cache', 'node_modules',
                '.vscode', '.idea', '*.pyc', '*.pyo', '*.pyd', '.DS_Store',
                'Thumbs.db', '*.log', '.env', 'venv', 'env', '.venv',
                'dist', 'build', '*.egg-info', '.coverage', 'coverage.xml'
            ]
            
            path_lower = path.lower()
            for pattern in ignore_patterns:
                if pattern in path_lower or path_lower.endswith(pattern.replace('*', '')):
                    return True
            return False
        
        def read_directory(dir_path: Path, current_depth: int = 0) -> dict:
            """Recursively read directory structure"""
            if current_depth >= max_depth:
                return {}
            
            structure = {'files': [], 'folders': {}}
            
            try:
                for item in sorted(dir_path.iterdir()):
                    if should_ignore(item.name):
                        continue
                    
                    if item.is_file():
                        # Get file info
                        try:
                            size = item.stat().st_size
                            if size < 1024 * 1024:  # Only include files < 1MB
                                structure['files'].append({
                                    'name': item.name,
                                    'path': str(item.relative_to(Path.cwd())),
                                    'size': size
                                })
                        except (OSError, ValueError):
                            continue
                            
                    elif item.is_dir():
                        # Recursively read subdirectory
                        subdir_structure = read_directory(item, current_depth + 1)
                        if subdir_structure.get('files') or subdir_structure.get('folders'):
                            structure['folders'][item.name] = subdir_structure
            
            except (PermissionError, OSError):
                pass
            
            return structure
        
        return read_directory(Path.cwd())
    
    def _format_directory_structure(self, structure: dict, prefix: str = "", is_root: bool = True) -> str:
        """Format directory structure into readable tree format"""
        lines = []
        
        # Get folders and files
        folders = structure.get('folders', {})
        files = structure.get('files', [])
        
        # Add folders first
        folder_items = list(folders.items())
        for i, (folder_name, folder_contents) in enumerate(folder_items):
            is_last_folder = (i == len(folder_items) - 1) and not files
            
            # Folder line
            connector = "└── " if is_last_folder else "├── "
            lines.append(f"{prefix}{connector}{folder_name}/")
            
            # Recurse into folder
            extension = "    " if is_last_folder else "│   "
            subfolder_lines = self._format_directory_structure(folder_contents, prefix + extension, False)
            if subfolder_lines:
                lines.append(subfolder_lines)
        
        # Add files
        for i, file_info in enumerate(files):
            is_last_file = (i == len(files) - 1)
            connector = "└── " if is_last_file else "├── "
            filename = file_info['name']
            lines.append(f"{prefix}{connector}{filename}")
        
        return "\\n".join(lines)
    
    def _detect_project_mode(self) -> str:
        """Detect if we're in create or edit mode based on current directory"""
        structure = self._read_current_directory_structure(max_depth=2)
        
        # Check for common project indicators
        project_indicators = [
            'package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml',
            'pom.xml', 'build.gradle', 'composer.json', 'go.mod', 'Gemfile'
        ]
        
        all_files = self._flatten_file_list(structure)
        
        # If we find project files, we're likely in edit mode
        for indicator in project_indicators:
            if any(f['name'] == indicator for f in all_files):
                return 'edit'
        
        # If there are multiple code files, probably edit mode
        code_files = [f for f in all_files if f['name'].endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'))]
        if len(code_files) >= 3:
            return 'edit'
        
        # Otherwise, assume create mode
        return 'create'
    
    def _flatten_file_list(self, structure: dict, current_path: str = "") -> list:
        """Flatten directory structure into a list of all files with paths"""
        files = []
        
        # Add files in current directory
        for file_info in structure.get('files', []):
            file_copy = file_info.copy()
            file_copy['full_path'] = os.path.join(current_path, file_info['name']) if current_path else file_info['name']
            files.append(file_copy)
        
        # Recursively add files from subdirectories
        for folder_name, folder_contents in structure.get('folders', {}).items():
            subpath = os.path.join(current_path, folder_name) if current_path else folder_name
            files.extend(self._flatten_file_list(folder_contents, subpath))
        
        return files
    
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
  • /debug, /dbg    - Show debug info OR toggle debug mode
                      /debug true/on/enable  - Enable debug mode
                      /debug false/off/disable - Disable debug mode
                      /debug info/show - Show debug information
  • /scan, /structure - Show current directory structure
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
    
    def _handle_debug_command(self, user_input: str):
        """Handle debug command with optional parameters"""
        parts = user_input.strip().split()
        
        if len(parts) == 1:
            # Just '/debug' - show debug info
            self._show_debug_info()
        elif len(parts) == 2:
            param = parts[1].lower()
            if param in ['true', 'on', '1', 'yes', 'enable']:
                # Enable debug mode
                old_verbose = self.verbose
                self.verbose = True
                
                if old_verbose:
                    self.console.print("[yellow]🔧 Debug mode was already enabled[/yellow]")
                else:
                    self.console.print("[green]🔧 Debug mode enabled![/green]")
                    OSUtils.debug_print("Debug mode activated by user command", True)
                
            elif param in ['false', 'off', '0', 'no', 'disable']:
                # Disable debug mode
                old_verbose = self.verbose
                if old_verbose:
                    OSUtils.debug_print("Debug mode being deactivated by user command", True)
                
                self.verbose = False
                
                if old_verbose:
                    self.console.print("[yellow]🔧 Debug mode disabled[/yellow]")
                else:
                    self.console.print("[yellow]🔧 Debug mode was already disabled[/yellow]")
                    
            elif param in ['info', 'show', 'status']:
                # Show debug info
                self._show_debug_info()
            else:
                self.console.print(f"[red]Unknown debug parameter: {param}[/red]")
                self.console.print("[dim]Valid options: true/false/on/off/enable/disable/info/show[/dim]")
        else:
            self.console.print("[red]Usage: /debug [true|false|on|off|enable|disable|info|show][/red]")
    
    def _show_debug_info(self):
        """Show comprehensive debug information including OS and platform details"""
        import platform
        
        # Get Ollama health info
        health = self.ollama_client.health_check()
        
        # Get OS commands
        os_commands = OSUtils.get_available_commands()
        
        debug_text = f"""
🖥️  PLATFORM INFO:
OS: {OSUtils.get_platform().upper()} ({platform.system()} {platform.release()})
Architecture: {platform.machine()}
Python: {platform.python_version()}
Windows: {OSUtils.is_windows()}
Unix-like: {OSUtils.is_unix_like()}

🔌 OLLAMA CONNECTION:
Connected: {'✅ Yes' if health['connected'] else '❌ No'}
Endpoint: {health['endpoint']}
Current Model: {health.get('current_model', 'None')}
Available Models: {health.get('models_available', 0)}

📂 WORKING DIRECTORY:
Path: {os.getcwd()}
Tracked Files: {len(self.history_manager.get_project_files())}
Conversation Messages: {len(self.history_manager.conversation_history)}

⚙️  OS COMMANDS AVAILABLE:
• Read File: {os_commands.get('read_file', 'N/A')}
• List Dir: {os_commands.get('list_dir', 'N/A')}
• Search File: {os_commands.get('search_file', 'N/A')}
• Head File: {os_commands.get('head_file', 'N/A')}
• Tail File: {os_commands.get('tail_file', 'N/A')}

🤖 AI PROMPT SYSTEM:
Chat Prompt Length: {len(PromptManager.get_chat_system_prompt())} chars
Task Prompt Length: {len(PromptManager.get_task_system_prompt_full_project())} chars
Command Prompt Length: {len(PromptManager.get_command_generation_prompt())} chars

⚡ DEBUG/VERBOSE MODE: {'✅ ENABLED' if self.verbose else '❌ DISABLED'}

📝 DEBUG ACTIONS AVAILABLE:
• OSUtils.debug_print() outputs when verbose=True
• Detailed error information and stack traces
• Command processing debug information
• AI response timing and context details
        """
        
        self.console.print(Panel(debug_text.strip(), title="🔧 Debug Information", border_style="cyan"))
    
    def _show_project_structure(self):
        """Show current project directory structure"""
        try:
            structure = self._read_current_directory_structure()
            project_mode = self._detect_project_mode()
            
            if structure:
                structure_display = self._format_directory_structure(structure)
                all_files = self._flatten_file_list(structure)
                
                mode_text = "🔧 Edit Mode" if project_mode == 'edit' else "🆕 Create Mode"
                
                info_text = f"""
{mode_text} - Current Directory Structure

{structure_display}

📊 Summary:
• Total files: {len(all_files)}
• Code files: {len([f for f in all_files if f['name'].endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'))])}
• Config files: {len([f for f in all_files if f['name'] in ['package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml']])}
• Mode detected: {project_mode}
                """
                
                self.console.print(Panel(info_text.strip(), title="Project Structure", border_style="cyan"))
            else:
                self.console.print("[yellow]No files found in current directory or unable to read structure.[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Error reading project structure: {e}[/red]")
    
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
    

