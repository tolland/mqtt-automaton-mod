from collections.abc import Awaitable, Callable
from typing import Protocol

from mqttbot.config.threads.thread_status import ThreadStatus
from mqttbot.core.protocol.task import Task
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.core.threads.scheduler_context import Context


class TaskThread(Protocol):
    thread_id: str
    priority: TaskPriority
    uninterruptible: bool

    _on_suspend: Callable[["TaskThreadBase", "Context"], Awaitable[None]] | None
    _on_resume: Callable[["TaskThreadBase", "Context"], Awaitable[None]] | None
    _on_cancel: Callable[["TaskThreadBase", "Context"], Awaitable[None]] | None
    _on_failed: Callable[["TaskThreadBase", "Context"], Awaitable[None]] | None

    def enqueue_task(self, task: Task) -> None: ...

    def start(self, ctx: Context) -> None: ...

    def step(self, ctx: Context) -> Awaitable[ThreadStatus]: ...
