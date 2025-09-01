"""
Auto Read Structure System
Sistema que SEMPRE lê a estrutura de pastas e arquivos para injetar no contexto da IA
"""

import os
import platform
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console

console = Console()


class AutoReadStructure:
    """Sistema que automaticamente lê e mapeia a estrutura do projeto"""
    
    def __init__(self, shell_executor):
        self.shell_exec = shell_executor
        self.last_structure_cache = None
        self.cache_working_dir = None
    
    def should_read_structure(self, working_dir: str) -> bool:
        """
        Determina se deve ler a estrutura (sempre True, mas pode cachear se mesmo diretório)
        
        Args:
            working_dir: Diretório de trabalho atual
            
        Returns:
            bool: True se deve ler estrutura
        """
        # Sempre lê se mudou de diretório ou não tem cache
        if self.cache_working_dir != working_dir or not self.last_structure_cache:
            return True
        return False
    
    def read_current_structure(self, working_dir: str = None) -> Dict[str, str]:
        """
        Lê a estrutura atual do diretório
        
        Args:
            working_dir: Diretório para ler (usa atual se None)
            
        Returns:
            Dict com informações da estrutura
        """
        if not working_dir:
            working_dir = self.shell_exec.current_dir
        
        # Verifica cache
        if not self.should_read_structure(working_dir):
            return self.last_structure_cache
        
        console.print("[dim]📁 Reading project structure...[/dim]")
        
        structure_info = {
            'working_directory': working_dir,
            'directory_listing': self._get_directory_listing(),
            'file_tree': self._get_file_tree(),
            'key_files': self._read_key_files(),
            'project_info': self._detect_project_info(),
            'read_timestamp': self._get_timestamp()
        }
        
        # Atualiza cache
        self.last_structure_cache = structure_info
        self.cache_working_dir = working_dir
        
        return structure_info
    
    def _get_directory_listing(self) -> str:
        """Obtém listagem do diretório atual"""
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            cmd = "dir /b"
        else:
            cmd = "ls -la"
        
        try:
            success, output = self.shell_exec.execute_command(cmd)
            if success:
                return output.strip()
            return "Error reading directory"
        except Exception as e:
            return f"Error: {e}"
    
    def _get_file_tree(self, max_depth: int = 3, max_files: int = 50) -> str:
        """Obtém árvore de arquivos com profundidade limitada"""
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            # Windows tree command with limited depth
            cmd = f"tree /f /a | head -n {max_files}"
        else:
            # Unix tree command
            cmd = f"tree -L {max_depth} -a | head -n {max_files}"
        
        try:
            success, output = self.shell_exec.execute_command(cmd)
            if success:
                return output.strip()
            
            # Fallback: manual tree using Python
            return self._manual_tree()
        except Exception:
            return self._manual_tree()
    
    def _manual_tree(self, max_depth: int = 3) -> str:
        """Cria árvore manual quando tree command não disponível"""
        try:
            working_path = Path(self.shell_exec.current_dir)
            tree_lines = []
            
            def add_items(path: Path, prefix: str = "", depth: int = 0):
                if depth >= max_depth:
                    return
                
                try:
                    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                    for i, item in enumerate(items[:20]):  # Limit items
                        is_last = i == len(items) - 1
                        current_prefix = "└── " if is_last else "├── "
                        tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                        
                        if item.is_dir() and not item.name.startswith('.'):
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            add_items(item, next_prefix, depth + 1)
                except PermissionError:
                    pass
            
            tree_lines.append(working_path.name)
            add_items(working_path)
            return "\n".join(tree_lines[:50])  # Limit total lines
            
        except Exception as e:
            return f"Manual tree failed: {e}"
    
    def _read_key_files(self) -> Dict[str, str]:
        """Lê arquivos-chave do projeto"""
        key_files = [
            'README.md', 'readme.md', 'README.txt',
            'package.json', 'requirements.txt', 'pyproject.toml',
            'Cargo.toml', 'composer.json', 'pom.xml',
            '.gitignore', 'Dockerfile', 'docker-compose.yml',
            'config.py', 'settings.py', 'app.py', 'main.py',
            'index.js', 'index.html', 'App.js', 'App.tsx'
        ]
        
        file_contents = {}
        
        for filename in key_files:
            file_path = Path(self.shell_exec.current_dir) / filename
            if file_path.exists() and file_path.is_file():
                try:
                    # Lê apenas primeiros 100 linhas para não sobrecarregar
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= 100:  # Limit lines
                                lines.append("... (file truncated)")
                                break
                            lines.append(line.rstrip())
                        
                        if lines:
                            file_contents[filename] = '\n'.join(lines)
                            
                except Exception as e:
                    file_contents[filename] = f"Error reading file: {e}"
        
        return file_contents
    
    def _detect_project_info(self) -> Dict[str, str]:
        """Detecta informações do tipo de projeto"""
        working_path = Path(self.shell_exec.current_dir)
        project_info = {
            'project_type': 'unknown',
            'main_language': 'unknown',
            'framework': 'unknown',
            'has_tests': False,
            'has_docs': False
        }
        
        # Detecta tipo de projeto por arquivos
        if (working_path / 'package.json').exists():
            project_info['project_type'] = 'Node.js/JavaScript'
            project_info['main_language'] = 'JavaScript'
            
            # Detecta framework JavaScript
            package_json_path = working_path / 'package.json'
            try:
                import json
                with open(package_json_path) as f:
                    package_data = json.load(f)
                    deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        project_info['framework'] = 'React'
                    elif 'vue' in deps:
                        project_info['framework'] = 'Vue.js'
                    elif 'angular' in deps:
                        project_info['framework'] = 'Angular'
                    elif 'express' in deps:
                        project_info['framework'] = 'Express.js'
            except:
                pass
                
        elif (working_path / 'requirements.txt').exists() or (working_path / 'pyproject.toml').exists():
            project_info['project_type'] = 'Python'
            project_info['main_language'] = 'Python'
            
            # Detecta framework Python
            req_file = working_path / 'requirements.txt'
            if req_file.exists():
                try:
                    with open(req_file) as f:
                        reqs = f.read().lower()
                        if 'django' in reqs:
                            project_info['framework'] = 'Django'
                        elif 'flask' in reqs:
                            project_info['framework'] = 'Flask'
                        elif 'fastapi' in reqs:
                            project_info['framework'] = 'FastAPI'
                except:
                    pass
        
        # Verifica testes
        test_indicators = ['tests/', 'test/', '__tests__/', 'spec/', 'pytest.ini', 'jest.config.js']
        project_info['has_tests'] = any((working_path / indicator).exists() for indicator in test_indicators)
        
        # Verifica documentação
        doc_indicators = ['docs/', 'documentation/', 'README.md', 'readme.md']
        project_info['has_docs'] = any((working_path / indicator).exists() for indicator in doc_indicators)
        
        return project_info
    
    def _get_timestamp(self) -> str:
        """Obtém timestamp atual"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def format_structure_for_context(self, structure_info: Dict[str, str]) -> str:
        """
        Formata informações da estrutura para injeção no contexto da IA
        
        Args:
            structure_info: Informações da estrutura do projeto
            
        Returns:
            String formatada para contexto
        """
        formatted = []
        
        # Cabeçalho
        formatted.append("=" * 80)
        formatted.append("📁 PROJECT STRUCTURE CONTEXT")
        formatted.append("=" * 80)
        
        # Informações básicas
        formatted.append(f"📂 Working Directory: {structure_info['working_directory']}")
        formatted.append(f"🕒 Read at: {structure_info['read_timestamp']}")
        formatted.append("")
        
        # Informações do projeto
        project_info = structure_info.get('project_info', {})
        if project_info:
            formatted.append("🏗️ PROJECT INFO:")
            formatted.append(f"   Type: {project_info.get('project_type', 'unknown')}")
            formatted.append(f"   Language: {project_info.get('main_language', 'unknown')}")
            formatted.append(f"   Framework: {project_info.get('framework', 'unknown')}")
            formatted.append(f"   Has Tests: {'✅' if project_info.get('has_tests') else '❌'}")
            formatted.append(f"   Has Docs: {'✅' if project_info.get('has_docs') else '❌'}")
            formatted.append("")
        
        # Listagem de diretório
        dir_listing = structure_info.get('directory_listing', '')
        if dir_listing:
            formatted.append("📋 CURRENT DIRECTORY LISTING:")
            formatted.append(dir_listing)
            formatted.append("")
        
        # Árvore de arquivos
        file_tree = structure_info.get('file_tree', '')
        if file_tree:
            formatted.append("🌳 FILE TREE:")
            formatted.append(file_tree)
            formatted.append("")
        
        # Arquivos-chave
        key_files = structure_info.get('key_files', {})
        if key_files:
            formatted.append("🔑 KEY FILES CONTENT:")
            for filename, content in key_files.items():
                formatted.append(f"   📄 {filename}:")
                # Indenta o conteúdo
                content_lines = content.split('\n')
                for line in content_lines[:20]:  # Primeiras 20 linhas apenas
                    formatted.append(f"      {line}")
                if len(content_lines) > 20:
                    formatted.append("      ... (content truncated)")
                formatted.append("")
        
        formatted.append("=" * 80)
        formatted.append("END PROJECT STRUCTURE CONTEXT")
        formatted.append("=" * 80)
        formatted.append("")
        
        return '\n'.join(formatted)
    
    def get_context_summary(self) -> str:
        """Retorna resumo do contexto atual"""
        if not self.last_structure_cache:
            return "❌ No structure context available"
        
        project_info = self.last_structure_cache.get('project_info', {})
        
        summary = []
        summary.append(f"📁 {self.last_structure_cache['working_directory']}")
        summary.append(f"🏗️ {project_info.get('project_type', 'Unknown')} ({project_info.get('framework', 'No framework')})")
        
        key_files = self.last_structure_cache.get('key_files', {})
        summary.append(f"📄 {len(key_files)} key files read")
        
        return " | ".join(summary)
