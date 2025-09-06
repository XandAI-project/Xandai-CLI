"""
XandAI Conversation - Gerenciador de Conversas
Sistema de histórico e contexto persistente entre sessões
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ConversationMessage:
    """Conversation message"""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    mode: str = "chat"  # "chat", "task", "command"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConversationSession:
    """Conversation session"""

    session_id: str
    start_time: datetime
    last_activity: datetime
    messages: List[ConversationMessage]
    total_tokens: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConversationManager:
    """
    Gerenciador de conversas e histórico

    Mantém contexto persistente, gerencia sessões e
    fornece funcionalidades de busca e resumo.
    """

    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

        self.current_session: Optional[ConversationSession] = None
        self.max_messages_in_memory = 100
        self.max_session_age_days = 30

        # Carrega ou cria sessão atual
        self._load_or_create_session()

    def _load_or_create_session(self):
        """Loads existing session or creates new one"""
        # Tenta carregar sessão mais recente
        latest_session = self._get_latest_session_file()

        if latest_session and self._is_session_recent(latest_session):
            self.current_session = self._load_session(latest_session)
        else:
            self._create_new_session()

    def _create_new_session(self):
        """Creates new session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = ConversationSession(
            session_id=session_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            messages=[],
        )
        self._save_session()

    def add_message(
        self,
        role: str,
        content: str,
        mode: str = "chat",
        metadata: Dict[str, Any] = None,
    ):
        """
        Adiciona mensagem à conversação atual

        Args:
            role: "user", "assistant", "system"
            content: Conteúdo da mensagem
            mode: Modo da interação ("chat", "task", "command")
            metadata: Metadados adicionais
        """
        if not self.current_session:
            self._create_new_session()

        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            mode=mode,
            metadata=metadata or {},
        )

        self.current_session.messages.append(message)
        self.current_session.last_activity = datetime.now()

        # Limita mensagens em memória
        if len(self.current_session.messages) > self.max_messages_in_memory:
            self._archive_old_messages()

        # Salva automaticamente
        self._save_session()

    def get_recent_history(
        self, limit: int = 10, mode_filter: Optional[str] = None
    ) -> List[ConversationMessage]:
        """
        Obtém histórico recente de mensagens

        Args:
            limit: Número máximo de mensagens
            mode_filter: Filtrar por modo específico
        """
        if not self.current_session:
            return []

        messages = self.current_session.messages

        if mode_filter:
            messages = [msg for msg in messages if msg.mode == mode_filter]

        return messages[-limit:] if limit > 0 else messages

    def get_context_for_ai(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        Retorna contexto formatado para o AI

        Args:
            max_tokens: Limite aproximado de tokens
        """
        if not self.current_session:
            return []

        # Estima tokens (aproximação: 1 token ≈ 4 caracteres)
        context = []
        total_chars = 0

        # Inclui mensagens recentes até o limite
        for message in reversed(self.current_session.messages):
            message_chars = len(message.content)
            if total_chars + message_chars > max_tokens * 4:
                break

            context.insert(0, {"role": message.role, "content": message.content})
            total_chars += message_chars

        return context

    def search_messages(self, query: str, limit: int = 20) -> List[ConversationMessage]:
        """
        Busca mensagens por conteúdo
        """
        if not self.current_session:
            return []

        query_lower = query.lower()
        matches = []

        for message in self.current_session.messages:
            if query_lower in message.content.lower():
                matches.append(message)
                if len(matches) >= limit:
                    break

        return matches

    def get_session_summary(self) -> Dict[str, Any]:
        """Returns current session summary"""
        if not self.current_session:
            return {}

        messages = self.current_session.messages
        mode_counts = {}

        for msg in messages:
            mode_counts[msg.mode] = mode_counts.get(msg.mode, 0) + 1

        return {
            "session_id": self.current_session.session_id,
            "start_time": self.current_session.start_time.isoformat(),
            "last_activity": self.current_session.last_activity.isoformat(),
            "total_messages": len(messages),
            "mode_breakdown": mode_counts,
            "total_tokens": self.current_session.total_tokens,
            "duration_minutes": self._get_session_duration_minutes(),
        }

    def clear_session(self):
        """Clears current session"""
        if self.current_session:
            # Arquiva sessão atual
            self._archive_session()

        # Cria nova sessão
        self._create_new_session()

    def export_session(self, format: str = "json") -> str:
        """
        Exporta sessão atual

        Args:
            format: "json" ou "txt"
        """
        if not self.current_session:
            return ""

        if format == "json":
            return self._export_json()
        elif format == "txt":
            return self._export_text()
        else:
            raise ValueError("Format deve ser 'json' ou 'txt'")

    def _export_json(self) -> str:
        """Exporta como JSON"""
        session_dict = asdict(self.current_session)
        # Converte timestamps para strings
        for msg in session_dict["messages"]:
            msg["timestamp"] = msg["timestamp"].isoformat()
        session_dict["start_time"] = session_dict["start_time"].isoformat()
        session_dict["last_activity"] = session_dict["last_activity"].isoformat()

        return json.dumps(session_dict, indent=2, ensure_ascii=False)

    def _export_text(self) -> str:
        """Exports as readable text"""
        if not self.current_session:
            return ""

        lines = [
            f"=== Sessão XandAI: {self.current_session.session_id} ===",
            f"Início: {self.current_session.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Última atividade: {self.current_session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total de mensagens: {len(self.current_session.messages)}",
            "",
            "=== Conversação ===",
        ]

        for msg in self.current_session.messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role, "❓")
            lines.append(f"\n[{timestamp}] {role_emoji} {msg.role.upper()} ({msg.mode}):")
            lines.append(msg.content)

        return "\n".join(lines)

    def _save_session(self):
        """Saves current session"""
        if not self.current_session:
            return

        filename = f"{self.current_session.session_id}.json"
        filepath = self.sessions_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                self._serialize_session(self.current_session),
                f,
                indent=2,
                ensure_ascii=False,
            )

    def _load_session(self, filepath: Path) -> ConversationSession:
        """Loads session from file"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self._deserialize_session(data)

    def _serialize_session(self, session: ConversationSession) -> Dict[str, Any]:
        """Serializes session for saving"""
        data = asdict(session)
        data["start_time"] = session.start_time.isoformat()
        data["last_activity"] = session.last_activity.isoformat()

        for msg in data["messages"]:
            msg["timestamp"] = msg["timestamp"].isoformat()

        return data

    def _deserialize_session(self, data: Dict[str, Any]) -> ConversationSession:
        """Deserializes session from file"""
        messages = []
        for msg_data in data["messages"]:
            msg_data["timestamp"] = datetime.fromisoformat(msg_data["timestamp"])
            messages.append(ConversationMessage(**msg_data))

        return ConversationSession(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            messages=messages,
            total_tokens=data.get("total_tokens", 0),
            metadata=data.get("metadata", {}),
        )

    def _get_latest_session_file(self) -> Optional[Path]:
        """Finds most recent session file"""
        session_files = list(self.sessions_dir.glob("session_*.json"))
        if not session_files:
            return None

        return max(session_files, key=lambda f: f.stat().st_mtime)

    def _is_session_recent(self, filepath: Path) -> bool:
        """Checks if session is recent enough"""
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age_days = (datetime.now() - mtime).days
        return age_days <= self.max_session_age_days

    def _archive_old_messages(self):
        """Arquiva mensagens antigas"""
        if not self.current_session:
            return

        # Mantém apenas as mensagens mais recentes
        keep_count = self.max_messages_in_memory // 2
        archived_messages = self.current_session.messages[:-keep_count]
        self.current_session.messages = self.current_session.messages[-keep_count:]

        # TODO: Salvar mensagens arquivadas em arquivo separado

    def _archive_session(self):
        """Archives current session"""
        if not self.current_session:
            return

        # Cria backup da sessão
        backup_name = f"backup_{self.current_session.session_id}.json"
        backup_path = self.sessions_dir / backup_name

        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(
                self._serialize_session(self.current_session),
                f,
                indent=2,
                ensure_ascii=False,
            )

    def _get_session_duration_minutes(self) -> int:
        """Calculates session duration in minutes"""
        if not self.current_session:
            return 0

        duration = self.current_session.last_activity - self.current_session.start_time
        return int(duration.total_seconds() / 60)
