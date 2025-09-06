"""
XandAI Utils - Display Utilities
Utilities for rich text display and formatted output
"""

from typing import Any, Dict, List

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from xandai.conversation.conversation_manager import ConversationMessage
from xandai.processors.task_processor import TaskResult


class DisplayUtils:
    """
    Utilities for rich text display and formatted output

    Provides methods to display responses, task results, history,
    and other information in a consistent, readable format.
    """

    def __init__(self, console: Console):
        self.console = console

    def show_chat_response(self, response: str):
        """Display chat mode response"""
        # Parse and render markdown if present
        try:
            if "```" in response or "#" in response or "*" in response:
                markdown = Markdown(response)
                self.console.print(markdown)
            else:
                self.console.print(response)
        except:
            # Fallback to plain text
            self.console.print(response)

        self.console.print()  # Add spacing

    def show_task_result(self, task_result: TaskResult):
        """Display structured task result"""
        # Header
        header = Text()
        header.append("📋 TASK RESULT", style="bold blue")

        self.console.print(Panel(header, border_style="blue"))

        # Basic info
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Field", style="cyan", width=15)
        info_table.add_column("Value")

        info_table.add_row("Project:", task_result.description)
        info_table.add_row("Type:", task_result.project_type)
        info_table.add_row("Complexity:", task_result.complexity)
        info_table.add_row("Estimated Time:", task_result.estimated_time)

        self.console.print(info_table)
        self.console.print()

        # Dependencies
        if task_result.dependencies:
            self.console.print("[cyan]Dependencies:[/cyan]")
            for dep in task_result.dependencies:
                self.console.print(f"  • {dep}")
            self.console.print()

        # Steps
        self.console.print("[cyan]Execution Steps:[/cyan]")
        for step in task_result.steps:
            step_text = Text()
            step_text.append(f"{step.step_number} - ", style="bold")
            step_text.append(f"{step.action} ", style=self._get_action_style(step.action))
            step_text.append(step.target)

            self.console.print(step_text)

            # Show content preview if available
            if step.content:
                preview = step.content[:100] + "..." if len(step.content) > 100 else step.content
                self.console.print(f"    [dim]Content preview: {preview}[/dim]")
            elif step.commands:
                cmd_preview = ", ".join(step.commands[:2])
                if len(step.commands) > 2:
                    cmd_preview += f" (+{len(step.commands)-2} more)"
                self.console.print(f"    [dim]Commands: {cmd_preview}[/dim]")

        self.console.print()

        # Notes
        if task_result.notes:
            self.console.print("[cyan]Important Notes:[/cyan]")
            for note in task_result.notes:
                self.console.print(f"  ⚠️  {note}")
            self.console.print()

    def show_history(self, messages: List[ConversationMessage]):
        """Display conversation history"""
        if not messages:
            self.console.print("[yellow]No conversation history found[/yellow]")
            return

        self.console.print(Panel("[bold]Recent Conversation History[/bold]", border_style="blue"))

        for msg in messages[-10:]:  # Show last 10 messages
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role, "❓")

            # Message header
            header = Text()
            header.append(f"[{timestamp}] ", style="dim")
            header.append(f"{role_emoji} {msg.role.upper()}", style="bold")
            header.append(f" ({msg.mode})", style="dim")

            self.console.print(header)

            # Message content (truncated)
            content = msg.content
            if len(content) > 200:
                content = content[:200] + "..."

            self.console.print(content, style="dim")
            self.console.print()

    def show_status(self, status: Dict[str, Any]):
        """Display application status"""
        status_table = Table(title="XandAI Status", box=None)
        status_table.add_column("Property", style="cyan", width=20)
        status_table.add_column("Value", style="green")

        for key, value in status.items():
            status_table.add_row(key, str(value))

        self.console.print(status_table)

    def show_error(self, error: str, context: str = None):
        """Display error message"""
        error_text = Text()
        error_text.append("❌ ERROR: ", style="bold red")
        error_text.append(error)

        if context:
            error_text.append(f"\nContext: {context}", style="dim")

        self.console.print(Panel(error_text, border_style="red"))

    def show_warning(self, warning: str):
        """Display warning message"""
        warning_text = Text()
        warning_text.append("⚠️  WARNING: ", style="bold yellow")
        warning_text.append(warning)

        self.console.print(warning_text)

    def show_success(self, message: str):
        """Display success message"""
        success_text = Text()
        success_text.append("✅ SUCCESS: ", style="bold green")
        success_text.append(message)

        self.console.print(success_text)

    def show_info(self, message: str):
        """Display info message"""
        info_text = Text()
        info_text.append("ℹ️  INFO: ", style="bold blue")
        info_text.append(message)

        self.console.print(info_text)

    def show_code_block(self, code: str, language: str = "python", title: str = None):
        """Display syntax highlighted code block"""
        try:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            if title:
                self.console.print(Panel(syntax, title=title, border_style="blue"))
            else:
                self.console.print(syntax)
        except:
            # Fallback to plain text
            if title:
                self.console.print(Panel(code, title=title, border_style="blue"))
            else:
                self.console.print(code)

    def show_progress(self, message: str):
        """Display progress message"""
        progress_text = Text()
        progress_text.append("⏳ ", style="yellow")
        progress_text.append(message, style="dim")

        self.console.print(progress_text)

    def _get_action_style(self, action: str) -> str:
        """Get Rich style for action type"""
        styles = {"create": "green", "edit": "yellow", "command": "blue"}
        return styles.get(action, "white")
