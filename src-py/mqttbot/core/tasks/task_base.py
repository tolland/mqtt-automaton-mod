import importlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any

from rich.repr import rich_repr

from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_status import TaskInternalState, TaskStatus
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.utils.tracing_tools import trace, trace_task_state

# This import is down at the bottom to avoid circular imports
# importlib.import_module("mqttbot.core.tasks")
# prevent intellij from removing this import
inspect = importlib.import_module("rich").inspect


def task(name: str | None = None):
    def decorator(cls: type[TaskBase]):
        task_name = name or cls.__name__.removesuffix("Task").lower()
        TaskRegistry.register(task_name, cls)
        return cls

    return decorator


class TaskFactory:
    @staticmethod
    def create(data: dict) -> "Task":
        data = dict(data)
        task_type = data.pop("type")
        task_cls = TaskRegistry.get(task_type)
        return task_cls(**data)


class TaskRegistry:
    _registry: dict[str, type["TaskBase"]] = {}

    @classmethod
    def register(cls, name: str, task_cls: type["TaskBase"]) -> None:
        cls._registry[name] = task_cls

    @classmethod
    def get(cls, name: str) -> type["TaskBase"]:
        return cls._registry[name]


@rich_repr
class TaskBase(ABC, Task):
    interruptible: bool = True
    resumable: bool = False
    intent: str = None
    log = logging.getLogger("task")

    _log_level: str = "DEBUG"

    def __init__(self, metadata: dict[str, Any] | None = None):
        """Initialize task with correlation_id set to None (injected by thread on enqueue)"""
        self.request_id = str(uuid.uuid4())[-10:]
        self.correlation_id: str | None = None
        self._internal_status: TaskInternalState = TaskInternalState.INITIAL
        self.metadata = metadata or {}

    @property
    def status(self) -> TaskStatus:
        """Public status for the parent Thread/Scheduler."""
        return self._internal_status.external

    @property
    def status_internal(self) -> TaskInternalState:
        """Private status for the parent Thread/Scheduler."""
        return self._internal_status

    def enqueue(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id
        self.transition_to(TaskInternalState.ENQUEUED)

    def enter(self, ctx):
        self._enter(ctx)

    def _enter(self, ctx: Context):
        """
        Default to resume behavior on enter.
        :param ctx: Task context
        """
        self.transition_to(TaskInternalState.READY)

    def step(self, ctx: Context) -> TaskStatus:
        # print(f"Stepping task: {type(self).__name__}")
        return self._step(ctx)

    @abstractmethod
    def _step(self, ctx) -> TaskStatus:
        pass

    def suspend(self, ctx: Context) -> None:
        return self._suspend(ctx)

    def _suspend(self, ctx: Context) -> None:
        self.transition_to(TaskInternalState.SUSPENDING)

    def cancel(self, ctx: Context) -> None:
        return self._cancel(ctx)

    def _cancel(self, ctx: Context) -> None:
        """Default suspend behavior: set status to SUSPENDED"""
        self.transition_to(TaskInternalState.CANCELING)

    def resume(self, ctx) -> None:
        self._resume(ctx)

    def _resume(self, ctx) -> None:
        self.transition_to(TaskInternalState.RESUMING)

    @trace
    def exit(self, ctx, status: TaskStatus):
        self._exit(ctx, status)

    def _exit(self, ctx, status: TaskStatus):
        pass

    @trace_task_state
    def transition_to(self, next_state: TaskInternalState):
        """Enforces validity and updates the internal state."""
        # Use the transition map logic here and update internal status
        new_state = self._internal_status.transition_to(next_state)
        self._internal_status = new_state

    def to_dict(self) -> dict:
        """Return a dictionary representation of the task state."""
        state = {
            "type": type(self).__name__,
            "status": self.status.name,
            "correlation_id": self.correlation_id,
        }

        # Add common attributes if they exist
        if hasattr(self, "target"):
            state["target"] = self.target
        if hasattr(self, "request_id"):
            state["request_id"] = self.request_id

        return state

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __rich_repr__(self):
        """Rich representation that varies based on log level."""
        # Always show class name

        # DEBUG level: show all relevant attributes
        if self._log_level == "DEBUG":
            if hasattr(self, "correlation_id") and self.correlation_id:
                yield "correlation_id", f"...{self.correlation_id[-8:]}", None

            yield "request_id", self.request_id
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
            if hasattr(self, "_internal_status"):
                yield "_internal_status", str(self._internal_status)
            if hasattr(self, "status"):
                yield "status", str(self.status.name)
            if self.metadata:
                yield "metadata", self.metadata
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

# We need to force import of task implementations to allow registration
# for the TaskFactory to work. Howevr they need to have seen TaskBase first.
# hence down here seems to avoid circular import issues.
importlib.import_module("mqttbot.core.tasks.concrete")
