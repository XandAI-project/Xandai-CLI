"""
XandAI Processors - Task Processor
Task Mode processor with structured output for automation
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from xandai.conversation.conversation_manager import ConversationManager
from xandai.core.app_state import AppState
from xandai.integrations.base_provider import LLMProvider, LLMResponse


@dataclass
class TaskStep:
    """Structured step of a task"""

    step_number: int
    action: str  # 'create', 'edit', 'command'
    description: str
    target: str  # file or command
    content: Optional[str] = None
    commands: Optional[List[str]] = None


@dataclass
class TaskResult:
    """Structured result of task processing"""

    description: str
    steps: List[TaskStep]
    project_type: str
    estimated_time: str
    complexity: str  # 'low', 'medium', 'high'
    dependencies: List[str]
    notes: List[str]


class TaskProcessor:
    """
    Task Mode Processor

    Converts high-level descriptions into structured specifications
    with ordered steps, each corresponding to an LLM call.
    """

    def __init__(self, llm_provider: LLMProvider, conversation_manager: ConversationManager):
        self.llm_provider = llm_provider
        self.conversation_manager = conversation_manager

        # System prompt specific for task mode
        self.system_prompt = """You are XandAI in TASK mode - an expert in breaking down complex projects into executable steps.

OBJECTIVE:
Convert high-level descriptions into structured specifications with ordered steps.

MANDATORY RESPONSE FORMAT:
```
PROJECT: [name/description]
TYPE: [python|javascript|web|react|api|etc]
COMPLEXITY: [low|medium|high]
ESTIMATED TIME: [e.g., 2-3 hours]

DEPENDENCIES:
- [dependency 1]
- [dependency 2]

STEPS:
1 - create [path/file.ext]
2 - edit [path/file.ext]
3 - command [shell command]
4 - create [another/file.ext]

STEP DETAILS:

=== STEP 1: create src/app.py ===
<code edit filename="src/app.py">
# complete file content
</code>

=== STEP 2: edit src/app.py ===
<code edit filename="src/app.py">
# updated file content
</code>

=== STEP 3: command setup ===
<commands>
pip install flask
python -m flask run
</commands>

NOTES:
- [important note 1]
- [important note 2]
```

CRITICAL RULES:
1. ALWAYS use the exact format above
2. Each step must be independently executable
3. Use <code edit> for files, <commands> for shell
4. Steps must be ordered and numbered
5. Include COMPLETE file content, not just snippets
6. Prioritize clarity and executability
7. Think like a senior engineer: anticipate problems, suggest best practices

VALID STEP EXAMPLES:
- "1 - create src/main.py"
- "2 - edit package.json"
- "3 - command npm install"
- "4 - create tests/test_api.py"

ALWAYS RESPOND IN ENGLISH."""

    def process(self, user_input: str, app_state: AppState) -> TaskResult:
        """
        Processes input in Task Mode

        Args:
            user_input: Task description
            app_state: Current application state

        Returns:
            Structured TaskResult
        """
        # Add user message to history
        self.conversation_manager.add_message(
            role="user",
            content=user_input,
            mode="task",
            metadata={"app_state": app_state.get_context_summary()},
        )

        # Increment interaction counter
        app_state.increment_task_interaction()

        try:
            # Prepare context
            context = self._prepare_task_context(user_input, app_state)

            # Generate structured response
            response = self._generate_task_response(context, app_state)

            # Parse response into TaskResult
            task_result = self._parse_task_response(response.content, user_input)

            # Add response to history
            self.conversation_manager.add_message(
                role="assistant",
                content=response.content,
                mode="task",
                metadata={
                    "model": response.model,
                    "tokens": response.total_tokens,
                    "steps_count": len(task_result.steps),
                },
            )

            return task_result

        except Exception as e:
            error_msg = f"Task processing error: {str(e)}"
            self.conversation_manager.add_message(
                role="system", content=error_msg, mode="task", metadata={"error": True}
            )

            # Return error task result
            return TaskResult(
                description=f"ERROR: {user_input}",
                steps=[],
                project_type="unknown",
                estimated_time="N/A",
                complexity="unknown",
                dependencies=[],
                notes=[error_msg],
            )

    def _prepare_task_context(self, user_input: str, app_state: AppState) -> List[Dict[str, str]]:
        """
        Prepares specific context for task mode
        """
        # Context with system prompt
        context = [{"role": "system", "content": self._get_enhanced_task_prompt(app_state)}]

        # Add relevant task history
        task_history = self.conversation_manager.get_recent_history(limit=5, mode_filter="task")
        for msg in task_history[-3:]:  # Last 3 tasks for context
            context.append({"role": msg.role, "content": msg.content})

        # Current input
        enhanced_input = self._enhance_task_input(user_input, app_state)
        context.append({"role": "user", "content": enhanced_input})

        return context

    def _get_enhanced_task_prompt(self, app_state: AppState) -> str:
        """
        Builds specific task prompt with context
        """
        context_info = app_state.get_context_summary()

        enhanced_prompt = self.system_prompt

        # Add project context
        if context_info.get("project_type") != "unknown":
            enhanced_prompt += f"\n\nCURRENT CONTEXT:\n"
            enhanced_prompt += f"- Project type: {context_info.get('project_type')}\n"
            enhanced_prompt += f"- Directory: {context_info.get('root_path')}\n"
            enhanced_prompt += f"- Existing files: {context_info.get('tracked_files')}\n"
            enhanced_prompt += "- CONSIDER existing project when planning steps\n"

        return enhanced_prompt

    def _enhance_task_input(self, user_input: str, app_state: AppState) -> str:
        """
        Adds relevant context to task input
        """
        context_info = app_state.get_context_summary()

        enhanced = f"TASK: {user_input}\n\n"

        # Add context if relevant
        if context_info.get("project_type") != "unknown":
            enhanced += f"CONTEXT: I'm working on a {context_info.get('project_type')} project "
            enhanced += f"in directory {context_info.get('root_path')}\n\n"

        enhanced += "Please create a structured plan following the specified format."

        return enhanced

    def _generate_task_response(
        self, context: List[Dict[str, str]], app_state: AppState
    ) -> LLMResponse:
        """
        Generates structured response for task
        """
        try:
            response = self.llm_provider.chat(
                messages=context,
                temperature=0.3,  # Lower temperature for more consistency
                max_tokens=4096,  # More tokens for detailed responses
            )
            return response

        except Exception as e:
            # Fallback
            prompt = self._context_to_prompt(context)
            return self.llm_provider.generate(prompt=prompt, temperature=0.3, max_tokens=4096)

    def _parse_task_response(self, response_content: str, original_input: str) -> TaskResult:
        """
        Parses AI response into structured TaskResult
        """
        try:
            # Extract basic information
            project_match = re.search(r"PROJETO:\s*(.+)", response_content)
            type_match = re.search(r"TIPO:\s*(.+)", response_content)
            complexity_match = re.search(r"COMPLEXIDADE:\s*(.+)", response_content)
            time_match = re.search(r"TEMPO ESTIMADO:\s*(.+)", response_content)

            # Extract dependencies
            dependencies = self._extract_dependencies(response_content)

            # Extract steps
            steps = self._extract_steps(response_content)

            # Extract notes
            notes = self._extract_notes(response_content)

            return TaskResult(
                description=(project_match.group(1).strip() if project_match else original_input),
                steps=steps,
                project_type=type_match.group(1).strip() if type_match else "unknown",
                estimated_time=time_match.group(1).strip() if time_match else "N/A",
                complexity=(complexity_match.group(1).strip() if complexity_match else "medium"),
                dependencies=dependencies,
                notes=notes,
            )

        except Exception as e:
            # Fallback: create basic result
            return TaskResult(
                description=original_input,
                steps=[],
                project_type="unknown",
                estimated_time="N/A",
                complexity="unknown",
                dependencies=[],
                notes=[
                    f"Parsing error: {str(e)}",
                    "Original response available in history",
                ],
            )

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extracts list of dependencies"""
        dependencies = []

        # Look for DEPENDENCIES section
        deps_match = re.search(r"DEPENDENCIES:\s*\n((?:- .+\n?)*)", content)
        if deps_match:
            for line in deps_match.group(1).split("\n"):
                if line.strip().startswith("- "):
                    dep = line.strip()[2:].strip()
                    if dep:
                        dependencies.append(dep)

        return dependencies

    def _extract_steps(self, content: str) -> List[TaskStep]:
        """Extracts structured steps"""
        steps = []

        # Procura seção STEPS
        steps_match = re.search(r"STEPS:\s*\n((?:\d+\s*-\s*.+\n?)*)", content)
        if not steps_match:
            return steps

        # Parseia cada step
        step_lines = steps_match.group(1).strip().split("\n")
        for line in step_lines:
            step = self._parse_step_line(line.strip())
            if step:
                steps.append(step)

        # Associate detailed content to steps
        self._associate_step_content(steps, content)

        return steps

    def _parse_step_line(self, line: str) -> Optional[TaskStep]:
        """Parses individual step line"""
        # Pattern: "1 - create src/app.py" or "2 - edit config.json" or "3 - command npm install"
        match = re.match(r"(\d+)\s*-\s*(create|edit|command)\s+(.+)", line)
        if not match:
            return None

        step_num = int(match.group(1))
        action = match.group(2)
        target = match.group(3).strip()

        return TaskStep(
            step_number=step_num,
            action=action,
            description=f"{action} {target}",
            target=target,
        )

    def _associate_step_content(self, steps: List[TaskStep], content: str):
        """Associates detailed content to steps"""
        for step in steps:
            if step.action in ["create", "edit"]:
                # Look for corresponding <code edit> block
                pattern = rf'=== STEP {step.step_number}:.*?===\s*\n<code edit filename="[^"]*">\s*\n(.*?)\n</code>'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    step.content = match.group(1).strip()

            elif step.action == "command":
                # Look for corresponding <commands> block
                pattern = (
                    rf"=== STEP {step.step_number}:.*?===\s*\n<commands>\s*\n(.*?)\n</commands>"
                )
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    commands = [
                        cmd.strip() for cmd in match.group(1).strip().split("\n") if cmd.strip()
                    ]
                    step.commands = commands

    def _extract_notes(self, content: str) -> List[str]:
        """Extracts important notes"""
        notes = []

        # Look for NOTES section
        notes_match = re.search(r"NOTAS:\s*\n((?:- .+\n?)*)", content)
        if notes_match:
            for line in notes_match.group(1).split("\n"):
                if line.strip().startswith("- "):
                    note = line.strip()[2:].strip()
                    if note:
                        notes.append(note)

        return notes

    def _context_to_prompt(self, context: List[Dict[str, str]]) -> str:
        """Converts context to single prompt (fallback)"""
        prompt_parts = []

        for message in context:
            role = message["role"]
            content = message["content"]

            if role == "system":
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(f"USER: {content}")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT: {content}")

        return "\n\n".join(prompt_parts)
