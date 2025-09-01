"""
Auto Recovery System
Sistema de recuperação automática para erros de diretório não encontrado
"""

import os
import re
from typing import List, Tuple, Optional
from rich.console import Console
from pathlib import Path

console = Console()


class AutoRecovery:
    """Sistema de recuperação automática para erros de navegação"""
    
    def __init__(self, shell_executor, ai_read_decision=None):
        self.shell_exec = shell_executor
        self.ai_read_decision = ai_read_decision
    
    def is_directory_not_found_error(self, error_message: str) -> bool:
        """
        Detecta se o erro é relacionado a diretório não encontrado
        
        Args:
            error_message: Mensagem de erro
            
        Returns:
            bool: True se for erro de diretório não encontrado
        """
        directory_error_patterns = [
            r"directory not found",
            r"the system cannot find the path specified",
            r"no such file or directory",
            r"cannot access",
            r"not a directory",
            r"path does not exist",
            r"invalid path",
            r"cannot find the path"
        ]
        
        error_lower = error_message.lower()
        return any(re.search(pattern, error_lower) for pattern in directory_error_patterns)
    
    def extract_failed_path(self, command: str, error_message: str) -> Optional[str]:
        """
        Extrai o caminho que falhou do comando ou erro
        
        Args:
            command: Comando que falhou
            error_message: Mensagem de erro
            
        Returns:
            Caminho que causou o erro
        """
        # Tenta extrair do comando cd
        if command.strip().startswith('cd '):
            path = command.strip()[3:].strip().strip('"').strip("'")
            return path
            
        # Tenta extrair da mensagem de erro
        path_patterns = [
            r"(?:path|directory|folder).*?[:\s]([^\s]+)",
            r"'([^']+)'",
            r'"([^"]+)"',
            r"([A-Z]:\\[^\s]+)",
            r"(/[^\s]+)"
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return None
    
    def auto_recover_directory_error(self, command: str, error_message: str) -> List[str]:
        """
        Recuperação automática para erros de diretório
        
        Args:
            command: Comando que falhou
            error_message: Mensagem de erro
            
        Returns:
            Lista de comandos de read para mapear estrutura
        """
        console.print(f"[yellow]🔍 Directory not found - initiating auto-recovery...[/yellow]")
        
        failed_path = self.extract_failed_path(command, error_message)
        if failed_path:
            console.print(f"[dim]Failed path: {failed_path}[/dim]")
        
        # Determina estratégia de read baseada no erro
        if self.ai_read_decision:
            return self._ai_driven_recovery(failed_path, error_message)
        else:
            return self._rule_based_recovery(failed_path)
    
    def _ai_driven_recovery(self, failed_path: str, error_message: str) -> List[str]:
        """
        Recuperação dirigida por IA
        
        Args:
            failed_path: Caminho que falhou
            error_message: Mensagem de erro original
            
        Returns:
            Lista de comandos de read
        """
        try:
            recovery_prompt = f"""
You are helping recover from a directory navigation error.

Failed Command Context:
- Attempted path: {failed_path or 'Unknown'}
- Error: {error_message}
- Current directory: {self.shell_exec.current_dir}

Your task: Generate the most effective read commands to understand the current directory structure and find the correct path.

Respond with ONLY a JSON list of commands:
["dir", "dir examples", "dir examples\\complex"]

Focus on:
1. Understanding current structure
2. Finding similar named directories
3. Mapping the correct path

Your response:"""

            response = ""
            for chunk in self.ai_read_decision.api.generate(
                self.ai_read_decision.selected_model, 
                recovery_prompt
            ):
                response += chunk
            
            # Extrai comandos da resposta JSON
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                import json
                try:
                    commands = json.loads(json_match.group(0))
                    console.print(f"[blue]🤖 AI suggested recovery strategy: {len(commands)} commands[/blue]")
                    return commands
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            console.print(f"[yellow]⚠️ AI recovery failed: {e}[/yellow]")
        
        # Fallback para recuperação baseada em regras
        return self._rule_based_recovery(failed_path)
    
    def _rule_based_recovery(self, failed_path: str) -> List[str]:
        """
        Recuperação baseada em regras
        
        Args:
            failed_path: Caminho que falhou
            
        Returns:
            Lista de comandos de read
        """
        is_windows = "windows" in self.shell_exec.get_os_info().lower()
        base_cmd = "dir" if is_windows else "ls -la"
        
        commands = [base_cmd]  # Sempre começar com listagem atual
        
        if failed_path:
            # Analisa o caminho falhou para entender o que procurar
            path_parts = failed_path.replace('\\', '/').split('/')
            
            # Procura por partes do caminho
            current_path = ""
            for part in path_parts:
                if part and part != '.':
                    if current_path:
                        test_path = f"{current_path}/{part}" if not is_windows else f"{current_path}\\{part}"
                    else:
                        test_path = part
                    
                    if is_windows:
                        commands.append(f"dir {test_path} 2>nul || echo Directory {test_path} not found")
                    else:
                        commands.append(f"ls -la {test_path} 2>/dev/null || echo 'Directory {test_path} not found'")
                    
                    current_path = test_path
        
        # Adiciona comandos para encontrar alternativas
        if "examples" in str(failed_path).lower():
            commands.extend([
                f"{base_cmd} | findstr /i examples" if is_windows else f"{base_cmd} | grep -i examples",
                f"dir /s /b examples 2>nul" if is_windows else "find . -name '*examples*' -type d 2>/dev/null"
            ])
        
        console.print(f"[blue]📋 Rule-based recovery: {len(commands)} commands[/blue]")
        return commands[:6]  # Limita a 6 comandos
    
    def suggest_correct_paths(self, read_results: List[str], failed_path: str) -> List[str]:
        """
        Sugere caminhos corretos baseado nos resultados da leitura
        
        Args:
            read_results: Resultados dos comandos de read
            failed_path: Caminho original que falhou
            
        Returns:
            Lista de sugestões de caminhos
        """
        suggestions = []
        
        if not failed_path:
            return suggestions
        
        # Extrai nomes de diretórios dos resultados
        directories = []
        for result in read_results:
            # Procura por linhas que indicam diretórios
            lines = result.split('\n')
            for line in lines:
                if '<DIR>' in line or 'd' in line[:10]:  # Windows DIR ou Unix ls -la
                    # Extrai nome do diretório
                    parts = line.split()
                    if parts:
                        dir_name = parts[-1]
                        if dir_name not in ['.', '..']:
                            directories.append(dir_name)
        
        # Procura por similaridades com o caminho falhou
        failed_parts = failed_path.replace('\\', '/').split('/')
        target_name = failed_parts[-1] if failed_parts else failed_path
        
        # Fuzzy matching simples
        for directory in directories:
            similarity = self._calculate_similarity(target_name.lower(), directory.lower())
            if similarity > 0.5:  # 50% de similaridade
                suggestions.append(directory)
        
        return suggestions[:3]  # Máximo 3 sugestões
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calcula similaridade simples entre duas strings"""
        if str1 == str2:
            return 1.0
        
        # Verifica se uma string contém a outra
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Conta caracteres em comum
        common_chars = sum(1 for c in str1 if c in str2)
        max_len = max(len(str1), len(str2))
        
        return common_chars / max_len if max_len > 0 else 0.0
