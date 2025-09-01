"""
File Editor System
Sistema robusto para edição e atualização de arquivos existentes
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console

console = Console()


class FileEditor:
    """Sistema robusto para edição de arquivos existentes"""
    
    def __init__(self, file_operations):
        self.file_ops = file_operations
        self.backup_enabled = True
        self.backup_suffix = ".backup"
    
    def can_edit_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Verifica se arquivo pode ser editado
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            Tuple (pode_editar, motivo)
        """
        file_path = Path(filepath)
        
        # Verifica se existe
        if not file_path.exists():
            return False, f"File does not exist: {filepath}"
        
        # Verifica se é arquivo
        if not file_path.is_file():
            return False, f"Path is not a file: {filepath}"
        
        # Verifica permissões
        if not os.access(file_path, os.R_OK):
            return False, f"No read permission: {filepath}"
        
        if not os.access(file_path, os.W_OK):
            return False, f"No write permission: {filepath}"
        
        # Verifica se é arquivo binário
        if self._is_binary_file(file_path):
            return False, f"Cannot edit binary file: {filepath}"
        
        return True, "File can be edited"
    
    def _is_binary_file(self, file_path: Path, sample_size: int = 8192) -> bool:
        """Verifica se arquivo é binário"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(sample_size)
                # Verifica se tem caracteres nulos (indica binário)
                return b'\0' in chunk
        except Exception:
            return True  # Se erro, assume binário por segurança
    
    def read_existing_file(self, filepath: str) -> Tuple[bool, str, List[str]]:
        """
        Lê arquivo existente e retorna conteúdo
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            Tuple (success, content, lines)
        """
        try:
            file_path = Path(filepath)
            
            can_edit, reason = self.can_edit_file(filepath)
            if not can_edit:
                return False, reason, []
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            return True, content, lines
            
        except Exception as e:
            return False, f"Error reading file: {e}", []
    
    def create_backup(self, filepath: str) -> Tuple[bool, str]:
        """
        Cria backup do arquivo
        
        Args:
            filepath: Caminho do arquivo original
            
        Returns:
            Tuple (success, backup_path)
        """
        if not self.backup_enabled:
            return True, ""
        
        try:
            file_path = Path(filepath)
            backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)
            
            # Se backup já existe, adiciona timestamp
            if backup_path.exists():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f"{file_path.suffix}.{timestamp}.backup")
            
            shutil.copy2(file_path, backup_path)
            return True, str(backup_path)
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to create backup: {e}[/yellow]")
            return False, str(e)
    
    def smart_file_update(self, filepath: str, new_content: str, update_mode: str = "replace") -> Tuple[bool, str]:
        """
        Atualiza arquivo de forma inteligente
        
        Args:
            filepath: Caminho do arquivo
            new_content: Novo conteúdo
            update_mode: Modo de atualização ('replace', 'append', 'prepend', 'smart_merge')
            
        Returns:
            Tuple (success, message)
        """
        file_path = Path(filepath)
        
        # Verifica se pode editar
        can_edit, reason = self.can_edit_file(filepath)
        
        if file_path.exists() and not can_edit:
            return False, f"Cannot edit file: {reason}"
        
        try:
            # Se arquivo não existe, cria novo
            if not file_path.exists():
                return self._create_new_file(filepath, new_content)
            
            # Lê conteúdo atual
            success, current_content, current_lines = self.read_existing_file(filepath)
            if not success:
                return False, current_content
            
            # Cria backup
            backup_success, backup_path = self.create_backup(filepath)
            
            # Atualiza baseado no modo
            if update_mode == "replace":
                final_content = new_content
                
            elif update_mode == "append":
                final_content = current_content + "\n" + new_content
                
            elif update_mode == "prepend":
                final_content = new_content + "\n" + current_content
                
            elif update_mode == "smart_merge":
                final_content = self._smart_merge_content(current_content, new_content)
                
            else:
                return False, f"Unknown update mode: {update_mode}"
            
            # Escreve novo conteúdo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            # Mensagem de sucesso
            action = "Updated" if file_path.exists() else "Created"
            backup_msg = f" (backup: {backup_path})" if backup_success else ""
            
            return True, f"{action} file: {filepath}{backup_msg}"
            
        except Exception as e:
            return False, f"Error updating file: {e}"
    
    def _create_new_file(self, filepath: str, content: str) -> Tuple[bool, str]:
        """Cria novo arquivo"""
        try:
            file_path = Path(filepath)
            
            # Cria diretórios se necessário
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, f"Created new file: {filepath}"
            
        except Exception as e:
            return False, f"Error creating file: {e}"
    
    def _smart_merge_content(self, current_content: str, new_content: str) -> str:
        """
        Merge inteligente de conteúdo
        
        Args:
            current_content: Conteúdo atual
            new_content: Novo conteúdo
            
        Returns:
            Conteúdo merged
        """
        current_lines = current_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Se novo conteúdo é completamente diferente, substitui
        if len(set(new_lines) & set(current_lines)) / len(new_lines) < 0.3:
            return new_content
        
        # Tenta preservar comentários e imports do arquivo atual
        imports_and_comments = []
        code_lines = []
        
        for line in current_lines:
            stripped = line.strip()
            if (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or
                stripped.startswith('import ') or
                stripped.startswith('from ') or
                stripped.startswith('require(')):
                imports_and_comments.append(line)
            elif stripped:
                code_lines.append(line)
        
        # Adiciona imports/comentários preservados + novo conteúdo
        merged = imports_and_comments + [''] + new_lines
        
        return '\n'.join(merged)
    
    def detect_file_changes(self, filepath: str, new_content: str) -> Dict[str, any]:
        """
        Detecta mudanças que serão feitas no arquivo
        
        Args:
            filepath: Caminho do arquivo
            new_content: Novo conteúdo proposto
            
        Returns:
            Dict com informações das mudanças
        """
        changes = {
            'file_exists': False,
            'is_new_file': True,
            'lines_added': 0,
            'lines_removed': 0,
            'lines_modified': 0,
            'total_lines_current': 0,
            'total_lines_new': 0,
            'changes_summary': ""
        }
        
        file_path = Path(filepath)
        
        # Arquivo novo
        if not file_path.exists():
            new_lines = new_content.splitlines()
            changes.update({
                'is_new_file': True,
                'lines_added': len(new_lines),
                'total_lines_new': len(new_lines),
                'changes_summary': f"Creating new file with {len(new_lines)} lines"
            })
            return changes
        
        # Arquivo existente
        success, current_content, current_lines = self.read_existing_file(filepath)
        if not success:
            changes['changes_summary'] = f"Error reading file: {current_content}"
            return changes
        
        new_lines = new_content.splitlines()
        
        changes.update({
            'file_exists': True,
            'is_new_file': False,
            'total_lines_current': len(current_lines),
            'total_lines_new': len(new_lines)
        })
        
        # Calcula diferenças simples
        current_set = set(current_lines)
        new_set = set(new_lines)
        
        added_lines = new_set - current_set
        removed_lines = current_set - new_set
        
        changes.update({
            'lines_added': len(added_lines),
            'lines_removed': len(removed_lines),
            'lines_modified': max(len(added_lines), len(removed_lines))
        })
        
        # Resumo das mudanças
        if len(added_lines) == 0 and len(removed_lines) == 0:
            changes['changes_summary'] = "No changes detected"
        else:
            changes['changes_summary'] = f"Will modify file: +{len(added_lines)} lines, -{len(removed_lines)} lines"
        
        return changes
    
    def preview_file_changes(self, filepath: str, new_content: str, context_lines: int = 3) -> str:
        """
        Gera preview das mudanças que serão feitas
        
        Args:
            filepath: Caminho do arquivo
            new_content: Novo conteúdo
            context_lines: Linhas de contexto para mostrar
            
        Returns:
            String com preview das mudanças
        """
        changes = self.detect_file_changes(filepath, new_content)
        
        preview = []
        preview.append(f"📝 File: {filepath}")
        preview.append(f"📊 {changes['changes_summary']}")
        
        if changes['is_new_file']:
            preview.append("🆕 This is a new file")
        else:
            preview.append(f"📏 Current: {changes['total_lines_current']} lines → New: {changes['total_lines_new']} lines")
        
        return '\n'.join(preview)
