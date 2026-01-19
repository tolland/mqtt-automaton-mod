import logging
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional

from rich.repr import rich_repr

from mqttbot.core.context import Context
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState


@rich_repr
class TaskBase(ABC):
    priority: int = 0
    interruptible: bool = True
    intent: str = None
    log = logging.getLogger("task")
    status: TaskStatus = TaskStatus.READY

    _log_level: str = "DEBUG"

    def __init__(self):
        """Initialize task with correlation_id set to None (injected by thread on enqueue)"""
        self.correlation_id: Optional[str] = None
        self._state: TaskState = TaskState.READY

    def enter(self, ctx):
        self._enter(ctx)

    def _enter(self, ctx: Context):
        """
        Default to resume behavior on enter.
        :param ctx: Task context
        """
        self._resume(ctx)

    def step(self, ctx: Context) -> TaskStatus:
        # print(f"Stepping task: {type(self).__name__}")
        return self._step(ctx)

    @abstractmethod
    def _step(self, ctx) -> TaskStatus:
        pass

    def suspend(self, ctx: Context) -> None:
        self.status = TaskStatus.SUSPENDED
        return self._suspend(ctx)

    def _suspend(self, ctx: Context) -> None:
        pass

    def resume(self, ctx) -> None:
        self.status = TaskStatus.RUNNING
        self._resume(ctx)

    def _resume(self, ctx) -> None:
        pass

    def exit(self, ctx, status: TaskStatus):
        self._exit(ctx, status)

    def _exit(self, ctx, status: TaskStatus):
        pass

    def to_dict(self) -> dict:
        """Return a dictionary representation of the task state."""
        state = {
            "type": type(self).__name__,
            "status": self.status.name,
            "state": self._state.name if hasattr(self, "_state") and isinstance(self._state, Enum) else str(self._state),
            "correlation_id": self.correlation_id,
        }

        # Add common attributes if they exist
        if hasattr(self, "target"):
            state["target"] = self.target
        if hasattr(self, "request_id"):
            state["request_id"] = self.request_id

        return state

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    def __rich_repr__(self):
        """Rich representation that varies based on log level."""
        # Always show class name

        # DEBUG level: show all relevant attributes
        if self._log_level == "DEBUG":
            if hasattr(self, "correlation_id") and self.correlation_id:
                yield "correlation_id", self.correlation_id
            if hasattr(self, "interruptible") and not self.interruptible:
                yield "interruptible", self.interruptible

            # Show task-specific attributes (common ones)
            if hasattr(self, "target"):
                yield "target", self.target
            if hasattr(self, "sent"):
                yield "sent", self.sent
            if hasattr(self, "steps") and self.steps:
                yield "steps_count", len(self.steps)
            if hasattr(self, "stage"):
                yield "stage", self.stage
            if hasattr(self, "service"):
                yield "service", self.service
            if hasattr(self, "method"):
                yield "method", self.method

            # Show state if available
            if hasattr(self, "_state"):
                yield "state", str(self._state)
            if hasattr(self, "status"):
                yield "status", str(self.status)
            if hasattr(self, "params"):
                yield "params", self.params

        # INFO level: show key attributes only
        elif self._log_level == "INFO":
            if hasattr(self, "target"):
                yield "target", self.target
            elif hasattr(self, "waypoint"):
                yield "waypoint", self.waypoint
            elif hasattr(self, "steps") and self.steps:
                yield "steps", len(self.steps)
            if hasattr(self, "service"):
                yield "service", self.service
            if hasattr(self, "method"):
                yield "method", self.method

        # WARNING/ERROR: minimal info (just class name, already shown)
