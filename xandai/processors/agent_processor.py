"""
XandAI Processors - Agent Processor
Multi-step LLM orchestrator with reasoning stages
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from xandai.core.app_state import AppState
from xandai.integrations.base_provider import LLMProvider, LLMResponse


class AgentStep:
    """Represents a single step in the agent pipeline"""

    def __init__(self, step_number: int, step_name: str, prompt: str):
        self.step_number = step_number
        self.step_name = step_name
        self.prompt = prompt
        self.response: Optional[str] = None
        self.tokens_used: int = 0
        self.model: str = ""
        self.timestamp: datetime = datetime.now()
        self.success: bool = False

    def set_response(self, response: LLMResponse):
        """Sets the response for this step"""
        self.response = response.content
        self.tokens_used = response.total_tokens
        self.model = response.model
        self.success = True

    def to_dict(self) -> Dict[str, Any]:
        """Converts step to dictionary"""
        return {
            "step_number": self.step_number,
            "step_name": self.step_name,
            "success": self.success,
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentResult:
    """Result of agent execution"""

    def __init__(self):
        self.steps: List[AgentStep] = []
        self.total_calls: int = 0
        self.total_tokens: int = 0
        self.success: bool = False
        self.final_output: str = ""
        self.error_message: Optional[str] = None
        self.completed_task: bool = False
        self.stopped_reason: str = ""  # "completed", "limit_reached", "error"
        self.files_created: List[str] = []  # Track files created
        self.files_edited: List[str] = []  # Track files edited
        self.commands_executed: List[Tuple[str, str]] = []  # Track (command, output)

    def add_step(self, step: AgentStep):
        """Adds a step to the result"""
        self.steps.append(step)
        self.total_calls += 1
        self.total_tokens += step.tokens_used

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to dictionary"""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "success": self.success,
            "completed_task": self.completed_task,
            "stopped_reason": self.stopped_reason,
            "steps": [step.to_dict() for step in self.steps],
        }


class AgentProcessor:
    """
    Agent Mode Processor

    Multi-step LLM orchestrator that chains multiple model calls
    to process complex instructions through reasoning stages.
    """

    DEFAULT_MAX_CALLS = 20

    def __init__(self, llm_provider: LLMProvider, conversation_manager, tool_manager=None):
        self.llm_provider = llm_provider
        self.conversation_manager = conversation_manager
        self.tool_manager = tool_manager
        self.max_calls = self.DEFAULT_MAX_CALLS
        self.verbose = os.getenv("XANDAI_VERBOSE", "0") == "1"

        # Detect if using HistoryManager or ConversationManager
        self._use_history_manager = hasattr(conversation_manager, "add_conversation")

    def set_max_calls(self, max_calls: int):
        """Sets the maximum number of LLM calls"""
        if max_calls < 1:
            raise ValueError("max_calls must be at least 1")
        if max_calls > 100:
            raise ValueError("max_calls cannot exceed 100")
        self.max_calls = max_calls

    def process(self, user_instruction: str, app_state: AppState) -> AgentResult:
        """
        Processes user instruction through multi-step LLM pipeline

        Args:
            user_instruction: Natural language instruction from user
            app_state: Current application state

        Returns:
            AgentResult with execution details
        """
        result = AgentResult()

        # Add user message to history
        self._add_to_history(
            role="user",
            content=user_instruction,
            mode="agent",
            metadata={"app_state": app_state.get_context_summary()},
        )

        try:
            # Step 1: Analyze intent
            intent_step = self._step_1_analyze_intent(user_instruction, app_state)
            result.add_step(intent_step)

            if not intent_step.success:
                result.stopped_reason = "error"
                result.error_message = "Failed to analyze intent"
                return result

            intent_data = self._parse_intent(intent_step.response)

            # Step 2: Gather context
            context_step = self._step_2_gather_context(user_instruction, intent_data, app_state)
            result.add_step(context_step)

            if not context_step.success:
                result.stopped_reason = "error"
                result.error_message = "Failed to gather context"
                return result

            context_data = self._parse_context(context_step.response)

            # Step 3: Execute main task
            task_step = self._step_3_execute_task(
                user_instruction, intent_data, context_data, app_state
            )
            result.add_step(task_step)

            if not task_step.success:
                result.stopped_reason = "error"
                result.error_message = "Failed to execute main task"
                return result

            # Step 4: Post-process and validate (optional)
            validation_step = self._step_4_validate_output(
                user_instruction, task_step.response, app_state
            )
            result.add_step(validation_step)

            if not validation_step.success:
                result.stopped_reason = "error"
                result.error_message = "Failed to validate output"
                return result

            # Check if task is complete
            is_complete = self._check_task_completion(validation_step.response)
            result.completed_task = is_complete

            # If task is not complete and we haven't reached limit, continue
            iteration = 0
            max_iterations = self.max_calls - 4  # Already used 4 calls

            while not is_complete and iteration < max_iterations:
                iteration += 1

                # Step N: Refine or continue task
                refinement_step = self._step_n_refine_task(
                    user_instruction,
                    task_step.response,
                    validation_step.response,
                    iteration,
                    app_state,
                )
                result.add_step(refinement_step)

                if not refinement_step.success:
                    result.stopped_reason = "error"
                    result.error_message = f"Failed at refinement step {iteration}"
                    break

                # Update task response
                task_step.response = refinement_step.response

                # Re-validate
                validation_step = self._step_4_validate_output(
                    user_instruction, task_step.response, app_state
                )
                result.add_step(validation_step)

                if not validation_step.success:
                    result.stopped_reason = "error"
                    result.error_message = f"Failed validation at iteration {iteration}"
                    break

                is_complete = self._check_task_completion(validation_step.response)
                result.completed_task = is_complete

                if is_complete:
                    break

            # Set final output and status
            result.final_output = task_step.response
            result.success = True

            # Process output tags (code creation, edits, commands)
            self._process_output_tags(result.final_output, result)

            if is_complete:
                result.stopped_reason = "completed"
            else:
                result.stopped_reason = "limit_reached"

            # Add result to conversation history
            self._add_to_history(
                role="assistant",
                content=result.final_output,
                mode="agent",
                metadata={
                    "total_calls": result.total_calls,
                    "total_tokens": result.total_tokens,
                    "stopped_reason": result.stopped_reason,
                },
            )

        except Exception as e:
            result.stopped_reason = "error"
            result.error_message = str(e)
            result.success = False

        return result

    def _step_1_analyze_intent(self, user_instruction: str, app_state: AppState) -> AgentStep:
        """Step 1: Analyze user instruction and classify intent"""
        step = AgentStep(
            step_number=1,
            step_name="Analyze Intent",
            prompt=self._build_intent_prompt(user_instruction, app_state),
        )

        if self.verbose:
            print(f"[Step 1] Analyzing intent...")

        try:
            response = self.llm_provider.generate(
                prompt=step.prompt,
                temperature=0.3,  # Lower temperature for classification
                max_tokens=500,
            )
            step.set_response(response)
            if self.verbose:
                print(f"[Step 1] ✓ Intent analyzed - {step.tokens_used} tokens")
        except Exception as e:
            if self.verbose:
                print(f"[Step 1] ✗ Error: {e}")

        return step

    def _step_2_gather_context(
        self, user_instruction: str, intent_data: Dict[str, Any], app_state: AppState
    ) -> AgentStep:
        """Step 2: Gather relevant context based on intent"""
        step = AgentStep(
            step_number=2,
            step_name="Gather Context",
            prompt=self._build_context_prompt(user_instruction, intent_data, app_state),
        )

        if self.verbose:
            print(f"[Step 2] Gathering context...")

        try:
            response = self.llm_provider.generate(
                prompt=step.prompt, temperature=0.3, max_tokens=1000
            )
            step.set_response(response)
            if self.verbose:
                print(f"[Step 2] ✓ Context gathered - {step.tokens_used} tokens")
        except Exception as e:
            if self.verbose:
                print(f"[Step 2] ✗ Error: {e}")

        return step

    def _step_3_execute_task(
        self,
        user_instruction: str,
        intent_data: Dict[str, Any],
        context_data: Dict[str, Any],
        app_state: AppState,
    ) -> AgentStep:
        """Step 3: Execute the main task"""
        step = AgentStep(
            step_number=3,
            step_name="Execute Task",
            prompt=self._build_task_prompt(user_instruction, intent_data, context_data, app_state),
        )

        if self.verbose:
            print(f"[Step 3] Executing main task...")

        try:
            response = self.llm_provider.generate(
                prompt=step.prompt,
                temperature=0.7,  # Higher temperature for creative tasks
                max_tokens=2048,
            )
            step.set_response(response)
            if self.verbose:
                print(f"[Step 3] ✓ Task executed - {step.tokens_used} tokens")
        except Exception as e:
            if self.verbose:
                print(f"[Step 3] ✗ Error: {e}")

        return step

    def _step_4_validate_output(
        self, user_instruction: str, task_output: str, app_state: AppState
    ) -> AgentStep:
        """Step 4: Validate and post-process the output"""
        step = AgentStep(
            step_number=4,
            step_name="Validate Output",
            prompt=self._build_validation_prompt(user_instruction, task_output),
        )

        if self.verbose:
            print(f"[Step 4] Validating output...")

        try:
            response = self.llm_provider.generate(
                prompt=step.prompt,
                temperature=0.2,  # Very low temperature for validation
                max_tokens=500,
            )
            step.set_response(response)
            if self.verbose:
                print(f"[Step 4] ✓ Output validated - {step.tokens_used} tokens")
        except Exception as e:
            if self.verbose:
                print(f"[Step 4] ✗ Error: {e}")

        return step

    def _step_n_refine_task(
        self,
        user_instruction: str,
        current_output: str,
        validation_feedback: str,
        iteration: int,
        app_state: AppState,
    ) -> AgentStep:
        """Step N: Refine task based on validation feedback"""
        step = AgentStep(
            step_number=4 + iteration,
            step_name=f"Refinement {iteration}",
            prompt=self._build_refinement_prompt(
                user_instruction, current_output, validation_feedback
            ),
        )

        if self.verbose:
            print(f"[Step {4 + iteration}] Refining output (iteration {iteration})...")

        try:
            response = self.llm_provider.generate(
                prompt=step.prompt, temperature=0.6, max_tokens=2048
            )
            step.set_response(response)
            if self.verbose:
                print(f"[Step {4 + iteration}] ✓ Refinement complete - {step.tokens_used} tokens")
        except Exception as e:
            if self.verbose:
                print(f"[Step {4 + iteration}] ✗ Error: {e}")

        return step

    # Prompt builders

    def _build_intent_prompt(self, user_instruction: str, app_state: AppState) -> str:
        """Builds prompt for intent analysis"""
        context_info = app_state.get_context_summary()

        return f"""Analyze the following user instruction and classify its intent.

USER INSTRUCTION: "{user_instruction}"

PROJECT CONTEXT:
- Type: {context_info.get('project_type', 'unknown')}
- Directory: {context_info.get('root_path', 'unknown')}

TASK:
Classify the intent into one of these categories:
- code_fix: Fix bugs or errors in code
- code_explain: Explain how code works
- code_create: Create new code or functionality
- code_analyze: Analyze code quality or patterns
- code_refactor: Improve or restructure existing code
- general: General question or conversation

Respond in this format:
INTENT: [category]
COMPLEXITY: [simple/moderate/complex]
REQUIRES_FILES: [yes/no]
FILE_PATTERNS: [file extensions or patterns needed, if any]
SUMMARY: [brief summary of what needs to be done]"""

    def _build_context_prompt(
        self, user_instruction: str, intent_data: Dict[str, Any], app_state: AppState
    ) -> str:
        """Builds prompt for context gathering"""
        context_info = app_state.get_context_summary()

        return f"""Based on the user instruction and detected intent, identify what contextual information is needed.

USER INSTRUCTION: "{user_instruction}"

DETECTED INTENT:
{self._format_dict(intent_data)}

PROJECT CONTEXT:
- Type: {context_info.get('project_type', 'unknown')}
- Directory: {context_info.get('root_path', 'unknown')}
- Tracked files: {context_info.get('tracked_files', 0)}

TASK:
List what information or context is needed to complete this task.

Respond in this format:
CONTEXT_NEEDED:
- [item 1]
- [item 2]
...

CURRENT_DIRECTORY_RELEVANT: [yes/no]
EXTERNAL_INFO_NEEDED: [yes/no]
SUMMARY: [brief summary of context requirements]"""

    def _build_task_prompt(
        self,
        user_instruction: str,
        intent_data: Dict[str, Any],
        context_data: Dict[str, Any],
        app_state: AppState,
    ) -> str:
        """Builds prompt for main task execution"""
        tools_info = ""
        if self.tool_manager:
            available_tools = self.tool_manager.get_available_tools()
            if available_tools:
                tools_list = "\n".join(
                    [f"  - {t['name']}: {t['description']}" for t in available_tools]
                )
                tools_info = f"""

AVAILABLE TOOLS:
{tools_list}
You can invoke tools by mentioning them naturally in your response."""

        return f"""Now execute the main task based on the user instruction and gathered information.

USER INSTRUCTION: "{user_instruction}"

INTENT ANALYSIS:
{self._format_dict(intent_data)}

CONTEXT GATHERED:
{self._format_dict(context_data)}
{tools_info}

TASK:
Execute the requested task. Provide a complete, well-formatted response.

*** CRITICAL: File Creation Syntax ***
When creating files, you MUST use this exact format (DO NOT use markdown code blocks):

<code create filename="path/to/file.ext">
file content here
</code>

Examples:
- <code create filename="main.py">print("Hello")</code>
- <code create filename="src/app.js">console.log("test")</code>
- <code create filename="config.json">{{"key": "value"}}</code>

To edit existing files:
<code edit filename="file.py">updated content</code>

To run commands:
<command>your command here</command>

*** IMPORTANT RULES ***
1. For code creation tasks, ALWAYS use <code create filename="..."> tags
2. DO NOT use markdown code blocks (```language ... ```) for files to be created
3. Each file must be wrapped in its own <code create> tag
4. Use complete file paths including directories (e.g., "src/models/user.py")
5. Include ALL file content - no placeholders or "..." abbreviations

For code-related tasks:
- Create ALL necessary files using <code create> tags
- Include complete, working code with proper syntax
- Add helpful comments and documentation
- Consider project structure and best practices

For explanation tasks:
- Be clear and thorough
- Use examples when appropriate
- You CAN use markdown code blocks for examples (not for actual file creation)

Provide your response below:"""

    def _build_validation_prompt(self, user_instruction: str, task_output: str) -> str:
        """Builds prompt for output validation"""
        return f"""Validate if the following output correctly addresses the user's instruction.

USER INSTRUCTION: "{user_instruction}"

GENERATED OUTPUT:
{task_output[:2000]}  # Limit to avoid token overflow

TASK:
Evaluate the output and respond in this format:

COMPLETE: [yes/no - is the task fully completed?]
QUALITY: [poor/adequate/good/excellent]
ISSUES: [list any issues found, or "none"]
SUGGESTIONS: [list improvements if needed, or "none"]
VERDICT: [one sentence summary]

SPECIAL VALIDATION RULES:
- If the task involves creating files, check if <code create filename="..."> tags are used
- If markdown code blocks (```language) are used instead of <code create> tags, mark COMPLETE: no
- Files must use <code create> tags, NOT markdown blocks
- All file content must be complete (no "..." or truncation)"""

    def _build_refinement_prompt(
        self, user_instruction: str, current_output: str, validation_feedback: str
    ) -> str:
        """Builds prompt for task refinement"""
        return f"""Refine the output based on validation feedback.

USER INSTRUCTION: "{user_instruction}"

CURRENT OUTPUT:
{current_output[:2000]}

VALIDATION FEEDBACK:
{validation_feedback}

TASK:
Improve the output to address the validation feedback. Provide the refined, complete response below.

*** CRITICAL: File Creation Syntax ***
When creating files, you MUST use this exact format:

<code create filename="path/to/file.ext">
complete file content here
</code>

Examples:
- <code create filename="main.py">print("Hello")</code>
- <code create filename="src/controller.py">class Controller: pass</code>

*** IMPORTANT RULES ***
1. ALWAYS use <code create filename="..."> tags for file creation
2. DO NOT use markdown code blocks (```python ... ```) for actual files
3. Include COMPLETE file content - no truncation or "..."
4. Each file needs its own <code create> tag

Provide the refined response below:"""

    # Helper methods

    def _parse_intent(self, intent_response: str) -> Dict[str, Any]:
        """Parses intent response into structured data"""
        intent_data = {
            "intent": "general",
            "complexity": "moderate",
            "requires_files": False,
            "file_patterns": [],
            "summary": "",
        }

        if not intent_response:
            return intent_data

        lines = intent_response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("INTENT:"):
                intent_data["intent"] = line.split(":", 1)[1].strip()
            elif line.startswith("COMPLEXITY:"):
                intent_data["complexity"] = line.split(":", 1)[1].strip()
            elif line.startswith("REQUIRES_FILES:"):
                value = line.split(":", 1)[1].strip().lower()
                intent_data["requires_files"] = value == "yes"
            elif line.startswith("FILE_PATTERNS:"):
                patterns = line.split(":", 1)[1].strip()
                if patterns and patterns.lower() != "none":
                    intent_data["file_patterns"] = [p.strip() for p in patterns.split(",")]
            elif line.startswith("SUMMARY:"):
                intent_data["summary"] = line.split(":", 1)[1].strip()

        return intent_data

    def _parse_context(self, context_response: str) -> Dict[str, Any]:
        """Parses context response into structured data"""
        context_data = {
            "context_needed": [],
            "current_directory_relevant": True,
            "external_info_needed": False,
            "summary": "",
        }

        if not context_response:
            return context_data

        lines = context_response.split("\n")
        in_context_list = False

        for line in lines:
            line = line.strip()

            if line.startswith("CONTEXT_NEEDED:"):
                in_context_list = True
                continue
            elif in_context_list and line.startswith("-"):
                context_data["context_needed"].append(line[1:].strip())
            elif line.startswith("CURRENT_DIRECTORY_RELEVANT:"):
                value = line.split(":", 1)[1].strip().lower()
                context_data["current_directory_relevant"] = value == "yes"
                in_context_list = False
            elif line.startswith("EXTERNAL_INFO_NEEDED:"):
                value = line.split(":", 1)[1].strip().lower()
                context_data["external_info_needed"] = value == "yes"
            elif line.startswith("SUMMARY:"):
                context_data["summary"] = line.split(":", 1)[1].strip()

        return context_data

    def _check_task_completion(self, validation_response: str) -> bool:
        """Checks if task is complete based on validation"""
        if not validation_response:
            return False

        lines = validation_response.split("\n")
        for line in lines:
            if line.strip().startswith("COMPLETE:"):
                value = line.split(":", 1)[1].strip().lower()
                return value == "yes"

        return False

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Formats dictionary for prompt inclusion"""
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _add_to_history(
        self, role: str, content: str, mode: str = "agent", metadata: Dict[str, Any] = None
    ):
        """Add message to history - compatible with both HistoryManager and ConversationManager"""
        if self._use_history_manager:
            # HistoryManager interface
            self.conversation_manager.add_conversation(
                role=role, content=content, metadata={**(metadata or {}), "mode": mode}
            )
        else:
            # ConversationManager interface
            self.conversation_manager.add_message(
                role=role, content=content, mode=mode, metadata=metadata
            )

    def _process_output_tags(self, output: str, result: AgentResult):
        """Process <code> and <command> tags in agent output"""
        import re

        if self.verbose:
            print("[DEBUG] Processing output tags...")

        # Process <code create> tags
        code_pattern = r'<code\s+create\s+filename="([^"]+)">(.+?)</code>'
        code_matches = re.findall(code_pattern, output, re.DOTALL)

        for filename, code_content in code_matches:
            try:
                self._create_file_from_code(filename, code_content.strip(), result)
            except Exception as e:
                if self.verbose:
                    print(f"[DEBUG] Failed to create file {filename}: {e}")

        # Process <code edit> tags
        edit_pattern = r'<code\s+edit\s+filename="([^"]+)">(.+?)</code>'
        edit_matches = re.findall(edit_pattern, output, re.DOTALL)

        for filename, code_content in edit_matches:
            try:
                self._edit_file_from_code(filename, code_content.strip(), result)
            except Exception as e:
                if self.verbose:
                    print(f"[DEBUG] Failed to edit file {filename}: {e}")

        # Process <command> tags
        command_pattern = r"<command>(.+?)</command>"
        command_matches = re.findall(command_pattern, output, re.DOTALL)

        for command in command_matches:
            try:
                self._execute_command(command.strip(), result)
            except Exception as e:
                if self.verbose:
                    print(f"[DEBUG] Failed to execute command '{command.strip()}': {e}")

    def _create_file_from_code(self, filename: str, code_content: str, result: AgentResult):
        """Create a file from code block"""

        # Create directory if needed
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            if self.verbose:
                print(f"[DEBUG] Created directory: {directory}")

        # Write file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_content)

        result.files_created.append(filename)

        if self.verbose:
            print(f"[DEBUG] ✓ Created file: {filename} ({len(code_content)} chars)")

    def _edit_file_from_code(self, filename: str, code_content: str, result: AgentResult):
        """Edit/update an existing file"""

        file_exists = os.path.exists(filename)

        if not file_exists:
            if self.verbose:
                print(f"[DEBUG] File {filename} doesn't exist, creating it...")
            self._create_file_from_code(filename, code_content, result)
            return

        # Overwrite file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_content)

        # Track as edited (not created)
        if filename not in result.files_edited:
            result.files_edited.append(filename)

        if self.verbose:
            print(f"[DEBUG] ✓ Updated file: {filename}")

    def _execute_command(self, command: str, result: AgentResult):
        """Execute a shell command"""
        import platform
        import subprocess

        try:
            # Determine shell based on platform
            if platform.system() == "Windows":
                shell_args = ["powershell", "-Command", command]
            else:
                shell_args = ["bash", "-c", command]

            # Execute command
            process = subprocess.run(
                shell_args, capture_output=True, text=True, timeout=30  # 30 second timeout
            )

            output = process.stdout + process.stderr
            result.commands_executed.append((command, output))

            if self.verbose:
                print(f"[DEBUG] ✓ Executed command: {command}")
                if output:
                    print(f"[DEBUG] Output: {output[:200]}...")

        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"[DEBUG] ✗ Command timed out: {command}")
            result.commands_executed.append((command, "TIMEOUT"))
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] ✗ Command failed: {command} - {e}")
            result.commands_executed.append((command, f"ERROR: {e}"))
