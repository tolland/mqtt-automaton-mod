from rich import print as rprint
from rich.repr import rich_repr
from rich.pretty import pprint
from abc import ABC, abstractmethod
import logging

from mqttbot.core.task.task import TaskStatus, TaskContext


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
            raise
    return wrapper

@rich_repr
class Task(ABC):
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
            rprint(f"[dim cyan][TASK][/dim cyan] [bold]{task_name}[/bold] {transition}" + (f": {details}" if details else ""))


    @trace
    def enter(self, ctx):
        self._enter(ctx)

    def _enter(self, ctx):
        self._resume(ctx)

    @trace
    def step(self, ctx) -> TaskStatus:
        return self._step(ctx)

    @abstractmethod
    def _step(self, ctx) -> TaskStatus:
        pass

    @trace
    def suspend(self) -> TaskContext:
        return self._suspend()

    def _suspend(self) -> TaskContext:
        pass

    @trace
    def resume(self, ctx) -> None:
        self._resume(ctx)

    def _resume(self, ctx) -> None:
        pass

    @trace
    def exit(self, ctx, status: TaskStatus):
        """Public method: handles logging and delegates to _exit."""
        self._debug_log("exit", status=status.value)
        self._exit(ctx, status)

    def _exit(self, ctx, status: TaskStatus):
        """Override this method in subclasses. Called when task exits."""
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
            
            # Show state if available
            if hasattr(self, "_state"):
                yield "state", str(self._state)
        
        # INFO level: show key attributes only
        elif self._log_level == "INFO":
            if hasattr(self, "target"):
                yield "target", self.target
            elif hasattr(self, "waypoint"):
                yield "waypoint", self.waypoint
            elif hasattr(self, "steps") and self.steps:
                yield "steps", len(self.steps)
        
        # WARNING/ERROR: minimal info (just class name, already shown)
