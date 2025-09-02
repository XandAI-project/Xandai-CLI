"""
Tag Processor
Processamento de tags especiais como <read>, <code>, <actions>
"""

import re
from typing import List, Tuple
from rich.console import Console
from .ai_read_decision import AIReadDecision

console = Console()


class TagProcessor:
    """Processa tags especiais em respostas do LLM"""
    
    def __init__(self, shell_executor, file_operations, file_context_manager, api=None, selected_model=None):
        self.shell_exec = shell_executor
        self.file_ops = file_operations
        self.file_context_manager = file_context_manager
        self.ai_read_decision = AIReadDecision(api, selected_model) if api and selected_model else None
    
    def execute_read_tags_only(self, response: str) -> List[str]:
        """
        Executa apenas as tags <read> e retorna o conteúdo lido
        
        Args:
            response: Resposta que contém tags <read>
            
        Returns:
            Lista com conteúdo dos arquivos lidos
        """
        read_content = []
        read_blocks = re.findall(r'<read>(.*?)</read>', response, re.DOTALL | re.IGNORECASE)
        
        if read_blocks:
            console.print("\n[bold blue]📖 Reading files...[/bold blue]")
            for reads in read_blocks:
                commands = [cmd.strip() for cmd in reads.strip().split('\n') if cmd.strip()]
                for command in commands:
                    if command:
                        console.print(f"[dim]$ {command}[/dim]")
                        try:
                            success, output = self.shell_exec.execute_command(command)
                            if success and output and output.strip():
                                read_content.append(f"--- Output from: {command} ---\n{output}\n")
                                
                                # Adiciona ao contexto persistente se for leitura de arquivo
                                if self._is_file_read_command(command):
                                    filename = self._extract_filename_from_command(command)
                                    if filename:
                                        self.file_context_manager.add_file_content(filename, output)
                            else:
                                read_content.append(f"--- Output from: {command} ---\n(No output or file not found)\n")
                        except Exception as e:
                            console.print(f"[red]❌ Error executing '{command}': {e}[/red]")
                            read_content.append(f"--- Error from: {command} ---\nError: {str(e)}\n")
        
        return read_content
    
    def _is_file_read_command(self, command: str) -> bool:
        """Verifica se o comando é de leitura de arquivo específico"""
        file_read_patterns = [
            r'cat\s+[\w\./\\-]+\.(py|js|html|css|json|md|txt|yml|yaml|xml)',
            r'type\s+[\w\./\\-]+\.(py|js|html|css|json|md|txt|yml|yaml|xml)',
        ]
        
        for pattern in file_read_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def _extract_filename_from_command(self, command: str) -> str:
        """Extrai o nome do arquivo do comando de leitura"""
        # Para comandos como "cat app.py" ou "type app.py"
        match = re.search(r'(?:cat|type)\s+([\w\./\\-]+\.\w+)', command, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def add_read_first_instruction(self, prompt: str, read_levels_manager, force_read: bool = False) -> Tuple[str, bool]:
        """
        Adds instruction to always start with <read> based on AI decision
        
        Args:
            prompt: Prompt (possibly already enhanced)
            read_levels_manager: ReadLevelsManager instance (fallback)
            force_read: If True, forces read instruction regardless of existing context
            
        Returns:
            Tuple (prompt_with_read_instruction, needs_read_first)
        """
        # If force_read is True, skip all checks and force reading
        if force_read:
            console.print("[yellow]🔧 FORCING read-first due to edit mode[/yellow]")
            suggested_reads = read_levels_manager.get_suggested_read_commands(prompt)
            if not suggested_reads:
                # Fallback to basic reads if no specific suggestions
                suggested_reads = """<read>
ls -la
find . -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.css" | head -10
</read>"""
            
            read_instruction = f"""

[FORCED READ-FIRST FOR EDIT MODE]
🚨 CRITICAL: You are in EDIT MODE. You MUST start by reading existing files before making any changes.

🚀 EFFICIENCY TIP: Read MULTIPLE files in ONE <read> block!

{suggested_reads}

After reading files, I will re-send your request with the EXISTING code content. You MUST then:
1. PRESERVE ALL existing code: endpoints, functions, classes, imports, variables
2. Analyze the existing code structure and patterns carefully
3. Make ONLY the specific changes requested - keep everything else identical
4. Use <code edit filename="..."> to modify existing files (include COMPLETE file)
5. NEVER delete or remove existing functionality unless explicitly requested
6. When editing, provide the FULL file with existing code + your changes
7. 🚀 EFFICIENCY: Process ALL required files in ONE response - don't stop after one
8. NEVER create new files unless specifically requested

PRESERVATION RULE: If existing code has endpoints A, B, C and you need to add D:
- Keep A, B, C exactly as they are
- Add D properly integrated
- Provide complete file with A, B, C, D all included

BATCH PROCESSING RULE: If you need to modify multiple files, do them all in ONE response
"""
            return prompt + read_instruction, True
        
        # Check if there's already persistent file context
        has_existing_context = self.file_context_manager.has_context()
        if has_existing_context:
            # Already have persistent context, inject it and don't need read
            persistent_context = self.file_context_manager.format_context_for_injection()
            return prompt + persistent_context, False
        
        # Check if there's already file context in current prompt
        has_file_content = any(marker in prompt for marker in [
            "[FILES READ - INJECTED CONTENT:]",
            "--- Output from:",
            "--- End of file content ---",
            "[Existing File Structure]",
            "[CURRENT PROJECT STRUCTURE:]",
            "[PERSISTENT FILE CONTEXT - INJECTED]"
        ])
        
        if has_file_content:
            # Já tem contexto de arquivos, não adiciona instrução read
            return prompt, False
        
        # *** NOVA FUNCIONALIDADE: IA decide se precisa ler ***
        if self.ai_read_decision:
            console.print("[blue]🤖 Asking AI to decide read strategy...[/blue]")
            try:
                ai_strategy = self.ai_read_decision.get_ai_driven_read_strategy(prompt, has_existing_context)
                
                if not ai_strategy:
                    # IA decidiu que não precisa ler arquivos
                    return prompt, False
                
                # IA decidiu ler - monta instrução com comandos da IA
                level = ai_strategy['level']
                commands = ai_strategy['commands']
                
                level_description = {
                    1: "Level 1 (Overview): Basic directory listing",
                    2: "Level 2 (Specific Files): Important project files",
                    3: "Level 3 (Nested Structure): Subfolders exploration", 
                    4: "Level 4 (Deep Analysis): Nested files content"
                }
                
                commands_text = "\n".join(commands)
                
                read_instruction = f"""

[AI-DRIVEN FIRST STEP - READ FILES]
CRITICAL: The AI has determined you need to read files to provide an accurate response.
Start your response with this exact read block:

AI Decision: {level_description.get(level, f"Level {level}")}

<read>
{commands_text}
</read>

After reading files, I will re-send your original request with the file content. You MUST then:
1. Use the actual file content to understand the current state
2. IMPLEMENT the requested changes using <code edit> for existing files or <code create> for new files
3. Use <actions> for any needed shell commands
4. NEVER stop without completing the implementation - provide the actual code/files requested
"""
                return prompt + read_instruction, True
                
            except Exception as e:
                console.print(f"[yellow]⚠️ AI decision failed, using fallback: {e}[/yellow]")
                # Fallback para sistema anterior
        
        # Fallback: usa sistema de detecção por palavras-chave
        suggested_reads = read_levels_manager.get_suggested_read_commands(prompt)
        
        if suggested_reads:
            read_level = read_levels_manager.determine_read_level(prompt.lower())
            
            level_description = {
                1: "Level 1 (Overview): Basic directory listing",
                2: "Level 2 (Specific Files): Important project files",
                3: "Level 3 (Nested Structure): Subfolders exploration", 
                4: "Level 4 (Deep Analysis): Nested files content"
            }
            
            read_instruction = f"""

[FALLBACK FIRST STEP - READ FILES]
CRITICAL: You MUST start your response with this exact read block to examine relevant files.

Read Level: {level_description.get(read_level, f"Level {read_level}")}

{suggested_reads}

After reading files, I will re-send your original request with the file content. You MUST then:
1. Use the actual file content to understand the current state
2. IMPLEMENT the requested changes using <code edit> for existing files or <code create> for new files
3. Use <actions> for any needed shell commands
4. NEVER stop without completing the implementation - provide the actual code/files requested
"""
            return prompt + read_instruction, True
        
        return prompt, False
    
    def send_original_with_file_content(self, original_prompt: str, working_prompt: str, read_content: List[str], api, selected_model):
        """
        Re-envia o prompt original (sem instrução read) mas com conteúdo dos arquivos injetado
        
        Args:
            original_prompt: Prompt original do usuário
            working_prompt: Prompt melhorado sem instrução read
            read_content: Lista com conteúdo lido dos arquivos
            api: Instância da API
            selected_model: Modelo selecionado
        """
        try:
            # Constrói prompt com conteúdo dos arquivos injetado
            if read_content:
                # Add emphasis that this is EXISTING code to be preserved
                formatted_content = []
                for content in read_content:
                    if content.strip():
                        formatted_content.append(f"📁 EXISTING CODE (MUST BE PRESERVED):\n{content.strip()}")
                file_content_text = "\n\n" + "="*60 + "\n".join(formatted_content) + "\n" + "="*60
                
                enhanced_prompt_with_files = f"""{working_prompt}

[EXISTING CODEBASE - READ FROM FILES:]
{file_content_text}
--- End of existing code content ---

NOW IMPLEMENT THE SOLUTION:
Based on the EXISTING code shown above, you MUST implement the requested changes for: {original_prompt}

🚨 CRITICAL PRESERVATION REQUIREMENTS:
1. PRESERVE ALL EXISTING CODE: Keep every function, endpoint, class, and variable that already exists
2. ONLY ADD/MODIFY what was specifically requested - DO NOT delete or remove existing functionality
3. MAINTAIN all existing endpoints, routes, API functions, and features
4. When editing files, include the COMPLETE file with both:
   - ALL existing code (unchanged)
   - Your new additions/modifications (clearly marked)

IMPLEMENTATION RULES:
1. Use <code edit filename="..."> to modify existing files (include FULL file content)
2. Use <code create filename="..."> only for completely new files
3. Use <actions> for shell commands if needed
4. When modifying existing files, show the COMPLETE file including:
   - All existing imports, functions, classes, endpoints
   - All existing code (preserved exactly as-is)
   - Your new additions/changes integrated properly
5. NEVER provide partial code - always provide the complete updated file
6. Mark your changes with comments like // NEW: or // MODIFIED: for clarity
7. 🚀 BATCH PROCESSING: Process ALL required files in ONE response - don't stop after one file

🚫 CODE FORMATTING RULES:
1. Provide ONLY clean, executable code - NO explanations or descriptions inside code blocks
2. NEVER add markdown blocks (```) inside source files
3. NEVER add implementation summaries or feature lists at the end of files
4. Code blocks should contain ONLY the file content - no external commentary
5. Keep files in their proper format (HTML files should be valid HTML, not markdown)
6. If you need to explain changes, do it OUTSIDE the code blocks, not inside files

⚡ EFFICIENCY EXAMPLES:
EXCELLENT - Multiple files in ONE response:
<code edit filename="app.py">...</code>
<code edit filename="config.py">...</code>
<code create filename="utils.py">...</code>

POOR - Only one file then stopping:
<code edit filename="app.py">...</code>
"Let me know if you want me to update other files..."

EXAMPLE of correct editing:
If existing file has endpoints A, B, C and you need to add endpoint D:
- Keep endpoints A, B, C exactly as they are
- Add endpoint D in the appropriate location
- Provide the complete file with A, B, C, D all included"""
            else:
                # Se não há conteúdo de arquivos, usa prompt melhorado normal
                enhanced_prompt_with_files = working_prompt
            # Gera resposta final com conteúdo dos arquivos
            full_response = ""
            chunk_count = 0
            try:
                with console.status("[bold green]🔄 Processing with file content...", spinner="dots") as status:
                    for chunk in api.generate(selected_model, enhanced_prompt_with_files):
                        full_response += chunk
                        chunk_count += 1
                        
                        # Update status every 8 chunks to show progress
                        if chunk_count % 8 == 0:
                            token_estimate = len(full_response.split())
                            line_count = full_response.count('\n')
                            status.update(f"[bold green]🔄 Processing with file content... ({chunk_count} chunks, ~{token_estimate} tokens, {line_count} lines)", spinner="dots")
            except KeyboardInterrupt:
                console.print("\n[yellow]💡 Re-processing interrupted by user[/yellow]")
                return full_response
            
            return full_response
            
        except Exception as e:
            console.print(f"[red]❌ Error in re-processing with file content: {e}[/red]")
            return None
