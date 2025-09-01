"""
Context Commands
Comandos relacionados ao gerenciamento de contexto de arquivos
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


class ContextCommands:
    """Comandos para gerenciar o contexto de arquivos"""
    
    def __init__(self, file_context_manager):
        self.file_context_manager = file_context_manager
    
    def show_file_context(self):
        """Mostra o contexto atual de arquivos"""
        summary = self.file_context_manager.get_context_summary()
        console.print(Panel(summary, title="📋 File Context", border_style="cyan"))
        
        if self.file_context_manager.has_context():
            console.print("[dim]💡 Use '/clear-context' to clear or '/refresh-context' to update[/dim]")
    
    def clear_file_context(self):
        """Limpa o contexto de arquivos"""
        if self.file_context_manager.has_context():
            self.file_context_manager.clear_context()
            console.print("[green]✅ File context cleared[/green]")
        else:
            console.print("[yellow]⚠️ No file context to clear[/yellow]")
    
    def refresh_file_context(self):
        """Atualiza o contexto de arquivos executando novamente os comandos de leitura"""
        if not self.file_context_manager.has_context():
            console.print("[yellow]⚠️ No existing context to refresh. Use a regular prompt to build new context.[/yellow]")
            return
            
        console.print("[blue]🔄 Refreshing file context...[/blue]")
        
        # Limpa contexto atual
        self.file_context_manager.clear_context()
        
        # Força nova leitura na próxima execução
        console.print("[green]✅ Context cleared. Next prompt will rebuild file context.[/green]")
