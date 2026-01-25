from typing import Protocol, Optional, List, Tuple
from enum import Enum, auto

from mqttbot.core.tasks.stack.task_base import TaskBase
from mqttbot.core.threads.scheduler_context import Context


class TaskStatus(Enum):
    """External status reported to the Thread."""

    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SUSPENDED = auto()
    CANCELLED = auto()


class TaskState(Protocol):
    @property
    def external_status(self) -> TaskStatus: ...

    def on_enter(self, task: "TaskBase", ctx: "Context") -> None: ...

    def step(self, task: "TaskBase", ctx: "Context") -> Optional["TaskState"]:
        """
        Logic for this tick.
        Return a NEW state to push it onto the stack.
        Return None to stay in this state.
        Pop the stack (external logic) to finish this phase.
        """
        ...

    def handle_suspend(self, task: "TaskBase", ctx: "Context") -> Optional["TaskState"]: ...
