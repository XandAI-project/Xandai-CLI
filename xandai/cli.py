#!/usr/bin/env python3
"""
XandAI CLI - Main CLI
Main coordination system with Chat Mode support
"""

import os
import sys
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from xandai.conversation.conversation_manager import ConversationManager
from xandai.core.app_state import AppState
from xandai.core.command_processor import CommandProcessor
from xandai.integrations.base_provider import LLMProvider
from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.processors.agent_processor import AgentProcessor
from xandai.processors.chat_processor import ChatProcessor
from xandai.processors.review_processor import ReviewProcessor
from xandai.processors.task_processor import TaskProcessor
from xandai.utils.display_utils import DisplayUtils
from xandai.utils.tool_manager import ToolManager


class XandAICLI:
    """
    XandAI Main CLI
    Coordinates interactions between components and manages application state
    """

    def __init__(self, provider_type: str = "ollama"):
        self.console = Console()
        self.app_state = AppState()
        self.command_processor = CommandProcessor(self.app_state)
        self.conversation_manager = ConversationManager()

        # Initialize LLM Provider with auto-detection fallback
        try:
            self.llm_provider = LLMProviderFactory.create_provider(provider_type)
        except Exception:
            self.llm_provider = LLMProviderFactory.create_auto_detect()

        # Tool manager for custom tools
        self.tool_manager = ToolManager(
            tools_dir="tools", llm_provider=self.llm_provider, verbose=False
        )

        self.chat_processor = ChatProcessor(self.llm_provider, self.conversation_manager)
        self.task_processor = TaskProcessor(self.llm_provider, self.conversation_manager)
        self.review_processor = ReviewProcessor(self.llm_provider, self.conversation_manager)
        self.agent_processor = AgentProcessor(
            self.llm_provider, self.conversation_manager, self.tool_manager
        )
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
            # Review mode
            "/review": self._process_review_mode,
            # Provider management
            "/provider": self._show_provider_status,
            "/providers": self._list_providers,
            "/switch": self._switch_provider,
            "/detect": self._auto_detect_provider,
            "/server": self._set_server_endpoint,
            "/list-models": self._list_and_select_models,
            "/models": self._list_and_select_models,
            # Agent mode
            "/agent": self._process_agent_mode,
            "/set-agent-limit": self._set_agent_limit,
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
            self.console.print(
                "\n[yellow]Tip: Use [bold]/ollama[/bold] to check connection status or [bold]/server[/bold] to set a different server.[/yellow]"
            )
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
            self.console.print(
                "\n[yellow]Tip: Use [bold]/ollama[/bold] to check connection status or [bold]/server[/bold] to set a different server.[/yellow]"
            )
        except Exception as e:
            self.console.print(f"[red]Error in task mode: {e}[/red]")

    # ===== EditModeEnhancer Commands =====

    def _force_edit_mode(self, args: str):
        """Forces edit mode (for existing projects)"""
        self.forced_mode = "edit"
        self.auto_mode = False
        self.console.print(
            "[green]✓[/green] Forced mode set to [bold]EDIT[/bold] - ideal for updating existing projects"
        )

    def _force_create_mode(self, args: str):
        """Forces create mode (for new projects)"""
        self.forced_mode = "create"
        self.auto_mode = False
        self.console.print(
            "[green]✓[/green] Forced mode set to [bold]CREATE[/bold] - ideal for new projects"
        )

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
        self.console.print(
            "[green]✓[/green] Automatic mode enabled - will detect context automatically"
        )

    # ===== Task Mode Command =====

    def _process_task_mode(self, args: str):
        """Processes /task command (DEPRECATED)"""
        self.console.print(
            "[yellow]⚠️  WARNING: The /task command is deprecated and will be removed in a future version.[/yellow]"
        )
        self.console.print(
            "[dim]💡 Use natural conversation instead of /task for better experience.[/dim]\n"
        )

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

    def _process_review_mode(self, args: str):
        """Processes /review command"""
        try:
            self.console.print("[dim]🔍 Analyzing Git changes...[/dim]")

            # Get current directory or use args as path
            repo_path = args.strip() if args.strip() else "."

            # Process code review
            review_result = self.review_processor.process(self.app_state, repo_path)

            # Display review results
            self.display.show_review_result(review_result)

        except Exception as e:
            self.console.print(f"[red]Review error: {e}[/red]")
            self.console.print("Check if you're in a Git repository with changes to review")

    def _process_agent_mode(self, args: str):
        """Processes /agent command - multi-step LLM orchestrator"""
        if not args.strip():
            self.console.print("[yellow]Usage: /agent <instruction>[/yellow]")
            self.console.print("[dim]Example: /agent fix the bug in main.py[/dim]")
            self.console.print(f"[dim]Current limit: {self.agent_processor.max_calls} calls[/dim]")
            return

        try:
            self.console.print("[bold cyan]🤖 Agent Mode - Multi-Step Processing[/bold cyan]")
            self.console.print(f"[dim]Max calls: {self.agent_processor.max_calls}[/dim]\n")

            self.console.print("[dim]💭 Starting multi-step reasoning...[/dim]")

            # Enable verbose temporarily to show progress
            original_verbose = self.agent_processor.verbose
            self.agent_processor.verbose = True

            # Process through agent
            result = self.agent_processor.process(args, self.app_state)

            # Restore verbose setting
            self.agent_processor.verbose = original_verbose

            # Display step-by-step progress
            self.console.print("[bold]Agent Execution Steps:[/bold]\n")

            for step in result.steps:
                status_icon = "✅" if step.success else "❌"
                self.console.print(f"{status_icon} [Step {step.step_number}] {step.step_name}")
                if self.app_state.verbose_mode and step.response:
                    # Show summary in verbose mode
                    summary = (
                        step.response[:100] + "..." if len(step.response) > 100 else step.response
                    )
                    self.console.print(f"[dim]  → {summary}[/dim]")

            self.console.print()

            # Show final result
            if result.success:
                self.console.print("[bold green]✓ Agent Task Complete[/bold green]")
                self.console.print(f"[dim]Reason: {result.stopped_reason}[/dim]")
                self.console.print(
                    f"[dim]Total calls: {result.total_calls}/{self.agent_processor.max_calls}[/dim]"
                )
                self.console.print(f"[dim]Total tokens: {result.total_tokens}[/dim]\n")

                # Display final output
                self.console.print(
                    Panel(result.final_output, title="Agent Output", border_style="green")
                )

                # Display files created/edited
                if result.files_created or result.files_edited:
                    self.console.print()
                    if result.files_created:
                        self.console.print("[bold green]📝 Files Created:[/bold green]")
                        for file in result.files_created:
                            self.console.print(f"  ✓ {file}")

                    if result.files_edited:
                        self.console.print("[bold yellow]✏️  Files Edited:[/bold yellow]")
                        for file in result.files_edited:
                            self.console.print(f"  ✓ {file}")

                # Display commands executed
                if result.commands_executed:
                    self.console.print()
                    self.console.print("[bold blue]⚙️  Commands Executed:[/bold blue]")
                    for cmd, output in result.commands_executed:
                        status = (
                            "✓"
                            if output and "ERROR" not in output and "TIMEOUT" not in output
                            else "✗"
                        )
                        self.console.print(f"  {status} {cmd}")
                        if self.app_state.verbose_mode and output:
                            # Show command output in verbose mode
                            output_preview = output[:100] + "..." if len(output) > 100 else output
                            self.console.print(f"     [dim]{output_preview}[/dim]")
            else:
                self.console.print("[bold red]✗ Agent Task Failed[/bold red]")
                if result.error_message:
                    self.console.print(f"[red]Error: {result.error_message}[/red]")
                self.console.print(f"[dim]Calls made: {result.total_calls}[/dim]\n")

        except ConnectionError as e:
            self.display.show_error(str(e), "LLM Connection")
        except Exception as e:
            self.console.print(f"[red]Agent error: {e}[/red]")

    def _set_agent_limit(self, args: str):
        """Sets the maximum number of LLM calls for agent mode"""
        if not args.strip():
            self.console.print(
                f"[cyan]Current agent limit:[/cyan] {self.agent_processor.max_calls} calls"
            )
            self.console.print("[dim]Usage: /set-agent-limit <number>[/dim]")
            self.console.print("[dim]Example: /set-agent-limit 30[/dim]")
            return

        try:
            new_limit = int(args.strip())
            self.agent_processor.set_max_calls(new_limit)
            self.console.print(f"[green]✓ Agent limit set to {new_limit} calls[/green]")
        except ValueError as e:
            if "at least 1" in str(e):
                self.console.print("[red]Error: Limit must be at least 1[/red]")
            elif "cannot exceed 100" in str(e):
                self.console.print("[red]Error: Limit cannot exceed 100[/red]")
            else:
                self.console.print(f"[red]Error: Please provide a valid number[/red]")
        except Exception as e:
            self.console.print(f"[red]Error setting limit: {e}[/red]")

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

[cyan]Task Mode (DEPRECATED):[/cyan]
  /task <desc>   - [DEPRECATED] Use natural conversation instead

[cyan]Agent Mode:[/cyan]
  /agent <instruction>  - Multi-step LLM orchestrator
                          Chains multiple AI calls for complex tasks
  /set-agent-limit <n>  - Set max LLM calls (default: 20, max: 100)

[cyan]Code Review:[/cyan]
  /review [path] - Analyze Git changes and provide code review

[cyan]LLM Provider Management:[/cyan]
  /provider      - Show provider connection status
  /providers     - List all available providers
  /switch <name> - Switch to another provider
  /detect        - Auto-detect available provider
  /server <url>  - Set server URL
  /list-models   - List available models and select one
  /models        - Alias for /list-models

[cyan]Operation Modes:[/cyan]
  [bold]Chat Mode[/bold] (default): Context-aware conversation
  [bold]Agent Mode[/bold]: Multi-step reasoning and task execution
  [bold]Task Mode[/bold]: [DEPRECATED] Use natural conversation
        """
        self.console.print(Panel(help_text, title="Help", border_style="blue"))

    def _show_provider_status(self, args: str):
        """Shows detailed provider connection status"""
        status = self.llm_provider.health_check()
        provider_name = self.llm_provider.get_provider_type().value.title()

        if status["connected"]:
            self.console.print(f"[green]✓ {provider_name} is connected[/green]")
            self.console.print(f"Endpoint: {status.get('endpoint', 'unknown')}")
            self.console.print(f"Current Model: {status.get('current_model', 'None')}")

            if status.get("available_models"):
                model_count = len(status["available_models"])
                self.console.print(f"Available Models ({model_count}):")
                for model in status["available_models"][:10]:  # Show first 10
                    self.console.print(f"  • {model}")
                if model_count > 10:
                    self.console.print(f"  ... and {model_count - 10} more")
            else:
                self.console.print("[yellow]No models found[/yellow]")
        else:
            self.console.print(f"[red]✗ {provider_name} is not connected[/red]")
            self.console.print(f"Endpoint: {status.get('endpoint', 'unknown')}")

            self.console.print("\n[cyan]Commands:[/cyan]")
            self.console.print("  [bold]/switch <provider>[/bold] - Switch to another provider")
            self.console.print("  [bold]/detect[/bold] - Auto-detect available provider")
            self.console.print("  [bold]/server <url>[/bold] - Set server endpoint")
            self.console.print("  [bold]/list-models[/bold] - List and select models")

    def _list_providers(self, args: str):
        """List all available providers"""
        providers = LLMProviderFactory.get_supported_providers()
        current_provider = self.llm_provider.get_provider_type().value

        self.console.print("\n[cyan]Available Providers:[/cyan]")
        for provider in providers:
            indicator = "[green]✓[/green]" if provider == current_provider else " "
            self.console.print(f"{indicator} {provider.title()}")

        self.console.print(f"\nCurrent provider: [bold]{current_provider.title()}[/bold]")
        self.console.print("Use [bold]/switch <provider>[/bold] to change providers")

    def _switch_provider(self, args: str):
        """Switch to a different provider"""
        if not args.strip():
            self.console.print("[yellow]Usage: /switch <provider>[/yellow]")
            self.console.print("Available: ollama, lm_studio")
            return

        new_provider = args.strip().lower()
        current_provider = self.llm_provider.get_provider_type().value

        if new_provider == current_provider:
            self.console.print(f"[yellow]Already using {new_provider.title()}[/yellow]")
            return

        try:
            # Create new provider
            new_llm_provider = LLMProviderFactory.create_provider(new_provider)

            # Test connection
            if new_llm_provider.is_connected():
                self.llm_provider = new_llm_provider

                # Update processors
                self.chat_processor = ChatProcessor(self.llm_provider, self.conversation_manager)
                self.task_processor = TaskProcessor(self.llm_provider, self.conversation_manager)
                self.review_processor = ReviewProcessor(
                    self.llm_provider, self.conversation_manager
                )
                self.agent_processor = AgentProcessor(
                    self.llm_provider, self.conversation_manager, self.tool_manager
                )
                self.tool_manager.llm_provider = new_llm_provider

                self.console.print(f"[green]✓ Switched to {new_provider.title()}[/green]")

                # Show available models and prompt selection if multiple
                models = self.llm_provider.list_models()
                if models:
                    if len(models) > 1:
                        self.console.print(f"Found {len(models)} models. Please select one:")
                        self._show_model_selection(models)
                    else:
                        self.llm_provider.set_model(models[0])
                        self.console.print(f"Using only available model: {models[0]}")
                else:
                    self.console.print("No models found")
            else:
                self.console.print(f"[red]✗ Could not connect to {new_provider.title()}[/red]")
                self.console.print("Please ensure the provider is running and accessible")

        except Exception as e:
            self.console.print(f"[red]Error switching to {new_provider}: {e}[/red]")

    def _auto_detect_provider(self, args: str):
        """Auto-detect the best available provider"""
        self.console.print("[dim]🔍 Auto-detecting providers...[/dim]")

        try:
            new_llm_provider = LLMProviderFactory.create_auto_detect()
            detected_provider = new_llm_provider.get_provider_type().value

            self.llm_provider = new_llm_provider

            # Update processors
            self.chat_processor = ChatProcessor(self.llm_provider, self.conversation_manager)
            self.task_processor = TaskProcessor(self.llm_provider, self.conversation_manager)
            self.review_processor = ReviewProcessor(self.llm_provider, self.conversation_manager)
            self.agent_processor = AgentProcessor(
                self.llm_provider, self.conversation_manager, self.tool_manager
            )
            self.tool_manager.llm_provider = new_llm_provider

            self.console.print(
                f"[green]✓ Auto-detected and switched to {detected_provider.title()}[/green]"
            )

            # Show status and handle model selection
            status = self.llm_provider.health_check()
            if status.get("available_models"):
                models = status["available_models"]
                model_count = len(models)
                if model_count > 1:
                    self.console.print(f"Found {model_count} models. Please select one:")
                    self._show_model_selection(models)
                else:
                    self.llm_provider.set_model(models[0])
                    self.console.print(f"Using only available model: {models[0]}")

        except Exception as e:
            self.console.print(f"[red]Auto-detection failed: {e}[/red]")

    def _set_server_endpoint(self, args: str):
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
        if not (new_url.startswith("http://") or new_url.startswith("https://")):
            new_url = "http://" + new_url

        old_url = self.llm_provider.get_base_url()
        self.console.print(f"Switching from [dim]{old_url}[/dim] to [bold]{new_url}[/bold]...")

        # Update the provider endpoint (this would need provider-specific implementation)
        # For now, we'll create a new provider with the new URL
        try:
            current_provider_type = self.llm_provider.get_provider_type().value
            self.llm_provider = LLMProviderFactory.create_provider(
                current_provider_type, base_url=new_url
            )

            # Update processors
            self.chat_processor = ChatProcessor(self.llm_provider, self.conversation_manager)
            self.task_processor = TaskProcessor(self.llm_provider, self.conversation_manager)
            self.review_processor = ReviewProcessor(self.llm_provider, self.conversation_manager)
            self.agent_processor = AgentProcessor(
                self.llm_provider, self.conversation_manager, self.tool_manager
            )
            self.tool_manager.llm_provider = self.llm_provider
        except Exception as e:
            self.console.print(f"[red]Failed to update endpoint: {e}[/red]")
            return

        # Test connection
        if self.llm_provider.is_connected():
            provider_name = self.llm_provider.get_provider_type().value.title()
            self.console.print(f"[green]✓ Successfully connected to {provider_name}![/green]")

            # Show available models and handle selection
            models = self.llm_provider.list_models()
            if models:
                if len(models) > 1:
                    self.console.print(f"Found {len(models)} models. Please select one:")
                    self._show_model_selection(models)
                else:
                    self.llm_provider.set_model(models[0])
                    self.console.print(f"Using only available model: {models[0]}")
            else:
                self.console.print(
                    "[yellow]No models found. You may need to pull a model first.[/yellow]"
                )
                self.console.print("Example: [bold]ollama pull llama3.2[/bold]")
        else:
            self.console.print(f"[red]✗ Could not connect to {new_url}[/red]")
            self.console.print("Please check the URL and ensure Ollama is running.")

    def _list_and_select_models(self, args: str):
        """Lists available models and allows selection"""
        if not self.llm_provider.is_connected():
            provider_name = self.llm_provider.get_provider_type().value.title()
            self.console.print(f"[red]✗ {provider_name} is not connected[/red]")
            self.console.print(
                "Use [bold]/server[/bold] or [bold]/switch[/bold] to connect to a provider first."
            )
            return

        models = self.llm_provider.list_models()
        if not models:
            self.console.print("[yellow]No models found.[/yellow]")
            self.console.print("You may need to pull a model first:")
            self.console.print("Example: [bold]ollama pull llama3.2[/bold]")
            return

        self._show_model_selection(models)

    def _show_model_selection(self, models: List[str]):
        """Shows model selection interface"""
        current_model = self.llm_provider.get_current_model()

        self.console.print(f"\n[cyan]Available Models ({len(models)}):[/cyan]")
        self.console.print(f"[dim]Current model: [bold]{current_model}[/bold][/dim]")
        self.console.print()

        # Display models with numbers
        for i, model in enumerate(models, 1):
            prefix = "[green]✓[/green]" if model == current_model else " "
            # Truncate long model names for display
            display_name = model if len(model) <= 50 else model[:47] + "..."
            self.console.print(f"{prefix} {i:2d}. {display_name}")

        self.console.print(
            f"\n[cyan]Enter model number (1-{len(models)}) or press Enter to cancel:[/cyan]"
        )

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
                        self.llm_provider.set_model(selected_model)
                        self.console.print(
                            f"[green]✓ Model set to: [bold]{selected_model}[/bold][/green]"
                        )

                        # Show model info if available
                        model_info = self.llm_provider.get_model_info(selected_model)
                        if model_info and "details" in model_info:
                            details = model_info["details"]
                            if "parameter_size" in details:
                                self.console.print(
                                    f"[dim]Parameters: {details['parameter_size']}[/dim]"
                                )
                            if "quantization_level" in details:
                                self.console.print(
                                    f"[dim]Quantization: {details['quantization_level']}[/dim]"
                                )
                    except Exception as e:
                        self.console.print(f"[red]Error setting model: {e}[/red]")
                else:
                    self.console.print(
                        f"[red]Invalid selection. Please choose 1-{len(models)}[/red]"
                    )
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
        provider_status = self.llm_provider.health_check()
        provider_name = self.llm_provider.get_provider_type().value.title()
        status = {
            "Mode": self._get_mode_description(),
            "Provider": provider_name,
            "Endpoint": provider_status.get("endpoint", "Unknown"),
            "Connected": "Yes" if provider_status.get("connected", False) else "No",
            "Current Model": provider_status.get("current_model", "None"),
            "Available Models": len(provider_status.get("available_models", [])),
            "Conversations": len(self.conversation_manager.get_recent_history()),
            "Status": "Active",
        }
        self.display.show_status(status)

        # Show connection help if not connected
        if not provider_status.get("connected", False):
            provider_name = self.llm_provider.get_provider_type().value.title()
            self.console.print(f"\n[yellow]{provider_name} Connection Help:[/yellow]")
            self.console.print("  Use [bold]/switch <provider>[/bold] to try another provider")
            self.console.print("  Use [bold]/detect[/bold] to auto-detect available providers")
            self.console.print("  Use [bold]/provider[/bold] to check current provider status")

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
@click.option("--model", "-m", help="Model to use (will auto-select if not specified)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.argument("input_text", required=False)
def main(model: str, verbose: bool, input_text: Optional[str]):
    """
    XandAI - CLI Assistant with Ollama Integration

    Examples:
      xandai                           # Interactive mode
      xandai "explain clean code"      # Direct chat mode
      xandai "create an API"           # Natural conversation
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
