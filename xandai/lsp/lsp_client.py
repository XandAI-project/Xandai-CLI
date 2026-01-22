"""
LSP Client Module

Handles communication with Language Server Protocol servers.
Provides a simple interface for common LSP operations.
"""

import asyncio
import json
import logging
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from xandai.lsp.lsp_config import LSPServerConfig


class LSPClient:
    """
    Language Server Protocol Client

    Manages communication with an LSP server process.
    Supports common operations like initialization, diagnostics, and completion.
    """

    def __init__(self, config: LSPServerConfig, root_path: str, verbose: bool = False):
        """
        Initialize LSP client

        Args:
            config: LSP server configuration
            root_path: Project root path
            verbose: Enable verbose logging
        """
        self.config = config
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.process: Optional[subprocess.Popen] = None
        self.message_id = 0
        self.is_initialized = False
        self._lock = threading.Lock()

        # Setup logging
        self.logger = logging.getLogger(f"LSPClient-{config.name}")
        if verbose:
            self.logger.setLevel(logging.DEBUG)

    def start(self) -> bool:
        """
        Start the LSP server process

        Returns:
            True if server started successfully
        """
        try:
            if not self.config.is_installed():
                if self.verbose:
                    print(f"⚠️  LSP server '{self.config.name}' is not installed")
                    print(f"   Install with: {self.config.install_command}")
                return False

            # Start server process
            cmd = [self.config.command] + self.config.args

            if self.verbose:
                print(f"🚀 Starting LSP server: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.root_path),
                bufsize=0,
            )

            # Initialize the server
            return self._initialize()

        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to start LSP server: {e}")
            self.logger.error(f"Failed to start server: {e}")
            return False

    def stop(self):
        """Stop the LSP server process"""
        if self.process:
            try:
                # Send shutdown request
                self._send_request("shutdown", {})

                # Send exit notification
                self._send_notification("exit", {})

                # Wait for process to terminate
                self.process.wait(timeout=5)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error during shutdown: {e}")
            finally:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(timeout=2)

                self.process = None
                self.is_initialized = False

    def get_diagnostics(self, file_path: str, content: str = None) -> List[Dict]:
        """
        Get diagnostics (errors, warnings) for a file

        Args:
            file_path: Path to the file
            content: File content (reads from disk if not provided)

        Returns:
            List of diagnostic messages
        """
        if not self.is_initialized:
            return []

        try:
            # Notify server about file open
            file_uri = self._path_to_uri(file_path)

            if content is None:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            # Send didOpen notification
            self._send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": file_uri,
                        "languageId": self.config.language,
                        "version": 1,
                        "text": content,
                    }
                },
            )

            # Wait for diagnostics (simplified - in production use async)
            # For now, return empty list (diagnostics are sent via notifications)
            return []

        except Exception as e:
            if self.verbose:
                print(f"❌ Error getting diagnostics: {e}")
            return []

    def get_completions(
        self, file_path: str, line: int, character: int, content: str = None
    ) -> List[Dict]:
        """
        Get code completions at a specific position

        Args:
            file_path: Path to the file
            line: Line number (0-indexed)
            character: Character position (0-indexed)
            content: File content

        Returns:
            List of completion items
        """
        if not self.is_initialized:
            return []

        try:
            file_uri = self._path_to_uri(file_path)

            # Open document if content provided
            if content:
                self._send_notification(
                    "textDocument/didOpen",
                    {
                        "textDocument": {
                            "uri": file_uri,
                            "languageId": self.config.language,
                            "version": 1,
                            "text": content,
                        }
                    },
                )

            # Request completions
            response = self._send_request(
                "textDocument/completion",
                {
                    "textDocument": {"uri": file_uri},
                    "position": {"line": line, "character": character},
                },
            )

            if response and "result" in response:
                items = response["result"]
                if isinstance(items, dict):
                    return items.get("items", [])
                return items if isinstance(items, list) else []

            return []

        except Exception as e:
            if self.verbose:
                print(f"❌ Error getting completions: {e}")
            return []

    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[str]:
        """
        Get hover information at a specific position

        Args:
            file_path: Path to the file
            line: Line number (0-indexed)
            character: Character position (0-indexed)

        Returns:
            Hover information text
        """
        if not self.is_initialized:
            return None

        try:
            file_uri = self._path_to_uri(file_path)

            response = self._send_request(
                "textDocument/hover",
                {
                    "textDocument": {"uri": file_uri},
                    "position": {"line": line, "character": character},
                },
            )

            if response and "result" in response:
                hover = response["result"]
                if hover and "contents" in hover:
                    return str(hover["contents"])

            return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error getting hover info: {e}")
            return None

    def _initialize(self) -> bool:
        """Initialize the LSP server"""
        try:
            init_params = {
                "processId": None,
                "rootPath": str(self.root_path),
                "rootUri": self._path_to_uri(str(self.root_path)),
                "capabilities": {
                    "textDocument": {
                        "completion": {"completionItem": {"snippetSupport": True}},
                        "hover": {"contentFormat": ["plaintext", "markdown"]},
                        "synchronization": {
                            "didSave": True,
                            "didOpen": True,
                            "didClose": True,
                            "didChange": True,
                        },
                    },
                    "workspace": {"workspaceFolders": True},
                },
                "initializationOptions": self.config.initialization_options or {},
            }

            response = self._send_request("initialize", init_params, timeout=10)

            if response and "result" in response:
                # Send initialized notification
                self._send_notification("initialized", {})
                self.is_initialized = True

                if self.verbose:
                    print(f"✅ LSP server '{self.config.name}' initialized")

                return True

            return False

        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize LSP server: {e}")
            return False

    def _send_request(self, method: str, params: Dict, timeout: int = 5) -> Optional[Dict]:
        """Send a JSON-RPC request and wait for response"""
        if not self.process or not self.process.stdin:
            return None

        with self._lock:
            self.message_id += 1
            msg_id = self.message_id

        message = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}

        try:
            self._write_message(message)

            # In a production system, you'd properly handle async responses
            # For simplicity, we'll use a basic synchronous approach
            response = self._read_message(timeout)
            return response

        except Exception as e:
            if self.verbose:
                self.logger.error(f"Request failed: {e}")
            return None

    def _send_notification(self, method: str, params: Dict):
        """Send a JSON-RPC notification (no response expected)"""
        if not self.process or not self.process.stdin:
            return

        message = {"jsonrpc": "2.0", "method": method, "params": params}

        try:
            self._write_message(message)
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Notification failed: {e}")

    def _write_message(self, message: Dict):
        """Write a JSON-RPC message to the server"""
        if not self.process or not self.process.stdin:
            return

        content = json.dumps(message)
        content_bytes = content.encode("utf-8")

        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"

        self.process.stdin.write(header.encode("utf-8"))
        self.process.stdin.write(content_bytes)
        self.process.stdin.flush()

    def _read_message(self, timeout: int = 5) -> Optional[Dict]:
        """Read a JSON-RPC message from the server"""
        if not self.process or not self.process.stdout:
            return None

        try:
            # Read headers
            content_length = 0
            while True:
                line = self.process.stdout.readline().decode("utf-8")
                if line == "\r\n":
                    break

                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())

            # Read content
            if content_length > 0:
                content = self.process.stdout.read(content_length).decode("utf-8")
                return json.loads(content)

        except Exception as e:
            if self.verbose:
                self.logger.error(f"Read failed: {e}")

        return None

    def _path_to_uri(self, path: str) -> str:
        """Convert file path to URI"""
        path_obj = Path(path).absolute()
        # Simple URI conversion (platform-specific handling needed for production)
        path_str = str(path_obj).replace("\\", "/")
        return f"file://{path_str}"

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()
