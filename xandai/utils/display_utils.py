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
from xandai.processors.review_processor import ReviewResult
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

    def show_review_result(self, review_result: ReviewResult):
        """Display code review result in structured format"""
        # Header with score
        header = Text()
        header.append("🔍 CODE REVIEW RESULT", style="bold blue")

        # Score color based on value
        score = review_result.code_quality_score
        if score >= 8:
            score_style = "bold green"
        elif score >= 6:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        header.append(f" - Score: {score}/10", style=score_style)

        self.console.print(Panel(header, border_style="blue"))

        # Summary section
        if review_result.summary:
            summary_panel = Panel(
                review_result.summary, title="📋 Executive Summary", border_style="cyan"
            )
            self.console.print(summary_panel)

        # Files reviewed info
        if review_result.files_reviewed:
            files_text = Text()
            files_text.append(
                f"📁 Files reviewed: {len(review_result.files_reviewed)}\n", style="bold"
            )
            files_text.append(f"📊 Lines analyzed: {review_result.total_lines_reviewed}\n")
            files_text.append(
                f"⏱️  Estimated manual review time: {review_result.review_time_estimate}"
            )

            self.console.print(Panel(files_text, title="📈 Statistics", border_style="blue"))

        # Key issues (critical problems)
        if review_result.key_issues:
            issues_text = "\n".join(f"• {issue}" for issue in review_result.key_issues)
            self.console.print(Panel(issues_text, title="🚨 Critical Issues", border_style="red"))

        # Suggestions for improvement
        if review_result.suggestions:
            suggestions_text = "\n".join(
                f"• {suggestion}" for suggestion in review_result.suggestions
            )
            self.console.print(
                Panel(suggestions_text, title="💡 Improvement Suggestions", border_style="yellow")
            )

        # Architecture notes
        if review_result.architecture_notes:
            arch_text = "\n".join(f"• {note}" for note in review_result.architecture_notes)
            self.console.print(
                Panel(arch_text, title="🏗️  Architecture & Design", border_style="blue")
            )

        # Security concerns
        if review_result.security_concerns:
            security_text = "\n".join(f"• {concern}" for concern in review_result.security_concerns)
            self.console.print(Panel(security_text, title="🔒 Security", border_style="red"))

        # Performance notes
        if review_result.performance_notes:
            perf_text = "\n".join(f"• {note}" for note in review_result.performance_notes)
            self.console.print(Panel(perf_text, title="⚡ Performance", border_style="green"))

        # Inline comments per file
        if review_result.inline_comments:
            self.console.print("\n[bold cyan]📝 File-Specific Comments:[/bold cyan]")

            for file_path, comments in review_result.inline_comments.items():
                if comments:
                    file_text = f"[bold]{file_path}[/bold]\n"
                    file_text += "\n".join(f"  • {comment}" for comment in comments)

                    self.console.print(
                        Panel(file_text, title=f"📄 {file_path}", border_style="cyan")
                    )

        # Files reviewed list
        if review_result.files_reviewed:
            files_list = ", ".join(review_result.files_reviewed)
            if len(files_list) > 100:  # Truncate if too long
                files_list = files_list[:100] + "..."

            self.console.print(f"\n[dim]Files analyzed: {files_list}[/dim]")

        self.console.print()  # Add spacing

    def _get_action_style(self, action: str) -> str:
        """Get Rich style for action type"""
        styles = {"create": "green", "edit": "yellow", "command": "blue"}
        return styles.get(action, "white")
