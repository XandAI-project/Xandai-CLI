#!/usr/bin/env python3

import sys
from xandai.cli import XandAICLI

def test_command_behavior():
    """Test real command behavior with session loaded"""
    print("=== TESTING REAL COMMAND BEHAVIOR ===")
    
    # Create CLI with endpoint like user does
    cli = XandAICLI(endpoint="http://192.168.3.70:11434")
    
    # Load session like real CLI does
    print("Loading session...")
    previous_session = cli.session_manager.load_session()
    if previous_session:
        print(f"Session loaded with model: {previous_session.get('model_name')}")
        
        # Restore settings exactly like load_previous_session does
        cli.selected_model = previous_session.get('model_name')
        cli.auto_execute_shell = previous_session.get('shell_settings', {}).get('auto_execute_shell', True)
        cli.better_prompting = previous_session.get('shell_settings', {}).get('better_prompting', True)
        cli.enhance_prompts = previous_session.get('shell_settings', {}).get('enhance_prompts', True)
        
        print(f"Settings after restore:")
        print(f"  auto_execute_shell: {cli.auto_execute_shell}")
        print(f"  better_prompting: {cli.better_prompting}")
        print(f"  enhance_prompts: {cli.enhance_prompts}")
        print(f"  selected_model: {cli.selected_model}")
    
    # Test command detection
    test_commands = ['ls', 'cd examples', 'mkdir test']
    
    for cmd in test_commands:
        print(f"\n--- Testing: '{cmd}' ---")
        
        # Check if it should be executed as command
        command_to_execute = cli._should_execute_as_command(cmd.strip())
        print(f"Detection result: {command_to_execute}")
        print(f"auto_execute_shell: {cli.auto_execute_shell}")
        print(f"Will execute directly: {cli.auto_execute_shell and command_to_execute}")
        
        if cli.auto_execute_shell and command_to_execute:
            print("✅ GOOD: Will execute directly")
        else:
            print("❌ BAD: Will go to LLM")

if __name__ == "__main__":
    test_command_behavior()
