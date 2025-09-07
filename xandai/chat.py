"""
XandAI - Chat REPL Interface
Interactive REPL with terminal command interception and LLM integration
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from xandai.core.app_state import AppState
from xandai.history import HistoryManager
from xandai.integrations.base_provider import LLMProvider, LLMResponse
from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.task import TaskProcessor, TaskStep
from xandai.utils.os_utils import OSUtils
from xandai.utils.prompt_manager import PromptManager
from xandai.web.web_manager import WebManager


class IntelligentCompleter(Completer):
    """Smart completer that provides context-aware suggestions"""

    def __init__(self):
        self.slash_commands = [
            "/task",
            "/help",
            "/h",
            "/clear",
            "/cls",
            "/history",
            "/hist",
            "/context",
            "/ctx",
            "/status",
            "/stat",
            "/scan",
            "/structure",
            "/interactive",
            "/toggle",
            "/provider",
            "/providers",
            "/switch",
            "/detect",
            "/server",
            "/models",
            "/exit",
            "/quit",
            "/bye",
        ]

        # Commands that need directory suggestions
        self.dir_commands = ["cd", "mkdir", "rmdir", "pushd", "popd"]

        # Commands that need file suggestions
        self.file_commands = [
            "cat",
            "type",
            "nano",
            "vim",
            "edit",
            "open",
            "head",
            "tail",
            "less",
            "more",
        ]

        # Commands that need both files and directories
        self.path_commands = [
            "ls",
            "dir",
            "cp",
            "copy",
            "mv",
            "move",
            "rm",
            "del",
            "find",
            "grep",
            "findstr",
            "tree",
            "du",
            "chmod",
            "chown",
            "stat",
        ]

        # All terminal commands
        self.terminal_commands = [
            # Sistema operacional básico
            "ls",
            "dir",
            "cd",
            "pwd",
            "cat",
            "type",
            "mkdir",
            "rmdir",
            "rm",
            "del",
            "cp",
            "copy",
            "mv",
            "move",
            "ren",
            "rename",
            "find",
            "findstr",
            "grep",
            "ps",
            "tasklist",
            "kill",
            "taskkill",
            "ping",
            "tracert",
            "netstat",
            "ipconfig",
            "ifconfig",
            "echo",
            "tree",
            "which",
            "where",
            "date",
            "time",
            "cls",
            "clear",
            "help",
            "man",
            "history",
            "alias",
            # Python
            "python",
            "python3",
            "py",
            "pip",
            "pip3",
            "pipenv",
            "poetry",
            "conda",
            "mamba",
            "pyenv",
            "virtualenv",
            "venv",
            "activate",
            "deactivate",
            # JavaScript/Node.js
            "node",
            "npm",
            "yarn",
            "pnpm",
            "bun",
            "deno",
            "npx",
            "nvm",
            "fnm",
            # Java
            "java",
            "javac",
            "jar",
            "maven",
            "mvn",
            "gradle",
            "gradlew",
            "ant",
            # C/C++
            "gcc",
            "g++",
            "clang",
            "clang++",
            "make",
            "cmake",
            "ninja",
            # C#/.NET
            "dotnet",
            "csc",
            "msbuild",
            "nuget",
            # Go
            "go",
            "gofmt",
            "goimports",
            "mod",
            # Rust
            "rustc",
            "cargo",
            "rustup",
            "rustfmt",
            # Ruby
            "ruby",
            "gem",
            "bundle",
            "rails",
            "rake",
            "rbenv",
            "rvm",
            # PHP
            "php",
            "composer",
            "artisan",
            "phpunit",
            # Swift
            "swift",
            "swiftc",
            "xcodebuild",
            # Kotlin
            "kotlin",
            "kotlinc",
            # Scala
            "scala",
            "scalac",
            "sbt",
            # Lua
            "lua",
            "luac",
            # Perl
            "perl",
            "cpan",
            "cpanm",
            # R
            "r",
            "rscript",
            # Julia
            "julia",
            # Haskell
            "ghc",
            "ghci",
            "cabal",
            "stack",
            # Databases
            "mysql",
            "psql",
            "sqlite3",
            "mongo",
            "redis-cli",
            "sqlcmd",
            # DevOps e Cloud
            "docker",
            "kubectl",
            "helm",
            "terraform",
            "ansible",
            "aws",
            "az",
            "gcloud",
            "heroku",
            "vercel",
            "netlify",
            # Version Control
            "git",
            "svn",
            "hg",
            "bzr",
            # Build Tools
            "webpack",
            "vite",
            "rollup",
            "parcel",
            "esbuild",
            "tsc",
            "babel",
            "grunt",
            "gulp",
            "bower",
            # Linting e Testing
            "eslint",
            "prettier",
            "jest",
            "mocha",
            "karma",
            "cypress",
            "pytest",
            "unittest",
            "nose",
            "tox",
            # Editores de terminal
            "vim",
            "vi",
            "nvim",
            "nano",
            "emacs",
            "micro",
            "joe",
            # Monitoramento e Performance
            "top",
            "htop",
            "iotop",
            "vmstat",
            "iostat",
            "free",
            "df",
            "du",
            "nproc",
            "lscpu",
            "lsblk",
            "lsusb",
            "lspci",
            # Rede
            "curl",
            "wget",
            "ssh",
            "scp",
            "rsync",
            "ftp",
            "sftp",
            "nslookup",
            "dig",
            "host",
            "whois",
            # Compressão
            "tar",
            "zip",
            "unzip",
            "gzip",
            "gunzip",
            "7z",
            "rar",
            "unrar",
            # Text processing
            "sed",
            "awk",
            "sort",
            "uniq",
            "wc",
            "head",
            "tail",
            "cut",
            "tr",
            # Process management
            "nohup",
            "screen",
            "tmux",
            "systemctl",
            "service",
            "crontab",
            # Environment
            "env",
            "export",
            "set",
            "unset",
            "printenv",
            "source",
            # Permissions
            "chmod",
            "chown",
            "chgrp",
            "su",
            "sudo",
            "whoami",
            "id",
            # Archives and packages
            "apt",
            "apt-get",
            "yum",
            "dnf",
            "zypper",
            "pacman",
            "brew",
            "choco",
            "snap",
            "flatpak",
            "rpm",
            "dpkg",
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
            if current_line.startswith("/"):
                yield from self._get_slash_completions(current_line)
                return

            # If typing a terminal command with arguments
            if len(words) >= 1:
                command = words[0].lower()

                # Get the current word being typed
                current_word = ""
                if current_line.endswith(" "):
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
                elif len(words) == 1 and not current_line.endswith(" "):
                    # Still typing the command itself
                    yield from self._get_command_completions(current_word)
                elif len(words) == 1 and current_line.endswith(" "):
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
        suggestions = self.slash_commands + ["help", "clear", "exit", "quit"]
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
        all_commands = self.terminal_commands + self.slash_commands + ["help", "clear", "exit"]
        for cmd in all_commands:
            if cmd.lower().startswith(prefix.lower()):
                yield Completion(cmd, start_position=-len(prefix))

    def _get_directory_completions(self, prefix: str):
        """Get directory completions"""
        try:
            current_dir = Path.cwd()

            # Handle relative paths
            if "/" in prefix or "\\" in prefix:
                # Extract directory part
                path_parts = prefix.replace("\\", "/").split("/")
                dir_part = "/".join(path_parts[:-1])
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
                    if item.is_dir() and not item.name.startswith("."):
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
            if "/" in prefix or "\\" in prefix:
                path_parts = prefix.replace("\\", "/").split("/")
                dir_part = "/".join(path_parts[:-1])
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
                    if item.is_file() and not item.name.startswith("."):
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

    def __init__(
        self,
        llm_provider: LLMProvider,
        history_manager: HistoryManager,
        verbose: bool = False,
    ):
        """Initialize Chat REPL"""
        self.llm_provider = llm_provider
        self.history_manager = history_manager
        self.verbose = verbose
        self.interactive_mode = True  # Default to interactive mode

        # Rich console for pretty output
        self.console = Console()

        # Initialize app state for configuration
        self.app_state = AppState()

        # Task processor (with shared verbose mode)
        self.task_processor = TaskProcessor(llm_provider, history_manager, verbose)

        # Web integration manager
        self.web_manager = WebManager(
            enabled=self.app_state.get_preference("web_integration_enabled", False),
            timeout=self.app_state.get_preference("web_request_timeout", 10),
            max_links=self.app_state.get_preference("max_links_per_request", 3),
        )

        # Prompt session with history and completion
        self.session = PromptSession(
            history=InMemoryHistory(),
            completer=IntelligentCompleter(),
            complete_while_typing=False,
        )

        # Terminal commands we intercept and run locally (Windows + Linux/macOS)
        self.terminal_commands = {
            # Directory/File listing
            "ls",
            "dir",
            # Navigation
            "pwd",
            "cd",
            # File operations
            "cat",
            "type",
            "head",
            "tail",
            "more",
            "less",
            "mkdir",
            "rmdir",
            "rm",
            "del",
            "erase",
            "cp",
            "copy",
            "mv",
            "move",
            "ren",
            "rename",
            # Search and text processing
            "find",
            "findstr",
            "grep",
            "wc",
            "sort",
            "uniq",
            # System info
            "ps",
            "tasklist",
            "top",
            "df",
            "du",
            "free",
            "uname",
            "whoami",
            "date",
            "time",
            "systeminfo",
            "ver",
            "hostname",
            # Network
            "ping",
            "tracert",
            "traceroute",
            "netstat",
            "ipconfig",
            "ifconfig",
            # Process management
            "kill",
            "taskkill",
            "killall",
            # File attributes
            "chmod",
            "chown",
            "attrib",
            "icacls",
            # Utilities
            "echo",
            "which",
            "where",
            "whereis",
            "tree",
            "file",
            # Clear screen
            "clear",
            "cls",
            # Help
            "help",
            "man",
            # ===== COMANDOS DE DESENVOLVIMENTO ADICIONADOS =====
            # Python
            "python",
            "python3",
            "py",
            "pip",
            "pip3",
            "pipenv",
            "poetry",
            "conda",
            "mamba",
            "pyenv",
            "virtualenv",
            "venv",
            "activate",
            "deactivate",
            # JavaScript/Node.js
            "node",
            "npm",
            "yarn",
            "pnpm",
            "bun",
            "deno",
            "npx",
            "nvm",
            "fnm",
            # Java
            "java",
            "javac",
            "jar",
            "maven",
            "mvn",
            "gradle",
            "gradlew",
            "ant",
            # C/C++
            "gcc",
            "g++",
            "clang",
            "clang++",
            "make",
            "cmake",
            "ninja",
            # C#/.NET
            "dotnet",
            "csc",
            "msbuild",
            "nuget",
            # Go
            "go",
            "gofmt",
            "goimports",
            "mod",
            # Rust
            "rustc",
            "cargo",
            "rustup",
            "rustfmt",
            # Ruby
            "ruby",
            "gem",
            "bundle",
            "rails",
            "rake",
            "rbenv",
            "rvm",
            # PHP
            "php",
            "composer",
            "artisan",
            "phpunit",
            # Git and version control
            "git",
            "hg",
            "svn",
            "bzr",
            # Text editors
            "nano",
            "vim",
            "emacs",
            "vi",
            "code",
            "notepad",
            # Container and deployment
            "docker",
            "podman",
            "kubectl",
            "helm",
            "terraform",
            "vagrant",
            # Network tools
            "curl",
            "wget",
            "ssh",
            "scp",
            "rsync",
            "nc",
            "telnet",
            "nmap",
            # Archive tools
            "tar",
            "gzip",
            "gunzip",
            "zip",
            "unzip",
            "rar",
            "unrar",
            "7z",
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
                # Simple prompt without highlighting
                prompt_text = "xandai> "

                # Get user input
                try:
                    user_input = self.session.prompt(prompt_text).strip()
                except (EOFError, KeyboardInterrupt):
                    break

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    break
                elif user_input.lower() == "help":
                    self._show_help()
                    continue
                elif user_input.lower() in ["clear", "cls"]:
                    self._clear_screen()
                    continue
                elif user_input.lower() == "history":
                    self._show_conversation_history()
                    continue
                elif user_input.lower() == "context":
                    self._show_project_context()
                    continue
                elif user_input.lower() == "status":
                    self._show_status()
                    continue

                # Process the input
                self._process_input(user_input)

        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("👋 Goodbye!")

    def _process_input(self, user_input: str):
        """Process user input - special commands, terminal commands, task mode, or LLM chat"""

        if self.verbose:
            OSUtils.debug_print(
                f"Processing input: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'",
                True,
            )

        # Check for special slash commands first
        if user_input.startswith("/"):
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
            OSUtils.debug_print(
                f"Sending to LLM for chat processing with {context_count} context messages (includes any recent task history)",
                True,
            )
        self._handle_chat(user_input)

    def _handle_slash_command(self, user_input: str) -> bool:
        """
        Handle special slash commands

        Returns:
            bool: True if command was handled, False otherwise
        """
        command = user_input.lower().strip()

        # Exit commands
        if command in ["/exit", "/quit", "/bye"]:
            raise KeyboardInterrupt()  # Will be caught by main loop

        # Web integration toggle
        if command == "/web":
            self._handle_web_command()
            return True

        if command.startswith("/web "):
            self._handle_web_command(user_input[5:].strip())
            return True

        # Task mode
        if command.startswith("/task "):
            task_request = user_input[6:].strip()
            if task_request:
                self._handle_task_mode(task_request)
            else:
                self.console.print("[yellow]Usage: /task <description>[/yellow]")
            return True

        # Help command
        if command in ["/help", "/h"]:
            self._show_help()
            return True

        # Clear screen
        if command in ["/clear", "/cls"]:
            self._clear_screen()
            return True

        # History command
        if command in ["/history", "/hist"]:
            self._show_conversation_history()
            return True

        # Context command
        if command in ["/context", "/ctx"]:
            self._show_project_context()
            return True

        # Status command
        if command in ["/status", "/stat"]:
            self._show_status()
            return True

        # Debug command - show OS and platform debug information or toggle debug mode
        if command.startswith("/debug") or command.startswith("/dbg"):
            self._handle_debug_command(user_input)
            return True

        # Scan current directory structure
        if command in ["/scan", "/structure"]:
            self._show_project_structure()
            return True

        # Interactive mode toggle
        if command in ["/interactive", "/toggle"]:
            self._toggle_interactive_mode()
            return True

        # Provider management commands
        if command in ["/provider"]:
            self._show_provider_status()
            return True

        if command in ["/providers"]:
            self._list_available_providers()
            return True

        if command.startswith("/switch "):
            provider_name = user_input[8:].strip()
            if provider_name:
                self._switch_provider(provider_name)
            else:
                self.console.print("[yellow]Usage: /switch <provider>[/yellow]")
                self.console.print("[dim]Available: ollama, lm_studio[/dim]")
            return True

        if command in ["/detect"]:
            self._auto_detect_provider()
            return True

        if command.startswith("/server "):
            server_url = user_input[8:].strip()
            if server_url:
                self._set_server_endpoint(server_url)
            else:
                self.console.print("[yellow]Usage: /server <url>[/yellow]")
                self.console.print("[dim]Example: /server http://localhost:11434[/dim]")
            return True

        if command in ["/models"]:
            self._list_and_select_models()
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
                role="user", content=command, metadata={"type": "terminal_command"}
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

            if command_name == "cd":
                self._handle_cd_command(command_parts)
                return
            elif command_name in ["cls", "clear"]:
                self._handle_clear_command(command)
                return

            # Check if command might be interactive
            if self._is_potentially_interactive_command(command):
                self._handle_interactive_command(command)
                return

            # Execute other commands with shorter timeout for non-interactive
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace problematic chars instead of crashing
                timeout=10,  # Shorter timeout to detect hanging commands
            )

            # Format output
            if result.returncode == 0:
                output = (
                    result.stdout.strip() if result.stdout else "Command completed successfully"
                )
                wrapped_output = f"<commands_output>\\n{output}\\n</commands_output>"

                self.console.print(
                    Panel(
                        output if output else "[dim]Command completed[/dim]",
                        title=f"Command: {command}",
                        border_style="green",
                    )
                )
            else:
                error_output = (
                    result.stderr.strip()
                    if result.stderr
                    else f"Command failed with code {result.returncode}"
                )
                wrapped_output = f"<commands_output>\\nError: {error_output}\\n</commands_output>"

                self.console.print(
                    Panel(
                        f"[red]{error_output}[/red]",
                        title=f"Command Failed: {command}",
                        border_style="red",
                    )
                )

            # Add result to history
            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_output", "return_code": result.returncode},
            )

        except subprocess.TimeoutExpired:
            # Command might be interactive, offer to run in interactive mode
            self.console.print(f"[yellow]⚠️  Command timed out - might need user input[/yellow]")
            self.console.print(
                f"[cyan]💡 Tip: Use 'python -i script.py' for interactive scripts[/cyan]"
            )

            error_msg = "Command timed out (10s limit) - possibly waiting for input"
            self.history_manager.add_conversation(
                role="system",
                content=f"<commands_output>\\n{error_msg}\\n</commands_output>",
                metadata={"type": "command_timeout"},
            )
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self.console.print(f"[red]{error_msg}[/red]")
            self.history_manager.add_conversation(
                role="system",
                content=f"<commands_output>\\n{error_msg}\\n</commands_output>",
                metadata={"type": "command_error"},
            )

    def _is_potentially_interactive_command(self, command: str) -> bool:
        """Detect if a command might require user input"""
        interactive_patterns = [
            # Python scripts that might use input()
            r"python\s+\w+\.py",
            r"python3\s+\w+\.py",
            r"py\s+\w+\.py",
            # Node.js scripts that might use readline
            r"node\s+\w+\.js",
            # Interactive shells
            r"^python$",
            r"^python3$",
            r"^node$",
            # Other interactive programs
            r"^npm\s+init",
            r"^git\s+rebase\s+-i",
        ]

        command_lower = command.lower().strip()
        for pattern in interactive_patterns:
            if re.search(pattern, command_lower):
                return True
        return False

    def _handle_interactive_command(self, command: str):
        """Handle potentially interactive commands with user confirmation"""
        self.console.print(f"[yellow]🤖 This command might need user input[/yellow]")
        self.console.print(f"[cyan]Command: {command}[/cyan]")
        self.console.print()

        # Give user options
        self.console.print("[bold]Choose execution mode:[/bold]")
        self.console.print("  [green]1[/green] - Run with full terminal access (interactive)")
        self.console.print("  [blue]2[/blue] - Run with output capture (non-interactive)")
        self.console.print("  [red]3[/red] - Cancel")

        try:
            choice = input("\n[cyan]Your choice (1-3): [/cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "3"

        if choice == "1":
            self._execute_interactive_command(command)
        elif choice == "2":
            self._execute_non_interactive_command(command)
        else:
            self.console.print("[yellow]Command cancelled[/yellow]")

    def _execute_interactive_command(self, command: str):
        """Execute command with full terminal access"""
        self.console.print(f"[green]🚀 Running interactively: {command}[/green]")
        self.console.print("[dim]Press Ctrl+C to return to XandAI if needed[/dim]")
        self.console.print()

        try:
            # Run with full terminal access - no output capture
            result = subprocess.run(command, shell=True, encoding="utf-8", errors="replace")

            if result.returncode == 0:
                self.console.print(f"[green]✅ Command completed successfully[/green]")
                output_msg = "Command executed interactively - output shown above"
            else:
                self.console.print(
                    f"[yellow]⚠️  Command completed with exit code {result.returncode}[/yellow]"
                )
                output_msg = f"Interactive command completed with exit code {result.returncode}"

            # Add to history
            self.history_manager.add_conversation(
                role="system",
                content=f"<commands_output>\\n{output_msg}\\n</commands_output>",
                metadata={
                    "type": "interactive_command",
                    "return_code": result.returncode,
                },
            )

        except KeyboardInterrupt:
            self.console.print("\\n[yellow]Command interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error running interactive command: {e}[/red]")

    def _execute_non_interactive_command(self, command: str):
        """Execute command with output capture (might fail for interactive scripts)"""
        self.console.print(f"[blue]📤 Running with output capture: {command}[/blue]")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,  # Very short timeout
                input="",  # Empty input to avoid hanging
            )

            # Format output normally
            if result.returncode == 0:
                output = result.stdout.strip() if result.stdout else "Command completed"
                self.console.print(Panel(output, title=f"Output: {command}", border_style="green"))
            else:
                error = (
                    result.stderr.strip() if result.stderr else f"Exit code: {result.returncode}"
                )
                self.console.print(Panel(f"[red]{error}[/red]", title="Error", border_style="red"))

        except subprocess.TimeoutExpired:
            self.console.print("[red]❌ Command timed out waiting for input[/red]")
            self.console.print(
                "[cyan]💡 Try option 1 (interactive mode) for scripts that need input[/cyan]"
            )

    def _handle_cd_command(self, command_parts: List[str]):
        """Handle cd command specially to change working directory"""
        try:
            if len(command_parts) == 1:
                # cd with no args - go to home
                new_dir = str(Path.home())
            else:
                # Join all arguments after the command to handle paths with spaces
                new_dir = " ".join(command_parts[1:])

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
                metadata={"type": "cd_command", "old_dir": old_dir, "new_dir": new_dir},
            )

        except Exception as e:
            error_msg = f"cd: {e}"
            wrapped_output = f"<commands_output>\\nError: {error_msg}\\n</commands_output>"
            self.console.print(f"[red]{error_msg}[/red]")

            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_error"},
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
                metadata={"type": "clear_command"},
            )

            self.console.print("[dim]Screen cleared[/dim]")

        except Exception as e:
            error_msg = f"Clear command error: {e}"
            wrapped_output = f"<commands_output>\\nError: {error_msg}\\n</commands_output>"
            self.console.print(f"[red]{error_msg}[/red]")

            self.history_manager.add_conversation(
                role="system",
                content=wrapped_output,
                metadata={"type": "command_error"},
            )

    def _handle_chat(self, user_input: str):
        """Handle LLM chat conversation with intelligent command generation"""
        try:
            if self.verbose:
                OSUtils.debug_print(
                    f"Starting chat processing for {len(user_input)} character input",
                    True,
                )

            # Process web integration if enabled
            web_result = self.web_manager.process_user_input(user_input)

            if web_result.success and web_result.extracted_contents:
                if self.verbose:
                    OSUtils.debug_print(
                        f"Web integration: processed {web_result.processing_info.get('successful_extractions', 0)} links",
                        True,
                    )

                # Show user what web content was found
                self._display_web_integration_info(web_result)

                # Use enhanced input with web context
                processed_input = web_result.processed_text
            else:
                processed_input = user_input

            # Add user message to history (original input for history tracking)
            self.history_manager.add_conversation(
                role="user", content=user_input, metadata={"type": "chat"}
            )

            # Check if we need to generate commands first (two-stage processing)
            command_output = ""
            if self._should_generate_commands(user_input):
                if self.verbose:
                    OSUtils.debug_print(
                        "Detected need for command generation - using two-stage LLM processing",
                        True,
                    )

                command_output = self._generate_and_execute_commands(user_input)

            # Get conversation context
            context_messages = self.history_manager.get_conversation_context(limit=20)

            if self.verbose:
                OSUtils.debug_print(
                    f"Retrieved {len(context_messages)} context messages from history",
                    True,
                )

            # Add current user input (use processed input with web context if available)
            context_messages.append({"role": "user", "content": processed_input})

            # If we have command output, add it as additional context
            if command_output:
                if self.verbose:
                    OSUtils.debug_print(
                        f"Adding command output as context: {len(command_output)} characters",
                        True,
                    )

                context_messages.append(
                    {
                        "role": "system",
                        "content": f"Command execution results for context:\n\n{command_output}",
                    }
                )

            if self.verbose:
                OSUtils.debug_print(f"Sending {len(context_messages)} total messages to LLM", True)

            # Show thinking indicator with streaming
            response = self._chat_with_streaming_progress(context_messages)

            if self.verbose:
                OSUtils.debug_print(f"Received response: {len(response.content)} characters", True)

            # Display response with syntax highlighting for code and execution confirmation
            self._display_response(response.content, allow_execution=True)

            # Display context usage
            self.console.print(f"[dim]{response.context_usage}[/dim]")

            # Add response to history
            self.history_manager.add_conversation(
                role="assistant",
                content=response.content,
                context_usage=str(response.context_usage),
                metadata={"type": "chat"},
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
            "read",
            "show",
            "display",
            "examine",
            "analyze",
            "describe",
            "look at",
            "check",
            "view",
            "see",
            "tell me about",
            "explain",
            "what is in",
            "contents of",
            "open",
            "cat",
            "type",
        ]

        # File-related keywords
        file_keywords = [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".kt",
            ".swift",
            ".css",
            ".html",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".md",
            ".txt",
            ".log",
            "file",
            "script",
            "code",
            "source",
            "app.py",
            "main.py",
            "index.js",
            "package.json",
            "requirements.txt",
            "config",
        ]

        user_lower = user_input.lower()

        # Check if we have both read intent and file references
        has_read_intent = any(keyword in user_lower for keyword in read_keywords)
        has_file_reference = any(keyword in user_lower for keyword in file_keywords)

        if self.verbose and (has_read_intent or has_file_reference):
            OSUtils.debug_print(
                f"Command generation analysis: read_intent={has_read_intent}, file_ref={has_file_reference}",
                True,
            )

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
                    OSUtils.debug_print(
                        "Using non-streaming for command generation to ensure reliability",
                        True,
                    )

                command_response = self.llm_provider.chat(
                    messages=command_messages,
                    stream=False,  # Use non-streaming for command generation to avoid "Extra data" JSON issues
                )

                if self.verbose:
                    OSUtils.debug_print(
                        f"Command LLM response: {len(command_response.content)} chars",
                        True,
                    )

            except Exception as e:
                if self.verbose:
                    OSUtils.debug_print(f"Command generation LLM error: {e}", True)
                    OSUtils.debug_print("Trying with minimal system prompt as final fallback", True)

                # Try with simpler system prompt as final fallback
                try:
                    simple_command_messages = [
                        {
                            "role": "user",
                            "content": f"Generate a Windows command to read the file mentioned in: {user_input}",
                        }
                    ]

                    command_response = self.llm_provider.chat(
                        messages=simple_command_messages, stream=False
                    )
                    if self.verbose:
                        OSUtils.debug_print(
                            "Command generation succeeded with simple fallback", True
                        )
                except Exception as fallback_error:
                    if self.verbose:
                        OSUtils.debug_print(
                            f"All command generation methods failed: {fallback_error}",
                            True,
                        )
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
                    OSUtils.debug_print(
                        f"Executing command {i}/{len(commands)}: {command[:50]}...",
                        True,
                    )

                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        cwd=os.getcwd(),
                        timeout=30,
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
                OSUtils.debug_print(
                    f"Step 3: Collected {len(output)} characters of command output",
                    True,
                )

            return output

        except Exception as e:
            if self.verbose:
                OSUtils.debug_print(f"Error in command generation/execution: {e}", True)
            return ""

    def _extract_commands_from_response(self, response_content: str) -> list:
        """Extract commands from LLM response that are in <commands> blocks"""
        import re

        if self.verbose:
            OSUtils.debug_print(
                f"Extracting commands from response: {response_content[:200]}...", True
            )

        # Find all <commands>...</commands> blocks
        pattern = r"<commands>\s*(.*?)\s*</commands>"
        matches = re.findall(pattern, response_content, re.DOTALL | re.IGNORECASE)

        commands = []
        for match in matches:
            # Split by newlines and filter empty lines
            lines = [line.strip() for line in match.split("\n") if line.strip()]
            # Filter out comments and empty lines
            filtered_lines = [
                line for line in lines if not line.startswith("#") and not line.startswith("//")
            ]
            commands.extend(filtered_lines)

        # If no commands found, try alternative patterns (fallback)
        if not commands:
            if self.verbose:
                OSUtils.debug_print(
                    "No <commands> blocks found, trying alternative extraction", True
                )

            # Try to find single command patterns like "type filename" or "cat filename"
            common_commands = [
                "type",
                "cat",
                "dir",
                "ls",
                "head",
                "tail",
                "grep",
                "findstr",
            ]
            lines = response_content.split("\n")

            for line in lines:
                line = line.strip()
                # Check if line starts with common file commands
                if any(line.lower().startswith(cmd) for cmd in common_commands):
                    # Remove markdown code block markers if present
                    line = line.replace("```", "").strip()
                    if line and not line.startswith("#") and not line.startswith("//"):
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
            r"\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]{1,4})\b",  # filename.ext
            r"\b(app\.py|main\.py|index\.js|package\.json|requirements\.txt|config\.py)\b",  # common files
        ]

        found_files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            found_files.extend(matches)

        if found_files:
            # Use the first file found
            target_file = found_files[0]

            # Generate OS-appropriate read command
            if "read" in user_lower or "show" in user_lower or "display" in user_lower:
                command = OSUtils.get_file_read_command(target_file)
                return command
            elif "head" in user_lower or "first" in user_lower:
                command = OSUtils.get_file_head_command(target_file, 20)
                return command
            elif "tail" in user_lower or "last" in user_lower:
                command = OSUtils.get_file_tail_command(target_file, 20)
                return command
            else:
                # Default to reading the file
                command = OSUtils.get_file_read_command(target_file)
                return command

        # No files found, try directory listing
        if "list" in user_lower or "show" in user_lower or "files" in user_lower:
            return OSUtils.get_directory_list_command(".")

        return None

    def _handle_task_mode(self, task_request: str):
        """Handle task mode request with enhanced progress display and shared context"""
        try:
            if self.verbose:
                # Show context sharing information
                context_count = len(self.history_manager.get_conversation_context(limit=15))
                OSUtils.debug_print(
                    f"Switching to task mode with {context_count} context messages available",
                    True,
                )

            # Detect project mode and read existing structure if needed
            project_mode = self._detect_project_mode()

            if project_mode == "edit":
                self.console.print(
                    "[dim]📁 Detected existing project - reading current structure...[/dim]"
                )
                self.current_project_structure = self._read_current_directory_structure()

                # Display current project structure
                if self.current_project_structure:
                    structure_display = self._format_directory_structure(
                        self.current_project_structure
                    )
                    if structure_display.strip():
                        self.console.print(
                            f"\\n[dim]Current project structure:\\n{structure_display}[/dim]"
                        )

                # Add existing files to history for context
                existing_files = self._flatten_file_list(self.current_project_structure)
                for file_info in existing_files:
                    self.history_manager.track_file_edit(file_info["full_path"], "", "existing")

                self.console.print(f"[dim]🔍 Found {len(existing_files)} existing files[/dim]")
            else:
                self.console.print("[dim]🆕 Creating new project...[/dim]")
                self.current_project_structure = None

            # Process task with progress indicators
            raw_response, steps = self.task_processor.process_task(
                task_request, console=self.console
            )

            # If no steps but response exists, it might be clarifying questions
            if not steps and raw_response:
                # Check if it's clarifying questions (starts with 🤔)
                if "🤔" in raw_response or "clarify" in raw_response.lower():
                    self.console.print("\\n" + raw_response.split("Context usage:")[0].strip())
                    return

            # Display task summary and steps
            if steps:
                # Store planned files for this session
                self.current_task_files = [
                    step.target for step in steps if step.action in ["create", "edit"]
                ]

                summary = self.task_processor.get_task_summary(steps)
                mode_indicator = "🔧 Editing" if project_mode == "edit" else "🆕 Creating"
                self.console.print(f"\\n[bold green]✅ {mode_indicator} - {summary}[/bold green]")

                # First, show simple step list (required format)
                self.console.print("\\n[bold cyan]Steps:[/bold cyan]")
                for step in steps:
                    if step.action == "run":
                        self.console.print(f"{step.step_number} - run: {step.target}")
                    else:
                        self.console.print(f"{step.step_number} - {step.action} {step.target}")

                # Execute the steps (create files, etc.)
                self.console.print("\\n[bold yellow]Executing steps...[/bold yellow]")
                self._execute_task_steps(steps)

            else:
                self.console.print("\\n[yellow]⚠️  No executable steps generated.[/yellow]")
                self.console.print(
                    "[dim]Try being more specific about what you want to build.[/dim]"
                )

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
                if step.action in ["create", "edit"]:
                    # Generate file content with individual LLM call
                    self.console.print(f"[blue]🧠 Generating {step.target}...[/blue]")

                    file_content = self._generate_file_content(step)

                    if file_content:
                        # Create/edit file
                        file_path = Path(step.target)

                        # Create directory if needed
                        file_path.parent.mkdir(parents=True, exist_ok=True)

                        # Write file content
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(file_content)

                        # Show success with preview
                        action_text = "Created" if step.action == "create" else "Updated"
                        self.console.print(f"[green]✅ {action_text} {step.target}[/green]")

                        # Show file preview (first few lines)
                        lines = file_content.split("\\n")[:3]
                        preview = "\\n".join(lines)
                        if len(lines) >= 3:
                            preview += "\\n..."
                        self.console.print(f"[dim]{preview}[/dim]")

                        # Track in history
                        self.history_manager.track_file_edit(step.target, file_content, step.action)

                    else:
                        self.console.print(
                            f"[red]❌ Failed to generate content for {step.target}[/red]"
                        )

                elif step.action == "run":
                    # Execute commands directly (no LLM needed)
                    if hasattr(step, "commands") and step.commands:
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
                                encoding="utf-8",
                                errors="replace",
                                timeout=60,
                            )

                            if result.returncode == 0:
                                self.console.print(
                                    f"[green]✅ Command completed successfully[/green]"
                                )
                                if result.stdout.strip():
                                    self.console.print(f"[dim]{result.stdout.strip()}[/dim]")
                            else:
                                self.console.print(
                                    f"[yellow]⚠️  Command completed with warnings[/yellow]"
                                )
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
                OSUtils.debug_print(
                    f"🔍 File generation using {len(conversation_context)} context messages for {step.target}",
                    True,
                )

            # Build specific prompt for this file
            file_prompt = self._build_file_generation_prompt(
                step, context, existing_files, conversation_context
            )

            # Prepare messages with conversation context
            messages = [{"role": "system", "content": self._get_file_generation_system_prompt()}]

            # Add conversation context (excluding system messages to avoid conflicts)
            context_without_system = [
                msg for msg in conversation_context if msg.get("role") != "system"
            ]
            messages.extend(context_without_system)

            # Add file generation request
            messages.append({"role": "user", "content": file_prompt})

            if self.verbose:
                OSUtils.debug_print(
                    f"🧠 File generation sending {len(messages)} total messages (with conversation context)",
                    True,
                )

            # Call LLM using chat() instead of generate() to include conversation context
            with self.console.status(f"[bold blue]Generating {step.target}..."):
                response = self.llm_provider.chat(
                    messages=messages,
                    stream=False,  # Use non-streaming for file generation
                    temperature=0.3,
                )

            # Extract file content from response
            content = self._extract_file_content_from_response(response.content)
            return content

        except Exception as e:
            self.console.print(f"[red]Error generating {step.target}: {e}[/red]")
            return ""

    def _build_file_generation_prompt(
        self,
        step: TaskStep,
        context: dict,
        existing_files: list,
        conversation_context: list = None,
    ) -> str:
        """Build specific prompt for generating a single file with conversation context"""
        prompt_parts = [
            f"GENERATE FILE: {step.target}",
            f"PURPOSE: {step.description}",
            f"ACTION: {step.action.upper()}",
        ]

        # CRITICAL: Add conversation context analysis instructions
        if conversation_context:
            prompt_parts.append("\\n🧠 CRITICAL - ANALYZE CONVERSATION CONTEXT ABOVE:")
            prompt_parts.append(
                "- Look for SPECIFIC API endpoints that were analyzed (GET /videos, POST /videos, etc.)"
            )
            prompt_parts.append("- Find EXACT data models and fields mentioned")
            prompt_parts.append("- Identify SPECIFIC business logic and validation rules discussed")
            prompt_parts.append(
                "- Use EXACT functionality from conversation, NOT generic examples!"
            )
            prompt_parts.append(
                "\\n❗ IMPORTANT: If specific API/code was analyzed in conversation, REPLICATE IT EXACTLY!"
            )

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
        file_ext = step.target.split(".")[-1].lower() if step.target and "." in step.target else ""

        if file_ext in ["py"]:
            prompt_parts.append("\\nPYTHON REQUIREMENTS:")
            prompt_parts.append("- Follow PEP8 style")
            prompt_parts.append(
                "- ONLY import from files listed in EXISTING or PLANNED files above"
            )
            prompt_parts.append("- Use relative imports correctly based on folder structure")
            prompt_parts.append("- Add docstrings and comments")
            prompt_parts.append("- Handle errors gracefully")
        elif file_ext in ["js"]:
            prompt_parts.append("\\nJAVASCRIPT REQUIREMENTS:")
            prompt_parts.append("- Use modern ES6+ syntax")
            prompt_parts.append("- ONLY require/import files that exist in the project structure")
            prompt_parts.append("- Use proper module syntax (CommonJS or ES6)")
            prompt_parts.append("- Add proper error handling")
            prompt_parts.append("- Include JSDoc comments")
        elif file_ext in ["html"]:
            prompt_parts.append("\\nHTML REQUIREMENTS:")
            prompt_parts.append("- Use semantic HTML5")
            prompt_parts.append("- Link only to CSS/JS files that will exist")
            prompt_parts.append("- Include meta tags")
            prompt_parts.append("- Make it responsive")
        elif file_ext in ["css"]:
            prompt_parts.append("\\nCSS REQUIREMENTS:")
            prompt_parts.append("- Use modern CSS3")
            prompt_parts.append("- Make it responsive")
            prompt_parts.append("- Include comments")
        elif file_ext in ["json"]:
            prompt_parts.append("\\nJSON REQUIREMENTS:")
            prompt_parts.append("- Valid JSON format")
            prompt_parts.append("- Include all necessary fields")
        elif file_ext in ["md"]:
            prompt_parts.append("\\nMARKDOWN REQUIREMENTS:")
            prompt_parts.append("- Clear structure with headers")
            prompt_parts.append("- Include examples where relevant")

        prompt_parts.append(f"\\nIMPORT CONSISTENCY RULE:")
        prompt_parts.append(f"- Do NOT import/require any files not listed above")
        prompt_parts.append(
            f"- Use only standard library imports or dependencies from requirements/package.json"
        )
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
        code_block_pattern = r"```(?:\w+)?\n(.*?)\n```"
        code_match = re.search(code_block_pattern, response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Remove any explanatory text before/after code
        lines = response.strip().split("\\n")

        # Find the start of actual content (skip explanatory lines)
        start_idx = 0
        for i, line in enumerate(lines):
            # Skip lines that look like explanations
            if line and (
                line.startswith(("Here", "This", "The file", "Below", "I will", "Let me"))
                or "generate" in line.lower()
                or "create" in line.lower()
            ):
                continue
            # Start from first line that looks like code/content
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break

        # Find the end of actual content (skip explanatory lines at end)
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if line and (
                line.startswith(("That", "This", "The above", "Hope this"))
                or "complete" in line.lower()
                or "should work" in line.lower()
            ):
                end_idx = i
            elif line.strip():
                break

        # Return the cleaned content
        content_lines = lines[start_idx:end_idx]
        return "\\n".join(content_lines).strip()

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
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""
            basename = filename.split("/")[-1].split(".")[0].lower()
        except (AttributeError, IndexError):
            return None

        # Determine framework and language safely
        framework = (context.get("framework") or "").lower()
        language = (context.get("language") or "").lower()

        # Generate expectations based on file type and context
        if framework == "flask" and file_ext == "py":
            if "app.py" in filename or "main.py" in filename:
                info_parts.append("# Main Flask application file")
                info_parts.append(
                    "Functions: create_app(), register_blueprints(), init_extensions()"
                )
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
                            status.update(
                                f"[bold green]Thinking... ({current_chunks} chunks)[/bold green]"
                            )
                        except:
                            status.update(f"[bold green]Thinking... ({message})[/bold green]")
                    else:
                        status.update(f"[bold green]{message}[/bold green]")

                # Try streaming first
                try:
                    return self.llm_provider.chat(
                        messages=messages,
                        system_prompt=self.system_prompt,
                        stream=True,
                        progress_callback=progress_callback,
                    )
                except Exception:
                    # Fallback but still use streaming
                    status.update("[bold green]Thinking... (streaming fallback)[/bold green]")
                    return self.llm_provider.chat(
                        messages=messages, system_prompt=self.system_prompt, stream=True
                    )

        except Exception as e:
            self.console.print(f"[red]Error in chat: {e}[/red]")
            # Final fallback - still use streaming
            return self.llm_provider.chat(
                messages=messages, system_prompt=self.system_prompt, stream=True
            )

    def _infer_folder_structure(self, current_file: str, all_files: list) -> str:
        """Infer and display project folder structure"""
        if not all_files:
            return ""

        # Build folder tree
        folders = {}
        for file_path in all_files:
            parts = file_path.split("/")
            current_level = folders

            # Navigate/create folder structure
            for part in parts[:-1]:  # All except filename
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

            # Add file to final folder
            filename = parts[-1]
            if "___files___" not in current_level:
                current_level["___files___"] = []
            current_level["___files___"].append(filename)

        # Add root level files
        root_files = [f for f in all_files if "/" not in f]
        if root_files:
            folders["___files___"] = root_files

        # Generate tree representation
        return self._format_folder_tree(folders, "", True)

    def _format_folder_tree(
        self, folder_dict: dict, prefix: str = "", is_root: bool = False
    ) -> str:
        """Format folder dictionary into tree structure"""
        lines = []

        # Get folders and files separately
        subfolders = {
            k: v for k, v in folder_dict.items() if k != "___files___" and isinstance(v, dict)
        }
        files = folder_dict.get("___files___", [])

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
            is_last_file = i == len(files) - 1
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
                ".git",
                ".gitignore",
                "__pycache__",
                ".pytest_cache",
                "node_modules",
                ".vscode",
                ".idea",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                ".DS_Store",
                "Thumbs.db",
                "*.log",
                ".env",
                "venv",
                "env",
                ".venv",
                "dist",
                "build",
                "*.egg-info",
                ".coverage",
                "coverage.xml",
            ]

            path_lower = path.lower()
            for pattern in ignore_patterns:
                if pattern in path_lower or path_lower.endswith(pattern.replace("*", "")):
                    return True
            return False

        def read_directory(dir_path: Path, current_depth: int = 0) -> dict:
            """Recursively read directory structure"""
            if current_depth >= max_depth:
                return {}

            structure = {"files": [], "folders": {}}

            try:
                for item in sorted(dir_path.iterdir()):
                    if should_ignore(item.name):
                        continue

                    if item.is_file():
                        # Get file info
                        try:
                            size = item.stat().st_size
                            if size < 1024 * 1024:  # Only include files < 1MB
                                structure["files"].append(
                                    {
                                        "name": item.name,
                                        "path": str(item.relative_to(Path.cwd())),
                                        "size": size,
                                    }
                                )
                        except (OSError, ValueError):
                            continue

                    elif item.is_dir():
                        # Recursively read subdirectory
                        subdir_structure = read_directory(item, current_depth + 1)
                        if subdir_structure.get("files") or subdir_structure.get("folders"):
                            structure["folders"][item.name] = subdir_structure

            except (PermissionError, OSError):
                pass

            return structure

        return read_directory(Path.cwd())

    def _format_directory_structure(
        self, structure: dict, prefix: str = "", is_root: bool = True
    ) -> str:
        """Format directory structure into readable tree format"""
        lines = []

        # Get folders and files
        folders = structure.get("folders", {})
        files = structure.get("files", [])

        # Add folders first
        folder_items = list(folders.items())
        for i, (folder_name, folder_contents) in enumerate(folder_items):
            is_last_folder = (i == len(folder_items) - 1) and not files

            # Folder line
            connector = "└── " if is_last_folder else "├── "
            lines.append(f"{prefix}{connector}{folder_name}/")

            # Recurse into folder
            extension = "    " if is_last_folder else "│   "
            subfolder_lines = self._format_directory_structure(
                folder_contents, prefix + extension, False
            )
            if subfolder_lines:
                lines.append(subfolder_lines)

        # Add files
        for i, file_info in enumerate(files):
            is_last_file = i == len(files) - 1
            connector = "└── " if is_last_file else "├── "
            filename = file_info["name"]
            lines.append(f"{prefix}{connector}{filename}")

        return "\\n".join(lines)

    def _detect_project_mode(self) -> str:
        """Detect if we're in create or edit mode based on current directory"""
        structure = self._read_current_directory_structure(max_depth=2)

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

        all_files = self._flatten_file_list(structure)

        # If we find project files, we're likely in edit mode
        for indicator in project_indicators:
            if any(f["name"] == indicator for f in all_files):
                return "edit"

        # If there are multiple code files, probably edit mode
        code_files = [
            f
            for f in all_files
            if f["name"].endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"))
        ]
        if len(code_files) >= 3:
            return "edit"

        # Otherwise, assume create mode
        return "create"

    def _flatten_file_list(self, structure: dict, current_path: str = "") -> list:
        """Flatten directory structure into a list of all files with paths"""
        files = []

        # Add files in current directory
        for file_info in structure.get("files", []):
            file_copy = file_info.copy()
            file_copy["full_path"] = (
                os.path.join(current_path, file_info["name"]) if current_path else file_info["name"]
            )
            files.append(file_copy)

        # Recursively add files from subdirectories
        for folder_name, folder_contents in structure.get("folders", {}).items():
            subpath = os.path.join(current_path, folder_name) if current_path else folder_name
            files.extend(self._flatten_file_list(folder_contents, subpath))

        return files

    def _display_response(self, content: str, allow_execution: bool = False):
        """Display LLM response with syntax highlighting and optional execution confirmation"""
        import re

        # Define executable languages/types
        executable_types = {
            "bash",
            "shell",
            "sh",
            "cmd",
            "powershell",
            "python",
            "py",
            "node",
            "js",
            "npm",
            "batch",
        }

        # Process content to find and extract all code blocks
        processed_content = content
        all_code_blocks = []

        # Find markdown code blocks: ```lang\ncode\n```
        markdown_pattern = r"```(\w+)?\n(.*?)\n```"
        for match in re.finditer(markdown_pattern, content, re.DOTALL):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            all_code_blocks.append(
                {
                    "lang": lang,
                    "code": code,
                    "type": "markdown",
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Find <code> tags: <code type="lang">code</code> or <code>code</code>
        code_tag_pattern = r'<code(?:\s+type=["\']?(\w+)["\']?)?>(.*?)</code>'
        for match in re.finditer(code_tag_pattern, content, re.DOTALL):
            lang = match.group(1) or "bash"  # Default to bash if no type specified
            code = match.group(2).strip()
            all_code_blocks.append(
                {
                    "lang": lang,
                    "code": code,
                    "type": "code_tag",
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Find <commands> tags: <commands>command1\ncommand2</commands>
        commands_tag_pattern = r"<commands>(.*?)</commands>"
        for match in re.finditer(commands_tag_pattern, content, re.DOTALL):
            commands_content = match.group(1).strip()
            all_code_blocks.append(
                {
                    "lang": "bash",  # Commands are typically shell commands
                    "code": commands_content,
                    "type": "commands_tag",
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Find <code edit filename="..."> and <code create filename="..."> tags
        file_operation_pattern = (
            r'<code\s+(edit|create)\s+filename=["\']([^"\']+)["\']>(.*?)</code>'
        )
        for match in re.finditer(file_operation_pattern, content, re.DOTALL):
            operation = match.group(1)  # 'edit' or 'create'
            filename = match.group(2)  # filename
            code_content = match.group(3).strip()
            all_code_blocks.append(
                {
                    "lang": "file_operation",  # Special type for file operations
                    "code": code_content,
                    "type": f"code_{operation}_file",
                    "filename": filename,
                    "operation": operation,
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        if all_code_blocks:
            # Sort blocks by position in content
            all_code_blocks.sort(key=lambda x: x["start"])

            # Display content with code blocks
            last_pos = 0

            for block in all_code_blocks:
                # Display text before this code block
                text_before = content[last_pos : block["start"]].strip()
                if text_before:
                    self.console.print(text_before)

                # Display code block with syntax highlighting
                if block["code"]:
                    # Handle file operations differently
                    if block["lang"] == "file_operation":
                        # Display file operation with special formatting
                        filename = block.get("filename", "unknown")
                        operation = block.get("operation", "unknown")

                        try:
                            # Detect language from filename for syntax highlighting
                            file_ext = (
                                filename.split(".")[-1].lower() if "." in filename else "text"
                            )
                            lang_map = {
                                "py": "python",
                                "js": "javascript",
                                "ts": "typescript",
                                "html": "html",
                                "css": "css",
                                "json": "json",
                                "md": "markdown",
                                "yml": "yaml",
                                "yaml": "yaml",
                                "xml": "xml",
                                "sql": "sql",
                                "sh": "bash",
                                "java": "java",
                                "cpp": "cpp",
                                "c": "c",
                                "php": "php",
                                "rb": "ruby",
                                "go": "go",
                            }
                            syntax_lang = lang_map.get(file_ext, "text")

                            syntax = Syntax(
                                block["code"],
                                syntax_lang,
                                theme="monokai",
                                line_numbers=True,
                            )
                            block_title = f"{operation.title()} File: {filename}"
                            if self.verbose:
                                block_title += f" - {block['type']}"
                            self.console.print(
                                Panel(syntax, title=block_title, border_style="green")
                            )
                        except:
                            # Fallback to plain text
                            self.console.print(
                                Panel(
                                    block["code"],
                                    title=f"{operation.title()} File: {filename}",
                                    border_style="green",
                                )
                            )

                        # Always prompt for file operations
                        if allow_execution:
                            self._prompt_file_operation(block["code"], filename, operation)
                    else:
                        # Regular code block display
                        try:
                            syntax = Syntax(
                                block["code"],
                                block["lang"],
                                theme="monokai",
                                line_numbers=True,
                            )
                            block_title = f"Code ({block['lang']})"
                            if self.verbose:
                                block_title += f" - {block['type']}"
                            self.console.print(
                                Panel(syntax, title=block_title, border_style="blue")
                            )
                        except:
                            # Fallback to plain text
                            self.console.print(
                                Panel(block["code"], title="Code", border_style="blue")
                            )

                        # Check if this is an executable block and we're in chat mode
                        if (
                            allow_execution
                            and block["lang"]
                            and block["lang"].lower() in executable_types
                        ):
                            self._prompt_code_execution(block["code"], block["lang"], block["type"])

                        # NEW: Check if this looks like a complete file and offer to save it
                        if allow_execution and self._is_complete_file(block["code"], block["lang"]):
                            self._prompt_file_save(block["code"], block["lang"])

                last_pos = block["end"]

            # Display any remaining text after the last code block
            remaining_text = content[last_pos:].strip()
            if remaining_text:
                self.console.print(remaining_text)
        else:
            # No code blocks, display as is
            self.console.print(content)

    def _prompt_code_execution(self, code: str, lang: str, block_type: str = "markdown"):
        """Prompt user to execute detected code/command"""
        try:
            # Customize prompt based on block type
            if block_type == "commands_tag":
                prompt_msg = f"\\n[yellow]⚡ Detected <commands> block. Execute these commands? (y/N):[/yellow]"
                exec_msg = "[green]🚀 Executing commands...[/green]"
            elif block_type == "code_tag":
                prompt_msg = (
                    f"\\n[yellow]⚡ Detected <code> tag ({lang}). Execute it? (y/N):[/yellow]"
                )
                exec_msg = f"[green]🚀 Executing {lang} code...[/green]"
            else:
                prompt_msg = (
                    f"\\n[yellow]⚡ Detected executable {lang} code. Execute it? (y/N):[/yellow]"
                )
                exec_msg = f"[green]🚀 Executing {lang} code...[/green]"

            # Show execution prompt
            self.console.print(prompt_msg, end=" ")

            # Get user response with EOF handling
            import sys

            sys.stdout.flush()

            # Check if interactive mode is disabled
            if not self.interactive_mode:
                self.console.print("[dim]Code execution skipped (interactive mode disabled).[/dim]")
                return

            # Interactive mode is enabled - always attempt to prompt user
            try:
                response = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.console.print("[dim]Code execution skipped.[/dim]")
                return
            except Exception as e:
                # Handle any other input issues gracefully
                self.console.print(f"[dim]Code execution skipped (input error: {e}).[/dim]")
                return

            if response in ["y", "yes", "sim", "s"]:
                self.console.print(exec_msg)

                # Execute based on language type using generalized system
                self._execute_code_by_language(code, lang)
            else:
                self.console.print("[dim]Code execution skipped.[/dim]")

        except KeyboardInterrupt:
            self.console.print("[dim]Code execution cancelled.[/dim]")
        except EOFError:
            self.console.print("[dim]Code execution skipped (EOF).[/dim]")
        except Exception as e:
            self.console.print(f"[red]Error prompting for execution: {e}[/red]")

    def _is_complete_file(self, code: str, lang: str) -> bool:
        """Analyze code to determine if it looks like a complete file"""
        if not code or not lang or len(code.strip()) < 20:  # Too small to be a file
            return False

        # Language-specific file indicators
        file_indicators = {
            "python": [
                "import ",
                "from ",
                "def ",
                "class ",
                "if __name__",
                "#!/usr/bin/env python",
                "# -*- coding",
            ],
            "javascript": [
                "const ",
                "let ",
                "var ",
                "function ",
                "class ",
                "import ",
                "export",
                "require(",
                "module.exports",
                "#!/usr/bin/env node",
            ],
            "typescript": [
                "interface ",
                "type ",
                "import ",
                "export ",
                "class ",
                "function ",
                "const ",
                "let ",
                "var ",
            ],
            "java": [
                "public class ",
                "private ",
                "public static void main",
                "import ",
                "package ",
                "@Override",
            ],
            "go": [
                "package ",
                "func ",
                "import ",
                "var ",
                "const ",
                "type ",
                "func main()",
            ],
            "rust": [
                "fn ",
                "use ",
                "mod ",
                "struct ",
                "impl ",
                "fn main()",
                "#[derive",
                "pub ",
            ],
            "php": [
                "<?php",
                "class ",
                "function ",
                "namespace ",
                "use ",
                "require ",
                "include ",
            ],
            "c": ["#include", "int main(", "void ", "struct ", "typedef", "#define"],
            "cpp": [
                "#include",
                "using namespace",
                "class ",
                "int main(",
                "template<",
                "std::",
            ],
            "css": [
                "body",
                "html",
                ".",
                "#",
                "@media",
                "@import",
                "margin:",
                "padding:",
            ],
            "html": [
                "<!DOCTYPE",
                "<html",
                "<head>",
                "<body>",
                "<div",
                "<script",
                "<style",
            ],
            "json": ["{", "}", "[", "]", '"'],  # Basic JSON structure
            "yaml": [
                "name:",
                "version:",
                "dependencies:",
                "scripts:",
                "---",
                "apiVersion:",
            ],
            "sql": [
                "SELECT",
                "CREATE",
                "INSERT",
                "UPDATE",
                "DELETE",
                "FROM",
                "WHERE",
                "TABLE",
            ],
        }

        # Normalize language name
        lang_lower = lang.lower()
        if lang_lower in ["js", "node"]:
            lang_lower = "javascript"
        elif lang_lower in ["ts"]:
            lang_lower = "typescript"
        elif lang_lower in ["py"]:
            lang_lower = "python"
        elif lang_lower in ["cpp", "cxx", "cc"]:
            lang_lower = "cpp"
        elif lang_lower in ["yml"]:
            lang_lower = "yaml"

        # Check for language-specific indicators
        if lang_lower in file_indicators:
            indicators = file_indicators[lang_lower]
            code_lower = code.lower()

            # Count matches (case-insensitive for keywords, case-sensitive for syntax)
            matches = 0
            for indicator in indicators:
                if indicator.lower() in code_lower:
                    matches += 1

            # Need at least 2 indicators for small files, 1 for large files
            min_matches = 1 if len(code) > 200 else 2
            return matches >= min_matches

        # For unknown languages, use heuristics
        lines = code.strip().split("\\n")
        if len(lines) < 3:  # Too few lines
            return False

        # Heuristics for any language:
        # - Has multiple lines
        # - Has some structure (functions, classes, imports)
        # - Not just a snippet
        structure_keywords = [
            "function",
            "class",
            "def",
            "import",
            "include",
            "module",
            "namespace",
            "package",
            "struct",
            "interface",
        ]

        has_structure = any(keyword in code.lower() for keyword in structure_keywords)
        has_multiple_statements = (
            len([line for line in lines if line.strip() and not line.strip().startswith("//")]) >= 5
        )

        return has_structure and has_multiple_statements

    def _infer_filename(self, code: str, lang: str) -> str:
        """Infer an appropriate filename based on code content and language"""
        # Language to extension mapping
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "rust": ".rs",
            "php": ".php",
            "c": ".c",
            "cpp": ".cpp",
            "css": ".css",
            "html": ".html",
            "json": ".json",
            "yaml": ".yml",
            "sql": ".sql",
            "bash": ".sh",
            "shell": ".sh",
            "powershell": ".ps1",
            "batch": ".bat",
        }

        # Normalize language
        lang_lower = lang.lower()
        if lang_lower in ["js", "node"]:
            lang_lower = "javascript"
        elif lang_lower in ["ts"]:
            lang_lower = "typescript"
        elif lang_lower in ["py"]:
            lang_lower = "python"
        elif lang_lower in ["sh"]:
            lang_lower = "bash"

        extension = ext_map.get(lang_lower, ".txt")

        # Try to extract filename from comments
        lines = code.strip().split("\\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Look for filename in comments
            if "//" in line or "#" in line or "/*" in line:
                # Common patterns: // filename.js, # filename.py, etc.
                import re

                filename_pattern = r"[/#*\\s]*([a-zA-Z0-9_-]+\\.[a-zA-Z0-9]+)"
                match = re.search(filename_pattern, line)
                if match:
                    potential_filename = match.group(1)
                    if potential_filename.endswith(extension) or "." in potential_filename:
                        return potential_filename

        # Try to extract class name or main function name
        class_patterns = {
            "python": r"class\\s+([A-Za-z][A-Za-z0-9_]*)",
            "javascript": r"class\\s+([A-Za-z][A-Za-z0-9_]*)",
            "typescript": r"class\\s+([A-Za-z][A-Za-z0-9_]*)",
            "java": r"public\\s+class\\s+([A-Za-z][A-Za-z0-9_]*)",
            "go": r"func\\s+([A-Za-z][A-Za-z0-9_]*)\\(",
            "rust": r"fn\\s+([A-Za-z][A-Za-z0-9_]*)\\(",
        }

        if lang_lower in class_patterns:
            import re

            match = re.search(class_patterns[lang_lower], code)
            if match:
                name = match.group(1).lower()
                return f"{name}{extension}"

        # Look for specific patterns
        if "package.json" in code or '"name"' in code and lang_lower == "json":
            return "package.json"
        elif "docker" in code.lower() and ("from " in code.lower() or "run " in code.lower()):
            return "Dockerfile"
        elif "requirements" in code.lower() and lang_lower == "txt":
            return "requirements.txt"
        elif "main(" in code and lang_lower in ["c", "cpp"]:
            return f"main{extension}"
        elif "if __name__" in code and lang_lower == "python":
            return f"main{extension}"

        # Default naming
        default_names = {
            "javascript": "script.js",
            "typescript": "script.ts",
            "python": "script.py",
            "java": "Main.java",
            "go": "main.go",
            "rust": "main.rs",
            "php": "index.php",
            "html": "index.html",
            "css": "styles.css",
            "json": "data.json",
            "yaml": "config.yml",
            "sql": "queries.sql",
        }

        return default_names.get(lang_lower, f"file{extension}")

    def _prompt_file_save(self, code: str, lang: str):
        """Prompt user to save a detected code file"""
        try:
            # Infer filename
            suggested_filename = self._infer_filename(code, lang)

            # Show save prompt
            self.console.print(
                f"\\n[cyan]💾 This looks like a complete {lang} file. Save it? (y/N):[/cyan]",
                end=" ",
            )

            # Get user response
            import sys

            sys.stdout.flush()
            response = input().strip().lower()

            if response in ["y", "yes", "sim", "s"]:
                # Ask for filename
                self.console.print(
                    f"[cyan]📝 Filename [default: {suggested_filename}]:[/cyan]",
                    end=" ",
                )
                sys.stdout.flush()
                filename_input = input().strip()

                # Use suggested filename if none provided
                final_filename = filename_input if filename_input else suggested_filename

                # Save the file
                self._execute_file_create(code, final_filename)
            else:
                self.console.print("[dim]File save cancelled.[/dim]")

        except KeyboardInterrupt:
            self.console.print("\\n[dim]File save cancelled.[/dim]")
        except Exception as e:
            self.console.print(f"[red]Error prompting for file save: {e}[/red]")

    def _prompt_file_operation(self, content: str, filename: str, operation: str):
        """Prompt user to execute file create/edit operations"""
        try:
            # Customize prompt based on operation type
            if operation == "create":
                prompt_msg = f"\\n[yellow]📄 Create file '{filename}'? (y/N):[/yellow]"
                exec_msg = f"[green]🚀 Creating file '{filename}'...[/green]"
            elif operation == "edit":
                prompt_msg = f"\\n[yellow]✏️  Edit file '{filename}'? (y/N):[/yellow]"
                exec_msg = f"[green]🚀 Editing file '{filename}'...[/green]"
            else:
                prompt_msg = f"\\n[yellow]📝 Apply file operation to '{filename}'? (y/N):[/yellow]"
                exec_msg = f"[green]🚀 Applying operation to '{filename}'...[/green]"

            # Show file operation prompt
            self.console.print(prompt_msg, end=" ")

            # Get user response
            import sys

            sys.stdout.flush()
            response = input().strip().lower()

            if response in ["y", "yes", "sim", "s"]:
                self.console.print(exec_msg)

                # Execute file operation
                if operation == "create":
                    self._execute_file_create(content, filename)
                elif operation == "edit":
                    self._execute_file_edit(content, filename)
                else:
                    self.console.print(f"[red]Unknown file operation: {operation}[/red]")
            else:
                self.console.print(f"[dim]File operation cancelled.[/dim]")

        except KeyboardInterrupt:
            self.console.print("\\n[dim]File operation cancelled.[/dim]")
        except Exception as e:
            self.console.print(f"[red]Error prompting for file operation: {e}[/red]")

    def _execute_file_create(self, content: str, filename: str):
        """Create a new file with the given content"""
        try:
            import os
            from pathlib import Path

            # Create directory if it doesn't exist
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file already exists
            if file_path.exists():
                self.console.print(
                    f"[yellow]⚠️  File '{filename}' already exists. Overwrite? (y/N):[/yellow]",
                    end=" ",
                )
                response = input().strip().lower()
                if response not in ["y", "yes", "sim", "s"]:
                    self.console.print("[dim]File creation cancelled.[/dim]")
                    return

            # Write file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Track file in history
            self.history_manager.track_file_edit(filename, content, "create")

            self.console.print(f"[green]✅ File '{filename}' created successfully![/green]")

        except Exception as e:
            self.console.print(f"[red]Error creating file '{filename}': {e}[/red]")

    def _execute_file_edit(self, content: str, filename: str):
        """Edit an existing file with the given content"""
        try:
            import os
            from pathlib import Path

            file_path = Path(filename)

            # Check if file exists for editing
            if not file_path.exists():
                self.console.print(
                    f"[yellow]⚠️  File '{filename}' doesn't exist. Create it? (y/N):[/yellow]",
                    end=" ",
                )
                response = input().strip().lower()
                if response in ["y", "yes", "sim", "s"]:
                    self._execute_file_create(content, filename)
                    return
                else:
                    self.console.print("[dim]File edit cancelled.[/dim]")
                    return

            # Create backup of existing file
            backup_path = f"{filename}.backup"
            if file_path.exists():
                import shutil

                shutil.copy2(file_path, backup_path)
                self.console.print(f"[dim]Backup created: {backup_path}[/dim]")

            # Write new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Track file in history
            self.history_manager.track_file_edit(filename, content, "edit")

            self.console.print(f"[green]✅ File '{filename}' edited successfully![/green]")

        except Exception as e:
            self.console.print(f"[red]Error editing file '{filename}': {e}[/red]")

    def _execute_shell_code(self, code: str):
        """Execute shell/bash commands (handles multiple separators)"""
        try:
            # Split multiple commands by various separators
            commands = []

            # First try && (logical AND - only run next if previous succeeds)
            if "&&" in code:
                commands = [cmd.strip() for cmd in code.split("&&") if cmd.strip()]
            # Then try ; (command separator - run all regardless)
            elif ";" in code:
                commands = [cmd.strip() for cmd in code.split(";") if cmd.strip()]
            # Finally try newlines (most common in <commands> tags)
            else:
                commands = [cmd.strip() for cmd in code.split("\\n") if cmd.strip()]

            # Execute each command and ensure output is shown
            for command in commands:
                if command and not command.startswith("#"):  # Skip comments
                    self.console.print(f"[blue]$ {command}[/blue]")
                    # Force immediate execution and output display
                    self._execute_command_with_output(command)

        except Exception as e:
            self.console.print(f"[red]Error executing shell command: {e}[/red]")

    def _execute_command_with_output(self, command: str):
        """Execute command and immediately display output - optimized for chat mode execution"""
        try:
            import subprocess
            import sys

            # Handle special commands first
            try:
                command_parts = shlex.split(command)
                command_name = command_parts[0].lower()
            except ValueError as e:
                # Handle shlex parsing errors
                if self.verbose:
                    OSUtils.debug_print(f"Shlex parsing error: {e}", True)
                command_parts = command.split()
                command_name = command_parts[0].lower() if command_parts else ""

            # Handle cd command specially
            if command_name == "cd":
                self._handle_cd_command(command_parts)
                return
            elif command_name in ["cls", "clear"]:
                self._handle_clear_command(command)
                return

            # Execute command with immediate output
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(
                    timeout=60
                )  # Increased timeout for long operations

                # Show output immediately
                if stdout and stdout.strip():
                    self.console.print(
                        Panel(
                            stdout.strip(),
                            title=f"✅ Output: {command}",
                            border_style="green",
                        )
                    )
                    # Also add to history
                    self.history_manager.add_conversation(
                        role="system",
                        content=f"<command_output>\\n{stdout.strip()}\\n</command_output>",
                        metadata={"type": "command_output", "command": command},
                    )
                elif process.returncode == 0:
                    self.console.print(
                        f"[green]✅ Command completed successfully: {command}[/green]"
                    )

                # Show errors if any
                if stderr and stderr.strip():
                    self.console.print(
                        Panel(
                            f"[red]{stderr.strip()}[/red]",
                            title=f"⚠️  Error: {command}",
                            border_style="red",
                        )
                    )
                    # Add error to history too
                    self.history_manager.add_conversation(
                        role="system",
                        content=f"<command_error>\\n{stderr.strip()}\\n</command_error>",
                        metadata={"type": "command_error", "command": command},
                    )
                elif process.returncode != 0:
                    self.console.print(
                        f"[red]❌ Command failed with code {process.returncode}: {command}[/red]"
                    )

            except subprocess.TimeoutExpired:
                process.kill()
                self.console.print(f"[red]⏰ Command timed out (60s): {command}[/red]")

        except Exception as e:
            self.console.print(f"[red]❌ Error executing command '{command}': {e}[/red]")
            if self.verbose:
                import traceback

                self.console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")

    def _get_language_config(self):
        """Get configuration for different programming languages"""
        import platform

        is_windows = platform.system().lower() == "windows"

        return {
            # Python
            "python": {
                "extensions": [".py"],
                "inline_command": "python -c",
                "file_command": "python",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "def ",
                    "class ",
                    "if __name__",
                    "for ",
                    "while ",
                    "with ",
                    "try:",
                    "import ",
                    "from ",
                ],
            },
            "py": {
                "extensions": [".py"],
                "inline_command": "python -c",
                "file_command": "python",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "def ",
                    "class ",
                    "if __name__",
                    "for ",
                    "while ",
                    "with ",
                    "try:",
                    "import ",
                    "from ",
                ],
            },
            # JavaScript/Node.js
            "javascript": {
                "extensions": [".js"],
                "inline_command": "node -e",
                "file_command": "node",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                    "class ",
                    "import ",
                    "require(",
                    "module.exports",
                ],
            },
            "js": {
                "extensions": [".js"],
                "inline_command": "node -e",
                "file_command": "node",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                    "class ",
                    "import ",
                    "require(",
                    "module.exports",
                ],
            },
            "node": {
                "extensions": [".js"],
                "inline_command": "node -e",
                "file_command": "node",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                    "class ",
                    "import ",
                    "require(",
                    "module.exports",
                ],
            },
            # C
            "c": {
                "extensions": [".c"],
                "inline_command": None,  # No inline support
                "file_command": "gcc -o {output} {input} && {output}",
                "file_command_windows": "gcc -o {output}.exe {input} && {output}.exe",
                "supports_inline": False,
                "needs_compilation": True,
                "complex_keywords": [
                    "#include",
                    "int main",
                    "printf",
                    "scanf",
                    "struct ",
                    "typedef",
                ],
            },
            # C++
            "cpp": {
                "extensions": [".cpp", ".cxx", ".cc"],
                "inline_command": None,
                "file_command": "g++ -o {output} {input} && {output}",
                "file_command_windows": "g++ -o {output}.exe {input} && {output}.exe",
                "supports_inline": False,
                "needs_compilation": True,
                "complex_keywords": [
                    "#include",
                    "int main",
                    "std::",
                    "cout",
                    "cin",
                    "class ",
                    "namespace",
                ],
            },
            "c++": {
                "extensions": [".cpp"],
                "inline_command": None,
                "file_command": "g++ -o {output} {input} && {output}",
                "file_command_windows": "g++ -o {output}.exe {input} && {output}.exe",
                "supports_inline": False,
                "needs_compilation": True,
                "complex_keywords": [
                    "#include",
                    "int main",
                    "std::",
                    "cout",
                    "cin",
                    "class ",
                    "namespace",
                ],
            },
            # Go
            "go": {
                "extensions": [".go"],
                "inline_command": None,
                "file_command": "go run",
                "supports_inline": False,
                "needs_compilation": False,  # go run handles compilation
                "complex_keywords": [
                    "package ",
                    "import ",
                    "func ",
                    "var ",
                    "const ",
                    "type ",
                    "struct",
                ],
            },
            # Shell scripts
            "bash": {
                "extensions": [".sh"],
                "inline_command": "bash -c" if not is_windows else "bash -c",
                "file_command": "bash",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "#!/bin/bash",
                    "function ",
                    "if ",
                    "for ",
                    "while ",
                    "case ",
                ],
            },
            "sh": {
                "extensions": [".sh"],
                "inline_command": "sh -c" if not is_windows else "sh -c",
                "file_command": "sh",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": ["#!/bin/sh", "if ", "for ", "while ", "case "],
            },
            "shell": {
                "extensions": [".sh"],
                "inline_command": (
                    "bash -c" if not is_windows else "cmd /c" if is_windows else "sh -c"
                ),
                "file_command": "bash" if not is_windows else "cmd /c",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": (
                    ["if ", "for ", "while ", "case "] if not is_windows else ["if ", "for "]
                ),
            },
            # Windows specific
            "cmd": {
                "extensions": [".cmd", ".bat"],
                "inline_command": "cmd /c",
                "file_command": "cmd /c",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": ["@echo", "if ", "for ", "goto ", "call ", "set "],
            },
            "batch": {
                "extensions": [".bat"],
                "inline_command": "cmd /c",
                "file_command": "cmd /c",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": ["@echo", "if ", "for ", "goto ", "call ", "set "],
            },
            "bat": {
                "extensions": [".bat"],
                "inline_command": "cmd /c",
                "file_command": "cmd /c",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": ["@echo", "if ", "for ", "goto ", "call ", "set "],
            },
            # PowerShell
            "powershell": {
                "extensions": [".ps1"],
                "inline_command": "powershell -Command",
                "file_command": "powershell -File",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "function ",
                    "param(",
                    "if (",
                    "foreach ",
                    "while (",
                    "$",
                    "Get-",
                    "Set-",
                ],
            },
            "ps1": {
                "extensions": [".ps1"],
                "inline_command": "powershell -Command",
                "file_command": "powershell -File",
                "supports_inline": True,
                "needs_compilation": False,
                "complex_keywords": [
                    "function ",
                    "param(",
                    "if (",
                    "foreach ",
                    "while (",
                    "$",
                    "Get-",
                    "Set-",
                ],
            },
            # NPM/Package managers
            "npm": {
                "extensions": [],
                "inline_command": None,
                "file_command": None,  # Special handling
                "supports_inline": False,
                "needs_compilation": False,
                "complex_keywords": [],
            },
        }

    def _should_use_temp_file(self, code: str, lang: str) -> bool:
        """Generalized logic to determine if code should be executed via temporary file"""
        lang_lower = lang.lower()
        config = self._get_language_config().get(lang_lower)

        if not config:
            # Unknown language, default to temp file for safety
            return True

        # If language doesn't support inline execution, always use temp file
        if not config["supports_inline"]:
            return True

        # Empty or whitespace-only code - safer with temp file
        if not code.strip():
            return True

        # Multi-line scripts
        if "\n" in code.strip():
            return True

        # Contains complex quotes that might break inline execution
        if code.count('"') > 2 or code.count("'") > 2:
            return True

        # Contains triple quotes (for languages that support them)
        if '"""' in code or "'''" in code:
            return True

        # Contains backslashes that might cause escaping issues
        if "\\" in code and not any(
            code.startswith(simple) for simple in ["print(", "echo ", "console.log("]
        ):
            return True

        # Long single-line scripts (>200 chars) - safer with temp file
        if len(code) > 200:
            return True

        # Contains language-specific complex keywords
        if any(keyword in code for keyword in config["complex_keywords"]):
            return True

        return False

    def _execute_code_by_language(self, code: str, lang: str):
        """Execute code in specified language with intelligent temp file handling"""
        import os
        import platform
        import tempfile
        from pathlib import Path

        try:
            code = code.strip()
            lang_lower = lang.lower()
            config = self._get_language_config().get(lang_lower)

            if not config:
                self.console.print(
                    f"[yellow]Warning: Unknown language '{lang}', attempting shell execution...[/yellow]"
                )
                return self._execute_shell_code(code)

            # Special handling for NPM
            if lang_lower == "npm":
                return self._execute_npm_code(code)

            # Determine execution method
            needs_temp_file = self._should_use_temp_file(code, lang)

            if needs_temp_file or not config["supports_inline"]:
                # Use temporary file approach
                self._execute_code_with_temp_file(code, lang, config)
            else:
                # Use inline execution
                self._execute_code_inline(code, lang, config)

        except Exception as e:
            self.console.print(f"[red]Error executing {lang} code: {e}[/red]")
            import traceback

            if self.verbose:
                self.console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")

    def _execute_code_with_temp_file(self, code: str, lang: str, config: dict):
        """Execute code using temporary file approach"""
        import os
        import platform
        import subprocess
        import tempfile

        is_windows = platform.system().lower() == "windows"
        extension = config["extensions"][0] if config["extensions"] else ".tmp"

        self.console.print(f"[dim]Creating temporary {lang} file for execution...[/dim]")

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=extension, delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            if config["needs_compilation"]:
                # Handle compiled languages (C, C++, Go)
                self._execute_compiled_code(temp_file_path, lang, config, is_windows)
            else:
                # Handle interpreted languages
                if is_windows and f"file_command_windows" in config:
                    base_command = config["file_command_windows"]
                else:
                    base_command = config["file_command"]

                command = f'{base_command} "{temp_file_path}"'
            self.console.print(f"[blue]$ {command}[/blue]")
            self._execute_command_with_output(command)

        finally:
            # Cleanup temporary file
            try:
                os.unlink(temp_file_path)
                self.console.print(f"[dim]Temporary {lang} file cleaned up.[/dim]")
            except OSError:
                pass

    def _execute_compiled_code(self, source_path: str, lang: str, config: dict, is_windows: bool):
        """Execute compiled languages (C, C++, etc.)"""
        import os
        import tempfile
        from pathlib import Path

        # Generate output executable name
        source_stem = Path(source_path).stem
        if is_windows:
            output_name = f"{source_stem}_temp"
            command_template = config.get("file_command_windows", config["file_command"])
        else:
            output_name = f"{source_stem}_temp"
            command_template = config["file_command"]

        try:
            # Format the compilation command
            command = command_template.format(input=f'"{source_path}"', output=output_name)

            self.console.print(f"[blue]$ {command}[/blue]")
            self._execute_command_with_output(command)

        finally:
            # Cleanup compiled executable
            try:
                # Check for both .exe and non-.exe versions
                exe_path = f"{output_name}.exe" if is_windows else output_name
                if os.path.exists(exe_path):
                    os.unlink(exe_path)
                    self.console.print(f"[dim]Compiled executable cleaned up.[/dim]")
                elif os.path.exists(output_name):
                    os.unlink(output_name)
                    self.console.print(f"[dim]Compiled executable cleaned up.[/dim]")
            except OSError:
                pass

    def _execute_code_inline(self, code: str, lang: str, config: dict):
        """Execute code using inline command approach"""
        inline_cmd = config["inline_command"]

        # Escape code for inline execution
        if lang.lower() in ["python", "py"]:
            escaped_code = code.replace('"', '\\"').replace("\n", "\\n")
        elif lang.lower() in ["javascript", "js", "node"]:
            escaped_code = code.replace('"', '\\"').replace("\n", "\\n")
        else:
            # Generic escaping
            escaped_code = code.replace('"', '\\"')

        command = f'{inline_cmd} "{escaped_code}"'
        self.console.print(f"[blue]$ {command}[/blue]")
        self._execute_command_with_output(command)

    # Legacy function - now handled by _execute_code_by_language
    def _execute_node_code(self, code: str):
        """Execute Node.js code (Legacy - use _execute_code_by_language instead)"""
        return self._execute_code_by_language(code, "node")

    def _execute_npm_code(self, code: str):
        """Execute NPM commands"""
        try:
            # Split multiple npm commands if on separate lines
            commands = [cmd.strip() for cmd in code.split("\\n") if cmd.strip()]

            for command in commands:
                if command:
                    self.console.print(f"[blue]$ {command}[/blue]")
                    self._execute_command_with_output(command)

        except Exception as e:
            self.console.print(f"[red]Error executing NPM command: {e}[/red]")

    def _display_task_steps(self, formatted_steps: str):
        """Display task steps with proper formatting"""
        # Parse and display each step with proper highlighting
        current_step = ""
        in_code_block = False
        in_commands_block = False

        for line in formatted_steps.split("\\n"):
            if line.startswith(("<code edit filename=", "</code>", "<commands>", "</commands>")):
                if line.startswith("<code edit filename="):
                    filename = line.split('"')[1]
                    self.console.print(f"\\n[bold green]📝 File: {filename}[/bold green]")
                    in_code_block = True
                elif line == "</code>":
                    in_code_block = False
                elif line == "<commands>":
                    self.console.print(f"\\n[bold yellow]⚡ Commands:[/bold yellow]")
                    in_commands_block = True
                elif line == "</commands>":
                    in_commands_block = False
            elif re.match(r"^\\d+ - (create|edit|run)", line):
                # Step header
                self.console.print(f"\\n[bold cyan]{line}[/bold cyan]")
            elif in_code_block and line.strip():
                # Code content - try to detect language
                try:
                    # Simple language detection based on content
                    if "import " in line or "def " in line or "class " in line:
                        lang = "python"
                    elif "function" in line or "const " in line or "let " in line:
                        lang = "javascript"
                    else:
                        lang = "text"

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
  • /interactive, /toggle - Toggle interactive mode for code execution
  • /scan, /structure - Show current directory structure
  • /exit, /quit, /bye - Exit XandAI

[yellow]Provider Management:[/yellow]
  • /provider         - Show current provider status
  • /providers        - List all available providers
  • /switch <provider> - Switch to another provider (ollama, lm_studio)
  • /detect           - Auto-detect best available provider
  • /server <url>     - Set custom server endpoint
  • /models           - List available models

[yellow]Web Integration:[/yellow]
  • /web              - Show web integration status
  • /web on           - Enable web integration (fetch content from links)
  • /web off          - Disable web integration
  • /web status       - Show detailed status and configuration
  • /web stats        - Show statistics and cache information
  • /web clear        - Clear web content cache

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

    def _toggle_interactive_mode(self):
        """Toggle interactive mode for code execution prompts"""
        self.interactive_mode = not self.interactive_mode
        status = "enabled" if self.interactive_mode else "disabled"
        color = "green" if self.interactive_mode else "yellow"

        self.console.print(f"[{color}]Interactive mode {status}[/{color}]")

        if self.interactive_mode:
            self.console.print(
                "[dim]You will be prompted before executing detected code blocks[/dim]"
            )
        else:
            self.console.print(
                "[dim]Code blocks will be automatically skipped without prompts[/dim]"
            )

    # ===== Provider Management Commands =====

    def _show_provider_status(self):
        """Show current provider status and connection info"""
        try:
            health = self.llm_provider.health_check()
            provider_type = self.llm_provider.get_provider_type().value.upper()
            current_model = self.llm_provider.get_current_model() or "None"

            # Status display
            status_info = f"""
[bold cyan]Provider Status:[/bold cyan]

🔧 Provider: [green]{provider_type}[/green]
🌐 Endpoint: {health.get('endpoint', 'Unknown')}
🔗 Connected: {'[green]Yes[/green]' if health.get('connected', False) else '[red]No[/red]'}
🤖 Current Model: [yellow]{current_model}[/yellow]
📊 Available Models: {len(health.get('available_models', []))}

💡 Use [bold]/providers[/bold] to see all available providers
💡 Use [bold]/switch <provider>[/bold] to change provider
💡 Use [bold]/models[/bold] to list and select models
"""

            self.console.print(
                Panel(status_info.strip(), title="Provider Information", border_style="cyan")
            )

            # Show connection help if not connected
            if not health.get("connected", False):
                self.console.print("\n[yellow]Connection Help:[/yellow]")
                self.console.print(
                    "  • Use [bold]/detect[/bold] to auto-detect available providers"
                )
                self.console.print("  • Use [bold]/server <url>[/bold] to set custom endpoint")
                self.console.print("  • Ensure your LLM server is running and accessible")

        except Exception as e:
            self.console.print(f"[red]Error getting provider status: {e}[/red]")

    def _list_available_providers(self):
        """List all available providers and their status"""
        self.console.print("[bold cyan]Available Providers:[/bold cyan]\n")

        providers = ["ollama", "lm_studio"]
        current_provider = self.llm_provider.get_provider_type().value

        for provider_name in providers:
            try:
                # Test connection to each provider
                test_provider = LLMProviderFactory.create_provider(provider_name)
                health = test_provider.health_check()
                connected = health.get("connected", False)
                endpoint = health.get("endpoint", "Unknown")

                status_icon = "🟢" if connected else "🔴"
                current_marker = (
                    " [bold yellow](current)[/bold yellow]"
                    if provider_name == current_provider
                    else ""
                )

                self.console.print(
                    f"{status_icon} [bold]{provider_name.upper()}[/bold]{current_marker}"
                )
                self.console.print(f"   Endpoint: {endpoint}")
                self.console.print(f"   Status: {'Connected' if connected else 'Not available'}")

                if connected:
                    models = health.get("available_models", [])
                    model_count = len(models)
                    self.console.print(f"   Models: {model_count} available")

                self.console.print()

            except Exception as e:
                status_icon = "❌"
                current_marker = (
                    " [bold yellow](current)[/bold yellow]"
                    if provider_name == current_provider
                    else ""
                )
                self.console.print(
                    f"{status_icon} [bold]{provider_name.upper()}[/bold]{current_marker}"
                )
                self.console.print(f"   Status: Error - {str(e)}")
                self.console.print()

        self.console.print("[dim]💡 Use [bold]/switch <provider>[/bold] to change provider[/dim]")

    def _switch_provider(self, provider_name: str):
        """Switch to a different provider"""
        provider_name = provider_name.lower()

        if provider_name not in ["ollama", "lm_studio"]:
            self.console.print(f"[red]Unknown provider: {provider_name}[/red]")
            self.console.print("[yellow]Available providers: ollama, lm_studio[/yellow]")
            return

        try:
            # Create new provider instance
            new_provider = LLMProviderFactory.create_provider(provider_name)

            # Test connection
            health = new_provider.health_check()
            if not health.get("connected", False):
                self.console.print(
                    f"[red]Cannot switch to {provider_name.upper()}: Not connected[/red]"
                )
                self.console.print(
                    f"[yellow]Endpoint: {health.get('endpoint', 'Unknown')}[/yellow]"
                )
                self.console.print("[dim]Make sure the server is running and accessible[/dim]")
                return

            # Switch provider
            old_provider = self.llm_provider.get_provider_type().value
            self.llm_provider = new_provider
            self.task_processor.llm_provider = new_provider  # Update task processor too

            # Get model info
            current_model = new_provider.get_current_model() or "None"
            available_models = health.get("available_models", [])

            self.console.print(
                f"[green]✅ Switched from {old_provider.upper()} to {provider_name.upper()}[/green]"
            )
            self.console.print(f"[blue]Endpoint: {health.get('endpoint')}[/blue]")
            self.console.print(f"[yellow]Current Model: {current_model}[/yellow]")
            self.console.print(f"[dim]Available Models: {len(available_models)}[/dim]")

            if len(available_models) > 1:
                self.console.print(
                    "\n[dim]💡 Use [bold]/models[/bold] to select a different model[/dim]"
                )

        except Exception as e:
            self.console.print(f"[red]Failed to switch to {provider_name}: {e}[/red]")

    def _auto_detect_provider(self):
        """Auto-detect the best available provider"""
        self.console.print("[blue]🔍 Auto-detecting providers...[/blue]")

        try:
            # Use factory's auto-detection
            detected_provider = LLMProviderFactory.create_auto_detect()
            health = detected_provider.health_check()

            if health.get("connected", False):
                provider_type = detected_provider.get_provider_type().value
                old_provider = self.llm_provider.get_provider_type().value

                if provider_type != old_provider:
                    self.llm_provider = detected_provider
                    self.task_processor.llm_provider = detected_provider

                    current_model = detected_provider.get_current_model() or "None"
                    available_models = health.get("available_models", [])

                    self.console.print(
                        f"[green]✅ Auto-detected and switched to {provider_type.upper()}[/green]"
                    )
                    self.console.print(f"[blue]Endpoint: {health.get('endpoint')}[/blue]")
                    self.console.print(f"[yellow]Current Model: {current_model}[/yellow]")
                    self.console.print(f"[dim]Available Models: {len(available_models)}[/dim]")
                else:
                    self.console.print(
                        f"[yellow]Already using the best available provider: {provider_type.upper()}[/yellow]"
                    )
            else:
                self.console.print("[red]❌ No providers available or connected[/red]")
                self.console.print("[dim]Make sure Ollama or LM Studio is running[/dim]")

        except Exception as e:
            self.console.print(f"[red]Auto-detection failed: {e}[/red]")

    def _set_server_endpoint(self, server_url: str):
        """Set custom server endpoint for current provider"""
        try:
            provider_type = self.llm_provider.get_provider_type().value

            # Create new provider with custom endpoint
            new_provider = LLMProviderFactory.create_provider(provider_type, base_url=server_url)

            # Test connection
            health = new_provider.health_check()
            if health.get("connected", False):
                self.llm_provider = new_provider
                self.task_processor.llm_provider = new_provider

                current_model = new_provider.get_current_model() or "None"
                available_models = health.get("available_models", [])

                self.console.print(f"[green]✅ Updated {provider_type.upper()} endpoint[/green]")
                self.console.print(f"[blue]New Endpoint: {server_url}[/blue]")
                self.console.print(f"[yellow]Current Model: {current_model}[/yellow]")
                self.console.print(f"[dim]Available Models: {len(available_models)}[/dim]")
            else:
                self.console.print(f"[red]❌ Cannot connect to {server_url}[/red]")
                self.console.print("[dim]Verify the URL and ensure the server is running[/dim]")

        except Exception as e:
            self.console.print(f"[red]Failed to set endpoint: {e}[/red]")

    def _list_and_select_models(self):
        """List available models and allow selection"""
        try:
            health = self.llm_provider.health_check()

            if not health.get("connected", False):
                self.console.print("[red]❌ Not connected to provider[/red]")
                self.console.print(
                    "[dim]Use [bold]/provider[/bold] to check connection status[/dim]"
                )
                return

            models = health.get("available_models", [])
            current_model = self.llm_provider.get_current_model()
            provider_type = self.llm_provider.get_provider_type().value.upper()

            if not models:
                self.console.print(f"[yellow]No models available from {provider_type}[/yellow]")
                return

            self.console.print(f"[bold cyan]Available Models ({provider_type}):[/bold cyan]\n")

            for i, model in enumerate(models, 1):
                current_marker = (
                    " [bold yellow](current)[/bold yellow]" if model == current_model else ""
                )
                self.console.print(f"  {i:2}. [green]{model}[/green]{current_marker}")

            self.console.print(f"\nCurrent model: [yellow]{current_model or 'None'}[/yellow]")
            self.console.print(
                "\n[dim]💡 Model selection/switching will be implemented in future version[/dim]"
            )
            self.console.print(
                "[dim]For now, use your provider's native tools to change models[/dim]"
            )

        except Exception as e:
            self.console.print(f"[red]Error listing models: {e}[/red]")

    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system("cls" if os.name == "nt" else "clear")

    def _show_conversation_history(self):
        """Show recent conversation history"""
        recent = self.history_manager.get_recent_conversation(10)
        if not recent:
            self.console.print("[yellow]No conversation history[/yellow]")
            return

        self.console.print("\\n[bold]Recent Conversation:[/bold]")
        for msg in recent:
            role_color = {"user": "green", "assistant": "blue", "system": "yellow"}.get(
                msg["role"], "white"
            )
            timestamp = msg["timestamp"].split("T")[1].split(".")[0]  # HH:MM:SS
            self.console.print(
                f"[{role_color}][{timestamp}] {msg['role']}:[/{role_color}] {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}"
            )

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
        health = self.llm_provider.health_check()

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
            if param in ["true", "on", "1", "yes", "enable"]:
                # Enable debug mode
                old_verbose = self.verbose
                self.verbose = True

                if old_verbose:
                    self.console.print("[yellow]🔧 Debug mode was already enabled[/yellow]")
                else:
                    self.console.print("[green]🔧 Debug mode enabled![/green]")
                    OSUtils.debug_print("Debug mode activated by user command", True)

            elif param in ["false", "off", "0", "no", "disable"]:
                # Disable debug mode
                old_verbose = self.verbose
                if old_verbose:
                    OSUtils.debug_print("Debug mode being deactivated by user command", True)

                self.verbose = False

                if old_verbose:
                    self.console.print("[yellow]🔧 Debug mode disabled[/yellow]")
                else:
                    self.console.print("[yellow]🔧 Debug mode was already disabled[/yellow]")

            elif param in ["info", "show", "status"]:
                # Show debug info
                self._show_debug_info()
            else:
                self.console.print(f"[red]Unknown debug parameter: {param}[/red]")
                self.console.print(
                    "[dim]Valid options: true/false/on/off/enable/disable/info/show[/dim]"
                )
        else:
            self.console.print(
                "[red]Usage: /debug [true|false|on|off|enable|disable|info|show][/red]"
            )

    def _show_debug_info(self):
        """Show comprehensive debug information including OS and platform details"""
        import platform

        # Get Ollama health info
        health = self.llm_provider.health_check()

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

        self.console.print(
            Panel(debug_text.strip(), title="🔧 Debug Information", border_style="cyan")
        )

    def _show_project_structure(self):
        """Show current project directory structure"""
        try:
            structure = self._read_current_directory_structure()
            project_mode = self._detect_project_mode()

            if structure:
                structure_display = self._format_directory_structure(structure)
                all_files = self._flatten_file_list(structure)

                mode_text = "🔧 Edit Mode" if project_mode == "edit" else "🆕 Create Mode"

                info_text = f"""
{mode_text} - Current Directory Structure

{structure_display}

📊 Summary:
• Total files: {len(all_files)}
• Code files: {len([f for f in all_files if f['name'].endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'))])}
• Config files: {len([f for f in all_files if f['name'] in ['package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml']])}
• Mode detected: {project_mode}
                """

                self.console.print(
                    Panel(
                        info_text.strip(),
                        title="Project Structure",
                        border_style="cyan",
                    )
                )
            else:
                self.console.print(
                    "[yellow]No files found in current directory or unable to read structure.[/yellow]"
                )

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

    def _display_web_integration_info(self, web_result):
        """Display information about web content that was processed"""
        if not web_result.extracted_contents:
            return

        info_parts = []

        for i, content in enumerate(web_result.extracted_contents, 1):
            title = content.title or "Untitled"
            word_count = content.word_count

            info_parts.append(f"📄 Page {i}: {title}")
            if word_count > 0:
                info_parts.append(f"   📊 {word_count} words processed")

            if content.language:
                info_parts.append(f"   💻 Technology: {content.language}")

            if content.code_blocks:
                info_parts.append(f"   🔧 {len(content.code_blocks)} code examples found")

        # Show summary
        processing_info = web_result.processing_info
        total_links = processing_info.get("links_found", 0)
        processed_links = processing_info.get("successful_extractions", 0)

        summary = f"🌐 Web Integration: Processed {processed_links}/{total_links} links"

        info_text = summary + "\n" + "\n".join(info_parts)

        self.console.print(
            Panel(info_text, title="Web Content Integrated", border_style="blue", padding=(0, 1))
        )

    def _handle_web_command(self, parameter: str = None):
        """Handle web integration commands"""
        if parameter is None:
            # Show current status
            self._show_web_status()
            return

        param = parameter.lower().strip()

        if param in ["on", "enable", "true", "1"]:
            self.web_manager.set_enabled(True)
            self.app_state.set_preference("web_integration_enabled", True)
            self.console.print("🌐 [green]Web integration enabled[/green]")
            self.console.print(
                "Links in your messages will now be automatically fetched and processed."
            )

        elif param in ["off", "disable", "false", "0"]:
            self.web_manager.set_enabled(False)
            self.app_state.set_preference("web_integration_enabled", False)
            self.console.print("🌐 [yellow]Web integration disabled[/yellow]")

        elif param == "status":
            self._show_web_status()

        elif param == "clear":
            self.web_manager.clear_cache()
            self.console.print("🗑️ Web content cache cleared")

        elif param == "stats":
            self._show_web_stats()

        else:
            self.console.print(
                """[yellow]Web Integration Commands:[/yellow]

/web                 - Show current status
/web on              - Enable web integration
/web off             - Disable web integration
/web status          - Show detailed status
/web stats           - Show statistics
/web clear           - Clear web content cache

When enabled, links in your messages will be automatically fetched
and their content added to the AI's context for better assistance.

Note: Only processes links that appear in regular text, not in
commands or code examples."""
            )

    def _show_web_status(self):
        """Show current web integration status"""
        enabled = self.web_manager.is_enabled()
        stats = self.web_manager.get_stats()
        cache_info = self.web_manager.get_cache_info()

        status_text = f"""🌐 Web Integration Status: {'🟢 ENABLED' if enabled else '🔴 DISABLED'}

Configuration:
• Request timeout: {stats['timeout']} seconds
• Max links per request: {stats['max_links']}
• Cache size: {cache_info['size']}/{cache_info['max_size']}

Components:
• Link detector: {stats['components']['link_detector']}
• Web fetcher: {stats['components']['web_fetcher']}
• Content extractor: {stats['components']['content_extractor']}

Usage: Type '/web on' to enable or '/web help' for more options."""

        self.console.print(
            Panel(status_text, title="Web Integration", border_style="blue" if enabled else "dim")
        )

    def _show_web_stats(self):
        """Show web integration statistics"""
        cache_info = self.web_manager.get_cache_info()
        stats = self.web_manager.get_stats()

        stats_text = f"""📊 Web Integration Statistics

Cache Information:
• Cached URLs: {cache_info['size']}
• Cache capacity: {cache_info['max_size']}
• Memory efficiency: {cache_info['size']}/{cache_info['max_size']} ({(cache_info['size']/cache_info['max_size']*100):.1f}%)

Configuration:
• Timeout: {stats['timeout']}s
• Max links: {stats['max_links']}
• Status: {'Enabled' if stats['enabled'] else 'Disabled'}"""

        if cache_info["urls"]:
            stats_text += "\n\nRecently cached domains:"
            domains = set()
            for url in cache_info["urls"][-10:]:  # Show last 10
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    continue

            for domain in sorted(domains):
                stats_text += f"\n• {domain}"

        self.console.print(
            Panel(stats_text, title="Web Integration Statistics", border_style="cyan")
        )
