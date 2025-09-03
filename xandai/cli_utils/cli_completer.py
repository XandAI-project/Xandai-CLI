"""
CLI Completer Module
Custom completer for XandAI CLI that handles both commands and file paths
"""

from prompt_toolkit.completion import WordCompleter, PathCompleter, Completer, Completion


class XandAICompleter(Completer):
    """Custom completer for XandAI CLI that handles both commands and file paths"""
    
    def __init__(self, commands, shell_executor):
        self.commands = commands
        self.shell_executor = shell_executor
        self.command_completer = WordCompleter(list(commands.keys()), ignore_case=True)
        self.path_completer = PathCompleter()
        
        # Shell commands that typically need file/directory completion
        self.file_commands = {
            'cd', 'ls', 'dir', 'cat', 'type', 'rm', 'del', 'cp', 'copy', 'mv', 'move',
            'mkdir', 'rmdir', 'touch', 'head', 'tail', 'less', 'more', 'nano', 'vim',
            'code', 'notepad', 'git', 'find', 'grep', 'chmod', 'chown', 'tar', 'zip',
            'unzip', 'python', 'node', 'npm', 'pip', 'cargo', 'go'
        }
    
    def get_completions(self, document, complete_event):
        text = document.text
        
        # If starts with /, complete CLI commands
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
            return
        
        # For shell commands, provide file/path completion
        words = text.split()
        if words and words[0] in self.file_commands:
            # Complete file paths for file-related commands
            yield from self.path_completer.get_completions(document, complete_event)
            return
        
        # Default: complete both CLI commands (with /) and file paths
        # CLI commands
        if not text or text.startswith('/'):
            cli_doc = document._replace(text='/' + text.lstrip('/'))
            for completion in self.command_completer.get_completions(cli_doc, complete_event):
                yield completion
        
        # File paths
        yield from self.path_completer.get_completions(document, complete_event)
