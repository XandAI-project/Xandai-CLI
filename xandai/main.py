#!/usr/bin/env python3
"""
XandAI - Main CLI Entry Point
Production-ready CLI assistant with Ollama integration
Enhanced with OS-aware utilities and intelligent prompts
"""

import argparse
import sys
import json
import platform
from typing import Optional
from pathlib import Path

from xandai.chat import ChatREPL
from xandai.ollama_client import OllamaClient
from xandai.history import HistoryManager
from xandai.utils.os_utils import OSUtils
from xandai.utils.prompt_manager import PromptManager


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser with OS-aware debug options"""
    parser = argparse.ArgumentParser(
        prog='xandai',
        description='XandAI - CLI Assistant with Ollama Integration (OS-Aware)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  xandai                                    # Start interactive REPL
  xandai --endpoint http://192.168.1.10:11434  # Use custom Ollama server
  xandai --debug --platform-info           # Start with debug and platform info
  xandai --show-commands                    # Show available OS commands

Platform: {OSUtils.get_platform().upper()} ({platform.system()} {platform.release()})
        """
    )
    
    # Connection options
    parser.add_argument(
        '--endpoint',
        metavar='URL',
        default='http://127.0.0.1:11434',
        help='Ollama server endpoint (default: http://127.0.0.1:11434)'
    )
    
    parser.add_argument(
        '--model',
        metavar='MODEL',
        help='Ollama model to use (will prompt to select if not specified)'
    )
    
    # Debug and platform options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed OS information'
    )
    
    parser.add_argument(
        '--platform-info',
        action='store_true',
        help='Show detailed platform information at startup'
    )
    
    parser.add_argument(
        '--show-commands',
        action='store_true',
        help='Show available OS-specific commands and exit'
    )
    
    parser.add_argument(
        '--test-commands',
        action='store_true',
        help='Test OS-specific commands with sample files and exit'
    )
    
    parser.add_argument(
        '--system-prompt',
        choices=['chat', 'task', 'command'],
        help='Show system prompt for specified mode and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='XandAI 2.1.0'
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
    
    if mode == 'chat':
        prompt = PromptManager.get_chat_system_prompt()
    elif mode == 'task':
        prompt = PromptManager.get_task_system_prompt_full_project()
    elif mode == 'command':
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
            OSUtils.debug_print(f"Available OS commands: {list(OSUtils.get_available_commands().keys())}", True)
            OSUtils.debug_print(f"Prompt manager initialized with {len(PromptManager.__dict__)} methods", True)
        
        # Initialize Ollama client
        if args.debug:
            OSUtils.debug_print(f"Connecting to Ollama at {args.endpoint}", True)
        print(f"🔌 Connecting to Ollama at {args.endpoint}...")
        ollama_client = OllamaClient(base_url=args.endpoint)
        
        # Check connection
        if not ollama_client.is_connected():
            print(f"❌ Could not connect to Ollama at {args.endpoint}")
            print("Please ensure Ollama is running and accessible.")
            
            # OS-specific help
            if OSUtils.is_windows():
                print("Windows: Try running 'ollama serve' in a separate PowerShell window")
            else:
                print("Unix-like: Try running 'ollama serve' in a separate terminal")
            
            if args.debug:
                OSUtils.debug_print("Connection failed - check if Ollama service is running", True)
                OSUtils.debug_print(f"Endpoint attempted: {args.endpoint}", True)
            
            sys.exit(1)
        
        if args.debug:
            OSUtils.debug_print("Ollama connection successful", True)
        print("✅ Connected to Ollama successfully!")
        
        # Get available models
        models = ollama_client.list_models()
        if not models:
            print("❌ No models found on Ollama server.")
            if OSUtils.is_windows():
                print("Try: ollama pull llama3.2 (in PowerShell)")
            else:
                print("Try: ollama pull llama3.2 (in terminal)")
            sys.exit(1)
        
        if args.debug:
            OSUtils.debug_print(f"Found {len(models)} models: {models}", True)
        
        # Handle model selection
        if args.model:
            if args.model in models:
                ollama_client.set_model(args.model)
                print(f"📦 Using model: {args.model}")
                if args.debug:
                    OSUtils.debug_print(f"Model set to: {args.model}", True)
            else:
                print(f"❌ Model '{args.model}' not found.")
                print(f"Available models: {', '.join(models)}")
                sys.exit(1)
        else:
            # Interactive model selection
            if len(models) == 1:
                ollama_client.set_model(models[0])
                print(f"📦 Using model: {models[0]}")
                if args.debug:
                    OSUtils.debug_print(f"Auto-selected single model: {models[0]}", True)
            else:
                print(f"\\n📦 Found {len(models)} models:")
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model}")
                
                while True:
                    try:
                        choice = input(f"\\nSelect model (1-{len(models)}): ").strip()
                        if choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(models):
                                selected_model = models[idx]
                                ollama_client.set_model(selected_model)
                                print(f"📦 Using model: {selected_model}")
                                if args.debug:
                                    OSUtils.debug_print(f"User selected model: {selected_model}", True)
                                break
                        print("Invalid selection. Please try again.")
                    except (KeyboardInterrupt, EOFError):
                        print("\\n👋 Goodbye!")
                        sys.exit(0)
        
        # Initialize history manager
        history_manager = HistoryManager()
        if args.debug:
            OSUtils.debug_print("History manager initialized", True)
        
        # Show enhanced startup info
        print("\\n🚀 Starting XandAI REPL...")
        print("Type 'help' for commands or start chatting!")
        print("Use '/task <description>' for structured project planning.")
        
        # OS-specific command hints
        if OSUtils.is_windows():
            print("Windows commands supported: type, dir, findstr, powershell, etc.")
        else:
            print("Unix commands supported: cat, ls, grep, head, tail, etc.")
        
        if args.debug:
            print(f"🔧 DEBUG MODE: Platform={OSUtils.get_platform().upper()}, Verbose={args.verbose}")
        
        print("-" * 50)
        
        # Enhanced REPL with OS-aware utilities
        repl = ChatREPL(
            ollama_client, 
            history_manager, 
            verbose=args.verbose or args.debug
        )
        
        if args.debug:
            OSUtils.debug_print("Starting REPL with enhanced configuration", True)
        
        repl.run()
        
    except KeyboardInterrupt:
        if args.debug:
            OSUtils.debug_print("Received KeyboardInterrupt", True)
        print("\\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose or args.debug:
            import traceback
            traceback.print_exc()
            if args.debug:
                OSUtils.debug_print(f"Fatal error details: {str(e)}", True)
        sys.exit(1)


if __name__ == '__main__':
    main()
