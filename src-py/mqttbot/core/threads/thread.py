from mqttbot.core.protocol.thread_status import ThreadInternalStatus
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.protocol.task_provider import TaskProvider
from mqttbot.core.threads.scheduler_context import Context
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
    ):
        super().__init__(thread_id, priority)
        self.main_source_provider = main_source_provider
        self.on_suspend_provider = on_suspend_provider
        self.on_resume_provider = on_resume_provider
        self.on_cancel_provider = on_cancel_provider
        self.on_failed_provider = on_failed_provider

    def start(self, ctx: Context) -> None:
        """Start this thread - transition to RUNNING and load initial tasks"""
        # Load initial tasks from main source
        initial_tasks = self.main_source_provider.get_tasks(self)
        for task in initial_tasks:
            self.enqueue_task(task)
        self._advance_to_next_task(ctx)
        self.transition_to(ThreadInternalStatus.RUNNING)

    def suspend(self, ctx: Context):
        # Trigger the dynamic delegate
        suspend_tasks = self.on_suspend_provider.get_tasks(self)
        self.task_queue.extendleft(suspend_tasks)

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
        yield "main_source_provider", self.main_source_provider
        yield "on_suspend_provider", self.on_suspend_provider
        yield "on_resume_provider", self.on_resume_provider
        yield "on_cancel_provider", self.on_cancel_provider
        yield "on_failed_provider", self.on_failed_provider
