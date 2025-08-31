#!/usr/bin/env python3

from xandai.cli import XandAICLI
from xandai.session_manager import SessionManager

# Test session creation with auto_execute_shell
cli = XandAICLI()
cli.selected_model = 'test-model'

# Set to False to test if it gets forced to True
cli.auto_execute_shell = False
print(f'Before save - auto_execute_shell: {cli.auto_execute_shell}')

# Save session
result = cli.session_manager.save_session(
    model_name=cli.selected_model,
    context_history=[],
    working_directory='/test/dir',
    shell_settings={
        'auto_execute_shell': cli.auto_execute_shell,  # This is False
        'enhance_prompts': True,
        'better_prompting': True
    }
)

print(f'Save result: {result}')

# Load and check what was actually saved
session_data = cli.session_manager.load_session()
if session_data:
    saved_settings = session_data.get('shell_settings', {})
    print(f'Saved auto_execute_shell: {saved_settings.get("auto_execute_shell")}')
    print('Should always be True!')
else:
    print('No session data found')
