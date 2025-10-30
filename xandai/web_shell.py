#!/usr/bin/env python3
"""
XandAI Web Shell Server
Provides a web interface for real-time interaction with XandAI CLI
"""

import threading
from typing import Optional

from flask import Flask, render_template_string, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit


class TeeConsole:
    """
    A console wrapper that writes to two consoles simultaneously.
    Similar to Unix 'tee' command - output goes to both destinations.
    """

    def __init__(self, console1, console2):
        """
        Initialize TeeConsole with two console destinations.

        Args:
            console1: First console (e.g., original terminal console)
            console2: Second console (e.g., web shell buffer console)
        """
        self.console1 = console1
        self.console2 = console2

    def print(self, *args, **kwargs):
        """Print to both consoles"""
        self.console1.print(*args, **kwargs)
        self.console2.print(*args, **kwargs)

    def __getattr__(self, name):
        """
        Delegate any other method calls to the first console.
        This allows TeeConsole to work as a drop-in replacement.
        """
        return getattr(self.console1, name)


class WebShellServer:
    """Web Shell Server for XandAI CLI"""

    def __init__(self, cli_instance, verbose: bool = False):
        """
        Initialize Web Shell Server

        Args:
            cli_instance: Instance of XandAICLI to interact with
            verbose: Whether to show Flask/SocketIO debug logs
        """
        self.cli_instance = cli_instance
        self.verbose = verbose

        # Suppress Flask logs BEFORE creating the app
        if not verbose:
            import logging
            import warnings

            # Suppress warnings
            warnings.filterwarnings("ignore")

            # Disable werkzeug logging (but don't fully disable)
            logging.getLogger("werkzeug").setLevel(logging.ERROR)
            # Don't set WERKZEUG_RUN_MAIN as it causes issues

        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "xandai-web-shell-secret"

        # Reduce Flask app logging (but don't fully disable)
        if not verbose:
            self.app.logger.setLevel(logging.ERROR)
            # Don't set disabled=True

        CORS(self.app)
        self.socketio = SocketIO(
            self.app, cors_allowed_origins="*", logger=verbose, engineio_logger=verbose
        )
        self.server_thread: Optional[threading.Thread] = None
        self.active_process = None  # Track running background process
        self.server_error = None  # Track server startup errors
        self._setup_routes()
        self._setup_socketio()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            """Serve the web shell interface"""
            return render_template_string(self._get_html_template())

        @self.app.route("/icon.png")
        def icon():
            """Serve the XandAI icon"""
            import os
            from pathlib import Path

            from flask import send_file

            # Get the icon path relative to the project root
            icon_path = Path(__file__).parent.parent / "images" / "icon.png"

            if icon_path.exists():
                return send_file(str(icon_path), mimetype="image/png")
            else:
                # Return 404 if icon not found
                return "Icon not found", 404

    def _setup_socketio(self):
        """Setup SocketIO event handlers"""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection"""
            emit("system_message", {"type": "info", "message": "Connected to XandAI Web Shell"})
            emit("prompt", {"text": "xandai> "})

        @self.socketio.on("execute_command")
        def handle_command(data):
            """Handle command execution from web interface"""
            command = data.get("command", "").strip()

            if not command:
                emit("prompt", {"text": "xandai> "})
                return

            # Kill any active background process before running new command
            if self.active_process and self.active_process.poll() is None:
                try:
                    emit(
                        "system_message",
                        {"type": "warning", "message": "⚠️ Stopping previous command..."},
                    )
                    self.active_process.terminate()
                    try:
                        self.active_process.wait(timeout=2)
                    except:
                        self.active_process.kill()
                    self.active_process = None
                except Exception as e:
                    emit(
                        "system_message",
                        {"type": "error", "message": f"Error stopping previous command: {e}"},
                    )

            # Check if it's a clear command before echoing
            is_clear_command = command.lower() in ["clear", "cls", "/clear", "/cls"]

            # Echo the command back
            emit("command_echo", {"command": command})

            # If it's a clear command, send clear event and return
            if is_clear_command:
                emit("clear_terminal", {})
                emit("command_response", {"response": "✨ Terminal cleared", "success": True})
                emit("prompt", {"text": "xandai> "})
                return

            try:
                # Process the command through CLI
                response = self._execute_cli_command(command)

                # Send response back to client
                emit("command_response", {"response": response, "success": True})

            except Exception as e:
                emit("command_response", {"response": f"Error: {str(e)}", "success": False})

            # Send new prompt
            emit("prompt", {"text": "xandai> "})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection"""
            pass

    def _execute_cli_command(self, command: str) -> str:
        """
        Execute a command through the CLI instance

        Args:
            command: Command to execute

        Returns:
            Response text
        """
        # Check for special web-only commands
        if command.startswith("/"):
            cmd = command.split(maxsplit=1)[0].lower()

            # Handle web-specific overrides
            if cmd == "/help":
                return self._get_help_text()
            elif cmd == "/status":
                return self._get_status_text()
            elif cmd == "/clear":
                self.cli_instance.history_manager.clear_conversation()
                return "✅ Conversation history cleared"
            elif cmd in ["/exit", "/quit", "/bye"]:
                return "💡 To exit, close the browser tab"

        # Process command through the CLI's normal input processor
        try:
            from io import StringIO

            from rich.console import Console

            # Create a string buffer to capture Rich output
            output_buffer = StringIO()

            # Create a temporary console that writes to our buffer
            temp_console = Console(file=output_buffer, force_terminal=False, width=100)

            # Store original settings
            original_console = self.cli_instance.console
            original_interactive = self.cli_instance.interactive_mode
            original_verbose = self.cli_instance.verbose
            original_auto_approve = getattr(self.cli_instance, "auto_approve_operations", False)

            # Show the command in the normal shell (terminal)
            original_console.print(f"[dim cyan][web-shell][/dim cyan] {command}")

            # Create a "Tee" console that writes to both places
            tee_console = TeeConsole(original_console, temp_console)

            # Temporarily replace console and configure for web shell
            self.cli_instance.console = tee_console
            self.cli_instance.interactive_mode = False  # Disable prompts
            self.cli_instance.verbose = False  # Disable debug logs
            self.cli_instance.auto_approve_operations = True  # Auto-approve file ops in web shell

            # Add a marker that we're in web shell context
            self.cli_instance._in_web_shell = True
            self.cli_instance._web_shell_instance = self  # Pass reference to web shell

            # Temporarily suppress socketio logging
            import logging

            socketio_logger = logging.getLogger("socketio")
            engineio_logger = logging.getLogger("engineio")
            original_socketio_level = socketio_logger.level
            original_engineio_level = engineio_logger.level
            socketio_logger.setLevel(logging.ERROR)
            engineio_logger.setLevel(logging.ERROR)

            try:
                # Process the command
                self.cli_instance._process_input(command)

                # Get the captured output
                result = output_buffer.getvalue()

                # If we captured output, return it; otherwise return confirmation
                if result.strip():
                    return result
                else:
                    # If no output captured, might be because output went elsewhere
                    return "✅ Command executed successfully (output may appear in terminal)"

            finally:
                # Always restore the original settings
                self.cli_instance.console = original_console
                self.cli_instance.interactive_mode = original_interactive
                self.cli_instance.verbose = original_verbose
                self.cli_instance.auto_approve_operations = original_auto_approve
                self.cli_instance._in_web_shell = False
                self.cli_instance._web_shell_instance = None  # Clear reference

                # Restore socketio logging
                socketio_logger.setLevel(original_socketio_level)
                engineio_logger.setLevel(original_engineio_level)

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            return f"❌ Error processing command: {str(e)}\n\n{error_detail}"

    def _get_help_text(self) -> str:
        """Get help text"""
        return """XandAI Web Shell Commands:

Basic Commands:
  /help              - Show this help message
  /status            - Show system status
  /clear, clear, cls - Clear terminal screen and conversation history
  /exit, /quit       - Close browser tab to exit

AI Commands:
  /agent <task>      - Execute complex multi-step tasks
  /review            - Run AI code review

Terminal Commands:
  All standard terminal commands work here!
  Examples: dir, ls, cd, mkdir, cat, python, npm, etc.

Chat Mode:
  Simply type your question or instruction without commands

Examples:
  dir                                   (list files)
  python myscript.py                    (run Python)
  How do I optimize Python code?        (ask AI)
  /agent refactor this code into modules
  /review
"""

    def _get_status_text(self) -> str:
        """Get status text"""
        provider_info = self.cli_instance.llm_provider.get_info()
        return f"""System Status:

Provider: {provider_info.get('name', 'Unknown')}
Model: {provider_info.get('model', 'Unknown')}
Status: Active

Web Shell: Running
"""

    def _get_html_template(self) -> str:
        """Get the HTML template for web shell"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XandAI Web Shell</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        #header {
            background: #2d2d30;
            padding: 15px 20px;
            border-bottom: 1px solid #3e3e42;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        #header h1 {
            font-size: 18px;
            color: #4ec9b0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        #header h1 img {
            width: 28px;
            height: 28px;
            object-fit: contain;
        }

        #status {
            font-size: 12px;
            color: #858585;
        }

        #terminal {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            font-size: 14px;
            line-height: 1.6;
        }

        .output-line {
            margin-bottom: 8px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .command {
            color: #4ec9b0;
        }

        .response {
            color: #d4d4d4;
            margin-left: 0;
        }

        .error {
            color: #f48771;
        }

        .system {
            color: #858585;
            font-style: italic;
        }

        .prompt {
            color: #569cd6;
            display: inline;
        }

        #input-container {
            background: #2d2d30;
            padding: 15px 20px;
            border-top: 1px solid #3e3e42;
            display: flex;
            align-items: center;
        }

        #prompt-text {
            color: #569cd6;
            margin-right: 8px;
        }

        #command-input {
            flex: 1;
            background: #3c3c3c;
            border: 1px solid #3e3e42;
            color: #d4d4d4;
            padding: 8px 12px;
            font-family: inherit;
            font-size: 14px;
            outline: none;
        }

        #command-input:focus {
            border-color: #569cd6;
        }

        #terminal::-webkit-scrollbar {
            width: 10px;
        }

        #terminal::-webkit-scrollbar-track {
            background: #1e1e1e;
        }

        #terminal::-webkit-scrollbar-thumb {
            background: #3e3e42;
            border-radius: 5px;
        }

        #terminal::-webkit-scrollbar-thumb:hover {
            background: #4e4e52;
        }

        .typing-indicator {
            color: #858585;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 49% { opacity: 1; }
            50%, 100% { opacity: 0; }
        }
    </style>
</head>
<body>
    <div id="header">
        <h1><img src="/icon.png" alt="XandAI" onerror="this.style.display='none'"> XandAI Web Shell</h1>
        <div id="status">Connected</div>
    </div>

    <div id="terminal"></div>

    <div id="input-container">
        <span id="prompt-text">xandai&gt;</span>
        <input type="text" id="command-input" autofocus autocomplete="off" placeholder="Type your command or question...">
    </div>

    <script>
        const socket = io();
        const terminal = document.getElementById('terminal');
        const commandInput = document.getElementById('command-input');
        const statusElement = document.getElementById('status');

        // Auto-scroll terminal
        function scrollToBottom() {
            terminal.scrollTop = terminal.scrollHeight;
        }

        // Add output to terminal
        function addOutput(text, className = 'response') {
            const line = document.createElement('div');
            line.className = `output-line ${className}`;
            line.textContent = text;
            terminal.appendChild(line);
            scrollToBottom();
        }

        // Clear terminal
        function clearTerminal() {
            terminal.innerHTML = '';
        }

        // Socket.IO event handlers
        socket.on('connect', () => {
            statusElement.textContent = 'Connected';
            statusElement.style.color = '#4ec9b0';
        });

        socket.on('disconnect', () => {
            statusElement.textContent = 'Disconnected';
            statusElement.style.color = '#f48771';
            addOutput('Disconnected from server', 'error');
        });

        socket.on('system_message', (data) => {
            addOutput(data.message, 'system');
        });

        socket.on('command_echo', (data) => {
            addOutput('xandai> ' + data.command, 'command');
        });

        socket.on('command_response', (data) => {
            const className = data.success ? 'response' : 'error';
            addOutput(data.response, className);
        });

        socket.on('clear_terminal', () => {
            clearTerminal();
        });

        socket.on('prompt', (data) => {
            // Prompt is already shown in input container
        });

        // Command input handler
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const command = commandInput.value.trim();
                if (command) {
                    commandInput.disabled = true;
                    socket.emit('execute_command', { command: command });
                    commandInput.value = '';
                    setTimeout(() => {
                        commandInput.disabled = false;
                        commandInput.focus();
                    }, 100);
                }
            }
        });

        // Focus input on page load
        window.onload = () => {
            commandInput.focus();
        };

        // Add welcome message
        addOutput('Welcome to XandAI Web Shell!', 'system');
        addOutput('Type /help for available commands', 'system');
        addOutput('', 'system');
    </script>
</body>
</html>
"""

    def start(self, host: str = "0.0.0.0", port: int = 4800):
        """
        Start the web shell server

        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        import sys

        self.server_error = None  # Store any startup errors

        def run_server():
            try:
                if self.verbose:
                    print(f"[DEBUG] Starting SocketIO server on {host}:{port}", file=sys.stderr)

                # Run the server (logging already configured in __init__)
                self.socketio.run(
                    self.app,
                    host=host,
                    port=port,
                    debug=False,
                    use_reloader=False,
                    allow_unsafe_werkzeug=True,
                )
            except Exception as e:
                # Store error for reporting
                self.server_error = str(e)
                # Always show critical errors
                import traceback

                print(f"[ERROR] Web shell server failed: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

        self.server_thread = threading.Thread(target=run_server, daemon=True, name="WebShellServer")
        self.server_thread.start()

        return f"Web Shell started at http://{host}:{port}"

    def stop(self):
        """Stop the web shell server"""
        if self.server_thread and self.server_thread.is_alive():
            # Note: Flask-SocketIO doesn't have a clean shutdown method
            # The daemon thread will stop when main program exits
            return "Web Shell server will stop when application exits"
        return "Web Shell server is not running"

    def is_running(self) -> bool:
        """Check if the web shell server is running"""
        return self.server_thread is not None and self.server_thread.is_alive()
