"""
CLI Manager

Manages command execution with OpenCode-style interface.
"""

import argparse
from typing import Any, List, Optional

from rich.console import Console

from xandai.cli.command_registry import Command, CommandCategory, CommandRegistry
from xandai.memory import MemoryManager
from xandai.session import SessionManager
from xandai.ui import StatusIndicator


class CLIManager:
    """
    CLI Manager

    Unified command-line interface manager.
    """

    def __init__(self):
        """Initialize CLI manager"""
        self.registry = CommandRegistry()
        self.console = Console()
        self.status = StatusIndicator(console=self.console)
        self.session_manager = SessionManager()
        self.memory_manager = MemoryManager()

        self._register_builtin_commands()

    def execute(self, command_name: str, args: List[str]) -> Any:
        """
        Execute a command

        Args:
            command_name: Command name
            args: Command arguments

        Returns:
            Command result
        """
        command = self.registry.get(command_name)

        if not command:
            self.status.error(f"Comando não encontrado: {command_name}")
            self.console.print("\nComandos disponíveis:")
            self.console.print(self.registry.get_help())
            return None

        try:
            return command.handler(args)
        except Exception as e:
            self.status.error(f"Erro ao executar comando: {e}")
            return None

    def parse_args(self, argv: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments

        Args:
            argv: Arguments to parse

        Returns:
            Parsed arguments
        """
        parser = argparse.ArgumentParser(
            prog="xandai", description="XandAI - Offline-first AI CLI with OpenCode UX"
        )

        # Add subparsers for categories
        subparsers = parser.add_subparsers(dest="category", help="Command category")

        # Code commands
        code_parser = subparsers.add_parser("code", help="Code operations")
        code_subparsers = code_parser.add_subparsers(dest="command")

        gen_parser = code_subparsers.add_parser("gen", help="Generate code")
        gen_parser.add_argument("description", help="What to generate")
        gen_parser.add_argument("--language", "-l", help="Programming language")

        edit_parser = code_subparsers.add_parser("edit", help="Edit code")
        edit_parser.add_argument("file", help="File to edit")
        edit_parser.add_argument("instruction", help="Edit instruction")

        review_parser = code_subparsers.add_parser("review", help="Review code")
        review_parser.add_argument("file", nargs="?", help="File to review")

        explain_parser = code_subparsers.add_parser("explain", help="Explain code")
        explain_parser.add_argument("file", help="File to explain")

        # Chat commands
        chat_parser = subparsers.add_parser("chat", help="Chat with AI")
        chat_parser.add_argument("message", nargs="*", help="Chat message")
        chat_parser.add_argument("--session", "-s", help="Session name")

        # Session commands
        session_parser = subparsers.add_parser("session", help="Session management")
        session_subparsers = session_parser.add_subparsers(dest="command")

        session_subparsers.add_parser("new", help="Create session")
        session_subparsers.add_parser("list", help="List sessions")

        load_parser = session_subparsers.add_parser("load", help="Load session")
        load_parser.add_argument("id", help="Session ID or name")

        delete_parser = session_subparsers.add_parser("delete", help="Delete session")
        delete_parser.add_argument("id", help="Session ID or name")

        # Agent commands
        agent_parser = subparsers.add_parser("agent", help="Agent operations")
        agent_subparsers = agent_parser.add_subparsers(dest="command")

        run_parser = agent_subparsers.add_parser("run", help="Run agent task")
        run_parser.add_argument("task", help="Task description")

        agent_subparsers.add_parser("status", help="Agent status")
        agent_subparsers.add_parser("stop", help="Stop agent")

        # Memory commands
        memory_parser = subparsers.add_parser("memory", help="Memory management")
        memory_subparsers = memory_parser.add_subparsers(dest="command")

        store_parser = memory_subparsers.add_parser("store", help="Store memory")
        store_parser.add_argument("content", help="Content to store")
        store_parser.add_argument("--type", "-t", help="Memory type")

        recall_parser = memory_subparsers.add_parser("recall", help="Recall memories")
        recall_parser.add_argument("query", help="Search query")

        memory_subparsers.add_parser("list", help="List memories")

        # Config commands
        config_parser = subparsers.add_parser("config", help="Configuration")
        config_subparsers = config_parser.add_subparsers(dest="command")

        set_parser = config_subparsers.add_parser("set", help="Set config")
        set_parser.add_argument("key", help="Config key")
        set_parser.add_argument("value", help="Config value")

        get_parser = config_subparsers.add_parser("get", help="Get config")
        get_parser.add_argument("key", help="Config key")

        config_subparsers.add_parser("list", help="List all config")

        # Git commands (existing)
        parser.add_argument("--commit", action="store_true", help="Generate commit message")
        parser.add_argument("--pr", action="store_true", help="Summarize PR")
        parser.add_argument("--diff", action="store_true", help="Explain diff")
        parser.add_argument("--blame", action="store_true", help="Explain blame")

        # General options
        parser.add_argument("--version", "-v", action="store_true", help="Show version")
        parser.add_argument("--help-all", action="store_true", help="Show all commands")

        return parser.parse_args(argv)

    def _register_builtin_commands(self):
        """Register built-in commands"""
        # Code commands
        self.registry.register(
            Command(
                name="gen",
                category=CommandCategory.CODE,
                description="Generate code from description",
                handler=self._code_gen,
                aliases=["generate", "create"],
                args=["description", "--language"],
                examples=["xandai code gen 'REST API with FastAPI'"],
            )
        )

        self.registry.register(
            Command(
                name="edit",
                category=CommandCategory.CODE,
                description="Edit file with AI",
                handler=self._code_edit,
                args=["file", "instruction"],
                examples=["xandai code edit main.py 'add error handling'"],
            )
        )

        self.registry.register(
            Command(
                name="review",
                category=CommandCategory.CODE,
                description="Review code",
                handler=self._code_review,
                args=["file?"],
                examples=["xandai code review app.py"],
            )
        )

        # Chat commands
        self.registry.register(
            Command(
                name="start",
                category=CommandCategory.CHAT,
                description="Start chat session",
                handler=self._chat_start,
                aliases=["chat"],
                args=["message*", "--session"],
                examples=["xandai chat 'Hello'"],
            )
        )

        # Session commands
        self.registry.register(
            Command(
                name="new",
                category=CommandCategory.SESSION,
                description="Create new session",
                handler=self._session_new,
                examples=["xandai session new"],
            )
        )

        self.registry.register(
            Command(
                name="list",
                category=CommandCategory.SESSION,
                description="List sessions",
                handler=self._session_list,
                examples=["xandai session list"],
            )
        )

        # Memory commands
        self.registry.register(
            Command(
                name="store",
                category=CommandCategory.MEMORY,
                description="Store a memory",
                handler=self._memory_store,
                args=["content", "--type"],
                examples=["xandai memory store 'Python uses indentation'"],
            )
        )

        self.registry.register(
            Command(
                name="recall",
                category=CommandCategory.MEMORY,
                description="Recall memories",
                handler=self._memory_recall,
                args=["query"],
                examples=["xandai memory recall 'Python'"],
            )
        )

    # Command handlers (placeholders)
    def _code_gen(self, args):
        """Generate code"""
        self.status.info("Code generation não implementado ainda")
        return None

    def _code_edit(self, args):
        """Edit code"""
        self.status.info("Code editing não implementado ainda")
        return None

    def _code_review(self, args):
        """Review code"""
        self.status.info("Code review não implementado ainda")
        return None

    def _chat_start(self, args):
        """Start chat"""
        self.status.info("Chat não implementado ainda")
        return None

    def _session_new(self, args):
        """Create session"""
        from xandai.session.session_commands import SessionCommands

        cmd = SessionCommands(self.session_manager)
        return cmd.cmd_new()

    def _session_list(self, args):
        """List sessions"""
        from xandai.session.session_commands import SessionCommands

        cmd = SessionCommands(self.session_manager)
        return cmd.cmd_list()

    def _memory_store(self, args):
        """Store memory"""
        self.status.info("Memory store não implementado ainda")
        return None

    def _memory_recall(self, args):
        """Recall memory"""
        self.status.info("Memory recall não implementado ainda")
        return None
