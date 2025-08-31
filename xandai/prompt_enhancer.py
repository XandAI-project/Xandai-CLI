"""
Module to enhance prompts with coding context
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from rich.console import Console
import tiktoken

console = Console()


class PromptEnhancer:
    """Enhances prompts by adding context and structure"""
    
    # Patterns to detect file mentions
    FILE_PATTERNS = [
        r'(?:file|script|code|arquivo|código)\s+(?:called\s+|chamado\s+)?([^\s,.:;]+\.[\w]+)',
        r'(?:em|in|no|na)\s+([^\s,.:;]+\.[\w]+)',
        r'([^\s,.:;]+\.(?:py|js|ts|java|c|cpp|rs|go|rb|php|html|css|json|xml|yaml|yml|md|txt|sh|bat))\b',
        r'`([^`]+\.[\w]+)`',
        r'"([^"]+\.[\w]+)"',
        r'\'([^\']+\.[\w]+)\'',
    ]
    
    # Error detection patterns
    ERROR_PATTERNS = {
        'webpack': [
            r'Module not found:.*Error.*Can\'t resolve',
            r'ERROR in .*\.tsx?:.*TS\d+',
            r'webpack compiled with \d+ error',
            r'Module build failed.*Error',
        ],
        'import': [
            r'ImportError:.*No module named',
            r'ModuleNotFoundError:.*No module named',
            r'Cannot find module.*or its corresponding type declarations',
            r'Unable to resolve path to module',
        ],
        'syntax': [
            r'SyntaxError:.*',
            r'ERROR in .*\.tsx?:.*TS\d+.*syntax',
            r'Parse error.*',
            r'Unexpected token',
        ],
        'runtime': [
            r'RuntimeError:.*',
            r'TypeError:.*',
            r'AttributeError:.*',
            r'ReferenceError:.*',
            r'Cannot read.*of undefined',
        ],
        'compilation': [
            r'error: .*\.(?:c|cpp|rs|go):.*',
            r'fatal error:.*',
            r'compilation terminated',
            r'build failed',
        ]
    }
    
    # Keywords that indicate coding tasks
    CODING_KEYWORDS = {
        'criar': 'create',
        'crie': 'create',
        'cria': 'create',
        'gerar': 'generate',
        'gere': 'generate',
        'escrever': 'write',
        'escreva': 'write',
        'implementar': 'implement',
        'implemente': 'implement',
        'desenvolver': 'develop',
        'desenvolva': 'develop',
        'adicionar': 'add',
        'adicione': 'add',
        'modificar': 'modify',
        'modifique': 'modify',
        'editar': 'edit',
        'edite': 'edit',
        'atualizar': 'update',
        'atualize': 'update',
        'corrigir': 'fix',
        'corrija': 'fix',
        'debugar': 'debug',
        'debug': 'debug',
        'refatorar': 'refactor',
        'refatore': 'refactor',
        'otimizar': 'optimize',
        'otimize': 'optimize',
        'melhorar': 'improve',
        'melhore': 'improve',
        'testar': 'test',
        'teste': 'test',
        'documentar': 'document',
        'documente': 'document',
        'analisar': 'analyze',
        'analise': 'analyze',
        'revisar': 'review',
        'revise': 'review',
        'construir': 'build',
        'construa': 'build',
        'fazer': 'make',
        'faça': 'make',
        'make': 'make'
    }
    
    # Technology detection patterns
    TECHNOLOGY_PATTERNS = {
        'react': [
            r'\breact\b', r'\bjsx\b', r'\btsx\b', r'react[-\s]app', r'create[-\s]react[-\s]app',
            r'usestate', r'useeffect', r'usememo', r'usecallback', r'usecontext',
            r'component', r'props', r'state'
        ],
        'python': [
            r'\.py\b', r'\bpython\b', r'\bpip\b', r'requirements\.txt', r'setup\.py',
            r'\bflask\b', r'\bdjango\b', r'\bfastapi\b', r'__init__\.py',
            r'import\s+\w+', r'from\s+\w+\s+import', r'def\s+\w+', r'class\s+\w+'
        ],
        'flask': [
            r'\bflask\b', r'flask[-\s]app', r'app\.route', r'render_template',
            r'jsonify', r'request', r'session', r'Blueprint'
        ],
        'javascript': [
            r'\.js\b', r'\.mjs\b', r'\bjavascript\b', r'\bnode\b', r'package\.json',
            r'npm\s+install', r'yarn\s+add', r'function\s*\(', r'=>\s*\{',
            r'const\s+\w+', r'let\s+\w+', r'var\s+\w+'
        ],
        'typescript': [
            r'\.ts\b', r'\.tsx\b', r'\btypescript\b', r'tsconfig\.json',
            r'interface\s+\w+', r'type\s+\w+', r'enum\s+\w+'
        ],
        'vue': [
            r'\bvue\b', r'\.vue\b', r'vue[-\s]cli', r'@vue/', r'v-if', r'v-for',
            r'v-model', r'<template>', r'<script>'
        ],
        'angular': [
            r'\bangular\b', r'@angular/', r'ng\s+new', r'ng\s+generate',
            r'@component', r'@injectable', r'@ngmodule'
        ],
        'express': [
            r'\bexpress\b', r'express\(\)', r'app\.get', r'app\.post',
            r'app\.listen', r'middleware'
        ],
        'fastapi': [
            r'\bfastapi\b', r'from\s+fastapi', r'@app\.get', r'@app\.post',
            r'pydantic', r'uvicorn'
        ],
        'django': [
            r'\bdjango\b', r'django[-\s]admin', r'models\.py', r'views\.py',
            r'urls\.py', r'settings\.py', r'manage\.py'
        ]
    }
    
    def __init__(self):
        """Initialize the PromptEnhancer with coding rules cache"""
        self.context_history: List[Dict] = []
        self.coding_rules_cache = {}
        self.coding_rules_dir = Path("coding-rules")
        self._load_coding_rules()
        
        # Token management
        self.max_context_tokens = 128000  # Typical LLM context limit
        self.current_context_tokens = 0
        self.token_flush_threshold = 0.90  # Flush at 90% to leave room for response
        
        # Initialize tokenizer (fallback to simple estimation if tiktoken not available)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        except Exception:
            self.tokenizer = None
            console.print("[yellow]Warning: tiktoken not available, using token estimation[/yellow]")
        
        # Context preservation settings
        self.preserve_recent_messages = 5  # Keep last 5 interactions
        self.preserve_system_context = True  # Always keep system/rules context
    
    def _load_coding_rules(self):
        """Load all coding rules from the coding-rules directory"""
        if not self.coding_rules_dir.exists():
            return
        
        for rule_file in self.coding_rules_dir.glob("*.md"):
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    rule_name = rule_file.stem.lower()
                    self.coding_rules_cache[rule_name] = content
                    console.print(f"[dim]Loaded coding rule: {rule_name}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load rule {rule_file}: {e}[/yellow]")
    
    def detect_technologies(self, text: str) -> Set[str]:
        """
        Detect technologies mentioned in the text
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of detected technology names
        """
        detected = set()
        text_lower = text.lower()
        
        for tech, patterns in self.TECHNOLOGY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected.add(tech)
                    break  # One match per technology is enough
        
        return detected
    
    def get_relevant_coding_rules(self, detected_technologies: Set[str]) -> str:
        """
        Get coding rules for detected technologies
        
        Args:
            detected_technologies: Set of technology names
            
        Returns:
            Combined coding rules content
        """
        if not detected_technologies:
            return ""
        
        rules_content = []
        
        for tech in detected_technologies:
            if tech in self.coding_rules_cache:
                rules_content.append(f"\n[CODING RULES FOR {tech.upper()}]")
                rules_content.append(self.coding_rules_cache[tech])
                rules_content.append(f"[END {tech.upper()} RULES]\n")
        
        if rules_content:
            header = "\n" + "="*60 + "\n"
            header += "AUTOMATIC CODING RULES INJECTION\n"
            header += f"Detected technologies: {', '.join(detected_technologies)}\n"
            header += "="*60 + "\n"
            
            return header + "\n".join(rules_content)
        
        return ""
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback estimation: ~4 characters per token
        return len(text) // 4
    
    def get_context_usage_percentage(self) -> float:
        """
        Get current context usage as percentage
        
        Returns:
            Percentage of context used (0-100)
        """
        if self.max_context_tokens == 0:
            return 0.0
        return (self.current_context_tokens / self.max_context_tokens) * 100
    
    def add_to_context_history(self, role: str, content: str, metadata: Dict = None):
        """
        Add message to context history with token tracking
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        tokens = self.count_tokens(content)
        
        message = {
            'role': role,
            'content': content,
            'tokens': tokens,
            'timestamp': os.times().elapsed,
            'metadata': metadata or {}
        }
        
        self.context_history.append(message)
        self.current_context_tokens += tokens
        
        # Check if we need to flush
        if self.get_context_usage_percentage() >= (self.token_flush_threshold * 100):
            console.print(f"[yellow]🔄 Context at {self.get_context_usage_percentage():.1f}% - Auto-flushing...[/yellow]")
            self.flush_context()
    
    def flush_context(self, preserve_recent: bool = True):
        """
        Flush context history while preserving important information
        
        Args:
            preserve_recent: Whether to preserve recent messages
        """
        if not self.context_history:
            return
        
        preserved_messages = []
        preserved_tokens = 0
        
        # Always preserve system messages and coding rules
        if self.preserve_system_context:
            for msg in self.context_history:
                if msg['role'] == 'system' or msg.get('metadata', {}).get('type') == 'coding_rules':
                    preserved_messages.append(msg)
                    preserved_tokens += msg['tokens']
        
        # Preserve recent messages
        if preserve_recent and len(self.context_history) > self.preserve_recent_messages:
            recent_messages = self.context_history[-self.preserve_recent_messages:]
            for msg in recent_messages:
                if msg not in preserved_messages:
                    preserved_messages.append(msg)
                    preserved_tokens += msg['tokens']
        
        # Create summary of flushed content
        flushed_count = len(self.context_history) - len(preserved_messages)
        if flushed_count > 0:
            summary = {
                'role': 'system',
                'content': f"[CONTEXT SUMMARY: {flushed_count} messages flushed to manage token limit]",
                'tokens': self.count_tokens(f"[CONTEXT SUMMARY: {flushed_count} messages flushed to manage token limit]"),
                'timestamp': os.times().elapsed,
                'metadata': {'type': 'flush_summary'}
            }
            preserved_messages.insert(0, summary)
            preserved_tokens += summary['tokens']
        
        # Update context
        old_tokens = self.current_context_tokens
        self.context_history = preserved_messages
        self.current_context_tokens = preserved_tokens
        
        console.print(f"[green]✓ Context flushed: {old_tokens} → {preserved_tokens} tokens ({self.get_context_usage_percentage():.1f}%)[/green]")
    
    def _format_conversation_history(self, max_messages: int = 10) -> str:
        """
        Format recent conversation history for LLM context
        
        Args:
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation history
        """
        if not self.context_history:
            return ""
        
        # Get recent messages (excluding system/rule messages)
        conversation_messages = [
            msg for msg in self.context_history 
            if msg['role'] in ['user', 'assistant'] and 
            msg.get('metadata', {}).get('type') != 'coding_rules'
        ]
        
        if not conversation_messages:
            return ""
        
        # Take last N messages, but ensure we don't exceed token limit
        recent_messages = conversation_messages[-max_messages:]
        
        formatted_parts = []
        for i, msg in enumerate(recent_messages):
            role_label = "🧑 USER" if msg['role'] == 'user' else "🤖 ASSISTANT"
            
            # Limit message content to prevent token overflow
            content = msg['content']
            if len(content) > 500:  # Limit long responses
                content = content[:500] + "... [truncated]"
            
            formatted_parts.append(f"{role_label}: {content}")
        
        return "\n".join(formatted_parts)
    
    def get_context_status(self) -> str:
        """
        Get current context status for display
        
        Returns:
            Formatted context status string
        """
        percentage = self.get_context_usage_percentage()
        messages_count = len(self.context_history)
        
        if percentage < 50:
            color = "green"
        elif percentage < 80:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{percentage:.1f}%[/{color}] ({messages_count} msgs, {self.current_context_tokens:,} tokens)"
        
    def extract_file_references(self, text: str) -> List[str]:
        """
        Extracts file references from text
        
        Args:
            text: Texto para analisar
            
        Returns:
            Lista de arquivos mencionados
        """
        files = set()
        
        for pattern in self.FILE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Limpa o nome do arquivo
                filename = match.strip().strip('"\'`')
                if filename and not filename.startswith('http'):
                    files.add(filename)
        
        return list(files)
    
    def detect_task_type(self, text: str) -> Optional[str]:
        """
        Detecta o tipo de tarefa do prompt
        
        Args:
            text: Texto do prompt
            
        Returns:
            Tipo de tarefa detectada ou None
        """
        text_lower = text.lower()
        
        for pt_word, en_word in self.CODING_KEYWORDS.items():
            if pt_word in text_lower:
                return en_word
                
        # Detecta perguntas
        if any(q in text_lower for q in ['como', 'o que', 'qual', 'quando', 'onde', 'por que']):
            return 'explain'
            
        # Detect code analysis
        if 'analis' in text_lower or 'revis' in text_lower:
            return 'analyze'
            
        return None
    
    def extract_code_context(self, text: str) -> Dict[str, any]:
        """
        Extracts code context from prompt
        
        Args:
            text: Texto do prompt
            
        Returns:
            Dictionary with extracted context
        """
        context = {
            'files': self.extract_file_references(text),
            'task_type': self.detect_task_type(text),
            'language': None,
            'framework': None,
            'has_code_block': '```' in text
        }
        
        # Detecta linguagem mencionada
        languages = {
            'python': ['python', 'py', 'django', 'flask'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
            'typescript': ['typescript', 'ts'],
            'java': ['java', 'spring', 'springboot'],
            'csharp': ['c#', 'csharp', '.net', 'dotnet'],
            'go': ['go', 'golang'],
            'rust': ['rust', 'cargo'],
            'cpp': ['c++', 'cpp'],
            'c': ['c ', ' c ', 'linguagem c'],
            'ruby': ['ruby', 'rails'],
            'php': ['php', 'laravel', 'symfony'],
            'swift': ['swift', 'ios'],
            'kotlin': ['kotlin', 'android']
        }
        
        text_lower = text.lower()
        for lang, keywords in languages.items():
            if any(kw in text_lower for kw in keywords):
                context['language'] = lang
                break
        
        # Detecta framework
        frameworks = {
            'django': 'Django',
            'flask': 'Flask',
            'fastapi': 'FastAPI',
            'react': 'React',
            'vue': 'Vue',
            'angular': 'Angular',
            'next': 'Next.js',
            'express': 'Express',
            'spring': 'Spring',
            'laravel': 'Laravel',
            'rails': 'Rails'
        }
        
        for fw_key, fw_name in frameworks.items():
            if fw_key in text_lower:
                context['framework'] = fw_name
                break
        
        return context
    
    def _get_file_structure(self, directory: str, max_depth: int = 2) -> str:
        """
        Gets file structure including parent directory
        
        Args:
            directory: Directory to list
            max_depth: Maximum search depth
            
        Returns:
            String formatada com a estrutura de arquivos
        """
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return ""
            
            structure = []
            file_count = 0
            dir_count = 0
            
            # Add parent directory information
            parent_dir = dir_path.parent
            if parent_dir != dir_path:  # Not at root
                structure.append(f"[Parent Directory: {parent_dir}]")
                
                # List some important files in parent directory
                parent_files = []
                for item in parent_dir.iterdir():
                    if item.is_file() and not item.name.startswith('.'):
                        if item.suffix in ['.py', '.js', '.json', '.yml', '.yaml', '.toml', '.md']:
                            parent_files.append(f"  ../{item.name}")
                            if len(parent_files) >= 3:  # Limita a 3 arquivos do pai
                                break
                
                if parent_files:
                    structure.append("Parent directory files:")
                    structure.extend(parent_files)
                    structure.append("")  # Linha em branco
            
            # Lista arquivos importantes na raiz
            structure.append(f"[Current Directory: {dir_path}]")
            root_files = []
            subdirs = []
            
            for item in dir_path.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    # Ignore system and temporary files
                    if item.suffix in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rb', '.php', 
                                      '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.md', '.txt']:
                        root_files.append(f"  - {item.name}")
                        file_count += 1
                elif item.is_dir() and not item.name.startswith('.') and item.name not in ['__pycache__', 'node_modules', 'venv', '.git', 'dist', 'build']:
                    subdirs.append(item)
                    dir_count += 1
            
            # Adiciona arquivos da raiz
            if root_files:
                structure.extend(root_files[:10])  # Limita a 10 arquivos da raiz
                if len(root_files) > 10:
                    structure.append(f"  ... ({len(root_files) - 10} more files)")
            
            # List subdirectories with some files
            for subdir in subdirs[:5]:  # Limit to 5 subdirectories
                subdir_files = []
                sub_file_count = 0
                
                for subitem in subdir.iterdir():
                    if subitem.is_file() and not subitem.name.startswith('.'):
                        if subitem.suffix in ['.py', '.js', '.html', '.css', '.json']:
                            subdir_files.append(f"    - {subitem.name}")
                            sub_file_count += 1
                            file_count += 1
                            if len(subdir_files) >= 3:  # Limita a 3 arquivos por subdir
                                break
                
                structure.append(f"  - {subdir.name}/ ({sub_file_count} files)")
                if subdir_files:
                    structure.extend(subdir_files)
            
            if len(subdirs) > 5:
                structure.append(f"  ... ({len(subdirs) - 5} more directories)")
            
            if structure:
                header = f"\nProject structure: {file_count} files in {dir_count + 1} directories"
                return "\n".join(structure) + "\n" + header
            else:
                return "Empty directory"
                
        except Exception:
            return ""
    
    def enhance_prompt(self, original_prompt: str, current_dir: str = None, os_info: str = None) -> str:
        """
        Enhances a prompt by adding context and structure
        
        Args:
            original_prompt: User's original prompt
            current_dir: Current directory (optional)
            os_info: Operating system information (optional)
            
        Returns:
            Enhanced prompt
        """
        # Extrai contexto
        context = self.extract_code_context(original_prompt)
        
        # Build enhanced prompt
        enhanced_parts = []
        
        # Adiciona contexto de sistema operacional
        if os_info:
            enhanced_parts.append(f"[Operating System: {os_info}]")
        
        # Add directory context with path analysis
        if current_dir:
            enhanced_parts.append(f"[Working Directory: {current_dir}]")
            
            # Analyze path components for better context
            path_components = Path(current_dir).parts
            if len(path_components) > 0:
                enhanced_parts.append(f"[Current Path Components: {' → '.join(path_components[-3:])}]")
                
                # Detect if we're in a project subdirectory
                project_indicators = ['examples', 'projects', 'src', 'app', 'lib', 'public', 'static']
                current_location = ""
                
                for component in path_components:
                    if component.lower() in project_indicators:
                        current_location = f"You are inside a '{component}' directory"
                        break
                
                if current_location:
                    enhanced_parts.append(f"[CONTEXT: {current_location} - DO NOT create another '{component}' folder]")
            
            # Add existing file structure
            file_structure = self._get_file_structure(current_dir)
            if file_structure:
                enhanced_parts.append(f"\n[Existing File Structure:]")
                enhanced_parts.append(file_structure)
                enhanced_parts.append("\n[CRITICAL: DO NOT recreate existing directories or files!]")
                enhanced_parts.append("[CRITICAL: Choose a UNIQUE project name that doesn't exist in the path!]")
        
        # Add file context and complete content if they exist
        if context['files']:
            files_str = ', '.join(context['files'])
            enhanced_parts.append(f"[Files Referenced: {files_str}]")
            
            # Read and include complete content of existing files
            for filename in context['files']:
                try:
                    # Try to resolve file path
                    if current_dir:
                        file_path = Path(current_dir) / filename
                        if not file_path.exists():
                            # Try with absolute path
                            file_path = Path(filename)
                        
                        if file_path.exists() and file_path.is_file():
                            # Read file content
                            try:
                                content = file_path.read_text(encoding='utf-8')
                                enhanced_parts.append(f"\n[EXISTING FILE CONTENT - {filename}]:")
                                enhanced_parts.append("```")
                                enhanced_parts.append(content)
                                enhanced_parts.append("```")
                                enhanced_parts.append(f"[END OF {filename}]")
                                enhanced_parts.append("\n⚠️ IMPORTANT: When editing this file, include the COMPLETE updated content!")
                            except Exception as e:
                                # If can't read, just continue
                                pass
                except Exception:
                    # Ignora erros ao tentar ler arquivos
                    pass
        
        # Adiciona contexto de linguagem/framework
        if context['language']:
            lang_info = f"[Language: {context['language']}"
            if context['framework']:
                lang_info += f", Framework: {context['framework']}"
            lang_info += "]"
            enhanced_parts.append(lang_info)
        
        # Adiciona tag de tarefa se detectada
        if context['task_type']:
            enhanced_parts.append(f"\n<task>\n{original_prompt}\n</task>")
            
            # Add specific instructions by task type
            if context['task_type'] == 'create':
                enhanced_parts.append("\n[Instructions: Create complete, working code with proper error handling and comments]")
            elif context['task_type'] == 'fix':
                enhanced_parts.append("\n[Instructions: Identify the issue, explain the fix, and provide corrected code]")
            elif context['task_type'] == 'explain':
                enhanced_parts.append("\n[Instructions: Provide clear, detailed explanation with examples]")
            elif context['task_type'] == 'optimize':
                enhanced_parts.append("\n[Instructions: Analyze performance issues and provide optimized solution]")
        else:
            # Prompt sem tag de tarefa
            enhanced_parts.append(f"\n{original_prompt}")
        
        # Detect technologies and inject coding rules
        detected_technologies = self.detect_technologies(original_prompt)
        if detected_technologies:
            coding_rules = self.get_relevant_coding_rules(detected_technologies)
            if coding_rules:
                enhanced_parts.append(coding_rules)
                # Add to context with metadata
                self.add_to_context_history("system", coding_rules, 
                                          {"type": "coding_rules", "technologies": list(detected_technologies)})
        
        # Add clear instructions about response structuring
        enhanced_parts.append("""
[RESPONSE STRUCTURE - MANDATORY TAGS]
ALWAYS use these tags to structure your response when applicable:

1. For shell/terminal commands (executed automatically):
   <actions>
   mkdir project
   cd project
   pip install flask
   </actions>
   
   IMPORTANT: Only put ACTUAL COMMANDS inside <actions>, not descriptions!
   ❌ WRONG: <actions>Create a folder to hold templates\nmkdir templates</actions>
   ✅ RIGHT: <actions>mkdir templates</actions>

2. For reading/examining existing files (executed automatically):
   <read>
   cat app.py
   ls -la
   dir
   </read>
   
   IMPORTANT: Only put ACTUAL COMMANDS inside <read>, not descriptions!
   ❌ WRONG: <read>Let's check the contents\ncat app.py</read>
   ✅ RIGHT: <read>cat app.py</read>

3. For creating or editing files (files created/updated automatically):
   <code filename="app.py">
   # ALWAYS INCLUDE THE COMPLETE FILE CONTENT!
   # NEVER output just the changed lines!
   from flask import Flask
   
   app = Flask(__name__)
   
   @app.route('/')
   def hello():
       return 'Hello World!'
   
   if __name__ == '__main__':
       app.run(debug=True)
   </code>

4. For explanatory text: use normal text (no tags)

CRITICAL RULES:
✅ ALWAYS use <code filename="..."> for ANY file creation or editing
✅ ALWAYS include the COMPLETE FILE CONTENT in <code> tags
✅ ALWAYS use <actions> for commands like pip install, mkdir, etc
✅ ALWAYS use <read> to examine existing files
❌ NEVER output just the changed lines - output the ENTIRE file
❌ NEVER use ``` blocks for files that should be created
❌ NEVER create files without proper filename
❌ NEVER mix descriptions with commands inside tags
⚠️  Use ``` ONLY for inline examples or code snippets (not for file creation)

FILE EDITING RULES:
⚠️  CRITICAL: When editing existing files, ALWAYS include the COMPLETE file content!
✅ Include ALL imports, ALL functions, ALL classes - the ENTIRE file
✅ Even if changing just one line, output the WHOLE file
❌ NEVER output partial files or just the modified sections
❌ NEVER use "..." or "# rest of the code remains the same"

DIRECTORY STRUCTURE RULES:
⚠️  CRITICAL: NEVER recreate directories that already exist in the current path!
⚠️  CRITICAL: If you see 'examples' in the path, DON'T create another 'examples' folder!
⚠️  CRITICAL: Choose UNIQUE project names (e.g., 'my-api-project', 'user-auth-system')!
✅ Create simple, flat structures when possible
✅ Only create necessary directories (e.g., templates/ for Flask)
✅ ALWAYS check [Existing File Structure] before creating files
✅ EDIT existing files instead of creating new ones with similar names
❌ AVOID nested directories with same name (project/project/project)
❌ AVOID creating unnecessary intermediate directories
❌ NEVER create directories from descriptive text
❌ NEVER create duplicate files (e.g., app.py if it already exists)
❌ NEVER put Python files inside templates/ directory
❌ NEVER create 'examples', 'public', 'src' folders if they already exist in the path!

FILE HANDLING RULES:
✅ If app.py exists, EDIT it - don't create app2.py or templates/app.py
✅ If templates/index.html exists, EDIT it - don't create templates/templates/index.html
✅ Use <code filename="existing_file.py"> to edit existing files
❌ Don't create newfile.py, code.py, a_1.txt, a_2.txt, or other generic names
❌ NEVER create files with generic names like a_1.txt, temp.txt, test.txt
❌ If you can't determine a good filename, use descriptive names based on content

EXAMPLE RESPONSE FORMAT:
First, I'll install Flask and create the project structure:

<actions>
pip install flask
mkdir unique-flask-api
cd unique-flask-api
</actions>

Now I'll create the main application file:

<code filename="app.py">
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Hello Flask!</h1>'

if __name__ == '__main__':
    app.run(debug=True)
</code>

This creates a basic Flask application...
""")
        
        # Add instruction about OS-specific commands
        if os_info:
            if 'Windows' in os_info:
                enhanced_parts.append("\n[OS Commands: Use Windows commands like dir, type, copy, move, del, cls, where, etc.]")
            else:
                enhanced_parts.append("\n[OS Commands: Use Unix commands like ls, cat, cp, mv, rm, clear, which, etc.]")
        
        # Add conversation history for memory (exclude current prompt)
        if self.context_history:
            conversation_context = self._format_conversation_history()
            if conversation_context:
                enhanced_parts.append("\n[CONVERSATION HISTORY]")
                enhanced_parts.append("Previous conversation to maintain context:")
                enhanced_parts.append(conversation_context)
                enhanced_parts.append("[/CONVERSATION HISTORY]\n")
            
            # Also add recent files for additional context
        recent_files = set()
        # Use a separate history for old-style context tracking to avoid conflicts
        if hasattr(self, '_old_context_history'):
            for hist in self._old_context_history[-3:]:  # Last 3 interactions
                recent_files.update(hist.get('files', []))
        
        if recent_files:
            enhanced_parts.append(f"[Recent Context: Previously worked with {', '.join(recent_files)}]")
        
        # Save context to separate history to avoid conflicts with message-based context
        if not hasattr(self, '_old_context_history'):
            self._old_context_history = []
        self._old_context_history.append(context)
        if len(self._old_context_history) > 10:
            self._old_context_history.pop(0)
        
        return '\n'.join(enhanced_parts)
    
    def create_enhance_code_prompt(self, original_prompt: str, current_dir: str = None) -> str:
        """
        Creates a specific prompt to improve existing code
        
        Args:
            original_prompt: User's original prompt
            current_dir: Current directory
            
        Returns:
            Specific prompt for enhancement
        """
        enhanced_parts = []
        
        # Header with specific instructions
        enhanced_parts.append("🔧 CODE ENHANCEMENT REQUEST")
        enhanced_parts.append("=" * 60)
        
        # Directory and file context
        if current_dir:
            enhanced_parts.append(f"[Working Directory: {current_dir}]")
            
            # Adiciona estrutura de arquivos
            file_structure = self._get_file_structure(current_dir)
            if file_structure:
                enhanced_parts.append(f"\n[Existing File Structure:]")
                enhanced_parts.append(file_structure)
        
        # Specific instructions for enhancement
        enhanced_parts.append("\n[ENHANCEMENT INSTRUCTIONS:]")
        enhanced_parts.append("""
✅ REQUIRED ACTIONS:
1. ADD MORE DETAILS: Expand functionality, add error handling, improve documentation
2. FIX BUGS AND LINTING: Check for syntax errors, type hints, code style issues
3. IMPROVE CODE QUALITY: Better variable names, proper structure, performance optimizations
4. ADD MISSING FEATURES: Complete partial implementations, add edge case handling

❌ STRICT RULES:
- DO NOT create new files - ONLY edit existing ones
- DO NOT change the core functionality unless fixing bugs
- DO NOT remove existing features
- ALWAYS use <code filename="existing_file.py"> for edits

🎯 FOCUS AREAS:
- Error handling and validation
- Code documentation and comments
- Type hints and proper typing
- Performance optimizations
- Security considerations
- Test coverage suggestions

📝 OUTPUT FORMAT:
1. Analysis of current code issues
2. List of improvements to be made
3. Enhanced code using <code filename="..."> tags
4. Summary of changes made

⚠️ IMPORTANT: Check [Existing File Structure] and ONLY edit files that already exist!
""")
        
        # Add original prompt with interpretation
        enhanced_parts.append(f"\n<enhance_request>\n{original_prompt}\n</enhance_request>")
        
        # Add specific interpretation of the request
        enhanced_parts.append("""
[TASK INTERPRETATION]
Based on the enhancement request above, you need to:
1. Transform the existing generic pages into a professional SAAS landing page
2. Update ALL text, styling, and functionality to match the SAAS theme
3. Make it look modern, professional, and conversion-focused
4. Include typical SAAS elements: hero section, features, pricing, CTA buttons, etc.
""")
        
        # Add final MORE DIRECT instructions
        enhanced_parts.append("")
        
        return "\n".join(enhanced_parts)
    
    def detect_error_type(self, text: str) -> Optional[Dict[str, any]]:
        """
        Detects if the input text contains error messages and identifies the error type
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with error information or None if no error detected
        """
        text_lower = text.lower()
        
        # Check for various error patterns
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    # Extract specific error details
                    error_info = {
                        'type': error_type,
                        'pattern_matched': pattern,
                        'raw_text': text
                    }
                    
                    # Extract file paths mentioned in the error
                    file_matches = []
                    for file_pattern in self.FILE_PATTERNS:
                        matches = re.findall(file_pattern, text)
                        file_matches.extend(matches)
                    
                    # Extract specific details based on error type
                    if error_type == 'webpack':
                        # Extract module path and file that failed
                        module_match = re.search(r"Can't resolve '([^']+)'", text)
                        file_match = re.search(r"ERROR in ([^\s]+)", text)
                        
                        error_info.update({
                            'missing_module': module_match.group(1) if module_match else None,
                            'failing_file': file_match.group(1) if file_match else None,
                            'files_mentioned': file_matches
                        })
                    
                    elif error_type == 'import':
                        # Extract module name
                        module_match = re.search(r"module named '([^']+)'", text, re.IGNORECASE)
                        error_info.update({
                            'missing_module': module_match.group(1) if module_match else None,
                            'files_mentioned': file_matches
                        })
                    
                    return error_info
        
        return None
    
    def create_error_fix_prompt(self, original_prompt: str, error_info: Dict[str, any], current_dir: str = None) -> str:
        """
        Creates an enhanced prompt specifically designed to help fix the detected error
        
        Args:
            original_prompt: Original user input (error message)
            error_info: Error information from detect_error_type
            current_dir: Current working directory
            
        Returns:
            Enhanced prompt for fixing the error
        """
        error_type = error_info['type']
        
        enhanced_parts = []
        enhanced_parts.append("🔧 ERROR ANALYSIS & FIX REQUEST")
        enhanced_parts.append("="*50)
        
        # Add current directory context
        if current_dir:
            enhanced_parts.append(f"\n📂 CURRENT DIRECTORY: {current_dir}")
            
            # Try to gather file structure around the error
            current_path = Path(current_dir)
            if current_path.exists():
                enhanced_parts.append("\n📋 CURRENT DIRECTORY STRUCTURE:")
                try:
                    # List relevant files (limit to avoid too much output)
                    files = []
                    for item in current_path.rglob("*"):
                        if item.is_file() and not any(ignore in str(item) for ignore in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                            relative_path = item.relative_to(current_path)
                            files.append(str(relative_path))
                            if len(files) >= 20:  # Limit to first 20 files
                                break
                    
                    for f in sorted(files):
                        enhanced_parts.append(f"  - {f}")
                    
                    if len(files) >= 20:
                        enhanced_parts.append("  ... (showing first 20 files)")
                        
                except Exception as e:
                    enhanced_parts.append(f"  (Could not list files: {e})")
        
        enhanced_parts.append(f"\n🚨 ERROR DETECTED: {error_type.upper()} ERROR")
        enhanced_parts.append(f"Raw Error Message:")
        enhanced_parts.append("```")
        enhanced_parts.append(original_prompt)
        enhanced_parts.append("```")
        
        # Add specific guidance based on error type
        if error_type == 'webpack':
            enhanced_parts.append("\n🎯 WEBPACK/MODULE ERROR ANALYSIS:")
            enhanced_parts.append("This appears to be a webpack module resolution error.")
            
            if error_info.get('missing_module'):
                enhanced_parts.append(f"- Missing module: '{error_info['missing_module']}'")
            if error_info.get('failing_file'):
                enhanced_parts.append(f"- File with error: '{error_info['failing_file']}'")
            
            enhanced_parts.append("\n✅ COMMON SOLUTIONS:")
            enhanced_parts.append("1. Check if the imported file/module actually exists at the specified path")
            enhanced_parts.append("2. Verify the import path is correct (relative vs absolute)")
            enhanced_parts.append("3. Check for typos in file names or import statements")
            enhanced_parts.append("4. Ensure file extensions are correct (.js, .ts, .tsx, etc.)")
            enhanced_parts.append("5. Check if the module is properly exported from the target file")
            enhanced_parts.append("6. For npm packages, verify they are installed (npm ls)")
            
        elif error_type == 'import':
            enhanced_parts.append("\n🎯 IMPORT ERROR ANALYSIS:")
            enhanced_parts.append("This appears to be a Python import error.")
            
            if error_info.get('missing_module'):
                enhanced_parts.append(f"- Missing module: '{error_info['missing_module']}'")
            
            enhanced_parts.append("\n✅ COMMON SOLUTIONS:")
            enhanced_parts.append("1. Install the missing package: pip install <package_name>")
            enhanced_parts.append("2. Check if the module name is spelled correctly")
            enhanced_parts.append("3. Verify the module is in your Python path")
            enhanced_parts.append("4. Check if you're in the correct virtual environment")
            enhanced_parts.append("5. For local modules, check file paths and __init__.py files")
        
        elif error_type == 'syntax':
            enhanced_parts.append("\n🎯 SYNTAX ERROR ANALYSIS:")
            enhanced_parts.append("This appears to be a syntax error.")
            enhanced_parts.append("\n✅ COMMON SOLUTIONS:")
            enhanced_parts.append("1. Check for missing brackets, parentheses, or quotes")
            enhanced_parts.append("2. Verify proper indentation (especially in Python)")
            enhanced_parts.append("3. Look for typos in keywords or variable names")
            enhanced_parts.append("4. Check for incorrect usage of language constructs")
        
        enhanced_parts.append("\n🔍 DEBUGGING INSTRUCTIONS:")
        enhanced_parts.append("Please analyze the error above and:")
        enhanced_parts.append("1. Identify the root cause of the problem")
        enhanced_parts.append("2. Examine the current file structure (provided above)")
        enhanced_parts.append("3. Provide step-by-step solution to fix this error")
        enhanced_parts.append("4. If files need to be created or modified, use appropriate <code filename=\"...\"> or <actions> tags")
        enhanced_parts.append("5. Explain why this error occurred and how to prevent it in the future")
        
        enhanced_parts.append("\n⚠️ IMPORTANT CONSTRAINTS:")
        enhanced_parts.append("- Only create/modify files that are actually needed to fix this error")
        enhanced_parts.append("- Maintain existing code structure and don't break working functionality")
        enhanced_parts.append("- Provide clear explanations for each step taken")
        enhanced_parts.append("- Test your solution logic before proposing changes")
        
        return "\n".join(enhanced_parts)
    
    def format_response_context(self, response: str, context: Dict) -> str:
        """
        Formata a resposta com contexto adicional
        
        Args:
            response: Resposta do modelo
            context: Contexto da conversa
            
        Returns:
            Resposta formatada
        """
        # For now, return response without modification
        # Can be expanded to add metadata or formatting
        return response