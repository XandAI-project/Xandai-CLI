"""
AI-Driven Read Decision System
A IA decide autonomamente se precisa ler arquivos, qual nível usar e quais comandos executar
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from rich.console import Console

console = Console()


class AIReadDecision:
    """Sistema de decisão inteligente para leitura de arquivos baseado em IA"""
    
    def __init__(self, api, selected_model):
        self.api = api
        self.selected_model = selected_model
    
    def should_read_files(self, user_prompt: str, has_existing_context: bool = False) -> bool:
        """
        Pergunta à IA se ela precisa ler arquivos para responder adequadamente
        
        Args:
            user_prompt: Prompt do usuário
            has_existing_context: Se já há contexto de arquivos disponível
            
        Returns:
            bool: True se a IA quer ler arquivos
        """
        decision_prompt = f"""
You are an intelligent assistant analyzing a user request. Your task is to decide if you need to read files to provide an accurate response.

User Request: "{user_prompt}"

Context Information:
- Has existing file context: {has_existing_context}
- Working directory: Current project folder

Instructions:
- Analyze the user's request carefully
- Determine if reading files would help provide a better, more accurate response
- Consider if the request requires knowledge of current code, configuration, or project structure
- Respond with ONLY "true" or "false" (no other text)

Examples:
- "fix this bug" → true (need to see code)
- "create a new React app" → false (general knowledge sufficient)
- "analyze this code" → true (need to see specific files)
- "what is React?" → false (general knowledge sufficient)
- "optimize this function" → true (need to see current implementation)

Your decision (true/false):"""

        try:
            response = ""
            for chunk in self.api.generate(self.selected_model, decision_prompt):
                response += chunk
                
            # Extrai apenas true/false da resposta
            response_clean = response.strip().lower()
            if "true" in response_clean:
                return True
            elif "false" in response_clean:
                return False
            else:
                # Fallback: assume que precisa ler se não conseguiu decidir claramente
                console.print("[yellow]⚠️ AI decision unclear, defaulting to read files[/yellow]")
                return True
                
        except Exception as e:
            console.print(f"[red]❌ Error in AI decision: {e}[/red]")
            # Fallback: assume que precisa ler
            return True
    
    def choose_read_level_and_commands(self, user_prompt: str) -> Tuple[int, List[str]]:
        """
        IA escolhe o nível de leitura e gera comandos específicos
        
        Args:
            user_prompt: Prompt do usuário
            
        Returns:
            Tuple (level, commands): Nível escolhido e lista de comandos
        """
        level_prompt = f"""
You are an intelligent assistant choosing the appropriate file reading strategy.

User Request: "{user_prompt}"

Available Read Levels:
1. Level 1 (Overview): Basic directory listing - when you need general project structure
2. Level 2 (Specific Files): Important project files - when you need to see key configuration/code files  
3. Level 3 (Nested Structure): Subfolders exploration - when you need to understand project organization
4. Level 4 (Deep Analysis): Nested files content - when you need comprehensive code analysis

Your task:
1. Choose the most appropriate level (1-4) for this request
2. Generate specific commands needed for that level
3. Adapt commands for Windows (use 'type' and 'dir') 

Respond in this EXACT JSON format:
{{
    "level": 2,
    "commands": [
        "dir",
        "type package.json",
        "type app.js"
    ],
    "reasoning": "Need to see project structure and main files to analyze the codebase"
}}

Your response:"""

        try:
            response = ""
            for chunk in self.api.generate(self.selected_model, level_prompt):
                response += chunk
            
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    level = data.get("level", 2)
                    commands = data.get("commands", ["dir"])
                    reasoning = data.get("reasoning", "")
                    
                    console.print(f"[blue]🤖 AI chose Level {level}: {reasoning}[/blue]")
                    return level, commands
                    
                except json.JSONDecodeError:
                    pass
            
            # Fallback: nível 2 com comandos básicos
            console.print("[yellow]⚠️ Could not parse AI response, using fallback[/yellow]")
            return 2, ["dir", "type README.md", "type package.json"]
            
        except Exception as e:
            console.print(f"[red]❌ Error in AI level choice: {e}[/red]")
            return 2, ["dir", "type README.md"]
    
    def get_ai_driven_read_strategy(self, user_prompt: str, has_existing_context: bool = False) -> Optional[Dict]:
        """
        Estratégia completa de leitura dirigida por IA
        
        Args:
            user_prompt: Prompt do usuário
            has_existing_context: Se já há contexto disponível
            
        Returns:
            Dict com estratégia ou None se não precisa ler
        """
        # Passo 1: IA decide se precisa ler
        should_read = self.should_read_files(user_prompt, has_existing_context)
        
        if not should_read:
            console.print("[blue]🤖 AI decided: No file reading needed[/blue]")
            return None
        
        # Passo 2: IA escolhe nível e comandos
        level, commands = self.choose_read_level_and_commands(user_prompt)
        
        return {
            "should_read": True,
            "level": level,
            "commands": commands,
            "strategy": "ai_driven"
        }
