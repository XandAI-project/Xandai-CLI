"""
Command Registry

Central registry for CLI commands with OpenCode-style structure.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class CommandCategory(Enum):
    """Command categories"""

    CODE = "code"
    CHAT = "chat"
    SESSION = "session"
    AGENT = "agent"
    PROJECT = "project"
    CONFIG = "config"
    GIT = "git"
    MEMORY = "memory"


@dataclass
class Command:
    """Command definition"""

    name: str
    category: CommandCategory
    description: str
    handler: Callable
    aliases: List[str] = None
    args: List[str] = None
    examples: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.args is None:
            self.args = []
        if self.examples is None:
            self.examples = []


class CommandRegistry:
    """
    Command Registry

    Manages all CLI commands with OpenCode-style organization.
    """

    def __init__(self):
        """Initialize command registry"""
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}
        self._init_default_commands()

    def register(self, command: Command):
        """
        Register a command

        Args:
            command: Command to register
        """
        full_name = f"{command.category.value}.{command.name}"
        self.commands[full_name] = command

        # Register aliases
        for alias in command.aliases:
            self.aliases[alias] = full_name

    def get(self, name: str) -> Optional[Command]:
        """
        Get a command by name or alias

        Args:
            name: Command name or alias

        Returns:
            Command or None
        """
        # Check direct name
        if name in self.commands:
            return self.commands[name]

        # Check aliases
        if name in self.aliases:
            return self.commands[self.aliases[name]]

        # Try category.command format
        for cmd_name, command in self.commands.items():
            if cmd_name.endswith(f".{name}"):
                return command

        return None

    def list_commands(self, category: Optional[CommandCategory] = None) -> List[Command]:
        """
        List all commands

        Args:
            category: Filter by category

        Returns:
            List of commands
        """
        commands = list(self.commands.values())

        if category:
            commands = [c for c in commands if c.category == category]

        return sorted(commands, key=lambda c: (c.category.value, c.name))

    def list_categories(self) -> List[CommandCategory]:
        """List all command categories"""
        categories = set(cmd.category for cmd in self.commands.values())
        return sorted(categories, key=lambda c: c.value)

    def get_help(self, name: Optional[str] = None) -> str:
        """
        Get help text

        Args:
            name: Command name (all commands if None)

        Returns:
            Help text
        """
        if name:
            command = self.get(name)
            if not command:
                return f"Comando não encontrado: {name}"

            return self._format_command_help(command)
        else:
            return self._format_all_help()

    def _format_command_help(self, command: Command) -> str:
        """Format help for a single command"""
        lines = []
        lines.append(f"\n{command.category.value}.{command.name}")
        lines.append("=" * 50)
        lines.append(f"\nDescrição: {command.description}")

        if command.aliases:
            lines.append(f"Aliases: {', '.join(command.aliases)}")

        if command.args:
            lines.append(f"\nArgumentos:")
            for arg in command.args:
                lines.append(f"  {arg}")

        if command.examples:
            lines.append(f"\nExemplos:")
            for example in command.examples:
                lines.append(f"  {example}")

        return "\n".join(lines)

    def _format_all_help(self) -> str:
        """Format help for all commands"""
        lines = []
        lines.append("\nXandAI - Comandos Disponíveis")
        lines.append("=" * 50)

        for category in self.list_categories():
            lines.append(f"\n{category.value.upper()}")
            lines.append("-" * 30)

            commands = self.list_commands(category)
            for cmd in commands:
                cmd_name = f"{cmd.category.value}.{cmd.name}"
                aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                lines.append(f"  {cmd_name}{aliases}")
                lines.append(f"    {cmd.description}")

        lines.append("\nUse 'xandai help <comando>' para mais detalhes")

        return "\n".join(lines)

    def _init_default_commands(self):
        """Initialize default command structure"""
        # This will be populated by individual command modules
        pass


# Global registry instance
_registry = None


def get_registry() -> CommandRegistry:
    """Get global command registry"""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry
