"""
Response Processing Module
Handles response formatting, code extraction, and content processing
"""

import re
from typing import List, Tuple
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()


class ResponseProcessor:
    """Processes and formats AI responses"""
    
    def __init__(self, shell_executor):
        self.shell_executor = shell_executor
    
    def display_formatted_response(self, response: str):
        """
        Exibe a resposta formatada de forma limpa
        
        Args:
            response: Resposta completa do modelo
        """
        # Remove special tags (already processed separately)
        clean_response = response
        clean_response = re.sub(r'<actions>.*?</actions>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        clean_response = re.sub(r'<read>.*?</read>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        clean_response = re.sub(r'<code[^>]*>.*?</code>', '', clean_response, flags=re.DOTALL | re.IGNORECASE)
        
        # Separate text and code blocks
        parts = re.split(r'(```[\s\S]*?```)', clean_response)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # It's a code block
                lines = part.split('\n')
                if len(lines) > 2:
                    # Extract language and code
                    lang_line = lines[0][3:].strip()
                    code_content = '\n'.join(lines[1:-1])
                    
                    # Detect language
                    lang = lang_line if lang_line else 'text'
                    
                    # Mapeia linguagens comuns
                    lang_map = {
                        'py': 'python', 'python': 'python',
                        'js': 'javascript', 'javascript': 'javascript',
                        'ts': 'typescript', 'typescript': 'typescript',
                        'java': 'java', 'c': 'c', 'cpp': 'cpp',
                        'go': 'go', 'rust': 'rust', 'rb': 'ruby',
                        'php': 'php', 'sql': 'sql', 'bash': 'bash',
                        'sh': 'bash', 'json': 'json', 'xml': 'xml',
                        'yaml': 'yaml', 'yml': 'yaml'
                    }
                    
                    display_lang = lang_map.get(lang.lower(), lang)
                    
                    # Display code with syntax highlighting
                    syntax = Syntax(code_content, display_lang, theme="monokai", line_numbers=True)
                    console.print("\n")
                    console.print(Panel(syntax, title=f"[bold yellow]{display_lang.upper()} Code[/bold yellow]", border_style="yellow"))
                    console.print("\n")
                else:
                    # Empty or malformed code block
                    console.print(part)
            else:
                # It's normal text
                # Remove extra spaces and format paragraphs
                paragraphs = part.strip().split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Formata listas
                        if para.strip().startswith(('- ', '* ', '• ')):
                            lines = para.split('\n')
                            for line in lines:
                                if line.strip():
                                    console.print(f"  {line.strip()}")
                        # Format titles
                        elif para.strip().startswith('#'):
                            console.print(f"\n[bold]{para.strip()}[/bold]\n")
                        else:
                            # Texto normal
                            console.print(para.strip())
                        console.print()  # Blank line between paragraphs
    
    def generate_filename(self, lang: str, code: str, context: str) -> str:
        """
        Generates an intelligent filename based on context and code
        
        Args:
            lang: Programming language
            code: Code content
            context: Context or description
            
        Returns:
            Generated filename
        """
        # Extract potential filename from code content
        potential_names = []
        
        # Look for class names
        class_matches = re.findall(r'class\s+(\w+)', code, re.IGNORECASE)
        if class_matches:
            potential_names.extend(class_matches)
        
        # Look for function names (but prefer class names)
        if not potential_names:
            func_matches = re.findall(r'(?:def|function)\s+(\w+)', code, re.IGNORECASE)
            potential_names.extend(func_matches[:3])  # Only first 3
        
        # Look for component names in React
        component_matches = re.findall(r'(?:const|function)\s+(\w+)\s*=.*?(?:React|JSX)', code, re.IGNORECASE)
        if component_matches:
            potential_names.extend(component_matches)
        
        # Choose the best name
        if potential_names:
            name = potential_names[0]
        else:
            # Use context-based name
            context_words = re.findall(r'\w+', context.lower())
            if context_words:
                name = '_'.join(context_words[:2])
            else:
                name = "generated"
        
        # Add appropriate extension
        extensions = {
            'python': '.py', 'py': '.py',
            'javascript': '.js', 'js': '.js',
            'typescript': '.ts', 'ts': '.ts',
            'html': '.html', 'htm': '.html',
            'css': '.css',
            'json': '.json',
            'yaml': '.yml', 'yml': '.yml',
            'xml': '.xml',
            'java': '.java',
            'c': '.c', 'cpp': '.cpp',
            'go': '.go',
            'rust': '.rs',
            'php': '.php',
            'ruby': '.rb', 'rb': '.rb',
            'bash': '.sh', 'shell': '.sh'
        }
        
        ext = extensions.get(lang.lower(), '.txt')
        return f"{name}{ext}"
    
    def extract_code_blocks(self, response: str) -> List[Tuple[str, str, str]]:
        """
        Extrai blocos de código da resposta com suporte para <code edit> e <code create>
        
        Args:
            response: Resposta do modelo
            
        Returns:
            Lista de tuplas (action_type, filename, code_content) onde action_type é 'edit' ou 'create'
        """
        code_blocks = []
        
        # Padrão para novas tags específicas: <code edit> e <code create>
        new_pattern = r'<code\s+(edit|create)\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)\s*</code>'
        
        # Primeiro, tenta o novo padrão com edit/create
        new_matches = re.findall(new_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if new_matches:
            for action_type, filename, content in new_matches:
                # Valida o filename
                clean_filename = filename.strip()
                if clean_filename and self.is_valid_filename(clean_filename):
                    code_blocks.append((action_type.lower(), clean_filename, content))
                else:
                    console.print(f"[yellow]⚠️  Invalid filename skipped: {filename}[/yellow]")
        
        # Compatibilidade com padrão antigo (sem edit/create) - assume 'create' como padrão
        old_pattern = r'<code\s+filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)\s*</code>'
        old_matches = re.findall(old_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if old_matches:
            for filename, content in old_matches:
                # Valida o filename
                clean_filename = filename.strip()
                if clean_filename and self.is_valid_filename(clean_filename):
                    # Verifica se o arquivo já existe para decidir o tipo de ação
                    current_dir = Path(self.shell_executor.get_current_directory())
                    file_path = self.resolve_file_path(clean_filename, current_dir)
                    action_type = 'edit' if file_path.exists() else 'create'
                    code_blocks.append((action_type, clean_filename, content))
                else:
                    console.print(f"[yellow]⚠️  Invalid filename skipped: {filename}[/yellow]")
        
        # Se não encontrou nada, tenta padrões alternativos para tags mal formatadas
        if not code_blocks:
            # Busca por tags incompletas ou mal fechadas
            alt_pattern = r'<code\s+(edit|create)?\s*filename\s*=\s*["\']([^"\']+)["\']>\s*(.*?)(?:</code>|$)'
            alt_matches = re.findall(alt_pattern, response, re.DOTALL | re.IGNORECASE)
            
            for action_type, filename, content in alt_matches:
                clean_filename = filename.strip()
                if clean_filename and self.is_valid_filename(clean_filename):
                    # Remove possível texto misturado após o código
                    cleaned_content = self.remove_mixed_content(content)
                    # Se action_type está vazio, determina baseado na existência do arquivo
                    if not action_type:
                        current_dir = Path(self.shell_executor.get_current_directory())
                        file_path = self.resolve_file_path(clean_filename, current_dir)
                        action_type = 'edit' if file_path.exists() else 'create'
                    code_blocks.append((action_type.lower(), clean_filename, cleaned_content))
        
        return code_blocks
    
    def is_valid_filename(self, filename: str) -> bool:
        """
        Verifica se um nome de arquivo é válido
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            True se o filename for válido
        """
        if not filename or not filename.strip():
            return False
        
        # Remove espaços
        filename = filename.strip()
        
        # Verifica caracteres inválidos
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in invalid_chars):
            return False
        
        # Verifica se não é apenas pontos
        if filename.replace('.', '').strip() == '':
            return False
        
        # Verifica se tem pelo menos um caractere alfanumérico
        if not re.search(r'[a-zA-Z0-9]', filename):
            return False
        
        # Verifica tamanho razoável
        if len(filename) > 255:
            return False
        
        return True
    
    def resolve_file_path(self, filepath: str, current_dir: Path) -> Path:
        """
        Resolve caminho do arquivo, considerando caminhos relativos e absolutos
        
        Args:
            filepath: Caminho do arquivo fornecido
            current_dir: Diretório atual
            
        Returns:
            Path object resolvido
        """
        path = Path(filepath)
        
        if path.is_absolute():
            return path
        else:
            return current_dir / path
    
    def remove_mixed_content(self, content: str) -> str:
        """
        Remove conteúdo misturado após o código (como tags HTML ou texto descritivo)
        
        Args:
            content: Conteúdo bruto
            
        Returns:
            Conteúdo limpo
        """
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # Para se encontrar uma tag HTML que não seja código
            if re.match(r'^\s*<[/]?(code|actions|read)\b', line, re.IGNORECASE):
                break
            
            # Para se encontrar texto descritivo típico (frases em inglês)
            if re.match(r'^\s*(Now I\'ll|First|Next|Then|Let me|I\'ll)', line, re.IGNORECASE):
                break
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def clean_code_content(self, content: str) -> str:
        """
        Limpa o conteúdo do código removendo espaços desnecessários e validando
        
        Args:
            content: Conteúdo bruto do código
            
        Returns:
            Código limpo
        """
        if not content:
            return ""
        
        # Remove espaços em branco no início e fim
        cleaned = content.strip()
        
        # Remove possíveis caracteres de controle
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        
        # Verifica se o conteúdo parece ser código válido
        if self.is_likely_code(cleaned):
            return cleaned
        else:
            # Se não parece código, tenta extrair apenas a parte que parece código
            return self.extract_code_portion(cleaned)
    
    def is_likely_code(self, content: str) -> bool:
        """
        Verifica se o conteúdo parece ser código válido
        
        Args:
            content: Conteúdo a verificar
            
        Returns:
            True se parece ser código
        """
        if not content.strip():
            return False
        
        # Indicadores de código válido
        code_indicators = [
            r'import\s+\w+',  # Python imports
            r'from\s+\w+\s+import',  # Python imports
            r'function\s+\w+',  # JavaScript functions
            r'const\s+\w+',  # JavaScript/TypeScript
            r'let\s+\w+',  # JavaScript/TypeScript
            r'interface\s+\w+',  # TypeScript
            r'class\s+\w+',  # Classes
            r'def\s+\w+',  # Python functions
            r'<\w+[^>]*>',  # HTML/JSX tags
            r'{\s*\w+',  # Object syntax
            r'export\s+(default\s+)?',  # ES6 exports
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def extract_code_portion(self, content: str) -> str:
        """
        Extrai apenas a porção que parece ser código válido
        
        Args:
            content: Conteúdo misto
            
        Returns:
            Parte do conteúdo que parece código
        """
        lines = content.split('\n')
        code_lines = []
        
        # Procura por linhas que parecem código
        for line in lines:
            if self.line_looks_like_code(line) and not self.line_looks_like_description(line):
                code_lines.append(line)
            elif code_lines:  # Se já começou a coletar código e encontrou uma linha não-código
                # Para de coletar, mas permite algumas linhas em branco
                if line.strip() == '' and len(code_lines) > 0:
                    code_lines.append(line)  # Mantém linha em branco
                else:
                    break  # Para na primeira linha que claramente não é código
        
        return '\n'.join(code_lines).strip()
    
    def line_looks_like_code(self, line: str) -> bool:
        """
        Verifica se uma linha parece código
        
        Args:
            line: Linha a verificar
            
        Returns:
            True se a linha parece código
        """
        line = line.strip()
        
        if not line:
            return True  # Linhas vazias são neutras
        
        # Indicadores de código
        code_patterns = [
            r'^import\s+',
            r'^from\s+\w+\s+import',
            r'^def\s+\w+',
            r'^class\s+\w+',
            r'^function\s+\w+',
            r'^const\s+\w+\s*=',
            r'^let\s+\w+\s*=',
            r'^var\s+\w+\s*=',
            r'^\s*if\s*\(',
            r'^\s*for\s*\(',
            r'^\s*while\s*\(',
            r'^\s*return\s+',
            r'^\s*console\.',
            r'^\s*print\(',
            r'^\s*\w+\s*=\s*',
            r'^\s*\}',
            r'^\s*\{',
            r'^\s*\);?\s*$',
            r'^\s*#.*',  # Comments
            r'^\s*//.*',  # Comments
            r'^\s*/\*.*',  # Comments
        ]
        
        return any(re.match(pattern, line) for pattern in code_patterns)
    
    def line_looks_like_description(self, line: str) -> bool:
        """
        Verifica se uma linha parece descrição/texto natural
        
        Args:
            line: Linha a verificar
            
        Returns:
            True se a linha parece descrição
        """
        line = line.strip()
        
        # Padrões de descrição
        description_patterns = [
            r'^This\s+',
            r'^Here\s+',
            r'^Now\s+',
            r'^First\s+',
            r'^Next\s+',
            r'^Then\s+',
            r'^Finally\s+',
            r'^Note\s+that',
            r'^Remember\s+to',
            r'^Don\'t\s+forget',
        ]
        
        return any(re.match(pattern, line, re.IGNORECASE) for pattern in description_patterns)
    
    def check_if_response_has_implementation(self, response: str) -> bool:
        """
        Verifica se a resposta contém implementação real (código/comandos)
        
        Args:
            response: Resposta do modelo
            
        Returns:
            True se contém implementação
        """
        # Verifica se há tags de código ou ações
        has_code_tags = bool(re.search(r'<code[^>]*>.*?</code>', response, re.DOTALL | re.IGNORECASE))
        has_action_tags = bool(re.search(r'<actions>.*?</actions>', response, re.DOTALL | re.IGNORECASE))
        has_read_tags = bool(re.search(r'<read>.*?</read>', response, re.DOTALL | re.IGNORECASE))
        
        # Verifica se há blocos de código markdown
        has_code_blocks = bool(re.search(r'```[\s\S]*?```', response))
        
        # Palavras que indicam apenas explicação/descrição
        explanation_keywords = [
            'here\'s how', 'you need to', 'you should', 'i recommend', 'i suggest',
            'first, you', 'then you', 'next, you', 'finally, you',
            'the approach', 'the solution', 'the idea', 'the concept'
        ]
        
        has_explanations = any(keyword in response.lower() for keyword in explanation_keywords)
        
        # Se tem tags específicas, definitivamente tem implementação
        if has_code_tags or has_action_tags or has_read_tags:
            return True
        
        # Se tem blocos de código e poucas explicações, provavelmente tem implementação
        if has_code_blocks and not has_explanations:
            return True
        
        # Se é muito explicativo e não tem código, provavelmente não tem implementação
        if has_explanations and not (has_code_blocks or has_code_tags):
            return False
        
        # Caso padrão: assume que tem implementação se não for claramente explicativo
        return not has_explanations
