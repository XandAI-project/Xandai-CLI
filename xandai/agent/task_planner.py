"""
Task Planner

Decomposes complex tasks into manageable steps.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class StepType(Enum):
    """Type of task step"""

    ANALYZE = "analyze"
    CODE = "code"
    TEST = "test"
    REVIEW = "review"
    EXECUTE = "execute"
    DOCUMENT = "document"


@dataclass
class TaskStep:
    """Individual task step"""

    id: int
    description: str
    step_type: StepType
    dependencies: List[int]
    estimated_complexity: float  # 0.0 to 1.0
    completed: bool = False
    result: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "step_type": self.step_type.value,
            "dependencies": self.dependencies,
            "estimated_complexity": self.estimated_complexity,
            "completed": self.completed,
            "result": self.result,
        }


class TaskPlanner:
    """
    Task Planner

    Decomposes tasks into executable steps with dependencies.
    """

    def __init__(self):
        """Initialize task planner"""
        self.step_counter = 0

    def plan_task(self, description: str) -> List[TaskStep]:
        """
        Create a plan for a task

        Args:
            description: Task description

        Returns:
            List of steps
        """
        # Analyze task to determine steps
        steps = []

        # Simple heuristic-based planning
        # In production, this would use LLM to generate plan

        keywords = description.lower()

        # Always start with analysis
        steps.append(
            self._create_step("Analyze requirements and approach", StepType.ANALYZE, [], 0.2)
        )

        # Code generation if needed
        if any(word in keywords for word in ["create", "build", "implement", "write", "code"]):
            steps.append(
                self._create_step("Implement core functionality", StepType.CODE, [steps[0].id], 0.5)
            )

        # Testing
        if any(word in keywords for word in ["test", "verify", "check"]):
            steps.append(
                self._create_step(
                    "Write and run tests",
                    StepType.TEST,
                    [s.id for s in steps if s.step_type == StepType.CODE],
                    0.3,
                )
            )

        # Review/optimize
        if any(word in keywords for word in ["optimize", "improve", "refactor", "review"]):
            steps.append(
                self._create_step(
                    "Review and optimize", StepType.REVIEW, [s.id for s in steps], 0.3
                )
            )

        # Documentation
        if any(word in keywords for word in ["document", "doc", "readme"]):
            steps.append(
                self._create_step(
                    "Generate documentation",
                    StepType.DOCUMENT,
                    [s.id for s in steps if s.step_type in [StepType.CODE, StepType.REVIEW]],
                    0.2,
                )
            )

        # If no specific steps identified, add generic execution
        if len(steps) == 1:  # Only analysis
            steps.append(self._create_step("Execute task", StepType.EXECUTE, [steps[0].id], 0.5))

        return steps

    def _create_step(
        self, description: str, step_type: StepType, dependencies: List[int], complexity: float
    ) -> TaskStep:
        """Create a task step"""
        step = TaskStep(
            id=self.step_counter,
            description=description,
            step_type=step_type,
            dependencies=dependencies,
            estimated_complexity=complexity,
        )
        self.step_counter += 1
        return step

    def get_next_steps(self, steps: List[TaskStep]) -> List[TaskStep]:
        """
        Get steps that can be executed next

        Args:
            steps: All steps

        Returns:
            Steps ready for execution
        """
        ready = []

        for step in steps:
            if step.completed:
                continue

            # Check if all dependencies are completed
            deps_completed = all(
                any(s.id == dep_id and s.completed for s in steps) for dep_id in step.dependencies
            )

            if not step.dependencies or deps_completed:
                ready.append(step)

        return ready

    def estimate_total_complexity(self, steps: List[TaskStep]) -> float:
        """Estimate total task complexity"""
        return sum(s.estimated_complexity for s in steps)

    def calculate_progress(self, steps: List[TaskStep]) -> float:
        """
        Calculate task progress

        Args:
            steps: All steps

        Returns:
            Progress (0.0 to 1.0)
        """
        if not steps:
            return 0.0

        completed_complexity = sum(s.estimated_complexity for s in steps if s.completed)
        total_complexity = self.estimate_total_complexity(steps)

        if total_complexity == 0:
            return 0.0

        return completed_complexity / total_complexity
