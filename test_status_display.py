#!/usr/bin/env python3
"""
Testa o novo formato de status com última linha
"""

from rich.console import Console
import time

def test_status_display():
    console = Console()
    
    print("Testando novo formato de status com última linha:")
    print("=" * 50)
    
    # Simula diferentes fases da geração
    with console.status('[bold green]🤔 Thinking...', spinner='dots') as status:
        time.sleep(1)
        
        status.update('[bold green]🤔 Thinking...\n[dim]💬 Analisando o erro do webpack...[/dim]', spinner='dots')
        time.sleep(1)
        
        status.update('[bold red]🔍 Analyzing error...\n[dim]💬 ERROR in src/App.tsx:2:17[/dim]', spinner='dots3')
        time.sleep(1)
        
        status.update('[bold yellow]💻 Writing code...\n[dim]💬 import React, { useState } from "react";[/dim]', spinner='dots2')
        time.sleep(1)
        
        status.update('[bold yellow]📄 Creating files...\n[dim]💬 function App() {[/dim]', spinner='dots2')
        time.sleep(1)
    
    print("\n✅ Teste concluído! Agora o status mostra sempre a última linha do LLM.")

if __name__ == "__main__":
    test_status_display()
