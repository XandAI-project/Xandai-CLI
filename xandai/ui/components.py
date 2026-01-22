"""
UI Components

Reusable terminal UI components with Rich styling.
"""

from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel as RichPanel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table as RichTable


class Panel:
    """Styled panel component"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "bold blue",
        border_style: str = "blue",
        expand: bool = False,
    ):
        """
        Render a panel

        Args:
            content: Panel content
            title: Optional title
            style: Content style
            border_style: Border color
            expand: Expand to terminal width
        """
        panel = RichPanel(
            content,
            title=title,
            style=style,
            border_style=border_style,
            expand=expand,
            box=box.ROUNDED,
        )
        self.console.print(panel)


class Table:
    """Styled table component"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render(
        self,
        title: Optional[str] = None,
        columns: Optional[List[str]] = None,
        rows: Optional[List[List[Any]]] = None,
        header_style: str = "bold cyan",
        show_lines: bool = False,
    ):
        """
        Render a table

        Args:
            title: Table title
            columns: Column headers
            rows: Table rows
            header_style: Header style
            show_lines: Show row lines
        """
        table = RichTable(
            title=title,
            show_header=bool(columns),
            header_style=header_style,
            show_lines=show_lines,
            box=box.ROUNDED,
        )

        # Add columns
        if columns:
            for col in columns:
                table.add_column(col)

        # Add rows
        if rows:
            for row in rows:
                table.add_row(*[str(cell) for cell in row])

        self.console.print(table)


class ProgressBar:
    """Progress bar component"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def create(self, total: int, description: str = "Processing"):
        """
        Create a progress bar context

        Args:
            total: Total items
            description: Progress description

        Returns:
            Progress context manager
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )
        return progress, progress.add_task(description, total=total)


class Spinner:
    """Loading spinner component"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def spin(self, message: str = "Loading..."):
        """
        Show spinner

        Args:
            message: Loading message

        Returns:
            Status context manager
        """
        return self.console.status(message, spinner="dots")


class CodeBlock:
    """Syntax-highlighted code block"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render(
        self, code: str, language: str = "python", theme: str = "monokai", line_numbers: bool = True
    ):
        """
        Render code block

        Args:
            code: Code content
            language: Programming language
            theme: Syntax theme
            line_numbers: Show line numbers
        """
        syntax = Syntax(code, language, theme=theme, line_numbers=line_numbers, word_wrap=False)
        self.console.print(syntax)


class StatusIndicator:
    """Status indicator (success, error, warning, info)"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def success(self, message: str):
        """Show success message"""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def error(self, message: str):
        """Show error message"""
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def warning(self, message: str):
        """Show warning message"""
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    def info(self, message: str):
        """Show info message"""
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")


class MessageBox:
    """Message box for important notifications"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def show(self, message: str, title: Optional[str] = None, msg_type: str = "info"):
        """
        Show message box

        Args:
            message: Message content
            title: Box title
            msg_type: Message type (info, success, error, warning)
        """
        style_map = {
            "info": "bold blue",
            "success": "bold green",
            "error": "bold red",
            "warning": "bold yellow",
        }

        style = style_map.get(msg_type, "bold blue")

        panel = RichPanel(
            message,
            title=title or msg_type.upper(),
            style=style,
            border_style=style,
            expand=False,
            box=box.DOUBLE,
        )

        self.console.print(panel)
