import logging
from abc import ABC, abstractmethod, ABCMeta
from typing import Type

from mqttbot.core.tasks.task_priority import TaskStatus
from rich import print as rprint
from rich.pretty import pprint
from rich.repr import rich_repr

from mqttbot.core.context import Context


def trace(fn):
    def wrapper(self, *a, **kw):
        # Print entry with method name and rich repr
        print(f"{fn.__name__}: enter")
        pprint(self)

        try:
            result = fn(self, *a, **kw)
            # Print exit with method name and rich repr
            print(f"{fn.__name__}: exit")
            pprint(self)
            return result
        except Exception as e:
            # Print exit with error
            print(f"{fn.__name__}: exit (error: {e})")
            pprint(self)
            raise e

    return wrapper


class TaskMeta(ABCMeta):
    registry: dict[str, Type["Task"]] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Task":  # Skip the base class
            task_name = namespace.get("task_name", name.removesuffix("Task").lower())
            mcs.registry[task_name] = cls
        return cls


@rich_repr
class Task(ABC, metaclass=TaskMeta):
    priority: int = 0
    interruptible: bool = True
    intent: str = None
    log = logging.getLogger("task")
    status: TaskStatus = TaskStatus.READY

    # Class variable for log level (set from Settings)
    _log_level: str = "INFO"

    def _debug_log(self, transition: str, **kwargs) -> None:
        """Log task transition if log level is DEBUG."""
        if self._log_level == "DEBUG":
            task_name = type(self).__name__
            details = ", ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
            rprint(
                f"[dim cyan][TASK][/dim cyan] [bold]{task_name}[/bold] {transition}"
                + (f": {details}" if details else "")
            )

    @trace
    def enter(self, ctx):
        self._enter(ctx)

    def _enter(self, ctx: Context):
        """
        Default to resume behavior on enter.
        :param ctx: Task context
        """
        self._resume(ctx)

    @trace
    def step(self, ctx: Context) -> TaskStatus:
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

    @classmethod
    def set_log_level(cls, level: str) -> None:
        """Set the log level for Task rich repr output.

        Args:
            level: Log level string (DEBUG, INFO, WARNING, ERROR)
        """
        cls._log_level = level.upper()

    def __rich_repr__(self):
        """Rich representation that varies based on log level."""
        # Always show class name
        yield "class", type(self).__name__

        # DEBUG level: show all relevant attributes
        if self._log_level == "DEBUG":
            if hasattr(self, "priority") and self.priority != 0:
                yield "priority", self.priority
            if hasattr(self, "interruptible") and not self.interruptible:
                yield "interruptible", self.interruptible
            if hasattr(self, "intent") and self.intent:
                yield "intent", self.intent

            # Show task-specific attributes (common ones)
            if hasattr(self, "target"):
                yield "target", self.target
            if hasattr(self, "sent"):
                yield "sent", self.sent
            if hasattr(self, "index"):
                yield "index", self.index
            if hasattr(self, "steps") and self.steps:
                yield "steps_count", len(self.steps)
            if hasattr(self, "stage"):
                yield "stage", self.stage
            if hasattr(self, "waypoint"):
                yield "waypoint", self.waypoint
            if hasattr(self, "patterns"):
                yield "patterns", self.patterns
            if hasattr(self, "service"):
                yield "service", self.service
            if hasattr(self, "method"):
                yield "method", self.method

            # Show state if available
            if hasattr(self, "_state"):
                yield "state", str(self._state)
            if hasattr(self, "status"):
                yield "status", str(self.status)

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


def create_task(data: dict) -> Task:
    task_type = data.pop("type")
    print(TaskMeta.registry)
    task_cls = TaskMeta.registry[task_type]
    return task_cls(**data)  # type: ignore[return-value]
