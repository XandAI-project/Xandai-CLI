"""
Prompt Management Module
Handles prompt analysis, enhancement, and instruction generation
"""

from typing import Dict, Any, Tuple
from rich.console import Console

console = Console()


class PromptManager:
    """Manages prompt analysis, enhancement, and instruction generation"""
    
    def __init__(self, api, selected_model_getter, tag_processor, read_levels_manager):
        self.api = api
        self.selected_model_getter = selected_model_getter  # Function to get current model
        self.tag_processor = tag_processor
        self.read_levels_manager = read_levels_manager
    
    def prompt_needs_special_tags(self, prompt: str) -> bool:
        """
        Detecta se um prompt precisa de instruções de tags especiais
        
        Args:
            prompt: Prompt do usuário
            
        Returns:
            True se o prompt indica criação de código/arquivos ou comandos
        """
        prompt_lower = prompt.lower()
        
        # Keywords que indicam necessidade de tags especiais
        code_creation_keywords = [
            'create', 'make', 'write', 'build', 'implement', 'generate',
            'file', 'script', 'code', 'function', 'class', 'app',
            'project', 'website', 'api', 'database', 'html', 'css', 'js',
            'python', 'flask', 'django', 'react', 'node'
        ]
        
        command_keywords = [
            'install', 'run', 'execute', 'setup', 'configure', 'mkdir',
            'cd', 'pip', 'npm', 'git', 'docker', 'start', 'stop'
        ]
        
        return (
            any(keyword in prompt_lower for keyword in code_creation_keywords) or
            any(keyword in prompt_lower for keyword in command_keywords) or
            'app.py' in prompt_lower or
            'requirements.txt' in prompt_lower or
            'package.json' in prompt_lower
        )
    
    def get_basic_tag_instructions(self) -> str:
        """
        Retorna instruções básicas sobre tags especiais
        
        Returns:
            String com instruções básicas sobre tags
        """
        return """

[MANDATORY TAGS FOR ACTIONS - CLEAN CODE ONLY]

⚡ EFFICIENCY TIP: Process multiple files in ONE response! Don't stop after editing just one file.

1. For shell/terminal commands:
   ✅ RIGHT: <actions>mkdir my-project</actions>
   ✅ RIGHT: <actions>pip install flask</actions>
   ❌ WRONG: ```bash
             mkdir my-project
             ```
   ❌ WRONG: Just describing: "Create a folder called my-project"

2. For editing existing files:
   ✅ RIGHT: <code edit filename="app.py">
             from flask import Flask
             app = Flask(__name__)
             if __name__ == '__main__':
                 app.run(debug=True)
             </code>
   ❌ WRONG: <code filename="app.py"> (missing edit/create)
   ❌ WRONG: Adding explanations at end of file
   
3. For creating new files:
   🚨 CRITICAL: ALWAYS check if file exists first!
   ✅ RIGHT: <read>ls app.py 2>/dev/null || dir app.py 2>nul</read>
             Then based on result:
             - If file EXISTS: <code edit filename="app.py">...</code>
             - If file NOT EXISTS: <code create filename="app.py">...</code>
   ✅ RIGHT: <code create filename="config.py">
             DEBUG = True
             SECRET_KEY = 'dev-key'
             </code>
   ❌ WRONG: <code filename="config.py"> (missing edit/create)
   ❌ WRONG: Creating files without checking existence first

4. For reading existing files:
   ✅ RIGHT: <read>cat app.py</read>
   ✅ RIGHT: <read>ls -la</read>
   ❌ WRONG: ```bash
             cat app.py
             ```
   ❌ WRONG: Just describing: "Check the contents of app.py"

🚀 MULTIPLE OPERATIONS EXAMPLES:

✅ EXCELLENT - Check existence first, then process multiple files in ONE response:
   <read>
   ls app.py config.py templates/base.html 2>/dev/null || dir app.py config.py templates\base.html 2>nul
   cat app.py
   cat config.py
   ls templates/
   </read>
   
   # Based on existence check results:
   <code edit filename="app.py">
   # Updated app.py content here (file existed)
   </code>
   
   <code edit filename="config.py">
   # Updated config.py content here (file existed)
   </code>
   
   <code create filename="templates/base.html">
   # New template content here (file didn't exist)
   </code>

❌ INEFFICIENT - Don't stop after just one operation:
   "I'll start by reading app.py and then wait for further instructions..."

❌ DANGEROUS - Don't assume file existence:
   <code create filename="app.py">  # BAD: Might overwrite existing file!

CRITICAL RULES:
- ALWAYS use <actions> for commands (mkdir, pip, npm, git, etc.)
- ALWAYS use <code edit filename="..."> for editing existing files
- ALWAYS use <code create filename="..."> for creating new files
- 🚨 ALWAYS check if file exists before deciding edit vs create:
  * Use <read>ls filename.ext 2>/dev/null || dir filename.ext 2>nul</read> first
  * If file exists → use <code edit filename="...">
  * If file doesn't exist → use <code create filename="...">
- ALWAYS use <read> for examining files
- NEVER use ``` blocks for files that should be created/edited
- NEVER just describe actions - use the tags!
- NEVER assume file existence - always verify first
- The old <code filename="..."> format is deprecated - always specify edit or create
- 🚀 BATCH OPERATIONS: Do multiple file operations in ONE response for efficiency

🚫 CLEAN CODE FORMATTING RULES:
- Code blocks must contain ONLY the file content - no explanations or summaries
- NEVER add markdown blocks (```) inside source files
- NEVER add implementation descriptions at the end of files
- Keep files in their proper format: HTML=HTML, JS=JS, CSS=CSS, not markdown wrapping
- Do not describe what you are doing inside file content - just provide clean, executable code

💡 BEST PRACTICES:
- Always process as many related operations as possible in ONE response
- Don't stop after creating/editing just one file when the task clearly needs multiple files
- Group related operations together (all reading first, then all file operations)
- When in doubt, read relevant files first to understand the current structure
"""
    
    def should_add_read_first_instruction(self, prompt: str) -> bool:
        """
        Determines if we should add read-first instruction based on prompt analysis
        
        Args:
            prompt: The prompt to analyze
            
        Returns:
            bool: True if should add read-first instruction
        """
        if not prompt:
            return False
        
        prompt_lower = prompt.lower()
        
        # Keywords that indicate need to read files first
        read_indicators = [
            'fix', 'debug', 'error', 'bug', 'issue', 'problem',
            'update', 'modify', 'change', 'edit', 'refactor',
            'analyze', 'review', 'check', 'examine', 'inspect',
            'improve', 'optimize', 'enhance', 'adjust',
            'add to', 'remove from', 'delete from',
            'current', 'existing', 'this file', 'this code',
            'in the', 'from the', 'to the'
        ]
        
        # Check if prompt contains read indicators
        has_read_indicators = any(indicator in prompt_lower for indicator in read_indicators)
        
        # Keywords that indicate creating new things (might not need reading)
        create_indicators = [
            'create new', 'build new', 'generate new', 'make a new',
            'start from scratch', 'from scratch', 'new project',
            'new app', 'new application'
        ]
        
        # Check if prompt is about creating new things
        has_create_indicators = any(indicator in prompt_lower for indicator in create_indicators)
        
        # If it's clearly about creating new things, might not need reading
        if has_create_indicators and not has_read_indicators:
            return False
        
        # If it has read indicators, definitely need reading
        if has_read_indicators:
            return True
        
        # For ambiguous cases in edit mode, err on the side of reading
        return True
    
    def add_read_first_instruction(self, prompt: str, force_read: bool = False) -> Tuple[str, bool]:
        """
        Adds instruction to always start with <read> except when there's already file context
        """
        return self.tag_processor.add_read_first_instruction(prompt, self.read_levels_manager, force_read)
    
    def get_suggested_read_commands(self, prompt: str) -> str:
        """
        Sugere comandos de leitura baseados no contexto do prompt usando sistema de níveis
        """
        return self.read_levels_manager.get_suggested_read_commands(prompt)
    
    def determine_read_level(self, prompt_lower: str) -> int:
        """
        Determina qual nível de read é necessário baseado no contexto
        """
        return self.read_levels_manager.determine_read_level(prompt_lower)
    
    def generate_mode_instructions(self, mode_decision: Dict[str, Any]) -> str:
        """
        Gera instruções específicas baseadas no modo detectado (edit vs create)
        
        Args:
            mode_decision: Resultado da detecção automática de modo
            
        Returns:
            String com instruções específicas para o modo
        """
        mode = mode_decision['mode']
        confidence = mode_decision['confidence']
        project_info = mode_decision['project_info']
        
        if mode == 'edit' and confidence > 30:
            instructions = [
                "\n## EDIT MODE DETECTED",
                "🚨 CRITICAL: The user wants to UPDATE/MODIFY an existing project, NOT create a new one!",
                "",
                "**PRESERVATION-FIRST Edit Mode Instructions:**",
                "- ALWAYS read existing files first using <read> tags (multiple files in ONE <read> block)",
                "- PRESERVE ALL existing code: functions, endpoints, classes, variables, imports",
                "- NEVER delete or remove existing functionality unless explicitly requested",
                "- Make ONLY the specific changes requested - keep everything else identical",
                "- When editing files, provide the COMPLETE file including all existing code",
                "- Use <code edit filename=\"...\"> for modifying existing files (FULL file content required)",
                "- Use <code create filename=\"...\"> ONLY for completely new files",
                "- 🚀 EFFICIENCY: Process multiple files in ONE response - don't stop after editing just one",
                "- Mark new additions with comments like // NEW: or // ADDED: for clarity",
                "- Maintain consistency with existing patterns and conventions",
                "- If you find config files (package.json, requirements.txt), UPDATE instead of creating new ones",
                "",
                "**CLEAN CODE FORMATTING:**",
                "- Provide ONLY executable code in <code> blocks - NO explanations inside files",
                "- NEVER add markdown blocks (```) inside source files",
                "- NEVER add implementation summaries or feature descriptions at end of files",
                "- Keep files in their proper format (HTML=HTML, JS=JS, CSS=CSS, not markdown)",
                "- Code blocks must contain ONLY the file content, no external commentary",
                "",
                "**ENDPOINT/API PRESERVATION:**",
                "- Keep ALL existing API endpoints, routes, and handlers",
                "- When adding new endpoints, integrate them without affecting existing ones",
                "- Preserve all existing middleware, error handlers, and utilities",
                "- Maintain existing database schemas, models, and connections",
                ""
            ]
            
            # Add information about detected project types
            if project_info['types']:
                instructions.append("**DETECTED PROJECT TYPES:**")
                for project_type in project_info['types'][:3]:  # Top 3 types
                    type_name = project_type['type']
                    type_conf = project_type['confidence']
                    instructions.append(f"- {type_name.upper()}: {type_conf}% confidence")
                    if project_type['indicators']:
                        indicators = ", ".join(project_type['indicators'][:5])  # First 5 indicators
                        instructions.append(f"  Files: {indicators}")
                instructions.append("")
            
            return "\n".join(instructions)
        
        elif mode == 'create' and confidence > 30:
            instructions = [
                "\n## CREATE MODE DETECTED",
                "🆕 The user wants to CREATE a new project or component from scratch!",
                "",
                "**NEW PROJECT Creation Mode Instructions:**",
                "- Focus on creating new, well-structured code and files",
                "- Use modern best practices and clean architecture",
                "- Create comprehensive project structure with proper organization",
                "- Include necessary configuration files (package.json, requirements.txt, etc.)",
                "- Use <code create filename=\"...\"> for all new files",
                "- Use <actions> for setup commands (mkdir, npm init, pip install, etc.)",
                "- 🚀 EFFICIENCY: Create multiple files in ONE response for complete functionality",
                "- Follow established conventions for the detected technology stack",
                "- Include basic documentation and setup instructions",
                "",
                "**CLEAN CODE FORMATTING:**",
                "- Provide ONLY executable code in <code> blocks - NO explanations inside files",
                "- NEVER add markdown blocks (```) inside source files",
                "- NEVER add implementation summaries at end of files",
                "- Keep files in their proper format (HTML=HTML, JS=JS, CSS=CSS)",
                "- Code blocks must contain ONLY the file content, no commentary",
                ""
            ]
            
            return "\n".join(instructions)
        
        # Fallback for ambiguous cases
        return ""
    
    def analyze_and_enhance_prompt(self, original_prompt: str) -> str:
        """
        Analyze user prompt and enhance it with better context and details
        
        Args:
            original_prompt: User's original prompt
            
        Returns:
            Enhanced prompt with more context and details
        """
        selected_model = self.selected_model_getter()
        if not selected_model:
            return original_prompt
        
        analysis_prompt = f"""You are a prompt analysis expert. Your job is to analyze user requests and provide a detailed, enhanced version that will get better results from an AI assistant.

ORIGINAL USER REQUEST:
"{original_prompt}"

ANALYSIS TASK:
1. Identify what the user is trying to accomplish
2. Determine what additional context or details would be helpful
3. Suggest specific requirements, constraints, or preferences
4. Consider technical details, best practices, or standards that should be included
5. Think about potential edge cases or considerations

ENHANCED REQUEST FORMAT:
Provide an enhanced version of the request that:
- Maintains the user's original intent
- Adds helpful context and details
- Specifies clear requirements when applicable  
- Includes relevant technical considerations
- Is more likely to produce a comprehensive, useful response

IMPORTANT: 
- Keep the enhanced request focused and practical
- Don't over-complicate simple requests
- Maintain the original tone and style
- Add value without changing the core request

Enhanced Request:"""

        try:
            console.print("[dim]🔍 Analyzing and enhancing your prompt...[/dim]")
            
            # Send to LLM for analysis
            response = ""
            chunk_count = 0
            
            with console.status("[dim]Analyzing prompt...", spinner="dots") as status:
                for chunk in self.api.generate(selected_model, analysis_prompt, stream=True):
                    response += chunk
                    chunk_count += 1
                    
                    # Update status periodically
                    if chunk_count % 20 == 0:
                        status.update(f"[dim]Analyzing... ({chunk_count} chunks received)", spinner="dots")
            
            # Check if we got a valid response
            if not response.strip():
                console.print("[yellow]⚠️ Empty response from analysis, using original prompt[/yellow]")
                return original_prompt
            
            # Extract the enhanced request from the response
            enhanced_prompt = response.strip()
            
            # Clean up the response to get just the enhanced prompt
            if "Enhanced Request:" in enhanced_prompt:
                enhanced_prompt = enhanced_prompt.split("Enhanced Request:")[-1].strip()
            elif "enhanced version:" in enhanced_prompt.lower():
                parts = enhanced_prompt.lower().split("enhanced version:")
                if len(parts) > 1:
                    enhanced_prompt = enhanced_prompt[len(parts[0]):].strip()
            
            # Remove any leading/trailing quotes or formatting
            enhanced_prompt = enhanced_prompt.strip('"').strip("'").strip()
            
            # Show the enhancement to the user
            console.print(f"\n[blue]🎯 Enhanced Prompt:[/blue]")
            console.print(f"[dim]{enhanced_prompt}[/dim]\n")
            
            return enhanced_prompt
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ Prompt analysis interrupted by user[/yellow]")
            console.print("[dim]Using original prompt[/dim]")
            return original_prompt
        except Exception as e:
            console.print(f"[yellow]⚠️ Prompt enhancement failed: {e}[/yellow]")
            console.print("[dim]Falling back to original prompt[/dim]")
            return original_prompt
