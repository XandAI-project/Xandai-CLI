"""
Module for automatic shell command execution
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from rich.console import Console

console = Console()


class ShellExecutor:
    """Executa comandos shell automaticamente"""
    
    # Comandos shell comuns que devem ser executados automaticamente
    SHELL_COMMANDS = {
        'ls', 'dir', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'cat', 'type',
        'echo', 'touch', 'grep', 'find', 'ps', 'kill', 'chmod', 'chown', 'which',
        'whereis', 'date', 'time', 'whoami', 'hostname', 'uname', 'df', 'du',
        'free', 'top', 'htop', 'clear', 'cls', 'exit', 'logout', 'history',
        'tree', 'nano', 'vim', 'vi', 'less', 'more', 'head', 'tail', 'wc',
        'sort', 'uniq', 'cut', 'awk', 'sed', 'tar', 'zip', 'unzip', 'gzip',
        'gunzip', 'wget', 'curl', 'ping', 'traceroute', 'nslookup', 'dig',
        'ifconfig', 'ipconfig', 'netstat', 'ss', 'route', 'arp', 'git',
        'npm', 'pip', 'python', 'python3', 'node', 'java', 'javac', 'gcc',
        'g++', 'make', 'cmake', 'cargo', 'rustc', 'go', 'docker', 'kubectl'
    }
    
    def __init__(self, initial_dir: Path = None):
        """Initializes the shell executor
        
        Args:
            initial_dir: Initial directory (default: user's current directory)
        """
        # Detecta sistema operacional
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.is_mac = self.system == 'Darwin'
        self.is_linux = self.system == 'Linux'
        
        # Define OS-specific commands
        self.os_commands = self._get_os_specific_commands()
        
        self.current_dir = initial_dir or Path.cwd()
        # Ensure we're in the correct directory
        os.chdir(str(self.current_dir))
        
    def is_shell_command(self, text: str) -> bool:
        """
        Verifica se o texto parece ser um comando shell
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se parece ser um comando shell
        """
        # Remove extra spaces
        text = text.strip()
        
        # Check if it starts with a known command
        first_word = text.split()[0] if text else ""
        
        # Check basic commands
        if first_word in self.SHELL_COMMANDS:
            return True
            
        # Verifica comandos com caminho
        if '/' in first_word or '\\' in first_word:
            return True
            
        # Verifica redirecionamentos e pipes
        if any(op in text for op in ['|', '>', '<', '>>', '2>', '&>', '&&', '||']):
            return True
            
        # Verifica comandos do Windows
        if self.is_windows and first_word.lower() in ['dir', 'cls', 'type', 'copy', 'move', 'del']:
            return True
            
        # Check if it looks like directory navigation
        if text.startswith('cd ') or text == 'cd' or text.startswith('../') or text.startswith('./'):
            return True
            
        return False
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """
        Executes a shell command
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple (success, output/error)
        """
        try:
            # Converte comando para o OS apropriado
            command = self.convert_command(command)
            
            # Trata comando cd especialmente
            if command.strip().startswith('cd '):
                path = command.strip()[3:].strip()
                return self._change_directory(path)
            elif command.strip() == 'cd':
                return self._change_directory(str(Path.home()))
            
            # Executa outros comandos
            if self.is_windows:
                # No Windows, usa cmd.exe
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_dir),
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                # No Unix, usa bash
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_dir),
                    executable='/bin/bash'
                )
            
            if result.returncode == 0:
                output = result.stdout
                if result.stderr:
                    output += f"\n[yellow]Avisos:[/yellow]\n{result.stderr}"
                return True, output
            else:
                error = result.stderr or result.stdout or "Comando falhou"
                return False, error
                
        except Exception as e:
            return False, f"Erro ao executar comando: {e}"
    
    def _change_directory(self, path: str) -> Tuple[bool, str]:
        """
        Changes current directory
        
        Args:
            path: Directory path
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Expande ~ para home
            if path.startswith('~'):
                path = str(Path.home()) + path[1:]
            
            # Resolve caminho relativo
            new_dir = (self.current_dir / path).resolve()
            
            if new_dir.exists() and new_dir.is_dir():
                self.current_dir = new_dir
                os.chdir(str(new_dir))
                return True, f"📁 Directory changed to: {new_dir}"
            else:
                return False, f"Directory not found: {path}"
                
        except Exception as e:
            return False, f"Error changing directory: {e}"
    
    def get_current_directory(self) -> str:
        """Returns current directory"""
        return str(self.current_dir)
    
    def _get_os_specific_commands(self) -> Dict[str, str]:
        """
        Returns mapping of generic commands to OS-specific commands
        
        Returns:
            Dictionary with appropriate commands for the OS
        """
        if self.is_windows:
            return {
                'ls': 'dir',
                'ls -la': 'dir',
                'ls -l': 'dir',
                'pwd': 'cd',
                'rm': 'del',
                'rm -rf': 'rmdir /s /q',
                'cp': 'copy',
                'mv': 'move',
                'cat': 'type',
                'touch': 'type nul >',
                'clear': 'cls',
                'grep': 'findstr',
                'which': 'where',
                'ps': 'tasklist',
                'kill': 'taskkill /PID',
                'mkdir -p': 'mkdir'
            }
        else:
            # Unix-like (Linux/Mac)
            return {
                'dir': 'ls -la',
                'cls': 'clear',
                'copy': 'cp',
                'move': 'mv',
                'del': 'rm',
                'type': 'cat',
                'findstr': 'grep',
                'where': 'which',
                'tasklist': 'ps aux',
                'taskkill': 'kill'
            }
    
    def convert_command(self, command: str) -> str:
        """
        Converte comando para o equivalente no OS atual
        
        Args:
            command: Comando original
            
        Returns:
            Comando convertido para o OS atual
        """
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return command
        
        # Check if base command needs conversion
        base_cmd = cmd_parts[0]
        
        # Verifica comandos compostos (como 'rm -rf')
        if len(cmd_parts) > 1:
            compound_cmd = f"{base_cmd} {cmd_parts[1]}"
            if compound_cmd in self.os_commands:
                # Substitui o comando composto
                new_cmd = self.os_commands[compound_cmd]
                remaining = ' '.join(cmd_parts[2:]) if len(cmd_parts) > 2 else ''
                return f"{new_cmd} {remaining}".strip()
        
        # Verifica comando simples
        if base_cmd in self.os_commands:
            new_cmd = self.os_commands[base_cmd]
            remaining = ' '.join(cmd_parts[1:]) if len(cmd_parts) > 1 else ''
            
            # Tratamento especial para touch no Windows
            if base_cmd == 'touch' and self.is_windows:
                return f"{new_cmd}{remaining}".strip()
            
            return f"{new_cmd} {remaining}".strip()
        
        return command
    
    def get_os_info(self) -> str:
        """
        Returns information about the operating system
        
        Returns:
            String with OS information
        """
        if self.is_windows:
            return f"Windows ({platform.version()})"
        elif self.is_mac:
            return f"macOS ({platform.mac_ver()[0]})"
        elif self.is_linux:
            try:
                import distro
                return f"Linux ({distro.name()} {distro.version()})"
            except:
                return f"Linux ({platform.version()})"
        else:
            return f"{self.system} ({platform.version()})"
