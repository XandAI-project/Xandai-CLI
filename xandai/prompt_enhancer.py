"""
Module to enhance prompts with coding context
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console

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
    
    def __init__(self):
        """Initializes the prompt enhancer"""
        self.context_history: List[Dict] = []
        
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
        
        # Add directory context
        if current_dir:
            enhanced_parts.append(f"[Working Directory: {current_dir}]")
            
            # Add existing file structure
            file_structure = self._get_file_structure(current_dir)
            if file_structure:
                enhanced_parts.append(f"\n[Existing File Structure:]")
                enhanced_parts.append(file_structure)
                enhanced_parts.append("\n[IMPORTANT: Edit existing files instead of creating duplicates!]")
        
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
✅ Create simple, flat structures when possible
✅ Only create necessary directories (e.g., templates/ for Flask)
✅ ALWAYS check [Existing File Structure] before creating files
✅ EDIT existing files instead of creating new ones with similar names
❌ AVOID nested directories with same name (project/project/project)
❌ AVOID creating unnecessary intermediate directories
❌ NEVER create directories from descriptive text
❌ NEVER create duplicate files (e.g., app.py if it already exists)
❌ NEVER put Python files inside templates/ directory

FILE HANDLING RULES:
✅ If app.py exists, EDIT it - don't create app2.py or templates/app.py
✅ If templates/index.html exists, EDIT it - don't create templates/templates/index.html
✅ Use <code filename="existing_file.py"> to edit existing files
❌ Don't create newfile.py, code.py, or other generic names

EXAMPLE RESPONSE FORMAT:
First, I'll install Flask and create the project structure:

<actions>
pip install flask
mkdir flask_project
cd flask_project
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
        
        # Add historical context if relevant
        if self.context_history:
            recent_files = set()
            for hist in self.context_history[-3:]:  # Last 3 interactions
                recent_files.update(hist.get('files', []))
            
            if recent_files:
                enhanced_parts.append(f"\n[Recent Context: Previously worked with {', '.join(recent_files)}]")
        
        # Save context to history
        self.context_history.append(context)
        if len(self.context_history) > 10:
            self.context_history.pop(0)
        
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
        enhanced_parts.append("""
[CRITICAL - YOU MUST FOLLOW THIS EXACT FORMAT]

Step 1: ANALYZE the existing files and identify what needs improvement

Step 2: EDIT each file using <code> tags (THIS IS MANDATORY):

<code filename="index.html">
PUT THE COMPLETE ENHANCED FILE CONTENT HERE
WITH ALL YOUR IMPROVEMENTS
</code>

<code filename="styles.css">
PUT THE COMPLETE ENHANCED CSS HERE
</code>

<code filename="app.py">
PUT THE COMPLETE ENHANCED PYTHON CODE HERE
</code>

Step 3: SUMMARY of what you changed

⚠️ CRITICAL RULES:
- YOU MUST USE <code filename="..."> tags for ALL file edits
- PUT THE COMPLETE FILE CONTENT inside the tags
- DO NOT create new files
- DO NOT just read files without editing
- YOU MUST ACTUALLY EDIT AND IMPROVE THE FILES

IF YOU DON'T USE <code> TAGS, THE ENHANCEMENT WILL FAIL!

EXAMPLE OF CORRECT RESPONSE:

Step 1: Analysis
I found that index.html is a generic template and needs to be transformed into a SAAS landing page...

Step 2: Enhanced Files

<code filename="index.html">
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>XANDSAAS - Your Solution</title>
    <!-- Complete enhanced HTML here -->
</head>
<body>
    <!-- Complete SAAS landing page HTML -->
</body>
</html>
</code>

<code filename="styles.css">
/* Complete enhanced CSS for SAAS landing page */
</code>

Step 3: Summary
I transformed the generic page into a professional SAAS landing page with...
""")
        
        return '\n'.join(enhanced_parts)
    
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