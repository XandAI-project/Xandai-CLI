"""
Display Utilities Module
Handles display, help, and debug information formatting
"""

from typing import Dict, Any
from rich.console import Console
from rich.markdown import Markdown

console = Console()


class DisplayUtils:
    """Utility class for display and formatting functions"""
    
    @staticmethod
    def show_context_status(prompt_enhancer):
        """Show current context usage status"""
        if hasattr(prompt_enhancer, 'get_context_status'):
            status = prompt_enhancer.get_context_status()
            console.print(f"[blue]📊 Context Status: {status}[/blue]")
            
            # Show detailed breakdown
            if hasattr(prompt_enhancer, 'context_history'):
                history = prompt_enhancer.context_history
                console.print(f"[dim]Messages breakdown:[/dim]")
                
                role_counts = {}
                for msg in history:
                    if isinstance(msg, dict) and 'role' in msg:
                        role = msg['role']
                        role_counts[role] = role_counts.get(role, 0) + 1
                    else:
                        role_counts['unknown'] = role_counts.get('unknown', 0) + 1
                
                for role, count in role_counts.items():
                    console.print(f"[dim]  {role}: {count} messages[/dim]")
        else:
            console.print("[yellow]Context status not available[/yellow]")
    
    @staticmethod
    def show_mode_detection_debug(mode_decision: Dict[str, Any]) -> None:
        """
        Shows detailed mode detection information for debugging
        
        Args:
            mode_decision: Result from automatic mode detection
        """
        console.print("\n[bold blue]🔍 DEBUG: Automatic Mode Detection[/bold blue]")
        
        # General information
        mode = mode_decision['mode']
        confidence = mode_decision['confidence']
        console.print(f"[green]📋 Final Decision: {mode.upper()} (confidence: {confidence:.1f}%)[/green]")
        
        # Existing project
        project_info = mode_decision['project_info']
        console.print(f"\n[cyan]📁 Project Analysis:[/cyan]")
        console.print(f"  • Project detected: {project_info['has_project']}")
        console.print(f"  • Confidence: {project_info['confidence']}%")
        console.print(f"  • Directory: {project_info['directory']}")
        
        if project_info['types']:
            console.print("  • Detected types:")
            for proj_type in project_info['types'][:3]:
                console.print(f"    - {proj_type['type']} ({proj_type['confidence']}%)")
                console.print(f"      Indicators: {', '.join(proj_type['indicators'])}")
        
        # User intention
        intent_info = mode_decision['intent_info']
        console.print(f"\n[yellow]🎯 Intent Analysis:[/yellow]")
        console.print(f"  • Intent: {intent_info['intent']}")
        console.print(f"  • Confidence: {intent_info['confidence']}%")
        console.print(f"  • Edit Score: {intent_info['edit_score']}")
        console.print(f"  • Create Score: {intent_info['create_score']}")
        
        if intent_info['edit_keywords']:
            console.print(f"  • Edit keywords: {', '.join(intent_info['edit_keywords'][:5])}")
        
        if intent_info['create_keywords']:
            console.print(f"  • Create keywords: {', '.join(intent_info['create_keywords'][:5])}")
        
        # Reasoning
        console.print(f"\n[magenta]🧠 Reasoning:[/magenta]")
        for i, reason in enumerate(mode_decision['reasoning'], 1):
            console.print(f"  {i}. {reason}")
        
        console.print("")  # Empty line
    
    @staticmethod
    def show_help():
        """Shows CLI help"""
        help_text = """
# Available Commands

- `/help` - Shows this help message
- `/models` - Lists available models
- `/clear` - Clears the screen
- `/exit` or `/quit` - Exits XandAI
- `/file <command> <file> [content]` - File operations
- `/shell` - Toggles automatic shell command execution
- `/enhance` - Toggles automatic prompt enhancement
- `/enhance_code <description>` - Improves existing code (adds details, fixes bugs)
- `/task <description>` - Executes complex task divided into steps
- `/flush` - Manually flush LLM context history to free up tokens
- `/context` - Show current context usage status and token percentage
- `/better` - Toggle better prompting system (two-stage prompt enhancement)
- `/debug` - Toggles debug mode (shows complete model responses)
- `/session <command>` - Session management commands
- `/history <command>` - Robust conversation history management

## File Commands

- `/file create <path> [content]` - Creates a file
- `/file edit <path> <content>` - Edits a file
- `/file append <path> <content>` - Adds content to file
- `/file read <path>` - Reads a file
- `/file delete <path>` - Deletes a file
- `/file list [directory] [pattern] [-r]` - Lists files (use -r for recursive search)
- `/file search <filename>` - Searches for file in parent and subdirectories

## Session Commands

- `/session info` - Shows information about current/previous session
- `/session clear` - Clears current session and archives it
- `/session backups` - Lists available session backups
- `/session restore <backup_name>` - Restores a session backup
- `/session save` - Manually saves current session

## History Commands

- `/history` - Shows conversation status and statistics
- `/history export [format]` - Exports conversation (json/markdown/txt)
- `/history summarize` - Forces conversation summarization
- `/history optimize` - Forces context optimization
- `/history stats` - Shows detailed conversation statistics
- `/history clear` - Clears conversation history (with confirmation)

## Automatic Shell Command Execution

When enabled with `/shell`, the AI can automatically execute shell commands it suggests.
Use with caution and review commands before enabling auto-execution.

## Smart File Operations

The AI can create, edit, and manage files using special tags:
- `<code create filename="file.py">code here</code>` - Creates new files
- `<code edit filename="file.py">code here</code>` - Edits existing files  
- `<actions>mkdir folder && cd folder</actions>` - Runs shell commands
- `<read>cat file.py</read>` - Reads files for context

## Enhanced Prompting

Enable `/better` for two-stage prompt enhancement that analyzes your request
and provides more detailed, context-aware responses.

## Context Management

The system automatically manages conversation context and token usage:
- Use `/flush` to clear context when it gets too large
- Use `/context` to see current context usage
- History is automatically saved and restored between sessions
"""
        
        console.print(Markdown(help_text))
    
    @staticmethod
    def show_history_help():
        """Show help for history command."""
        console.print("\n[bold cyan]Available history commands:[/bold cyan]")
        console.print("  [yellow]/history[/yellow] - Show conversation status and statistics")
        console.print("  [yellow]/history export [format][/yellow] - Export conversation (json/markdown/txt)")
        console.print("  [yellow]/history summarize[/yellow] - Force conversation summarization")
        console.print("  [yellow]/history optimize[/yellow] - Force context optimization")
        console.print("  [yellow]/history stats[/yellow] - Show detailed statistics")
        console.print("  [yellow]/history clear[/yellow] - Clear conversation history (with confirmation)")
        console.print("\n[dim]The robust history system automatically manages token budgets and summarization.[/dim]")
    
    @staticmethod
    def show_toggle_status(feature_name: str, is_enabled: bool, description: str = "", tip: str = ""):
        """Show status for toggle features"""
        status = "enabled" if is_enabled else "disabled"
        console.print(f"[green]✓ {feature_name} {status}[/green]")
        
        if description:
            if is_enabled:
                console.print(f"[dim]{description}[/dim]")
            else:
                console.print(f"[dim]{description}[/dim]")
        
        if tip:
            console.print(f"[dim]💡 {tip}[/dim]")
    
    @staticmethod
    def show_error(message: str, details: str = ""):
        """Display error message with optional details"""
        console.print(f"[red]❌ {message}[/red]")
        if details:
            console.print(f"[dim]{details}[/dim]")
    
    @staticmethod
    def show_success(message: str, details: str = ""):
        """Display success message with optional details"""
        console.print(f"[green]✓ {message}[/green]")
        if details:
            console.print(f"[dim]{details}[/dim]")
    
    @staticmethod
    def show_warning(message: str, details: str = ""):
        """Display warning message with optional details"""
        console.print(f"[yellow]⚠️ {message}[/yellow]")
        if details:
            console.print(f"[dim]{details}[/dim]")
    
    @staticmethod
    def show_info(message: str, details: str = ""):
        """Display info message with optional details"""
        console.print(f"[blue]ℹ️ {message}[/blue]")
        if details:
            console.print(f"[dim]{details}[/dim]")
    
    @staticmethod
    def show_loading(message: str = "Processing..."):
        """Show loading message"""
        console.print(f"[dim]⏳ {message}[/dim]")
    
    @staticmethod
    def clear_screen():
        """Clear the console screen"""
        console.clear()
    
    @staticmethod
    def show_separator():
        """Show a visual separator"""
        console.print("[dim]" + "─" * 50 + "[/dim]")
    
    @staticmethod
    def show_welcome():
        """Show welcome message"""
        console.print("\n[bold blue]🚀 XandAI CLI - Enhanced AI Programming Assistant[/bold blue]")
        console.print("[dim]Type '/help' for available commands or just start chatting![/dim]\n")
