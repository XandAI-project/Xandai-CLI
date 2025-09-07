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
  /task <description> - Structured project planning mode
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

    parser.add_argument(
        "--version", action="version", version="XandAI 2.1.5 - Multi-Provider Edition"
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
                print(
                    f"📦 Available models on {llm_provider.get_provider_type().value.title()} server:"
                )
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model}")

                while True:
                    try:
                        choice = input(f"Select model (1-{len(models)}): ").strip()
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(models):
                                selected_model = models[idx]
                                llm_provider.set_model(selected_model)
                                print(f"📦 Using model: {selected_model}")
                                if args.debug:
                                    OSUtils.debug_print(
                                        f"User selected model: {selected_model}", True
                                    )
                                break
                        print("Invalid selection. Please try again.")
                    except (KeyboardInterrupt, EOFError):
                        print("👋 Goodbye!")
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

        # Show ASCII title and startup info
        provider_name = llm_provider.get_provider_type().value.title()
        current_model = llm_provider.get_current_model() or "None"

        print(
            """
 __  __               _       _
 \\ \\/ /__ _ _ __   __| | __ _(_)
  \\  // _` | '_ \\ / _` |/ _` | |
  /  \\ (_| | | | | (_| | (_| | |
 /_/\\_\\__,_|_| |_|\\__,_|\\__,_|_|
                                """
        )
        print(f"- Provider: {provider_name}")
        print()
        print("🚀 Starting XandAI REPL...")
        print("Type 'help' for commands or start chatting!")
        print("Use '/task <description>' for structured project planning.")
        print(f"Model: {current_model}")

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
