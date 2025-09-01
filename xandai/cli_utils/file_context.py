"""
File Context Manager
Gerencia o contexto persistente de arquivos lidos
"""

import time
from typing import Dict


class FileContextManager:
    """Gerencia o contexto persistente de arquivos lidos"""
    
    def __init__(self):
        self.file_context = {}  # {filename: content}
        self.last_read_time = None
        self.working_directory = None
        
    def add_file_content(self, filename: str, content: str):
        """Adiciona conteúdo de arquivo ao contexto"""
        self.file_context[filename] = content
        self.last_read_time = time.time()
        
    def get_all_context(self) -> dict:
        """Retorna todo o contexto de arquivos"""
        return self.file_context.copy()
        
    def has_context(self) -> bool:
        """Verifica se há contexto disponível"""
        return len(self.file_context) > 0
        
    def clear_context(self):
        """Limpa todo o contexto"""
        self.file_context.clear()
        self.last_read_time = None
        
    def get_context_summary(self) -> str:
        """Retorna um resumo do contexto atual"""
        if not self.file_context:
            return "No file context available"
            
        summary = f"📋 Current File Context ({len(self.file_context)} files):\n"
        for filename, content in self.file_context.items():
            lines = len(content.split('\n'))
            chars = len(content)
            summary += f"  📄 {filename} ({lines} lines, {chars} chars)\n"
            
        if self.last_read_time:
            time_ago = time.time() - self.last_read_time
            if time_ago < 60:
                summary += f"  🕒 Last updated: {int(time_ago)} seconds ago\n"
            else:
                summary += f"  🕒 Last updated: {int(time_ago/60)} minutes ago\n"
                
        return summary
        
    def format_context_for_injection(self) -> str:
        """Formata o contexto para injeção no prompt"""
        if not self.file_context:
            return ""
            
        formatted = "\n[PERSISTENT FILE CONTEXT - INJECTED]\n"
        for filename, content in self.file_context.items():
            formatted += f"\n--- File: {filename} ---\n{content}\n--- End of {filename} ---\n"
            
        formatted += "\n[END OF PERSISTENT CONTEXT]\n"
        return formatted
