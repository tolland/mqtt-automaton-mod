from typing import Protocol

from mqttbot.core.tasks.task_status import TaskStatus
from mqttbot.core.threads.scheduler_context import Context


class Task(Protocol):
    status: TaskStatus

    def enter(self, ctx: Context) -> None: ...

    def step(self, ctx: Context) -> TaskStatus: ...

    def suspend(self, ctx: Context) -> None: ...

    def resume(self, ctx: Context) -> None: ...

    def exit(self, ctx: Context, status: TaskStatus) -> None: ...
