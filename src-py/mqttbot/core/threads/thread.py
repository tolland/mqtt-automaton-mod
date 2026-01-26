from typing import Any

from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.protocol.task_provider import TaskProvider
from mqttbot.core.threads.thread_base import TaskThreadBase


class TaskThread(TaskThreadBase):
    def __init__(
        self,
        main_source_provider: TaskProvider,
        on_suspend_provider: TaskProvider,
        on_resume_provider: TaskProvider,
        on_cancel_provider: TaskProvider,
        on_failed_provider: TaskProvider,
        thread_id: str,
        priority: ThreadPriority,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(thread_id, priority, metadata=metadata)
        self.main_source_provider = main_source_provider
        self.on_suspend_provider = on_suspend_provider
        self.on_resume_provider = on_resume_provider
        self.on_cancel_provider = on_cancel_provider
        self.on_failed_provider = on_failed_provider

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "correlation_id", self.correlation_id
        yield "priority", self.priority.name
        yield "status", self.status.name
        yield "uninterruptible", self.uninterruptible
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        if self.current_task:
            yield "current_task", self.current_task
        yield "task_queue_len", len(self.task_queue)
        yield "done_queue_len", len(self.done_tasks)
        yield "main_source_provider", self.main_source_provider
        yield "on_suspend_provider", self.on_suspend_provider
        yield "on_resume_provider", self.on_resume_provider
        yield "on_cancel_provider", self.on_cancel_provider
        yield "on_failed_provider", self.on_failed_provider
