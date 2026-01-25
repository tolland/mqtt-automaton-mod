from typing import Protocol, Any

from mqttbot.core.protocol.thread_status import ThreadStatus
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.threads.scheduler_context import Context


class ThreadInterface(Protocol):
    thread_id: str
    priority: ThreadPriority
    uninterruptible: bool

    @property
    def status(self) -> ThreadStatus: ...

    def enqueue_task(self, task: Task) -> None: ...

    def start(self, ctx: Context) -> None: ...

    def suspend(self, ctx: Context) -> None: ...

    def resume(self, ctx: Context) -> None: ...

    def cancel(self, ctx: Context) -> None: ...

    def step(self, ctx: Context) -> ThreadStatus:
        """
        1. if there is no current task, and we are "active",
          then we are 'COMPLETED', thus later operations must
          call _advance_to_next
        """

    def __lt__(self, other: Any) -> bool: ...

    def to_dict(self) -> dict[str, Any]: ...

    def to_json(self) -> str: ...
