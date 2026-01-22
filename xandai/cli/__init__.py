"""
XandAI CLI Commands

OpenCode-style command structure.
"""

from xandai.cli.cli_manager import CLIManager
from xandai.cli.command_registry import Command, CommandRegistry

__all__ = ["CommandRegistry", "Command", "CLIManager"]
