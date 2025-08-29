"""
Module to manage Git operations automatically
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console

console = Console()


class GitManager:
    """Manages Git operations automatically"""
    
    def __init__(self, working_dir: Path):
        """
        Initializes the Git manager
        
        Args:
            working_dir: Working directory
        """
        self.working_dir = working_dir
        self.git_initialized = self._check_git_repo()
        
        # If no git, initialize
        if not self.git_initialized:
            self._init_git_repo()
    
    def _check_git_repo(self) -> bool:
        """
        Checks if current directory has a git repository
        
        Returns:
            True if has git, False otherwise
        """
        git_dir = self.working_dir / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def _init_git_repo(self) -> bool:
        """
        Initializes a new git repository
        
        Returns:
            True if success, False otherwise
        """
        try:
            console.print("[dim]🔧 Initializing Git repository...[/dim]")
            
            # git init
            result = subprocess.run(
                ["git", "init"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print("[green]✓ Git repository initialized[/green]")
                
                # Configure user.name and user.email if not set
                self._ensure_git_config()
                
                # Fazer commit inicial
                self.commit("Initial commit - XandAI project initialized")
                
                self.git_initialized = True
                return True
            else:
                console.print(f"[yellow]⚠️  Falha ao inicializar Git: {result.stderr}[/yellow]")
                return False
                
        except FileNotFoundError:
            console.print("[yellow]⚠️  Git is not installed on the system[/yellow]")
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  Erro ao inicializar Git: {e}[/yellow]")
            return False
    
    def _ensure_git_config(self):
        """Ensures Git has basic user configuration"""
        try:
            # Check if user.name is configured
            result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                # Set a default name
                subprocess.run(
                    ["git", "config", "user.name", "XandAI User"],
                    cwd=self.working_dir
                )
            
            # Check if user.email is configured
            result = subprocess.run(
                ["git", "config", "user.email"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                # Set a default email
                subprocess.run(
                    ["git", "config", "user.email", "xandai@localhost"],
                    cwd=self.working_dir
                )
                
        except Exception:
            # Ignore configuration errors
            pass
    
    def add_file(self, filepath: Path) -> bool:
        """
        Adiciona um arquivo ao staging do git
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            True if success, False otherwise
        """
        if not self.git_initialized:
            return False
            
        try:
            # Converte para caminho relativo
            try:
                rel_path = filepath.relative_to(self.working_dir)
            except ValueError:
                # If not relative to working_dir, use absolute path
                rel_path = filepath
            
            result = subprocess.run(
                ["git", "add", str(rel_path)],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def commit(self, message: str) -> bool:
        """
        Faz um commit com a mensagem especificada
        
        Args:
            message: Mensagem do commit
            
        Returns:
            True if success, False otherwise
        """
        if not self.git_initialized:
            return False
            
        try:
            # Primeiro adiciona tudo ao staging
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.working_dir,
                capture_output=True
            )
            
            # Faz o commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print(f"[green]✓ Git commit: {message}[/green]")
                return True
            elif "nothing to commit" in result.stdout:
                # No changes to commit
                return True
            else:
                console.print(f"[yellow]⚠️  Falha no commit: {result.stderr}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Erro no commit: {e}[/yellow]")
            return False
    
    def commit_file_operation(self, operation: str, filepath: Path):
        """
        Makes commit after a file operation
        
        Args:
            operation: Operation type (created, edited, deleted)
            filepath: File path
        """
        if not self.git_initialized:
            return
            
        try:
            # Add the file (if not deleted)
            if operation != "deleted":
                self.add_file(filepath)
            
            # Prepara mensagem de commit
            filename = filepath.name
            message = f"XandAI: {operation} {filename}"
            
            # Faz o commit
            self.commit(message)
            
        except Exception:
            # Ignore git errors to not interrupt flow
            pass
