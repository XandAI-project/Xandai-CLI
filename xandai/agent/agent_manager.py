"""
Agent Manager

Manages multi-step agent workflows with planning and execution.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Agent task definition"""

    id: str
    description: str
    status: TaskStatus
    created_at: str
    updated_at: str
    steps: List[Any] = field(default_factory=list)
    current_step: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0  # 0.0 to 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "steps": [
                step.to_dict() if hasattr(step, "to_dict") else str(step) for step in self.steps
            ],
            "current_step": self.current_step,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "progress": self.progress,
        }


class AgentManager:
    """
    Agent Manager

    Orchestrates multi-step agent workflows.
    """

    def __init__(self):
        """Initialize agent manager"""
        self.tasks: Dict[str, AgentTask] = {}
        self.active_task: Optional[AgentTask] = None
        self.callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_fail": [],
            "on_step_start": [],
            "on_step_complete": [],
        }

    def create_task(self, description: str, **metadata) -> AgentTask:
        """
        Create a new task

        Args:
            description: Task description
            **metadata: Additional metadata

        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        task = AgentTask(
            id=task_id,
            description=description,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )

        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[AgentTask]:
        """
        List all tasks

        Args:
            status: Filter by status

        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by creation date (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks

    def update_task_status(self, task_id: str, status: TaskStatus, error: Optional[str] = None):
        """Update task status"""
        task = self.get_task(task_id)
        if not task:
            return

        task.status = status
        task.updated_at = datetime.now().isoformat()

        if error:
            task.error = error

        # Trigger callbacks
        if status == TaskStatus.RUNNING:
            self._trigger_callbacks("on_task_start", task)
        elif status == TaskStatus.COMPLETED:
            self._trigger_callbacks("on_task_complete", task)
        elif status == TaskStatus.FAILED:
            self._trigger_callbacks("on_task_fail", task)

    def update_progress(self, task_id: str, progress: float):
        """Update task progress (0.0 to 1.0)"""
        task = self.get_task(task_id)
        if task:
            task.progress = max(0.0, min(1.0, progress))
            task.updated_at = datetime.now().isoformat()

    def set_active_task(self, task_id: str):
        """Set the active task"""
        task = self.get_task(task_id)
        if task:
            self.active_task = task

    def get_active_task(self) -> Optional[AgentTask]:
        """Get the currently active task"""
        return self.active_task

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False

        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now().isoformat()

        if self.active_task and self.active_task.id == task_id:
            self.active_task = None

        return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]

            if self.active_task and self.active_task.id == task_id:
                self.active_task = None

            return True

        return False

    def register_callback(self, event: str, callback: Callable):
        """
        Register a callback for an event

        Args:
            event: Event name (on_task_start, on_task_complete, etc.)
            callback: Callback function
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str, task: AgentTask):
        """Trigger callbacks for an event"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(task)
                except Exception:
                    pass  # Don't let callback errors break execution

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total = len(self.tasks)
        by_status = {}

        for status in TaskStatus:
            count = len([t for t in self.tasks.values() if t.status == status])
            by_status[status.value] = count

        completed = by_status.get(TaskStatus.COMPLETED.value, 0)
        failed = by_status.get(TaskStatus.FAILED.value, 0)
        success_rate = (completed / total * 100) if total > 0 else 0

        return {
            "total_tasks": total,
            "by_status": by_status,
            "success_rate": success_rate,
            "active_task": self.active_task.id if self.active_task else None,
        }
