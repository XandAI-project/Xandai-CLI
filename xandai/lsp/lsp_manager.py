"""
LSP Manager Module

Coordinates multiple Language Server Protocol clients.
Manages lifecycle, routing requests to appropriate servers.
"""

import atexit
from pathlib import Path
from typing import Dict, List, Optional

from xandai.lsp.language_detector import LanguageDetector
from xandai.lsp.lsp_client import LSPClient
from xandai.lsp.lsp_config import LSPServerConfig, get_server_for_file, get_server_for_language


class LSPManager:
    """
    LSP Manager

    Central coordinator for all LSP servers in the project.
    Handles automatic detection, initialization, and routing.
    """

    def __init__(self, root_path: str = None, verbose: bool = False):
        """
        Initialize LSP Manager

        Args:
            root_path: Project root path (defaults to current directory)
            verbose: Enable verbose logging
        """
        self.root_path = root_path or str(Path.cwd())
        self.verbose = verbose

        # Active LSP clients by language
        self.clients: Dict[str, LSPClient] = {}

        # Language detector
        self.detector = LanguageDetector(self.root_path)

        # Track initialization status
        self.is_initialized = False
        self.auto_start_enabled = True

        # Register cleanup on exit
        atexit.register(self.shutdown_all)

    def initialize(self, auto_start: bool = True, languages: List[str] = None) -> Dict[str, bool]:
        """
        Initialize LSP servers

        Args:
            auto_start: Automatically start servers for detected languages
            languages: Specific languages to initialize (None = auto-detect)

        Returns:
            Dictionary mapping language to initialization success status
        """
        results = {}

        # Detect languages if not specified
        if languages is None and auto_start:
            detected = self.detector.detect_languages(min_files=2)
            languages = list(detected.keys())

            if self.verbose:
                print(f"🔍 Detected languages: {', '.join(languages)}")

        if not languages:
            if self.verbose:
                print("ℹ️  No languages to initialize")
            return results

        # Initialize servers for each language
        for language in languages:
            success = self._start_server_for_language(language)
            results[language] = success

        self.is_initialized = True
        return results

    def start_server(self, language: str) -> bool:
        """
        Start LSP server for a specific language

        Args:
            language: Language name (e.g., 'python', 'javascript')

        Returns:
            True if server started successfully
        """
        return self._start_server_for_language(language)

    def stop_server(self, language: str):
        """Stop LSP server for a specific language"""
        if language in self.clients:
            self.clients[language].stop()
            del self.clients[language]

            if self.verbose:
                print(f"🛑 Stopped LSP server for {language}")

    def shutdown_all(self):
        """Shutdown all active LSP servers"""
        if self.verbose and self.clients:
            print("🛑 Shutting down all LSP servers...")

        for language in list(self.clients.keys()):
            self.stop_server(language)

    def get_diagnostics(self, file_path: str, content: str = None) -> List[Dict]:
        """
        Get diagnostics for a file

        Args:
            file_path: Path to the file
            content: File content (optional)

        Returns:
            List of diagnostic messages
        """
        client = self._get_client_for_file(file_path)

        if client:
            return client.get_diagnostics(file_path, content)

        return []

    def get_completions(
        self, file_path: str, line: int, character: int, content: str = None
    ) -> List[Dict]:
        """
        Get code completions

        Args:
            file_path: Path to the file
            line: Line number (0-indexed)
            character: Character position (0-indexed)
            content: File content (optional)

        Returns:
            List of completion items
        """
        client = self._get_client_for_file(file_path)

        if client:
            return client.get_completions(file_path, line, character, content)

        return []

    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[str]:
        """
        Get hover information

        Args:
            file_path: Path to the file
            line: Line number (0-indexed)
            character: Character position (0-indexed)

        Returns:
            Hover information text
        """
        client = self._get_client_for_file(file_path)

        if client:
            return client.get_hover_info(file_path, line, character)

        return None

    def get_active_languages(self) -> List[str]:
        """Get list of languages with active LSP servers"""
        return list(self.clients.keys())

    def get_detected_languages(self) -> Dict[str, int]:
        """Get all detected languages in the project"""
        return self.detector.detect_languages()

    def get_project_statistics(self) -> Dict:
        """Get detailed project language statistics"""
        return self.detector.get_statistics()

    def get_lsp_status(self) -> Dict:
        """
        Get status of all LSP servers

        Returns:
            Dictionary with LSP status information
        """
        detected = self.detector.detect_languages()

        status = {
            "initialized": self.is_initialized,
            "root_path": self.root_path,
            "active_servers": {},
            "available_servers": {},
            "project_stats": self.detector.get_statistics(),
        }

        # Active servers
        for language, client in self.clients.items():
            status["active_servers"][language] = {
                "server_name": client.config.name,
                "is_running": client.is_initialized,
                "file_count": detected.get(language, 0),
            }

        # Available but not started servers
        for language in detected.keys():
            if language not in self.clients:
                server = get_server_for_language(language)
                if server:
                    status["available_servers"][language] = {
                        "server_name": server.name,
                        "is_installed": server.is_installed(),
                        "install_command": server.install_command,
                        "file_count": detected.get(language, 0),
                    }

        return status

    def is_server_active(self, language: str) -> bool:
        """Check if LSP server is active for a language"""
        return language in self.clients and self.clients[language].is_initialized

    def _start_server_for_language(self, language: str) -> bool:
        """Internal method to start a server for a language"""
        # Check if already running
        if language in self.clients:
            if self.verbose:
                print(f"ℹ️  LSP server for {language} already running")
            return True

        # Get server configuration
        server_config = get_server_for_language(language)

        if not server_config:
            if self.verbose:
                print(f"⚠️  No LSP server configuration for {language}")
            return False

        # Check if server is installed
        if not server_config.is_installed():
            if self.verbose:
                print(f"⚠️  LSP server for {language} not installed")
                print(f"   Install with: {server_config.install_command}")
            return False

        # Create and start client
        client = LSPClient(server_config, self.root_path, verbose=self.verbose)

        if client.start():
            self.clients[language] = client

            if self.verbose:
                print(f"✅ Started LSP server for {language}: {server_config.name}")

            return True
        else:
            if self.verbose:
                print(f"❌ Failed to start LSP server for {language}")
            return False

    def _get_client_for_file(self, file_path: str) -> Optional[LSPClient]:
        """Get appropriate LSP client for a file"""
        # Determine language from file extension
        language = self.detector.get_file_language(file_path)

        if language == "unknown":
            return None

        # Return existing client or try to start one
        if language in self.clients:
            return self.clients[language]

        # Auto-start if enabled
        if self.auto_start_enabled:
            if self._start_server_for_language(language):
                return self.clients.get(language)

        return None

    def refresh_detection(self):
        """Refresh language detection (clears cache)"""
        self.detector.clear_cache()
        self.detector.detect_languages()

    def get_file_context(self, file_path: str) -> Dict:
        """
        Get comprehensive context for a file using LSP

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file context information
        """
        language = self.detector.get_file_language(file_path)

        context = {
            "file_path": file_path,
            "language": language,
            "lsp_available": False,
            "diagnostics": [],
            "server_info": None,
        }

        client = self._get_client_for_file(file_path)

        if client and client.is_initialized:
            context["lsp_available"] = True
            context["server_info"] = {
                "name": client.config.name,
                "description": client.config.description,
            }

            # Get diagnostics
            try:
                diagnostics = client.get_diagnostics(file_path)
                context["diagnostics"] = diagnostics
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error getting diagnostics: {e}")

        return context
