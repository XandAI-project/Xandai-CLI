#!/usr/bin/env python3
"""
XandAI - Main CLI Entry Point
Production-ready CLI assistant with Ollama integration
"""

import argparse
import sys
from typing import Optional

from xandai.chat import ChatREPL
from xandai.ollama_client import OllamaClient
from xandai.history import HistoryManager


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        prog='xandai',
        description='XandAI - CLI Assistant with Ollama Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  xandai                                    # Start interactive REPL
  xandai --endpoint http://192.168.1.10:11434  # Use custom Ollama server
        """
    )
    
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
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='XandAI 2.1.0'
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Initialize Ollama client
        print(f"🔌 Connecting to Ollama at {args.endpoint}...")
        ollama_client = OllamaClient(base_url=args.endpoint)
        
        # Check connection
        if not ollama_client.is_connected():
            print(f"❌ Could not connect to Ollama at {args.endpoint}")
            print("Please ensure Ollama is running and accessible.")
            print("Try: ollama serve")
            sys.exit(1)
        
        print("✅ Connected to Ollama successfully!")
        
        # Get available models
        models = ollama_client.list_models()
        if not models:
            print("❌ No models found on Ollama server.")
            print("Please pull a model first, e.g.: ollama pull llama3.2")
            sys.exit(1)
        
        # Handle model selection
        if args.model:
            if args.model in models:
                ollama_client.set_model(args.model)
                print(f"📦 Using model: {args.model}")
            else:
                print(f"❌ Model '{args.model}' not found.")
                print(f"Available models: {', '.join(models)}")
                sys.exit(1)
        else:
            # Interactive model selection
            if len(models) == 1:
                ollama_client.set_model(models[0])
                print(f"📦 Using model: {models[0]}")
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
                                ollama_client.set_model(models[idx])
                                print(f"📦 Using model: {models[idx]}")
                                break
                        print("Invalid selection. Please try again.")
                    except (KeyboardInterrupt, EOFError):
                        print("\\n👋 Goodbye!")
                        sys.exit(0)
        
        # Initialize history manager
        history_manager = HistoryManager()
        
        # Start REPL
        print("\\n🚀 Starting XandAI REPL...")
        print("Type 'help' for commands or start chatting!")
        print("Use '/task <description>' for structured project planning.")
        print("Terminal commands (ls, cd, cat, etc.) are supported.")
        print("-" * 50)
        
        repl = ChatREPL(ollama_client, history_manager, verbose=args.verbose)
        repl.run()
        
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
