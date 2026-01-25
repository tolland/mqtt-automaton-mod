from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.protocol.thread_lifecycle_hooks import ThreadLifecycleHooks
from mqttbot.core.threads.scheduler_context import Context


class DefaultThreadHooks(ThreadLifecycleHooks):
    """Default 'do nothing' implementation."""

    def on_suspend(self, thread: "ThreadInterface", ctx: Context) -> list["Task"]: return self.get_hook_steps(thread,
                                                                                                         "on_suspend_steps")

    def on_resume(self, thread, ctx) -> list["Task"]: return self.get_hook_steps(thread, "on_resume_steps")

    def on_cancel(self, thread, ctx) -> list["Task"]: return self.get_hook_steps(thread, "on_cancel_steps")

    def on_failed(self, thread, ctx) -> list["Task"]: return self.get_hook_steps(thread, "on_failed_steps")

    def get_hook_steps(self, thread: "ThreadInterface", hook_name: str) -> list["Task"]:
        return []
    # PatternThreadHelper._tasks_from_steps((getattr(thread, hook_name, [])), thread.correlation_id)
