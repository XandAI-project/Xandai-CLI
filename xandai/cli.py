#!/usr/bin/env python3
"""
XandAI CLI - Main CLI
Main coordination system with Chat Mode and Task Mode support
"""

import sys
import os
import click
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from xandai.core.app_state import AppState
from xandai.core.command_processor import CommandProcessor
from xandai.processors.chat_processor import ChatProcessor
from xandai.processors.task_processor import TaskProcessor
from xandai.conversation.conversation_manager import ConversationManager
from xandai.integrations.ollama_client import OllamaClient
from xandai.utils.display_utils import DisplayUtils


class XandAICLI:
    """
    XandAI Main CLI
    Coordinates interactions between components and manages application state
    """
    
    def __init__(self):
        self.console = Console()
        self.app_state = AppState()
        self.command_processor = CommandProcessor(self.app_state)
        self.conversation_manager = ConversationManager()
        self.ollama_client = OllamaClient()
        self.chat_processor = ChatProcessor(self.ollama_client, self.conversation_manager)
        self.task_processor = TaskProcessor(self.ollama_client, self.conversation_manager)
        self.display = DisplayUtils(self.console)
        
        # EditModeEnhancer state variables
        self.forced_mode: Optional[str] = None  # 'edit', 'create', or None
        self.auto_mode: bool = True
        
        # Command mappings
        self.commands = {
            "/help": self._show_help,
            "/exit": self._exit_application,
            "/quit": self._exit_application,
            "/clear": self._clear_session,
            "/history": self._show_history,
            "/status": self._show_status,
            # EditModeEnhancer commands
            "/edit": self._force_edit_mode,
            "/create": self._force_create_mode,
            "/mode": self._show_current_mode,
            "/auto": self._enable_auto_mode,
            # Task mode
            "/task": self._process_task_mode,
            # Ollama connection management
            "/ollama": self._show_ollama_status,
            "/server": self._set_ollama_server,
            "/list-models": self._list_and_select_models,
            "/models": self._list_and_select_models
        }
    
    def run(self, initial_input: Optional[str] = None):
        """
        Main application loop
        """
        try:
            self._show_welcome()
            
            # If there's initial input, process it and exit
            if initial_input:
                self._process_input(initial_input)
                return
            
            # Interactive loop
            while True:
                try:
                    user_input = self._get_user_input()
                    if not user_input.strip():
                        continue
                    
                    self._process_input(user_input)
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Exiting...[/yellow]")
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            self.console.print(f"[red]Fatal error: {e}[/red]")
            sys.exit(1)
    
    def _process_input(self, user_input: str):
        """
        Processes user input - commands or conversation
        """
        user_input = user_input.strip()
        
        # Check if it's a command
        if user_input.startswith("/"):
            self._process_command(user_input)
            return
        
        # Determine mode based on EditModeEnhancer
        current_mode = self._determine_current_mode(user_input)
        
        # Process based on mode
        if current_mode == "task":
            self._handle_task_mode(user_input)
        else:
            self._handle_chat_mode(user_input)
    
    def _process_command(self, command_input: str):
        """
        Processes system commands
        """
        parts = command_input.split(" ", 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        if command in self.commands:
            self.commands[command](args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("Type [bold]/help[/bold] to see available commands")
    
    def _determine_current_mode(self, user_input: str) -> str:
        """
        EditModeEnhancer: Determines current mode based on context
        """
        # If forced mode, use it
        if self.forced_mode:
            return self.forced_mode
        
        # If automatic mode, analyze context
        if self.auto_mode:
            return self.command_processor.detect_mode(user_input)
        
        # Default: chat mode
        return "chat"
    
    def _handle_chat_mode(self, user_input: str):
        """
        Processes input in Chat Mode
        """
        try:
            response = self.chat_processor.process(user_input, self.app_state)
            self.display.show_chat_response(response)
        except ConnectionError as e:
            # Special handling for Ollama connection errors
            self.display.show_error(str(e), "Ollama Connection")
            self.console.print("\n[yellow]Tip: Use [bold]/ollama[/bold] to check connection status or [bold]/server[/bold] to set a different server.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error in chat mode: {e}[/red]")
    
    def _handle_task_mode(self, user_input: str):
        """
        Processes input in Task Mode
        """
        try:
            task_result = self.task_processor.process(user_input, self.app_state)
            self.display.show_task_result(task_result)
        except ConnectionError as e:
            # Special handling for Ollama connection errors
            self.display.show_error(str(e), "Ollama Connection")
            self.console.print("\n[yellow]Tip: Use [bold]/ollama[/bold] to check connection status or [bold]/server[/bold] to set a different server.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error in task mode: {e}[/red]")
    
    # ===== EditModeEnhancer Commands =====
    
    def _force_edit_mode(self, args: str):
        """Forces edit mode (for existing projects)"""
        self.forced_mode = "edit"
        self.auto_mode = False
        self.console.print("[green]✓[/green] Forced mode set to [bold]EDIT[/bold] - ideal for updating existing projects")
    
    def _force_create_mode(self, args: str):
        """Forces create mode (for new projects)"""
        self.forced_mode = "create"
        self.auto_mode = False
        self.console.print("[green]✓[/green] Forced mode set to [bold]CREATE[/bold] - ideal for new projects")
    
    def _show_current_mode(self, args: str):
        """Shows current mode"""
        if self.forced_mode:
            mode_text = f"Forced: [bold]{self.forced_mode.upper()}[/bold]"
        else:
            mode_text = "Automatic (context detection)"
        
        self.console.print(f"[blue]Current mode:[/blue] {mode_text}")
    
    def _enable_auto_mode(self, args: str):
        """Enables automatic mode detection"""
        self.forced_mode = None
        self.auto_mode = True
        self.console.print("[green]✓[/green] Automatic mode enabled - will detect context automatically")
    
    # ===== Task Mode Command =====
    
    def _process_task_mode(self, args: str):
        """Processes /task command"""
        if not args.strip():
            self.console.print("[yellow]Usage: /task <task description>[/yellow]")
            return
        
        # Force task mode temporarily
        previous_mode = self.forced_mode
        self.forced_mode = "task"
        try:
            self._handle_task_mode(args)
        finally:
            self.forced_mode = previous_mode
    
    # ===== Utility Commands =====
    
    def _show_help(self, args: str):
        """Shows command help"""
        help_text = """
[bold]XandAI - Available Commands[/bold]

[cyan]Basic Commands:[/cyan]
  /help          - Shows this help
  /exit, /quit   - Exit application
  /clear         - Clear current session
  /history       - Show conversation history
  /status        - Show application status

[cyan]EditModeEnhancer:[/cyan]
  /edit          - Force EDIT mode (update existing projects)
  /create        - Force CREATE mode (new projects)
  /mode          - Show current mode
  /auto          - Enable automatic detection

[cyan]Task Mode:[/cyan]
  /task <desc>   - Process task with structured output

[cyan]Ollama Management:[/cyan]
  /ollama        - Show Ollama connection status
  /server <url>  - Set Ollama server URL
  /list-models   - List available models and select one
  /models        - Alias for /list-models

[cyan]Operation Modes:[/cyan]
  [bold]Chat Mode[/bold] (default): Context-aware conversation
  [bold]Task Mode[/bold]: Structured output for automation
        """
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def _show_ollama_status(self, args: str):
        """Shows detailed Ollama connection status"""
        status = self.ollama_client.get_connection_status()
        
        if status["connected"]:
            self.console.print("[green]✓ Ollama is connected[/green]")
            self.console.print(f"Server: {status['base_url']}")
            self.console.print(f"Current Model: {status['current_model']}")
            
            if status["available_models"]:
                self.console.print(f"Available Models ({status['model_count']}):")
                for model in status["available_models"][:10]:  # Show first 10
                    self.console.print(f"  • {model}")
                if status["model_count"] > 10:
                    self.console.print(f"  ... and {status['model_count'] - 10} more")
            else:
                self.console.print("[yellow]No models found[/yellow]")
        else:
            self.console.print("[red]✗ Ollama is not connected[/red]")
            self.console.print(f"Trying to connect to: {status['base_url']}")
            
            if "error_help" in status:
                self.console.print("\n[yellow]Connection Help:[/yellow]")
                for help_item in status["error_help"]:
                    self.console.print(f"  {help_item}")
                    
            self.console.print("\n[cyan]Commands:[/cyan]")
            self.console.print("  [bold]/server <url>[/bold] - Set Ollama server URL")
            self.console.print("  [bold]/server[/bold] - Prompt for server URL")
            self.console.print("  [bold]/list-models[/bold] - List and select models")
            self.console.print("  [bold]/models[/bold] - Alias for /list-models")
    
    def _set_ollama_server(self, args: str):
        """Sets Ollama server URL"""
        if args.strip():
            new_url = args.strip()
        else:
            # Prompt for URL
            try:
                new_url = input("Enter Ollama server URL (e.g., http://localhost:11434): ").strip()
                if not new_url:
                    self.console.print("[yellow]No URL provided, keeping current server[/yellow]")
                    return
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Cancelled[/yellow]")
                return
        
        # Validate URL format
        if not (new_url.startswith('http://') or new_url.startswith('https://')):
            new_url = 'http://' + new_url
        
        old_url = self.ollama_client.base_url
        self.console.print(f"Switching from [dim]{old_url}[/dim] to [bold]{new_url}[/bold]...")
        
        # Update the client
        self.ollama_client.set_base_url(new_url)
        
        # Test connection
        if self.ollama_client.is_connected():
            self.console.print("[green]✓ Successfully connected to Ollama![/green]")
            
            # Show available models
            models = self.ollama_client.list_models()
            if models:
                self.console.print(f"Found {len(models)} model(s): {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
                
                # Ask if user wants to select a model
                self.console.print("\n[cyan]Would you like to select a model? (y/n)[/cyan]")
                try:
                    choice = input("> ").strip().lower()
                    if choice in ['y', 'yes']:
                        self._show_model_selection(models)
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[yellow]Skipped model selection[/yellow]")
            else:
                self.console.print("[yellow]No models found. You may need to pull a model first.[/yellow]")
                self.console.print("Example: [bold]ollama pull llama3.2[/bold]")
        else:
            self.console.print(f"[red]✗ Could not connect to {new_url}[/red]")
            self.console.print("Please check the URL and ensure Ollama is running.")
    
    def _list_and_select_models(self, args: str):
        """Lists available models and allows selection"""
        if not self.ollama_client.is_connected():
            self.console.print("[red]✗ Ollama is not connected[/red]")
            self.console.print("Use [bold]/server[/bold] to connect to an Ollama server first.")
            return
        
        models = self.ollama_client.list_models()
        if not models:
            self.console.print("[yellow]No models found.[/yellow]")
            self.console.print("You may need to pull a model first:")
            self.console.print("Example: [bold]ollama pull llama3.2[/bold]")
            return
        
        self._show_model_selection(models)
    
    def _show_model_selection(self, models: List[str]):
        """Shows model selection interface"""
        current_model = self.ollama_client.get_current_model()
        
        self.console.print(f"\n[cyan]Available Models ({len(models)}):[/cyan]")
        self.console.print(f"[dim]Current model: [bold]{current_model}[/bold][/dim]")
        self.console.print()
        
        # Display models with numbers
        for i, model in enumerate(models, 1):
            prefix = "[green]✓[/green]" if model == current_model else " "
            # Truncate long model names for display
            display_name = model if len(model) <= 50 else model[:47] + "..."
            self.console.print(f"{prefix} {i:2d}. {display_name}")
        
        self.console.print(f"\n[cyan]Enter model number (1-{len(models)}) or press Enter to cancel:[/cyan]")
        
        try:
            choice = input("> ").strip()
            if not choice:
                self.console.print("[yellow]Model selection cancelled[/yellow]")
                return
            
            try:
                model_index = int(choice) - 1
                if 0 <= model_index < len(models):
                    selected_model = models[model_index]
                    
                    # Set the model
                    try:
                        self.ollama_client.set_model(selected_model)
                        self.console.print(f"[green]✓ Model set to: [bold]{selected_model}[/bold][/green]")
                        
                        # Show model info if available
                        model_info = self.ollama_client.get_model_info(selected_model)
                        if model_info and 'details' in model_info:
                            details = model_info['details']
                            if 'parameter_size' in details:
                                self.console.print(f"[dim]Parameters: {details['parameter_size']}[/dim]")
                            if 'quantization_level' in details:
                                self.console.print(f"[dim]Quantization: {details['quantization_level']}[/dim]")
                    except Exception as e:
                        self.console.print(f"[red]Error setting model: {e}[/red]")
                else:
                    self.console.print(f"[red]Invalid selection. Please choose 1-{len(models)}[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
                
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Model selection cancelled[/yellow]")
    
    def _exit_application(self, args: str):
        """Exits the application"""
        self.console.print("[yellow]Shutting down XandAI...[/yellow]")
        sys.exit(0)
    
    def _clear_session(self, args: str):
        """Clears current session"""
        self.conversation_manager.clear_session()
        self.app_state.reset()
        self.console.print("[green]✓[/green] Session cleared")
    
    def _show_history(self, args: str):
        """Shows conversation history"""
        history = self.conversation_manager.get_recent_history(limit=10)
        self.display.show_history(history)
    
    def _show_status(self, args: str):
        """Shows application status"""
        ollama_status = self.ollama_client.get_connection_status()
        status = {
            "Mode": self._get_mode_description(),
            "Ollama Server": ollama_status["base_url"],
            "Ollama Connected": "Yes" if ollama_status["connected"] else "No",
            "Current Model": ollama_status["current_model"],
            "Available Models": ollama_status["model_count"],
            "Conversations": len(self.conversation_manager.get_recent_history()),
            "Status": "Active"
        }
        self.display.show_status(status)
        
        # Show connection help if not connected
        if not ollama_status["connected"] and "error_help" in ollama_status:
            self.console.print("\n[yellow]Ollama Connection Help:[/yellow]")
            for help_item in ollama_status["error_help"]:
                self.console.print(f"  {help_item}")
    
    def _get_mode_description(self) -> str:
        """Returns current mode description"""
        if self.forced_mode:
            return f"Forced: {self.forced_mode.upper()}"
        return "Automatic"
    
    def _show_welcome(self):
        """Shows welcome message"""
        welcome_text = Text()
        welcome_text.append("XandAI", style="bold blue")
        welcome_text.append(" - CLI Assistant v2.0\n")
        welcome_text.append("Ollama Integration | Context-Aware | Multi-Mode\n\n")
        welcome_text.append("Type ", style="dim")
        welcome_text.append("/help", style="bold")
        welcome_text.append(" for commands or start chatting!", style="dim")
        
        self.console.print(Panel(welcome_text, title="Welcome", border_style="green"))
    
    def _get_user_input(self) -> str:
        """Gets user input with custom prompt"""
        mode_indicator = self._get_mode_indicator()
        return input(f"{mode_indicator} ")
    
    def _get_mode_indicator(self) -> str:
        """Returns visual indicator of current mode"""
        if self.forced_mode == "edit":
            return "🔧 [EDIT]>"
        elif self.forced_mode == "create":
            return "✨ [CREATE]>"
        elif self.forced_mode == "task":
            return "📋 [TASK]>"
        else:
            return "💬 [AUTO]>"


@click.command()
@click.option("--model", "-m", default="llama3.2", help="Ollama model to use")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.argument("input_text", required=False)
def main(model: str, verbose: bool, input_text: Optional[str]):
    """
    XandAI - CLI Assistant with Ollama Integration
    
    Examples:
      xandai                           # Interactive mode
      xandai "explain clean code"      # Direct chat mode
      xandai "/task create an API"     # Direct task mode
    """
    
    # Global configuration
    if verbose:
        os.environ["XANDAI_VERBOSE"] = "1"
    os.environ["XANDAI_MODEL"] = model
    
    # Initialize and run CLI
    cli = XandAICLI()
    cli.run(input_text)


if __name__ == "__main__":
    main()
