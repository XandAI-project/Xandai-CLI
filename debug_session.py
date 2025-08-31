#!/usr/bin/env python3

from xandai.cli import XandAICLI

def test_with_restored_session():
    """Test exactly what happens with a real restored session"""
    print("=== DEBUGGING SESSION RESTORATION ===")
    
    # Create CLI exactly like the real CLI
    cli = XandAICLI(endpoint="http://192.168.3.70:11434")
    
    print(f"1. Initial state:")
    print(f"   auto_execute_shell: {cli.auto_execute_shell}")
    print(f"   better_prompting: {cli.better_prompting}")
    print(f"   selected_model: {cli.selected_model}")
    
    # Load session like the real CLI does  
    print(f"\n2. Loading session...")
    session_data = cli.session_manager.load_session()
    if session_data:
        print(f"   Session found with model: {session_data.get('model_name')}")
        
        # Manually restore settings like load_previous_session does
        cli.selected_model = session_data.get('model_name')
        cli.auto_execute_shell = session_data.get('shell_settings', {}).get('auto_execute_shell', True)
        cli.better_prompting = session_data.get('shell_settings', {}).get('better_prompting', True)
        
        print(f"   After restore:")
        print(f"   auto_execute_shell: {cli.auto_execute_shell}")
        print(f"   better_prompting: {cli.better_prompting}")
        print(f"   selected_model: {cli.selected_model}")
    
    print(f"\n3. Testing command detection:")
    command = "cd examples"
    result = cli._should_execute_as_command(command)
    print(f"   Command: '{command}'")
    print(f"   Detection result: {result}")
    print(f"   Will execute directly: {cli.auto_execute_shell and result}")
    
    print(f"\n4. Testing process_prompt with restored session:")
    print(f"   Calling cli.process_prompt('{command}')")
    
    # This should execute directly, not analyze
    try:
        cli.process_prompt(command)
        print("   ✓ Completed successfully")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_with_restored_session()
