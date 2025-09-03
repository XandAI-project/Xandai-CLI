"""
Project Mode Detection Module
Automatically detects if the user wants to update an existing project or create a new project
"""

import os
import re
from typing import Dict, Any


class ProjectModeDetector:
    """
    Automatically detects if the user wants to update an existing project 
    or create a new project based on context and prompt
    """
    
    def __init__(self, shell_executor):
        self.shell_executor = shell_executor
        
        # Files that indicate existing projects
        self.project_indicators = {
            'web_frontend': ['package.json', 'yarn.lock', 'package-lock.json', 'index.html', 'src/index.js', 'src/App.js'],
            'web_backend': ['app.py', 'main.py', 'server.js', 'requirements.txt', 'Pipfile', 'poetry.lock'],
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '__init__.py', 'main.py'],
            'node': ['package.json', 'node_modules/', 'yarn.lock', 'package-lock.json'],
            'react': ['package.json', 'src/App.js', 'src/index.js', 'public/index.html'],
            'next': ['next.config.js', 'package.json', 'pages/', 'app/'],
            'django': ['manage.py', 'settings.py', 'urls.py', 'requirements.txt'],
            'flask': ['app.py', 'requirements.txt', 'templates/', 'static/'],
            'go': ['go.mod', 'go.sum', 'main.go'],
            'rust': ['Cargo.toml', 'Cargo.lock', 'src/main.rs'],
            'java': ['pom.xml', 'build.gradle', 'src/main/java/'],
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'git': ['.git/', '.gitignore', 'README.md']
        }
        
        # Keywords that indicate editing/updating
        self.edit_keywords = {
            'explicit_edit': ['atualizar', 'modificar', 'editar', 'alterar', 'corrigir', 'ajustar', 'melhorar', 'otimizar', 'refatorar'],
            'add_features': ['adicionar', 'incluir', 'implementar', 'inserir', 'acrescentar'],
            'fix_issues': ['corrigir', 'consertar', 'resolver', 'debugar', 'reparar', 'solucionar'],
            'update_existing': ['atualizar', 'renovar', 'modernizar', 'migrar', 'upgradar'],
            'modify_behavior': ['modificar', 'alterar', 'mudar', 'adaptar', 'personalizar']
        }
        
        # Keywords that indicate creation
        self.create_keywords = {
            'explicit_create': ['criar', 'gerar', 'construir', 'desenvolver', 'fazer', 'produzir', 'estabelecer'],
            'new_project': ['novo', 'nova', 'from scratch', 'do zero', 'começar', 'iniciar'],
            'project_types': ['aplicação', 'app', 'sistema', 'plataforma', 'website', 'site', 'api', 'microserviço']
        }

    def detect_existing_projects(self, directory: str = None) -> Dict[str, Any]:
        """
        Analyzes the current directory and detects existing project types
        
        Returns:
            Dict with information about detected projects
        """
        if not directory:
            directory = self.shell_executor.get_current_directory()
        
        try:
            # List files in current directory
            success, files_output = self.shell_executor.execute_command('dir /b' if os.name == 'nt' else 'ls -la')
            if not success:
                return {'has_project': False, 'confidence': 0, 'types': [], 'indicators': []}
            
            # List files recursively limited (only 2 levels)
            success2, recursive_output = self.shell_executor.execute_command(
                'dir /s /b' if os.name == 'nt' else 'find . -maxdepth 2 -type f'
            )
            
            all_files = files_output.lower() + '\n' + (recursive_output.lower() if success2 else '')
            
            detected_types = []
            found_indicators = []
            confidence_score = 0
            
            # Analyze each project type
            for project_type, indicators in self.project_indicators.items():
                type_score = 0
                type_indicators = []
                
                for indicator in indicators:
                    if indicator.lower() in all_files or indicator.replace('/', '\\').lower() in all_files:
                        type_indicators.append(indicator)
                        # Main files have higher weight
                        if indicator in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']:
                            type_score += 30
                        else:
                            type_score += 10
                
                if type_score > 0:
                    detected_types.append({
                        'type': project_type,
                        'confidence': min(type_score, 100),
                        'indicators': type_indicators
                    })
                    found_indicators.extend(type_indicators)
                    confidence_score = max(confidence_score, type_score)
            
            # Check if it has typical directory structure
            common_dirs = ['src', 'lib', 'app', 'components', 'utils', 'config', 'static', 'templates']
            for dir_name in common_dirs:
                if dir_name in all_files:
                    confidence_score += 5
            
            has_project = confidence_score > 15  # Threshold to consider there's a project
            
            return {
                'has_project': has_project,
                'confidence': min(confidence_score, 100),
                'types': sorted(detected_types, key=lambda x: x['confidence'], reverse=True),
                'indicators': list(set(found_indicators)),
                'directory': directory
            }
            
        except Exception as e:
            return {'has_project': False, 'confidence': 0, 'types': [], 'indicators': [], 'error': str(e)}

    def analyze_user_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes the user prompt to detect intention of editing vs creating
        
        Returns:
            Dict with user intention analysis
        """
        prompt_lower = prompt.lower()
        
        edit_score = 0
        create_score = 0
        detected_edit_keywords = []
        detected_create_keywords = []
        
        # Analyze edit keywords
        for category, keywords in self.edit_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_edit_keywords.append(keyword)
                    # Explicit edit words have higher weight
                    if category == 'explicit_edit':
                        edit_score += 25
                    else:
                        edit_score += 15
        
        # Analyze creation keywords
        for category, keywords in self.create_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    detected_create_keywords.append(keyword)
                    # Explicit creation words have higher weight
                    if category == 'explicit_create':
                        create_score += 25
                    else:
                        create_score += 15
        
        # Specific patterns that indicate editing
        edit_patterns = [
            r'no\s+(arquivo|código|projeto)\s+atual',
            r'neste\s+(arquivo|código|projeto)',
            r'arquivo\s+existente',
            r'código\s+que\s+já\s+existe'
        ]
        
        for pattern in edit_patterns:
            if re.search(pattern, prompt_lower):
                edit_score += 20
                detected_edit_keywords.append(f"pattern: {pattern}")
        
        # Specific patterns that indicate creation
        create_patterns = [
            r'criar\s+um\s+novo',
            r'fazer\s+uma?\s+nova?',
            r'desenvolver\s+um',
            r'from\s+scratch',
            r'do\s+zero'
        ]
        
        for pattern in create_patterns:
            if re.search(pattern, prompt_lower):
                create_score += 30
                detected_create_keywords.append(f"pattern: {pattern}")
        
        # Determine main intention
        if edit_score > create_score and edit_score > 20:
            intent = 'edit'
            confidence = min(edit_score, 100)
        elif create_score > edit_score and create_score > 20:
            intent = 'create'
            confidence = min(create_score, 100)
        else:
            intent = 'ambiguous'
            confidence = max(edit_score, create_score)
        
        return {
            'intent': intent,
            'confidence': confidence,
            'edit_score': edit_score,
            'create_score': create_score,
            'edit_keywords': detected_edit_keywords,
            'create_keywords': detected_create_keywords
        }

    def detect_project_mode(self, prompt: str, directory: str = None) -> Dict[str, Any]:
        """
        Makes the final decision about mode (edit vs create) based on all factors
        
        Returns:
            Dict with final decision and justification
        """
        # Analyze existing project
        project_info = self.detect_existing_projects(directory)
        
        # Analyze user intention
        intent_info = self.analyze_user_intent(prompt)
        
        # Decision logic
        final_mode = 'create'  # default
        confidence = 0
        reasoning = []
        
        # If there's an existing project with high confidence
        if project_info['has_project'] and project_info['confidence'] > 30:
            reasoning.append(f"Existing project detected (confidence: {project_info['confidence']}%)")
            
            # If intention is ambiguous or explicitly edit, prefer editing
            if intent_info['intent'] in ['ambiguous', 'edit']:
                final_mode = 'edit'
                confidence = project_info['confidence'] + intent_info['confidence']
                reasoning.append(f"User intention favors editing (score: {intent_info['edit_score']})")
            
            # If intention is explicitly creation with high confidence, keep creation
            elif intent_info['intent'] == 'create' and intent_info['confidence'] > 60:
                final_mode = 'create'
                confidence = intent_info['confidence']
                reasoning.append(f"Explicit creation intention overrides existing project")
            
            # Default case: if there's existing project, prefer editing
            else:
                final_mode = 'edit'
                confidence = project_info['confidence'] + (intent_info['confidence'] * 0.5)
                reasoning.append("Default: existing project indicates edit mode")
        
        # If there's no existing project
        else:
            if intent_info['intent'] == 'edit' and intent_info['confidence'] > 40:
                final_mode = 'edit'
                confidence = intent_info['confidence'] * 0.7  # Reduced because no project
                reasoning.append("Edit intention but no existing project detected")
            else:
                final_mode = 'create'
                confidence = max(50, intent_info['confidence'])  # Minimum 50% for creation
                reasoning.append("No existing project detected, creation mode")
        
        return {
            'mode': final_mode,
            'confidence': min(confidence, 100),
            'reasoning': reasoning,
            'project_info': project_info,
            'intent_info': intent_info
        }
