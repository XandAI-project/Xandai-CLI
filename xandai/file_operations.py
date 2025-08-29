"""
Module for file operations (create, edit, delete)
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Union, Dict, List
from rich.console import Console
from rich.prompt import Confirm

console = Console()


class FileOperationError(Exception):
    """Exception for file operation errors"""
    pass


class FileOperations:
    """Class to manage file operations"""
    
    def __init__(self, confirm_before_delete: bool = True):
        """
        Initializes the file operations manager
        
        Args:
            confirm_before_delete: Whether to ask for confirmation before deleting
        """
        self.confirm_before_delete = confirm_before_delete
    
    def create_file(self, filepath: Union[str, Path], content: str = "") -> None:
        """
        Creates a new file with the specified content
        
        Args:
            filepath: Path of the file to create
            content: Initial content of the file
            
        Raises:
            FileOperationError: If there is an error creating the file
        """
        try:
            filepath = Path(filepath)
            
            # Create parent directories if necessary
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if filepath.exists():
                console.print(f"[yellow]Warning: File '{filepath}' already exists and will be overwritten.[/yellow]")
            
            filepath.write_text(content, encoding='utf-8')
            console.print(f"[green]✓ File created: {filepath}[/green]")
            
        except Exception as e:
            raise FileOperationError(f"Error creating file '{filepath}': {e}")
    
    def edit_file(self, filepath: Union[str, Path], content: str) -> None:
        """
        Edits an existing file, replacing its content
        
        Args:
            filepath: Caminho do arquivo a editar
            content: New file content
            
        Raises:
            FileOperationError: Se houver erro ao editar o arquivo
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise FileOperationError(f"File '{filepath}' does not exist")
            
            # Faz backup antes de editar
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            shutil.copy2(filepath, backup_path)
            
            try:
                filepath.write_text(content, encoding='utf-8')
                console.print(f"[green]✓ Arquivo editado: {filepath}[/green]")
                
                # Remove backup se tudo deu certo
                backup_path.unlink()
                
            except Exception as e:
                # Restaura backup em caso de erro
                shutil.copy2(backup_path, filepath)
                backup_path.unlink()
                raise e
                
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Erro ao editar arquivo '{filepath}': {e}")
    
    def append_to_file(self, filepath: Union[str, Path], content: str) -> None:
        """
        Adds content to the end of an existing file
        
        Args:
            filepath: File path
            content: Content to add
            
        Raises:
            FileOperationError: If there is an error adding content
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise FileOperationError(f"File '{filepath}' does not exist")
            
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            
            console.print(f"[green]✓ Content added to: {filepath}[/green]")
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Error adding content to file '{filepath}': {e}")
    
    def delete_file(self, filepath: Union[str, Path]) -> None:
        """
        Deletes a file after confirmation
        
        Args:
            filepath: Caminho do arquivo a deletar
            
        Raises:
            FileOperationError: Se houver erro ao deletar o arquivo
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise FileOperationError(f"File '{filepath}' does not exist")
            
            if self.confirm_before_delete:
                if not Confirm.ask(f"[red]Tem certeza que deseja deletar '{filepath}'?[/red]"):
                    console.print("[yellow]Operation cancelled.[/yellow]")
                    return
            
            filepath.unlink()
            console.print(f"[green]✓ Arquivo deletado: {filepath}[/green]")
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Erro ao deletar arquivo '{filepath}': {e}")
    
    def read_file(self, filepath: Union[str, Path]) -> str:
        """
        Reads the content of a file
        
        Args:
            filepath: Caminho do arquivo a ler
            
        Returns:
            File content
            
        Raises:
            FileOperationError: Se houver erro ao ler o arquivo
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                raise FileOperationError(f"File '{filepath}' does not exist")
            
            return filepath.read_text(encoding='utf-8')
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Erro ao ler arquivo '{filepath}': {e}")
    
    def list_files(self, directory: Union[str, Path] = ".", pattern: str = "*", recursive: bool = False) -> list[Path]:
        """
        Lists files in a directory
        
        Args:
            directory: Directory to list
            pattern: Glob pattern to filter files
            recursive: If True, search recursively in subdirectories
            
        Returns:
            Lista de caminhos de arquivo
            
        Raises:
            FileOperationError: Se houver erro ao listar arquivos
        """
        try:
            directory = Path(directory)
            
            if not directory.exists():
                raise FileOperationError(f"Directory '{directory}' does not exist")
            
            if not directory.is_dir():
                raise FileOperationError(f"'{directory}' is not a directory")
            
            if recursive:
                # Busca recursiva usando rglob
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"Erro ao listar arquivos em '{directory}': {e}")
    
    def search_file(self, filename: str, start_dir: Union[str, Path] = ".", 
                   search_parent: bool = True, max_depth: int = 3) -> Optional[Path]:
        """
        Searches for a file in parent and subdirectories
        
        Args:
            filename: Name of file to search
            start_dir: Initial search directory
            search_parent: If True, also search in parent directories
            max_depth: Maximum depth to search in parent directories
            
        Returns:
            Caminho do arquivo encontrado ou None
        """
        try:
            start_path = Path(start_dir).resolve()
            
            # First, search in current directory and subdirectories
            console.print(f"[dim]🔍 Searching for '{filename}' in {start_path} and subdirectories...[/dim]")
            
            # Recursive search in current directory
            matches = list(start_path.rglob(filename))
            if matches:
                console.print(f"[green]✓ Encontrado: {matches[0]}[/green]")
                return matches[0]
            
            # If search_parent, search in parent directories
            if search_parent:
                current = start_path
                for level in range(max_depth):
                    parent = current.parent
                    if parent == current:  # Reached root
                        break
                    
                    console.print(f"[dim]🔍 Searching in parent directory: {parent}[/dim]")
                    
                    # Search in parent directory and its subdirectories
                    matches = list(parent.rglob(filename))
                    if matches:
                        # Prefer files closer to initial directory
                        matches.sort(key=lambda p: len(p.parts))
                        console.print(f"[green]✓ Encontrado: {matches[0]}[/green]")
                        return matches[0]
                    
                    current = parent
            
            console.print(f"[yellow]⚠️  File '{filename}' not found[/yellow]")
            return None
            
        except Exception as e:
            console.print(f"[red]Search error: {e}[/red]")
            return None
    
    def search_file_or_directory(self, name: str, start_dir: Union[str, Path] = ".", 
                                search_parent: bool = True, max_depth: int = 3) -> Dict[str, List[Path]]:
        """
        Searches for files AND directories with the specified name
        
        Args:
            name: Name of file or directory to search
            start_dir: Initial search directory  
            search_parent: If True, also search in parent directories
            max_depth: Maximum depth to search in parent directories
            
        Returns:
            Dictionary with 'files' and 'directories' found
        """
        results = {'files': [], 'directories': []}
        
        try:
            start_path = Path(start_dir).resolve()
            
            # Helper function to process matches
            def process_matches(base_path: Path):
                # Search for exact files and directories
                matches = list(base_path.rglob(name))
                for match in matches:
                    if match.is_file():
                        results['files'].append(match)
                    elif match.is_dir():
                        results['directories'].append(match)
                
                # Search directories with similar name (without extension)
                name_without_ext = Path(name).stem
                if name_without_ext != name and name_without_ext:  # Had extension
                    dir_matches = list(base_path.rglob(name_without_ext))
                    for match in dir_matches:
                        if match.is_dir() and match not in results['directories']:
                            results['directories'].append(match)
                
                # Search for similar patterns (case-insensitive)
                pattern_variations = [
                    name.lower(),
                    name.upper(),
                    name.capitalize(),
                    name_without_ext.lower() if name_without_ext else None,
                    name_without_ext.upper() if name_without_ext else None,
                    name_without_ext.capitalize() if name_without_ext else None
                ]
                
                for pattern in pattern_variations:
                    if pattern and pattern != name:
                        pattern_matches = list(base_path.rglob(f"*{pattern}*"))
                        for match in pattern_matches[:5]:  # Limit to 5 suggestions per pattern
                            if match.is_file() and match not in results['files']:
                                results['files'].append(match)
                            elif match.is_dir() and match not in results['directories']:
                                results['directories'].append(match)
            
            # Search in current directory
            console.print(f"[dim]🔍 Buscando '{name}' em {start_path}...[/dim]")
            process_matches(start_path)
            
            # If search_parent and found nothing exact, search in parent directories
            if search_parent and not (results['files'] or results['directories']):
                current = start_path
                for level in range(max_depth):
                    parent = current.parent
                    if parent == current:  # Reached root
                        break
                    
                    console.print(f"[dim]🔍 Searching in parent directory: {parent}[/dim]")
                    process_matches(parent)
                    
                    if results['files'] or results['directories']:
                        break
                    
                    current = parent
            
            # Sort results by proximity (fewer parts = closer)
            results['files'].sort(key=lambda p: len(p.parts))
            results['directories'].sort(key=lambda p: len(p.parts))
            
            # Remove duplicatas mantendo ordem
            results['files'] = list(dict.fromkeys(results['files']))
            results['directories'] = list(dict.fromkeys(results['directories']))
            
            return results
            
        except Exception as e:
            console.print(f"[red]Search error: {e}[/red]")
            return results
