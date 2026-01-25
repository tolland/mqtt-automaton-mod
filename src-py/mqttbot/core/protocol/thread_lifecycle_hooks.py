from typing import Protocol, runtime_checkable

from mqttbot.core.protocol.task import Task


@runtime_checkable
class ThreadLifecycleHooks(Protocol):
    """Protocol for objects that handle thread lifecycle events."""

    def on_suspend(self, thread: "TaskThreadBase", ctx: "Context") -> list["Task"]: ...

    def on_resume(self, thread: "TaskThreadBase", ctx: "Context") -> list["Task"]: ...

    def on_cancel(self, thread: "TaskThreadBase", ctx: "Context") -> list["Task"]: ...

    def on_failed(self, thread: "TaskThreadBase", ctx: "Context") -> list["Task"]: ...
