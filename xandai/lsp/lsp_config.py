"""
LSP Configuration Module

Defines Language Server Protocol configurations for various programming languages.
Supports automatic server detection and installation recommendations.
"""

import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LSPServerConfig:
    """Configuration for a Language Server"""

    name: str
    language: str
    command: str  # Command to start the server
    args: List[str]  # Command arguments
    file_extensions: List[str]  # Supported file extensions
    initialization_options: Dict = None  # Server-specific init options
    install_command: Optional[str] = None  # Installation command/instructions
    description: str = ""

    def is_installed(self) -> bool:
        """Check if the LSP server is installed and available"""
        # Check if command exists in PATH
        return shutil.which(self.command) is not None


# LSP Server Configurations for Major Languages
LSP_SERVERS: Dict[str, LSPServerConfig] = {
    "python": LSPServerConfig(
        name="Pyright",
        language="python",
        command="pyright-langserver",
        args=["--stdio"],
        file_extensions=[".py", ".pyi"],
        initialization_options={},
        install_command="pip install pyright",
        description="Microsoft's static type checker and language server for Python",
    ),
    "python_jedi": LSPServerConfig(
        name="Jedi Language Server",
        language="python",
        command="jedi-language-server",
        args=[],
        file_extensions=[".py", ".pyi"],
        initialization_options={},
        install_command="pip install jedi-language-server",
        description="Python language server based on Jedi autocomplete",
    ),
    "javascript": LSPServerConfig(
        name="TypeScript Language Server",
        language="javascript",
        command="typescript-language-server",
        args=["--stdio"],
        file_extensions=[".js", ".jsx", ".ts", ".tsx"],
        initialization_options={},
        install_command="npm install -g typescript-language-server typescript",
        description="Language server for JavaScript and TypeScript",
    ),
    "typescript": LSPServerConfig(
        name="TypeScript Language Server",
        language="typescript",
        command="typescript-language-server",
        args=["--stdio"],
        file_extensions=[".ts", ".tsx"],
        initialization_options={},
        install_command="npm install -g typescript-language-server typescript",
        description="Official TypeScript language server",
    ),
    "rust": LSPServerConfig(
        name="rust-analyzer",
        language="rust",
        command="rust-analyzer",
        args=[],
        file_extensions=[".rs"],
        initialization_options={},
        install_command="rustup component add rust-analyzer",
        description="Official Rust language server",
    ),
    "go": LSPServerConfig(
        name="gopls",
        language="go",
        command="gopls",
        args=["serve"],
        file_extensions=[".go"],
        initialization_options={},
        install_command="go install golang.org/x/tools/gopls@latest",
        description="Official Go language server",
    ),
    "java": LSPServerConfig(
        name="Eclipse JDT Language Server",
        language="java",
        command="jdtls",
        args=[],
        file_extensions=[".java"],
        initialization_options={},
        install_command="Download from https://download.eclipse.org/jdtls/snapshots/",
        description="Java language server from Eclipse",
    ),
    "cpp": LSPServerConfig(
        name="clangd",
        language="cpp",
        command="clangd",
        args=["--background-index"],
        file_extensions=[".cpp", ".cc", ".cxx", ".h", ".hpp"],
        initialization_options={},
        install_command="Install LLVM/Clang package for your system",
        description="Language server for C/C++",
    ),
    "c": LSPServerConfig(
        name="clangd",
        language="c",
        command="clangd",
        args=["--background-index"],
        file_extensions=[".c", ".h"],
        initialization_options={},
        install_command="Install LLVM/Clang package for your system",
        description="Language server for C",
    ),
    "ruby": LSPServerConfig(
        name="Solargraph",
        language="ruby",
        command="solargraph",
        args=["stdio"],
        file_extensions=[".rb"],
        initialization_options={},
        install_command="gem install solargraph",
        description="Ruby language server",
    ),
    "php": LSPServerConfig(
        name="Intelephense",
        language="php",
        command="intelephense",
        args=["--stdio"],
        file_extensions=[".php"],
        initialization_options={},
        install_command="npm install -g intelephense",
        description="PHP language server",
    ),
    "html": LSPServerConfig(
        name="HTML Language Server",
        language="html",
        command="vscode-html-language-server",
        args=["--stdio"],
        file_extensions=[".html", ".htm"],
        initialization_options={},
        install_command="npm install -g vscode-langservers-extracted",
        description="HTML language server",
    ),
    "css": LSPServerConfig(
        name="CSS Language Server",
        language="css",
        command="vscode-css-language-server",
        args=["--stdio"],
        file_extensions=[".css", ".scss", ".sass", ".less"],
        initialization_options={},
        install_command="npm install -g vscode-langservers-extracted",
        description="CSS language server",
    ),
    "json": LSPServerConfig(
        name="JSON Language Server",
        language="json",
        command="vscode-json-language-server",
        args=["--stdio"],
        file_extensions=[".json"],
        initialization_options={},
        install_command="npm install -g vscode-langservers-extracted",
        description="JSON language server",
    ),
}


def get_server_for_language(language: str) -> Optional[LSPServerConfig]:
    """Get LSP server configuration for a specific language"""
    return LSP_SERVERS.get(language.lower())


def get_server_for_file(file_path: str) -> Optional[LSPServerConfig]:
    """Get LSP server configuration for a file based on extension"""
    file_path = file_path.lower()

    for server in LSP_SERVERS.values():
        for ext in server.file_extensions:
            if file_path.endswith(ext):
                return server

    return None


def get_available_servers() -> List[LSPServerConfig]:
    """Get list of all installed LSP servers"""
    return [server for server in LSP_SERVERS.values() if server.is_installed()]


def get_installation_instructions(language: str) -> Optional[str]:
    """Get installation instructions for a language's LSP server"""
    server = get_server_for_language(language)
    if server:
        return f"{server.name}: {server.install_command}"
    return None
