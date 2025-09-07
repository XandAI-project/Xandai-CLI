"""
XandAI Core - Estado da Aplicação
Gerencia estado global da aplicação e contexto de sessão
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProjectContext:
    """Contexto do projeto atual"""

    root_path: Optional[str] = None
    project_type: Optional[str] = None  # 'python', 'javascript', 'web', etc.
    files_tracked: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    is_git_repo: bool = False


@dataclass
class SessionMetrics:
    """Current session metrics"""

    start_time: datetime = field(default_factory=datetime.now)
    commands_executed: int = 0
    chat_interactions: int = 0
    task_interactions: int = 0
    last_activity: datetime = field(default_factory=datetime.now)


class AppState:
    """
    Estado global da aplicação XandAI

    Mantém contexto de sessão, informações do projeto,
    configurações e métricas de uso.
    """

    def __init__(self):
        self.project_context = ProjectContext()
        self.session_metrics = SessionMetrics()
        self.user_preferences: Dict[str, Any] = {}
        self.active_conversation_id: Optional[str] = None
        self.current_model: str = os.getenv("XANDAI_MODEL", "llama3.2")
        self.verbose_mode: bool = os.getenv("XANDAI_VERBOSE", "0") == "1"

        # EditModeEnhancer state
        self.detected_mode_cache: Dict[str, str] = {}
        self.context_analysis_cache: Dict[str, Any] = {}

        # Carrega configurações persistentes
        self._load_preferences()
        self._detect_project_context()

    def reset(self):
        """Resets session state keeping configurations"""
        self.session_metrics = SessionMetrics()
        self.active_conversation_id = None
        self.detected_mode_cache.clear()
        self.context_analysis_cache.clear()

    def update_activity(self):
        """Atualiza timestamp da última atividade"""
        self.session_metrics.last_activity = datetime.now()

    def increment_chat_interaction(self):
        """Increments chat interaction counter"""
        self.session_metrics.chat_interactions += 1
        self.update_activity()

    def increment_task_interaction(self):
        """Increments task interaction counter"""
        self.session_metrics.task_interactions += 1
        self.update_activity()

    def increment_command(self):
        """Incrementa contador de comandos executados"""
        self.session_metrics.commands_executed += 1
        self.update_activity()

    def set_project_context(self, root_path: str, project_type: str = None):
        """Define contexto do projeto"""
        self.project_context.root_path = root_path
        self.project_context.project_type = project_type or self._detect_project_type(root_path)
        self.project_context.last_modified = datetime.now()
        self.project_context.is_git_repo = os.path.exists(os.path.join(root_path, ".git"))

    def add_tracked_file(self, file_path: str):
        """Adiciona arquivo ao tracking"""
        if file_path not in self.project_context.files_tracked:
            self.project_context.files_tracked.append(file_path)

    def get_context_summary(self) -> Dict[str, Any]:
        """Retorna resumo do contexto atual"""
        return {
            "project_type": self.project_context.project_type,
            "root_path": self.project_context.root_path,
            "tracked_files": len(self.project_context.files_tracked),
            "session_duration": self._get_session_duration(),
            "interactions": {
                "chat": self.session_metrics.chat_interactions,
                "task": self.session_metrics.task_interactions,
                "commands": self.session_metrics.commands_executed,
            },
            "model": self.current_model,
            "verbose": self.verbose_mode,
        }

    def cache_mode_detection(self, input_text: str, detected_mode: str):
        """Cache mode detection result"""
        # Usa hash simples para key (primeiras/últimas palavras)
        words = input_text.split()
        if len(words) > 0:
            key = f"{words[0]}...{words[-1]}" if len(words) > 1 else words[0]
            self.detected_mode_cache[key] = detected_mode

    def get_cached_mode(self, input_text: str) -> Optional[str]:
        """Retrieves cached mode if available"""
        words = input_text.split()
        if len(words) > 0:
            key = f"{words[0]}...{words[-1]}" if len(words) > 1 else words[0]
            return self.detected_mode_cache.get(key)
        return None

    def _detect_project_context(self):
        """Detecta contexto do projeto atual"""
        current_dir = os.getcwd()
        self.set_project_context(current_dir)

    def _detect_project_type(self, root_path: str) -> str:
        """Detecta tipo do projeto baseado em arquivos"""
        indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json", "package-lock.json", "yarn.lock"],
            "web": ["index.html", "app.html", "main.html"],
            "react": ["package.json"],  # Será refinado se package.json contém react
            "django": ["manage.py", "django"],
            "flask": ["app.py", "wsgi.py"],
            "git": [".git"],
        }

        files_in_root = os.listdir(root_path) if os.path.exists(root_path) else []

        for project_type, files in indicators.items():
            if any(f in files_in_root for f in files):
                # Refinamento para React
                if project_type == "javascript" and "package.json" in files_in_root:
                    try:
                        import json

                        with open(os.path.join(root_path, "package.json"), "r") as f:
                            package_data = json.load(f)
                            deps = {
                                **package_data.get("dependencies", {}),
                                **package_data.get("devDependencies", {}),
                            }
                            if "react" in deps:
                                return "react"
                    except:
                        pass

                return project_type

        return "unknown"

    def _get_session_duration(self) -> str:
        """Calculates current session duration"""
        duration = datetime.now() - self.session_metrics.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _load_preferences(self):
        """Loads user preferences"""
        # TODO: Implementar carregamento de arquivo de configuração
        self.user_preferences = {
            "auto_save_history": True,
            "show_timestamps": False,
            "compact_mode": False,
            "default_model": "llama3.2",
            # Web integration settings
            "web_integration_enabled": False,
            "web_request_timeout": 10,
            "max_links_per_request": 3,
        }

    def set_preference(self, key: str, value: Any):
        """Sets user preference"""
        self.user_preferences[key] = value
        # TODO: Salvar em arquivo de configuração

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Gets user preference"""
        return self.user_preferences.get(key, default)
