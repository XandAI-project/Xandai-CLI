"""
Theme System

Customizable color themes for terminal UI.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from rich.console import Console
from rich.theme import Theme as RichTheme


@dataclass
class Theme:
    """UI Theme definition"""

    name: str
    primary: str
    secondary: str
    success: str
    error: str
    warning: str
    info: str
    text: str
    dim: str
    border: str

    def to_rich_theme(self) -> RichTheme:
        """Convert to Rich theme"""
        return RichTheme(
            {
                "primary": self.primary,
                "secondary": self.secondary,
                "success": self.success,
                "error": self.error,
                "warning": self.warning,
                "info": self.info,
                "text": self.text,
                "dim": self.dim,
                "border": self.border,
            }
        )


class ThemeManager:
    """
    Theme Manager

    Manages UI themes and allows switching between them.
    """

    # Built-in themes
    THEMES: Dict[str, Theme] = {
        "default": Theme(
            name="default",
            primary="bold cyan",
            secondary="bold blue",
            success="bold green",
            error="bold red",
            warning="bold yellow",
            info="bold blue",
            text="white",
            dim="dim white",
            border="cyan",
        ),
        "dark": Theme(
            name="dark",
            primary="bold bright_cyan",
            secondary="bold bright_blue",
            success="bold bright_green",
            error="bold bright_red",
            warning="bold bright_yellow",
            info="bold bright_blue",
            text="bright_white",
            dim="dim bright_white",
            border="bright_cyan",
        ),
        "light": Theme(
            name="light",
            primary="bold blue",
            secondary="bold cyan",
            success="bold green",
            error="bold red",
            warning="bold yellow",
            info="bold blue",
            text="black",
            dim="dim black",
            border="blue",
        ),
        "ocean": Theme(
            name="ocean",
            primary="bold deep_sky_blue1",
            secondary="bold dodger_blue2",
            success="bold sea_green2",
            error="bold red1",
            warning="bold gold1",
            info="bold sky_blue1",
            text="white",
            dim="dim white",
            border="deep_sky_blue1",
        ),
        "forest": Theme(
            name="forest",
            primary="bold green3",
            secondary="bold green4",
            success="bold green1",
            error="bold red3",
            warning="bold yellow3",
            info="bold cyan3",
            text="white",
            dim="dim white",
            border="green3",
        ),
        "sunset": Theme(
            name="sunset",
            primary="bold orange1",
            secondary="bold orange3",
            success="bold green1",
            error="bold red1",
            warning="bold yellow1",
            info="bold cyan1",
            text="white",
            dim="dim white",
            border="orange1",
        ),
        "cyberpunk": Theme(
            name="cyberpunk",
            primary="bold magenta",
            secondary="bold purple",
            success="bold green",
            error="bold red1",
            warning="bold yellow1",
            info="bold cyan",
            text="white",
            dim="dim white",
            border="magenta",
        ),
        "minimal": Theme(
            name="minimal",
            primary="white",
            secondary="bright_white",
            success="green",
            error="red",
            warning="yellow",
            info="blue",
            text="white",
            dim="dim",
            border="white",
        ),
    }

    def __init__(self, default_theme: str = "default"):
        """
        Initialize theme manager

        Args:
            default_theme: Default theme name
        """
        self.current_theme_name = default_theme
        self.custom_themes: Dict[str, Theme] = {}

    def get_theme(self, name: Optional[str] = None) -> Theme:
        """
        Get theme by name

        Args:
            name: Theme name (None for current)

        Returns:
            Theme object
        """
        theme_name = name or self.current_theme_name

        # Check custom themes first
        if theme_name in self.custom_themes:
            return self.custom_themes[theme_name]

        # Check built-in themes
        if theme_name in self.THEMES:
            return self.THEMES[theme_name]

        # Fallback to default
        return self.THEMES["default"]

    def set_theme(self, name: str):
        """
        Set active theme

        Args:
            name: Theme name
        """
        if name not in self.THEMES and name not in self.custom_themes:
            raise ValueError(f"Theme '{name}' not found")

        self.current_theme_name = name

    def register_theme(self, theme: Theme):
        """
        Register a custom theme

        Args:
            theme: Theme object
        """
        self.custom_themes[theme.name] = theme

    def list_themes(self) -> list:
        """List all available themes"""
        builtin = list(self.THEMES.keys())
        custom = list(self.custom_themes.keys())
        return sorted(builtin + custom)

    def create_console(self, theme: Optional[str] = None) -> Console:
        """
        Create a console with theme applied

        Args:
            theme: Theme name (None for current)

        Returns:
            Themed Console instance
        """
        theme_obj = self.get_theme(theme)
        rich_theme = theme_obj.to_rich_theme()

        return Console(theme=rich_theme)

    def preview_theme(self, name: str):
        """
        Preview a theme

        Args:
            name: Theme name to preview
        """
        theme = self.get_theme(name)
        console = Console()

        console.print(f"\n[bold]Theme Preview: {name}[/bold]\n")
        console.print(f"[{theme.primary}]Primary: This is primary text[/{theme.primary}]")
        console.print(f"[{theme.secondary}]Secondary: This is secondary text[/{theme.secondary}]")
        console.print(
            f"[{theme.success}]Success: Operation completed successfully[/{theme.success}]"
        )
        console.print(f"[{theme.error}]Error: Something went wrong[/{theme.error}]")
        console.print(f"[{theme.warning}]Warning: Please be careful[/{theme.warning}]")
        console.print(f"[{theme.info}]Info: Just so you know[/{theme.info}]")
        console.print(f"[{theme.text}]Text: Regular text content[/{theme.text}]")
        console.print(f"[{theme.dim}]Dim: Dimmed text[/{theme.dim}]")
        console.print()


# Global theme manager
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
