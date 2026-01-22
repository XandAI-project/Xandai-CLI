"""
Session CLI Commands

Command-line interface for session management.
"""

from typing import Optional

from rich import box
from rich.console import Console
from rich.table import Table as RichTable

from xandai.session.session_manager import SessionManager
from xandai.ui import Panel, StatusIndicator, Table


class SessionCommands:
    """
    Session management commands

    Provides CLI interface for session operations.
    """

    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Initialize session commands

        Args:
            session_manager: SessionManager instance
        """
        self.manager = session_manager or SessionManager()
        self.console = Console()
        self.status = StatusIndicator(console=self.console)

    def cmd_new(self, name: Optional[str] = None, provider: str = "ollama", model: str = "default"):
        """
        Create a new session

        Args:
            name: Session name
            provider: LLM provider
            model: Model name
        """
        try:
            session = self.manager.create_session(name=name, provider=provider, model=model)

            self.status.success(f"Criada sessão: {session.name} (ID: {session.id[:8]})")
            self.manager.set_current_session(session)

            return session

        except Exception as e:
            self.status.error(f"Erro ao criar sessão: {e}")
            return None

    def cmd_list(self, limit: Optional[int] = 20):
        """
        List sessions

        Args:
            limit: Maximum sessions to show
        """
        try:
            sessions = self.manager.list_sessions(limit=limit)

            if not sessions:
                self.status.info("Nenhuma sessão encontrada")
                return

            # Create table
            table = RichTable(title=f"Sessões ({len(sessions)})", box=box.ROUNDED, show_lines=True)

            table.add_column("ID", style="cyan")
            table.add_column("Nome", style="bold")
            table.add_column("Provider", style="green")
            table.add_column("Model", style="yellow")
            table.add_column("Tokens", style="magenta", justify="right")
            table.add_column("Atualizada", style="dim")

            current_id = self.manager.current_session.id if self.manager.current_session else None

            for session in sessions:
                is_current = session["id"] == current_id
                prefix = "➤ " if is_current else ""

                table.add_row(
                    f"{prefix}{session['id'][:8]}",
                    session["name"],
                    session["provider"],
                    session["model"],
                    str(session["total_tokens"]),
                    session["updated_at"][:19].replace("T", " "),
                )

            self.console.print(table)

        except Exception as e:
            self.status.error(f"Erro ao listar sessões: {e}")

    def cmd_load(self, identifier: str):
        """
        Load a session by ID or name

        Args:
            identifier: Session ID or name
        """
        try:
            # Try loading by ID first
            session = self.manager.load_session(identifier)

            # If not found, try by name
            if not session:
                session = self.manager.load_session_by_name(identifier)

            if not session:
                self.status.error(f"Sessão não encontrada: {identifier}")
                return None

            self.manager.set_current_session(session)
            self.status.success(f"Carregada sessão: {session.name}")

            # Show session info
            self._show_session_info(session.id)

            return session

        except Exception as e:
            self.status.error(f"Erro ao carregar sessão: {e}")
            return None

    def cmd_delete(self, identifier: str, confirm: bool = False):
        """
        Delete a session

        Args:
            identifier: Session ID or name
            confirm: Skip confirmation
        """
        try:
            # Find session
            session = self.manager.load_session(identifier)
            if not session:
                session = self.manager.load_session_by_name(identifier)

            if not session:
                self.status.error(f"Sessão não encontrada: {identifier}")
                return False

            # Confirm deletion
            if not confirm:
                response = input(f"Deletar sessão '{session.name}'? (s/n): ")
                if response.lower() not in ["s", "sim", "y", "yes"]:
                    self.status.info("Cancelado")
                    return False

            # Delete
            deleted = self.manager.delete_session(session.id)

            if deleted:
                self.status.success(f"Sessão deletada: {session.name}")

                # Clear current if deleted
                if self.manager.current_session and self.manager.current_session.id == session.id:
                    self.manager.set_current_session(None)

                return True
            else:
                self.status.error("Erro ao deletar sessão")
                return False

        except Exception as e:
            self.status.error(f"Erro ao deletar sessão: {e}")
            return False

    def cmd_info(self, identifier: Optional[str] = None):
        """
        Show session information

        Args:
            identifier: Session ID/name (current if None)
        """
        try:
            if identifier:
                session_id = identifier
                session = self.manager.load_session(session_id)
                if not session:
                    session = self.manager.load_session_by_name(session_id)
                    if session:
                        session_id = session.id
            else:
                if not self.manager.current_session:
                    self.status.error("Nenhuma sessão ativa")
                    return
                session_id = self.manager.current_session.id
                session = self.manager.current_session

            if not session:
                self.status.error(f"Sessão não encontrada: {identifier}")
                return

            self._show_session_info(session_id)

        except Exception as e:
            self.status.error(f"Erro ao mostrar info: {e}")

    def cmd_export(self, identifier: str, filepath: str, format: str = "json"):
        """
        Export session to file

        Args:
            identifier: Session ID or name
            filepath: Output file path
            format: Export format (json, markdown)
        """
        try:
            # Find session
            session = self.manager.load_session(identifier)
            if not session:
                session = self.manager.load_session_by_name(identifier)
                if session:
                    identifier = session.id

            if not session:
                self.status.error(f"Sessão não encontrada: {identifier}")
                return False

            # Export
            self.manager.export_session(identifier, filepath, format)
            self.status.success(f"Sessão exportada para: {filepath}")

            return True

        except Exception as e:
            self.status.error(f"Erro ao exportar: {e}")
            return False

    def cmd_import(self, filepath: str):
        """
        Import session from file

        Args:
            filepath: Input file path
        """
        try:
            session = self.manager.import_session(filepath)
            self.status.success(f"Sessão importada: {session.name}")

            return session

        except Exception as e:
            self.status.error(f"Erro ao importar: {e}")
            return None

    def cmd_search(self, query: str):
        """
        Search sessions

        Args:
            query: Search query
        """
        try:
            sessions = self.manager.search_sessions(query)

            if not sessions:
                self.status.info(f"Nenhuma sessão encontrada para: {query}")
                return

            # Show results in table
            table = RichTable(title=f"Resultados: '{query}' ({len(sessions)})", box=box.ROUNDED)

            table.add_column("ID", style="cyan")
            table.add_column("Nome", style="bold")
            table.add_column("Provider", style="green")
            table.add_column("Tokens", style="magenta", justify="right")
            table.add_column("Atualizada", style="dim")

            for session in sessions:
                table.add_row(
                    session["id"][:8],
                    session["name"],
                    session["provider"],
                    str(session["total_tokens"]),
                    session["updated_at"][:19].replace("T", " "),
                )

            self.console.print(table)

        except Exception as e:
            self.status.error(f"Erro na busca: {e}")

    def cmd_clear(self, identifier: Optional[str] = None):
        """
        Clear messages from session

        Args:
            identifier: Session ID/name (current if None)
        """
        try:
            if identifier:
                session = self.manager.load_session(identifier)
                if not session:
                    session = self.manager.load_session_by_name(identifier)
            else:
                session = self.manager.current_session

            if not session:
                self.status.error("Sessão não encontrada")
                return False

            session.clear_messages()
            self.manager.save_session(session)

            self.status.success(f"Mensagens limpas: {session.name}")
            return True

        except Exception as e:
            self.status.error(f"Erro ao limpar mensagens: {e}")
            return False

    def _show_session_info(self, session_id: str):
        """Show detailed session information"""
        stats = self.manager.get_session_stats(session_id)

        if not stats:
            return

        info_text = f"""
**Nome**: {stats['name']}
**ID**: {stats['id'][:16]}...
**Provider**: {stats['provider']}
**Model**: {stats['model']}

**Mensagens**: {stats['total_messages']} total
  - Usuário: {stats['user_messages']}
  - Assistente: {stats['assistant_messages']}

**Tokens**: {stats['total_tokens']} total
  - Média por mensagem: {stats['avg_tokens_per_message']:.1f}

**Criada**: {stats['created_at'][:19].replace('T', ' ')}
**Atualizada**: {stats['updated_at'][:19].replace('T', ' ')}
**Duração**: {stats['duration']}
"""

        Panel(console=self.console).render(
            info_text.strip(), title="Informações da Sessão", style="cyan", border_style="cyan"
        )
