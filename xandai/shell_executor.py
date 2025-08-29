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
            
            # Clean path and prevent duplication
            path = path.strip().strip('"').strip("'")
            
            # Check if path is absolute to prevent duplication
            if Path(path).is_absolute():
                new_dir = Path(path).resolve()
            else:
                # Resolve caminho relativo
                new_dir = (self.current_dir / path).resolve()
            
            # Advanced path duplication prevention
            try:
                str_path = str(new_dir)
                path_parts = str_path.replace('\\', '/').split('/')
                
                # Remove empty parts and normalize
                path_parts = [part for part in path_parts if part and part != '.']
                
                # Advanced duplication detection
                cleaned_parts = self._remove_path_duplications(path_parts)
                
                if len(cleaned_parts) != len(path_parts):
                    # Reconstruct path with cleaned parts
                    if self.is_windows and len(cleaned_parts) > 0:
                        # Windows path reconstruction
                        if ':' not in cleaned_parts[0] and len(cleaned_parts[0]) == 1:
                            cleaned_parts[0] = cleaned_parts[0] + ':'
                        new_dir = Path('\\'.join(cleaned_parts))
                    else:
                        # Unix path reconstruction  
                        new_dir = Path('/'.join(cleaned_parts))
                        
                    console.print(f"[dim]🔧 Path cleaned: {str_path} → {new_dir}[/dim]")
            except Exception as e:
                console.print(f"[dim]⚠️ Path cleaning failed: {e}[/dim]")
                pass  # Use original path if cleaning fails
            
            if new_dir.exists() and new_dir.is_dir():
                self.current_dir = new_dir
                os.chdir(str(new_dir))
                return True, f"📁 Directory changed to: {new_dir}"
            else:
                return False, f"❌ Directory not found: {path}"
                
        except Exception as e:
            return False, f"❌ Error changing directory: {e}"
    
    def _remove_path_duplications(self, path_parts: List[str]) -> List[str]:
        """
        Advanced algorithm to remove path duplications
        
        Args:
            path_parts: List of path components
            
        Returns:
            Cleaned path components
        """
        if len(path_parts) <= 1:
            return path_parts
        
        cleaned = []
        i = 0
        
        while i < len(path_parts):
            current_part = path_parts[i]
            
            # Always add the first part (usually drive or root)
            if not cleaned:
                cleaned.append(current_part)
                i += 1
                continue
            
            # Look for duplication patterns
            found_duplication = False
            
            # Check for immediate consecutive duplicates
            if current_part == cleaned[-1]:
                # Skip consecutive duplicate
                i += 1
                found_duplication = True
                continue
            
            # Check for more complex patterns like 'examples/XandAI-CLI/examples'
            if len(cleaned) >= 2:
                # Look for patterns where we have A/B/A
                for j in range(len(cleaned) - 1, -1, -1):
                    if cleaned[j] == current_part:
                        # Found a duplication pattern
                        # Check if this creates a meaningful duplication
                        if self._is_meaningful_duplication(cleaned, j, current_part, path_parts[i:]):
                            # Skip this part and continue with the next
                            i += 1
                            found_duplication = True
                            break
                            
                if found_duplication:
                    continue
            
            # No duplication found, add the part
            cleaned.append(current_part)
            i += 1
        
        return cleaned
    
    def _is_meaningful_duplication(self, cleaned: List[str], found_index: int, 
                                  current_part: str, remaining_parts: List[str]) -> bool:
        """
        Determine if a duplication is meaningful and should be removed
        
        Args:
            cleaned: Current cleaned path parts
            found_index: Index where duplication was found
            current_part: The duplicated part
            remaining_parts: Remaining parts to process
            
        Returns:
            True if this is a meaningful duplication to remove
        """
        # If we find 'examples' again after 'examples/XandAI-CLI', it's likely a duplication
        if found_index < len(cleaned) - 1:
            between_parts = cleaned[found_index + 1:]
            # If there's exactly one part between the duplicates, it's likely a duplication
            if len(between_parts) == 1:
                return True
        
        # Check for project folder duplications (like 'XandAI-CLI/examples/XandAI-CLI')
        if current_part in cleaned and len(cleaned) >= 2:
            # Look for patterns where project name appears multiple times
            project_appearances = [i for i, part in enumerate(cleaned) if part == current_part]
            if len(project_appearances) >= 1:
                return True
        
        return False

    def get_current_directory(self) -> str:
        """Returns current directory with path deduplication applied"""
        current_path = str(self.current_dir)
        
        # Apply the same deduplication logic as directory changes
        try:
            path_parts = current_path.replace('\\', '/').split('/')
            path_parts = [part for part in path_parts if part and part != '.']
            cleaned_parts = self._remove_path_duplications(path_parts)
            
            if len(cleaned_parts) != len(path_parts):
                if self.is_windows and len(cleaned_parts) > 0:
                    if ':' not in cleaned_parts[0] and len(cleaned_parts[0]) == 1:
                        cleaned_parts[0] = cleaned_parts[0] + ':'
                    clean_path = '\\'.join(cleaned_parts)
                else:
                    clean_path = '/'.join(cleaned_parts)
                
                # Update internal current_dir to the clean path
                self.current_dir = Path(clean_path)
                console.print(f"[dim]🔧 Current directory cleaned: {current_path} → {clean_path}[/dim]")
                return clean_path
        except Exception as e:
            console.print(f"[dim]⚠️ Directory path cleaning failed: {e}[/dim]")
        
        return current_path
    
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
