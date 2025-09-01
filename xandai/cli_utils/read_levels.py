"""
Read Levels Manager
Sistema de níveis para comandos de leitura de arquivos
"""

from typing import List


class ReadLevelsManager:
    """Gerencia o sistema de níveis de leitura de arquivos"""
    
    def __init__(self, shell_executor):
        self.shell_exec = shell_executor
    
    def determine_read_level(self, prompt_lower: str) -> int:
        """
        Determina qual nível de read é necessário baseado no contexto
        
        Args:
            prompt_lower: Prompt em lowercase
            
        Returns:
            Nível de read (1-4)
        """
        # Level 3: Exploração de estrutura ou debugging (verificar primeiro para evitar conflito com Level 4)
        if any(word in prompt_lower for word in [
            'explore', 'organize', 'debug', 'trace',
            'find', 'locate', 'search', 'where', 'how many',
            'folders', 'directories', 'components', 'modules'
        ]):
            return 3
        
        # Level 4: Análise profunda ou problemas complexos
        if any(word in prompt_lower for word in [
            'deep', 'thorough', 'complete', 'full analysis', 'comprehensive',
            'complex', 'architecture', 'structure', 'nested', 'hierarchy',
            'entire project', 'all files', 'whole codebase'
        ]):
            return 4
        
        # Level 2: Análise específica de arquivos
        if any(word in prompt_lower for word in [
            'analyze', 'review', 'check', 'examine', 'fix', 'error',
            'code', 'function', 'implementation', 'specific', 'file',
            'content', 'details', 'config', 'settings'
        ]):
            return 2
        
        # Level 1: Overview básico (padrão)
        return 1
    
    def generate_read_commands_by_level(self, level: int, prompt_lower: str) -> List[str]:
        """
        Gera comandos de leitura baseados no nível especificado
        
        Args:
            level: Nível de read (1-4)
            prompt_lower: Prompt em lowercase
            
        Returns:
            Lista de comandos para execução
        """
        os_info = self.shell_exec.get_os_info().lower()
        is_windows = "windows" in os_info
        
        commands = []
        
        if level >= 1:
            # Level 1: Overview básico da pasta atual
            commands.extend(self._get_level1_commands(is_windows))
        
        if level >= 2:
            # Level 2: Arquivos específicos importantes
            commands.extend(self._get_level2_commands(is_windows, prompt_lower))
        
        if level >= 3:
            # Level 3: Exploração de subpastas
            commands.extend(self._get_level3_commands(is_windows, prompt_lower))
        
        if level >= 4:
            # Level 4: Arquivos aninhados específicos
            commands.extend(self._get_level4_commands(is_windows, prompt_lower))
        
        # Limita total de comandos para não sobrecarregar
        max_commands = min(level * 2 + 2, 8)  # Level 1: 4, Level 2: 6, Level 3: 8, Level 4: 8
        return commands[:max_commands]
    
    def _get_level1_commands(self, is_windows: bool) -> List[str]:
        """Level 1: Overview básico - listagem da pasta atual"""
        if is_windows:
            return ["dir /b"]  # /b para formato simples
        else:
            return ["ls -la"]
    
    def _get_level2_commands(self, is_windows: bool, prompt_lower: str) -> List[str]:
        """Level 2: Arquivos específicos importantes"""
        commands = []
        
        # Detecta tipo de projeto e adiciona arquivos relevantes
        if any(word in prompt_lower for word in ['python', 'flask', 'django', 'py']):
            if is_windows:
                commands.extend([
                    "type app.py 2>nul || type main.py 2>nul || echo No main Python file",
                    "type requirements.txt 2>nul || echo No requirements.txt",
                    "type config.py 2>nul || echo No config.py"
                ])
            else:
                commands.extend([
                    "cat app.py 2>/dev/null || cat main.py 2>/dev/null || echo 'No main Python file'",
                    "cat requirements.txt 2>/dev/null || echo 'No requirements.txt'",
                    "cat config.py 2>/dev/null || echo 'No config.py'"
                ])
        
        elif any(word in prompt_lower for word in ['react', 'vue', 'angular', 'node', 'js', 'javascript']):
            if is_windows:
                commands.extend([
                    "type package.json 2>nul || echo No package.json",
                    "type app.js 2>nul || type index.js 2>nul || echo No main JS file",
                    "type webpack.config.js 2>nul || echo No webpack config"
                ])
            else:
                commands.extend([
                    "cat package.json 2>/dev/null || echo 'No package.json'",
                    "cat app.js 2>/dev/null || cat index.js 2>/dev/null || echo 'No main JS file'",
                    "cat webpack.config.js 2>/dev/null || echo 'No webpack config'"
                ])
        
        else:
            # Arquivos gerais comuns
            if is_windows:
                commands.extend([
                    "type README.md 2>nul || echo No README",
                    "type package.json 2>nul || type requirements.txt 2>nul || echo No project config"
                ])
            else:
                commands.extend([
                    "cat README.md 2>/dev/null || echo 'No README'",
                    "cat package.json 2>/dev/null || cat requirements.txt 2>/dev/null || echo 'No project config'"
                ])
        
        return commands
    
    def _get_level3_commands(self, is_windows: bool, prompt_lower: str) -> List[str]:
        """Level 3: Exploração de subpastas"""
        commands = []
        
        # Pastas comuns para explorar baseadas no tipo de projeto
        common_dirs = []
        
        if any(word in prompt_lower for word in ['react', 'vue', 'angular', 'frontend']):
            common_dirs = ['src', 'components', 'public', 'assets', 'styles']
        elif any(word in prompt_lower for word in ['python', 'flask', 'django', 'api']):
            common_dirs = ['src', 'app', 'models', 'views', 'templates', 'static']
        else:
            # Pastas gerais
            common_dirs = ['src', 'lib', 'components', 'modules', 'config', 'docs']
        
        for dir_name in common_dirs[:3]:  # Máximo 3 diretórios
            if is_windows:
                commands.append(f"dir {dir_name} 2>nul || echo No {dir_name} folder")
            else:
                commands.append(f"ls -la {dir_name}/ 2>/dev/null || echo 'No {dir_name} folder'")
        
        return commands
    
    def _get_level4_commands(self, is_windows: bool, prompt_lower: str) -> List[str]:
        """Level 4: Arquivos específicos aninhados"""
        commands = []
        
        # Arquivos aninhados baseados no tipo de projeto
        if any(word in prompt_lower for word in ['react', 'vue', 'angular']):
            nested_files = [
                'src/App.js', 'src/index.js', 'src/components/index.js',
                'public/index.html', 'src/App.css'
            ]
        elif any(word in prompt_lower for word in ['python', 'flask', 'django']):
            nested_files = [
                'app/__init__.py', 'app/models.py', 'app/views.py',
                'src/main.py', 'config/settings.py'
            ]
        else:
            # Arquivos aninhados gerais
            nested_files = [
                'src/index.js', 'src/main.py', 'lib/index.js',
                'config/config.json', 'docs/README.md'
            ]
        
        for file_path in nested_files[:2]:  # Máximo 2 arquivos aninhados
            if is_windows:
                # Converte / para \ no Windows
                win_path = file_path.replace('/', '\\')
                commands.append(f"type {win_path} 2>nul || echo No {win_path}")
            else:
                commands.append(f"cat {file_path} 2>/dev/null || echo 'No {file_path}'")
        
        return commands
    
    def get_suggested_read_commands(self, prompt: str) -> str:
        """
        Sugere comandos de leitura baseados no contexto do prompt usando sistema de níveis
        
        Args:
            prompt: Prompt do usuário
            
        Returns:
            String com comandos de leitura sugeridos
        """
        prompt_lower = prompt.lower()
        
        # Detecta qual nível de read é necessário baseado no contexto
        read_level = self.determine_read_level(prompt_lower)
        
        # Gera comandos para o nível detectado
        suggested_commands = self.generate_read_commands_by_level(read_level, prompt_lower)
        
        if suggested_commands:
            commands_text = "\n".join(suggested_commands)
            return f"""<read>
{commands_text}
</read>"""
        
        return ""
