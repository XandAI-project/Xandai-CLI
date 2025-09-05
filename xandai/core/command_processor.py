"""
XandAI Core - Command Processor
Automatic mode detection system (EditModeEnhancer)
"""

import os
import re
from typing import Dict, List, Optional

from xandai.core.app_state import AppState


class CommandProcessor:
    """
    Command processor and automatic mode detection

    Implements the EditModeEnhancer system that automatically detects
    whether the user wants to edit an existing project or create something new.
    """

    def __init__(self, app_state: AppState):
        self.app_state = app_state

        # Patterns for mode detection
        self.create_patterns = [
            r"creat\w*",
            r"new\w*",
            r"start\w*",
            r"initial\w*",
            r"implement\w*",
            r"develop\w*",
            r"build\w*",
            r"make\s+(a|an)",
            r"generat\w*",
            r"setup",
            r"scaffold",
            r"begin\w*",
        ]

        self.edit_patterns = [
            r"edit\w*",
            r"modif\w*",
            r"alter\w*",
            r"updat\w*",
            r"fix\w*",
            r"adjust\w*",
            r"improv\w*",
            r"refactor\w*",
            r"chang\w*",
            r"add\w*",
            r"remov\w*",
            r"delet\w*",
            r"correct\w*",
        ]

        self.task_patterns = [
            r"list\w*",
            r"create\s+(a|an)?\s+(list|structure|project)",
            r"break\w*\s+(down|into)\s+(steps|tasks)",
            r"divid\w*\s+into\s+steps",
            r"plan\w*",
            r"organiz\w*",
            r"structur\w*\s+the\s+work",
            r"make\s+(a\s+)?roadmap",
            r"steps?\s+(for|to)",
        ]

    def detect_mode(self, user_input: str) -> str:
        """
        Automatically detects mode based on user input

        Returns:
            'create': For new projects
            'edit': For modifications to existing projects
            'task': For structured tasks
            'chat': For normal conversation
        """
        # Check cache first
        cached_mode = self.app_state.get_cached_mode(user_input)
        if cached_mode:
            return cached_mode

        input_lower = user_input.lower()

        # 1. Explicit task mode detection
        if self._matches_patterns(input_lower, self.task_patterns):
            mode = "task"

        # 2. Project context analysis
        elif self._analyze_project_context(input_lower):
            mode = self._determine_project_mode(input_lower)

        # 3. Linguistic pattern analysis
        else:
            mode = self._analyze_linguistic_patterns(input_lower)

        # Cache result
        self.app_state.cache_mode_detection(user_input, mode)

        return mode

    def _analyze_project_context(self, input_text: str) -> bool:
        """
        Analyzes if input refers to a specific project/context
        """
        project_indicators = [
            # References to existing files
            r"\.(py|js|ts|html|css|json|md|txt)(\s|$)",
            # References to directories
            r"src/",
            r"components/",
            r"utils/",
            r"api/",
            # References to tools/frameworks
            r"(django|flask|react|vue|angular|express)",
            # References to common files
            r"(requirements\.txt|package\.json|setup\.py|main\.py|app\.py|index\.html)",
        ]

        return any(re.search(pattern, input_text) for pattern in project_indicators)

    def _determine_project_mode(self, input_text: str) -> str:
        """
        Determines mode based on project context
        """
        # If there are files in current directory, probably edit
        current_files = self._get_current_directory_files()
        has_project_files = len(current_files) > 0

        # Check creation vs editing patterns
        create_score = self._calculate_pattern_score(input_text, self.create_patterns)
        edit_score = self._calculate_pattern_score(input_text, self.edit_patterns)

        # If there's existing project and patterns suggest editing
        if has_project_files and edit_score > create_score:
            return "edit"

        # If patterns suggest strong creation
        elif create_score > edit_score * 1.5:
            return "create"

        # If there's existing project, default to edit
        elif has_project_files:
            return "edit"

        # Otherwise, create
        else:
            return "create"

    def _analyze_linguistic_patterns(self, input_text: str) -> str:
        """
        Analyzes linguistic patterns to determine intention
        """
        create_score = self._calculate_pattern_score(input_text, self.create_patterns)
        edit_score = self._calculate_pattern_score(input_text, self.edit_patterns)

        if create_score > edit_score:
            return "create"
        elif edit_score > create_score:
            return "edit"
        else:
            return "chat"

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Checks if text matches any pattern"""
        return any(re.search(pattern, text) for pattern in patterns)

    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> int:
        """Calculates score based on number of patterns found"""
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            score += len(matches)
        return score

    def _get_current_directory_files(self) -> List[str]:
        """Returns list of files in current directory"""
        try:
            files = []
            for item in os.listdir("."):
                if os.path.isfile(item) and not item.startswith("."):
                    files.append(item)
            return files
        except:
            return []

    def get_mode_explanation(self, detected_mode: str, user_input: str) -> str:
        """
        Returns explanation of why the mode was detected
        """
        explanations = {
            "create": "Detected intention to create something new based on verbs and context used.",
            "edit": "Detected intention to modify existing project based on context and files present.",
            "task": "Detected need for structuring into steps based on language patterns.",
            "chat": "Default conversation mode - no specific creation or editing intention detected.",
        }
        return explanations.get(detected_mode, "Default mode")

    def suggest_mode_override(self, detected_mode: str) -> Optional[str]:
        """
        Suggests mode override if detection seems uncertain
        """
        # If detected chat but there are files in project, suggest edit
        if detected_mode == "chat":
            current_files = self._get_current_directory_files()
            if len(current_files) > 3:  # Threshold to suggest edit
                return "edit"

        return None
