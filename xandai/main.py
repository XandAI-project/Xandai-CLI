#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XandAI - Main CLI Entry Point
Production-ready CLI assistant with multi-provider support
Enhanced with OS-aware utilities and intelligent prompts
"""

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 encoding for Windows compatibility
if os.name == "nt":  # Windows
    import codecs
    import locale

    # Set UTF-8 encoding for stdout/stderr to avoid UnicodeEncodeError
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

    # Set default encoding for subprocess operations
    os.environ["PYTHONIOENCODING"] = "utf-8"

from xandai.chat import ChatREPL
from xandai.git.git_commands import GitCommands
from xandai.history import HistoryManager
from xandai.integrations.base_provider import LLMProvider
from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.utils.os_utils import OSUtils
from xandai.utils.prompt_manager import PromptManager


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser with OS-aware debug options"""
    parser = argparse.ArgumentParser(
        prog="xandai",
        description="XandAI - Multi-Provider AI Terminal Assistant with Interactive Code Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
🚀 Multi-Provider Support:
  • Ollama (local LLM server)
  • LM Studio (OpenAI-compatible API)
  • Auto-detection of available providers

📋 Interactive Features:
  • Smart code detection and execution prompts
  • Toggle interactive mode with /interactive command
  • Cross-platform terminal command integration
  • Real-time conversation with context tracking

Examples:
  xandai                                    # Start with auto-detected provider
  xandai --provider ollama                  # Use Ollama specifically
  xandai --provider lm_studio               # Use LM Studio
  xandai --auto-detect                      # Auto-detect best provider
  xandai --endpoint http://192.168.1.10:11434  # Custom Ollama server
  xandai --debug --platform-info           # Debug mode with platform info

🎯 Interactive Commands (available in REPL):
  /help               - Show available commands
  /interactive        - Toggle code execution prompts
  /status             - Show provider and model status
  /task <description> - [DEPRECIADO] Structured project planning mode
  /debug              - Toggle debug information
  /exit               - Exit XandAI

Platform: {OSUtils.get_platform().upper()} ({platform.system()} {platform.release()})
        """,
    )

    # Provider and connection options
    parser.add_argument(
        "--provider",
        metavar="PROVIDER",
        default="ollama",
        choices=["ollama", "lm_studio"],
        help="LLM provider to use (default: ollama) - 'ollama' for local Ollama server, 'lm_studio' for LM Studio OpenAI-compatible API",
    )

    parser.add_argument(
        "--endpoint",
        metavar="URL",
        help="Provider server endpoint (auto-detected if not specified)",
    )

    parser.add_argument(
        "--model",
        metavar="MODEL",
        help="Model to use (will prompt to select if not specified)",
    )

    # Debug and platform options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed OS information",
    )

    parser.add_argument(
        "--platform-info",
        action="store_true",
        help="Show detailed platform information at startup",
    )

    parser.add_argument(
        "--show-commands",
        action="store_true",
        help="Show available OS-specific commands and exit",
    )

    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect best available provider (scans for Ollama and LM Studio servers)",
    )

    parser.add_argument(
        "--test-commands",
        action="store_true",
        help="Test OS-specific commands with sample files and exit",
    )

    parser.add_argument(
        "--system-prompt",
        choices=["chat", "task", "command"],
        help="Show system prompt for specified mode and exit",
    )

    # Git AI commands
    parser.add_argument(
        "command",
        nargs="?",
        choices=["commit", "pr", "diff", "blame"],
        help="Git AI commands: commit (generate commit message), pr (summarize PR), diff (explain diff), blame (explain line)",
    )

    parser.add_argument(
        "--file", metavar="FILE", help="File path for git operations (used with diff, blame)"
    )

    parser.add_argument("--line", type=int, metavar="LINE", help="Line number for blame command")

    parser.add_argument(
        "--base",
        metavar="BRANCH",
        default="main",
        help="Base branch for PR comparison (default: main)",
    )

    parser.add_argument(
        "--head", metavar="BRANCH", help="Head branch for PR comparison (default: current branch)"
    )

    parser.add_argument("--commit-hash", metavar="HASH", help="Commit hash for diff command")

    parser.add_argument(
        "--version", action="version", version="XandAI 2.1.12 - Multi-Provider Edition"
    )

    return parser


def show_platform_info():
    """Show detailed platform information"""
    print("🖥️  Platform Information")
    print("=" * 50)
    print(f"Operating System: {OSUtils.get_platform().title()}")
    print(f"Platform Name: {platform.system()}")
    print(f"Platform Release: {platform.release()}")
    print(f"Platform Version: {platform.version()}")
    print(f"Machine Type: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Is Windows: {OSUtils.is_windows()}")
    print(f"Is Unix-like: {OSUtils.is_unix_like()}")
    print()


def show_os_commands():
    """Show available OS-specific commands"""
    commands = OSUtils.get_available_commands()

    print("📋 Available OS-Specific Commands")
    print("=" * 50)
    print(f"Platform: {OSUtils.get_platform().upper()}")
    print()

    for cmd_type, cmd_template in commands.items():
        print(f"• {cmd_type.replace('_', ' ').title()}: {cmd_template}")

    print()
    print("Usage Examples:")
    print(f"• Read file: {OSUtils.get_file_read_command('example.txt')}")
    print(f"• List directory: {OSUtils.get_directory_list_command('.')}")
    print(f"• Search pattern: {OSUtils.get_file_search_command('TODO', 'src/')}")
    print()


def test_os_commands():
    """Test OS-specific commands with sample scenarios"""
    print("🔧 Testing OS-Specific Commands")
    print("=" * 50)

    # Test file reading commands
    test_files = ["README.md", "setup.py", "requirements.txt"]
    existing_files = [f for f in test_files if Path(f).exists()]

    if existing_files:
        test_file = existing_files[0]
        print(f"Testing with existing file: {test_file}")
        print()

        print("Commands that would be generated:")
        print(f"• Read entire file: {OSUtils.get_file_read_command(test_file)}")
        print(f"• First 5 lines: {OSUtils.get_file_head_command(test_file, 5)}")
        print(f"• Last 5 lines: {OSUtils.get_file_tail_command(test_file, 5)}")
        print(f"• Search 'import': {OSUtils.get_file_search_command('import', test_file)}")
        print()

        # Test directory commands
        print(f"• List current dir: {OSUtils.get_directory_list_command('.')}")
        if OSUtils.is_windows():
            print("• PowerShell commands available for advanced operations")
        else:
            print("• Unix commands available with powerful options")
    else:
        print("No test files found in current directory")

    print()
    print("Debug output test:")
    OSUtils.debug_print("This is a test debug message", True)
    OSUtils.debug_print("This debug message won't show", False)
    print()


def show_system_prompt(mode: str):
    """Show system prompt for specified mode"""
    print(f"🤖 System Prompt for {mode.upper()} Mode")
    print("=" * 50)

    if mode == "chat":
        prompt = PromptManager.get_chat_system_prompt()
    elif mode == "task":
        prompt = PromptManager.get_task_system_prompt_full_project()
    elif mode == "command":
        prompt = PromptManager.get_command_generation_prompt()
    else:
        print(f"Unknown mode: {mode}")
        return

    print(prompt)
    print()
    print("=" * 50)
    print(f"Prompt length: {len(prompt)} characters")
    print()


def handle_git_command(args, git_commands: GitCommands):
    """Handle Git AI commands"""
    try:
        repo_path = os.getcwd()

        if args.command == "commit":
            print("🤖 Generating commit message from staged changes...")
            message = git_commands.generate_commit_message(repo_path)
            print("\n" + "=" * 60)
            print("SUGGESTED COMMIT MESSAGE:")
            print("=" * 60)
            print(message)
            print("=" * 60)
            print("\nTo use this message:")
            print(f'  git commit -m "{message.split(chr(10))[0]}"')
            if "\n" in message:
                print("  (or copy the full message above for a detailed commit)")

        elif args.command == "pr":
            print(f"🤖 Summarizing PR from '{args.base}' to '{args.head or 'current branch'}'...")
            summary = git_commands.summarize_pr(repo_path, args.base, args.head)
            print("\n" + "=" * 60)
            print("PULL REQUEST SUMMARY:")
            print("=" * 60)
            if summary.get("summary"):
                print(f"\n{summary['summary']}\n")
            if summary.get("changes"):
                print("CHANGES:")
                print(summary["changes"])
                print()
            if summary.get("risks"):
                print("RISKS:")
                print(summary["risks"])
            print("=" * 60)

        elif args.command == "diff":
            if args.file:
                print(f"🤖 Explaining diff for {args.file}...")
            else:
                print("🤖 Explaining current diff...")
            explanation = git_commands.explain_diff(repo_path, args.file, args.commit_hash)
            print("\n" + "=" * 60)
            print("DIFF EXPLANATION:")
            print("=" * 60)
            print(explanation)
            print("=" * 60)

        elif args.command == "blame":
            if not args.file:
                print("Error: --file is required for blame command")
                print("Usage: xandai blame --file <path> [--line <number>]")
                sys.exit(1)

            if args.line:
                print(f"🤖 Explaining line {args.line} in {args.file}...")
            else:
                print(f"🤖 Explaining first line of {args.file}...")

            explanation = git_commands.explain_blame(repo_path, args.file, args.line)
            print("\n" + "=" * 60)
            print("BLAME EXPLANATION:")
            print("=" * 60)
            print(explanation)
            print("=" * 60)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose or args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point with OS-aware debugging and enhanced functionality"""
    parser = create_parser()
    args = parser.parse_args()

    # Handle debug/info commands that exit immediately
    if args.show_commands:
        show_os_commands()
        sys.exit(0)

    if args.test_commands:
        test_os_commands()
        sys.exit(0)

    if args.system_prompt:
        show_system_prompt(args.system_prompt)
        sys.exit(0)

    try:
        # Show platform info if requested
        if args.platform_info or args.debug:
            show_platform_info()

        # Debug initialization
        if args.debug:
            OSUtils.debug_print(f"Debug mode enabled on {OSUtils.get_platform()}", True)
            OSUtils.debug_print(
                f"Available OS commands: {list(OSUtils.get_available_commands().keys())}",
                True,
            )
            OSUtils.debug_print(
                f"Prompt manager initialized with {len(PromptManager.__dict__)} methods",
                True,
            )

        # Initialize LLM Provider
        print("🔌 Initializing LLM provider...")

        if args.auto_detect:
            if args.debug:
                OSUtils.debug_print("Auto-detecting best available provider", True)
            print("🔍 Auto-detecting best available provider...")
            llm_provider = LLMProviderFactory.create_auto_detect()
        else:
            if args.debug:
                OSUtils.debug_print(f"Creating {args.provider} provider", True)

            config_options = {}
            if args.endpoint:
                config_options["base_url"] = args.endpoint
            if args.model:
                config_options["model"] = args.model

            llm_provider = LLMProviderFactory.create_provider(
                provider_type=args.provider, **config_options
            )

        # Check connection
        if not llm_provider.is_connected():
            provider_name = llm_provider.get_provider_type().value.title()
            endpoint = llm_provider.get_base_url()

            print(f"❌ Could not connect to {provider_name} at {endpoint}")
            print(f"Please ensure {provider_name} is running and accessible.")

            # Provider-specific help
            if llm_provider.get_provider_type().value == "ollama":
                if OSUtils.is_windows():
                    print("Windows: Try running 'ollama serve' in a separate PowerShell window")
                else:
                    print("Unix-like: Try running 'ollama serve' in a separate terminal")
            elif llm_provider.get_provider_type().value == "lm_studio":
                print("Make sure LM Studio is running with a model loaded")
                print("Check the 'Server' tab in LM Studio and ensure it's started")

            if args.debug:
                OSUtils.debug_print(
                    f"Connection failed - check if {provider_name} service is running",
                    True,
                )
                OSUtils.debug_print(f"Endpoint attempted: {endpoint}", True)

            sys.exit(1)

        provider_name = llm_provider.get_provider_type().value.title()
        if args.debug:
            OSUtils.debug_print(f"{provider_name} connection successful", True)
        print(f"✅ Connected to {provider_name} successfully!")

        # Get available models
        models = llm_provider.list_models()
        if not models:
            provider_name = llm_provider.get_provider_type().value.title()
            print(f"❌ No models found on {provider_name} server.")

            if llm_provider.get_provider_type().value == "ollama":
                if OSUtils.is_windows():
                    print("Try: ollama pull llama3.2 (in PowerShell)")
                else:
                    print("Try: ollama pull llama3.2 (in terminal)")
            elif llm_provider.get_provider_type().value == "lm_studio":
                print("Load a model in LM Studio first")

            sys.exit(1)

        if args.debug:
            OSUtils.debug_print(f"Found {len(models)} models: {models}", True)

        # Handle model selection
        current_model = llm_provider.get_current_model()
        if args.model:
            # User specified a model
            if args.model in models:
                llm_provider.set_model(args.model)
                print(f"📦 Using model: {args.model}")
                if args.debug:
                    OSUtils.debug_print(f"Model set to: {args.model}", True)
            else:
                print(f"❌ Model '{args.model}' not found.")
                print(f"Available models: {', '.join(models)}")
                sys.exit(1)
        elif not current_model:
            # No model specified - always show selection if multiple models
            if len(models) == 1:
                llm_provider.set_model(models[0])
                print(f"📦 Auto-selected model: {models[0]} (only model available)")
                if args.debug:
                    OSUtils.debug_print(f"Auto-selected single model: {models[0]}", True)
            else:
                # Always show interactive selection when multiple models available
                print()
                print(
                    f"\033[1;36m📦 Available models on {llm_provider.get_provider_type().value.title()} server:\033[0m"
                )
                print("\033[1;35m" + "╔" + "═" * 70 + "╗\033[0m")

                for i, model in enumerate(models, 1):
                    # Extract model name parts for better formatting
                    if "/" in model:
                        parts = model.split("/")
                        org = parts[0] if len(parts) > 0 else ""
                        name = "/".join(parts[1:]) if len(parts) > 1 else model
                        formatted = f"\033[90m{org}/\033[0m\033[1;33m{name}\033[0m"
                    else:
                        formatted = f"\033[1;33m{model}\033[0m"

                    print(f"\033[1;35m║\033[0m \033[1;32m{i:2d}.\033[0m {formatted}")

                print("\033[1;35m" + "╚" + "═" * 70 + "╝\033[0m")
                print()

                while True:
                    try:
                        choice = input(
                            f"\033[1;36m→ Select model (1-{len(models)}):\033[0m "
                        ).strip()
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(models):
                                selected_model = models[idx]
                                llm_provider.set_model(selected_model)
                                print(
                                    f"\033[1;32m✓ Using model:\033[0m \033[1;33m{selected_model}\033[0m"
                                )
                                if args.debug:
                                    OSUtils.debug_print(
                                        f"User selected model: {selected_model}", True
                                    )
                                break
                        print("\033[1;31m✗ Invalid selection. Please try again.\033[0m")
                    except (KeyboardInterrupt, EOFError):
                        print("\n👋 Goodbye!")
                        sys.exit(0)
        else:
            # Model was auto-selected or already configured
            print(f"📦 Using model: {current_model}")
            if args.debug:
                OSUtils.debug_print(f"Using configured model: {current_model}", True)

        # Initialize history manager
        history_manager = HistoryManager()
        if args.debug:
            OSUtils.debug_print("History manager initialized", True)

        # Handle Git AI commands (if specified)
        if args.command:
            git_commands = GitCommands(llm_provider, verbose=args.verbose or args.debug)
            handle_git_command(args, git_commands)
            sys.exit(0)

        # Show ASCII title and startup info
        provider_name = llm_provider.get_provider_type().value.title()
        current_model = llm_provider.get_current_model() or "None"

        # Beautiful ASCII art logo with sunset gradient (red → orange → yellow)
        print()
        print("\033[38;5;196m ██╗  ██╗  █████╗  ███╗   ██╗ ██████╗   █████╗  ██╗\033[0m")
        print("\033[38;5;202m ╚██╗██╔╝ ██╔══██╗ ████╗  ██║ ██╔══██╗ ██╔══██╗ ██║\033[0m")
        print("\033[38;5;208m  ╚███╔╝  ███████║ ██╔██╗ ██║ ██║  ██║ ███████║ ██║\033[0m")
        print("\033[38;5;214m  ██╔██╗  ██╔══██║ ██║╚██╗██║ ██║  ██║ ██╔══██║ ██║\033[0m")
        print("\033[38;5;220m ██╔╝ ██╗ ██║  ██║ ██║ ╚████║ ██████╔╝ ██║  ██║ ██║\033[0m")
        print("\033[38;5;226m ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝ ╚═════╝  ╚═╝  ╚═╝ ╚═╝\033[0m")
        print()
        print("\033[38;5;214m  ██████╗ ██╗      ██╗\033[0m")
        print("\033[38;5;220m ██╔════╝ ██║      ██║\033[0m")
        print("\033[38;5;226m ██║      ██║      ██║\033[0m")
        print("\033[38;5;228m ██║      ██║      ██║\033[0m")
        print("\033[38;5;230m ╚██████╗ ███████╗ ██║\033[0m")
        print("\033[38;5;231m  ╚═════╝ ╚══════╝ ╚═╝\033[0m")
        print()

        # Provider and Model info with better formatting
        box_width = max(len(f"Provider: {provider_name}"), len(f"Model: {current_model}")) + 6
        border_line = "═" * box_width

        print("\033[1;35m╔" + border_line + "╗\033[0m")
        provider_line = f"Provider: \033[1;32m{provider_name}\033[1;35m"
        provider_padding = box_width - len(f"Provider: {provider_name}")
        print("\033[1;35m║ " + provider_line + " " * provider_padding + " ║\033[0m")

        model_line = f"Model:    \033[1;33m{current_model}\033[1;35m"
        model_padding = box_width - len(f"Model:    {current_model}")
        print("\033[1;35m║ " + model_line + " " * model_padding + " ║\033[0m")
        print("\033[1;35m╚" + border_line + "╝\033[0m")
        print()

        print("\033[1;32m🚀 Starting XandAI REPL...\033[0m")
        print("Type '\033[1;36mhelp\033[0m' for commands or start chatting!")
        print(
            "\033[1;33m⚠️  Note: /task command is deprecated. Use natural conversation instead.\033[0m"
        )

        # OS-specific command hints
        if OSUtils.is_windows():
            print("Windows commands supported: type, dir, findstr, powershell, etc.")
        else:
            print("Unix commands supported: cat, ls, grep, head, tail, etc.")

        if args.debug:
            print(
                f"🔧 DEBUG MODE: Platform={OSUtils.get_platform().upper()}, Verbose={args.verbose}"
            )

        print("-" * 50)

        # Enhanced REPL with LLM Provider
        repl = ChatREPL(llm_provider, history_manager, verbose=args.verbose or args.debug)

        if args.debug:
            OSUtils.debug_print("Starting REPL with enhanced configuration", True)

        repl.run()

    except KeyboardInterrupt:
        if args.debug:
            OSUtils.debug_print("Received KeyboardInterrupt", True)
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose or args.debug:
            import traceback

            traceback.print_exc()
            if args.debug:
                OSUtils.debug_print(f"Fatal error details: {str(e)}", True)
        sys.exit(1)


if __name__ == "__main__":
    main()
