import logging
from abc import ABC, abstractmethod

from rich.repr import rich_repr

from mqttbot.core.context import Context
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.utils.tracing_tools import trace


@rich_repr
class TaskBase(ABC):
    priority: int = 0
    interruptible: bool = True
    intent: str = None
    log = logging.getLogger("task")
    status: TaskStatus = TaskStatus.READY

    _log_level: str = "DEBUG"

    @trace
    def enter(self, ctx):
        self._enter(ctx)

    def _enter(self, ctx: Context):
        """
        Default to resume behavior on enter.
        :param ctx: Task context
        """
        self._resume(ctx)

    # @trace
    def step(self, ctx: Context) -> TaskStatus:
        # print(f"Stepping task: {type(self).__name__}")
        return self._step(ctx)

    @abstractmethod
    def _step(self, ctx) -> TaskStatus:
        pass

    @trace
    def suspend(self) -> None:
        return self._suspend()

    def _suspend(self) -> None:
        pass

    @trace
    def resume(self, ctx) -> None:
        self._resume(ctx)

    def _resume(self, ctx) -> None:
        pass

    @trace
    def exit(self, ctx, status: TaskStatus):
        self._exit(ctx, status)

    def _exit(self, ctx, status: TaskStatus):
        pass

    def __rich_repr__(self):
        """Rich representation that varies based on log level."""
        # Always show class name

        # DEBUG level: show all relevant attributes
        if self._log_level == "DEBUG":
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
