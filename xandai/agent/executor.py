"""
Task Executor

Executes task steps with retry and error handling.
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from xandai.agent.task_planner import TaskStep


@dataclass
class ExecutionResult:
    """Result of step execution"""

    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0


class TaskExecutor:
    """
    Task Executor

    Executes task steps with retry logic and error handling.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize task executor

        Args:
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute_step(
        self,
        step: TaskStep,
        executor_func: Callable[[TaskStep], Any],
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> ExecutionResult:
        """
        Execute a single step

        Args:
            step: Step to execute
            executor_func: Function to execute the step
            on_progress: Progress callback

        Returns:
            Execution result
        """
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                if on_progress:
                    on_progress(f"Executing: {step.description} (attempt {attempt + 1})")

                # Execute step
                result = executor_func(step)

                # Mark as completed
                step.completed = True
                step.result = str(result) if result else None

                duration = time.time() - start_time

                if on_progress:
                    on_progress(f"✓ Completed: {step.description}")

                return ExecutionResult(success=True, result=step.result, duration=duration)

            except Exception as e:
                error_msg = str(e)

                if attempt < self.max_retries - 1:
                    if on_progress:
                        on_progress(f"⚠ Retry {attempt + 1}/{self.max_retries}: {error_msg}")

                    time.sleep(self.retry_delay)
                else:
                    duration = time.time() - start_time

                    if on_progress:
                        on_progress(f"✗ Failed: {step.description}")

                    return ExecutionResult(success=False, error=error_msg, duration=duration)

        # Should not reach here
        return ExecutionResult(success=False, error="Unknown error")

    def execute_parallel(
        self, steps: list, executor_func: Callable, on_progress: Optional[Callable] = None
    ) -> list:
        """
        Execute multiple steps in parallel

        Args:
            steps: Steps to execute
            executor_func: Execution function
            on_progress: Progress callback

        Returns:
            List of execution results
        """
        # Simple sequential execution
        # In production, would use threading/asyncio
        results = []

        for step in steps:
            result = self.execute_step(step, executor_func, on_progress)
            results.append(result)

            # Stop on first failure if critical
            if not result.success:
                break

        return results

    def rollback_step(self, step: TaskStep, rollback_func: Optional[Callable] = None):
        """
        Rollback a step

        Args:
            step: Step to rollback
            rollback_func: Optional rollback function
        """
        if rollback_func:
            try:
                rollback_func(step)
            except Exception:
                pass  # Best effort rollback

        step.completed = False
        step.result = None
