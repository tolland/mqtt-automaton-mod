import uuid
from collections import deque
from functools import total_ordering
from typing import Any

from loguru import logger
from rich import inspect
from rich import print as rprint

from mqttbot.config.threads.default_thread_hooks import DefaultThreadHooks
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.protocol.task_status import TaskStatus
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.protocol.thread_lifecycle_hooks import ThreadLifecycleHooks
from mqttbot.core.protocol.thread_status import ThreadStatus, ThreadInternalStatus
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.utils.tracing_tools import trace


@total_ordering
class TaskThreadBase(ThreadInterface):
    """
    A thread of execution: manages a sequence of tasks that need to be completed
    as a set. A TaskThread can be interrupted and suspended and later resumed.
    The TaskThread implementation

    """

    def __init__(
        self,
        thread_id: str,
        priority: ThreadPriority,
        hooks: ThreadLifecycleHooks | None = None,
        uninterruptible: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.thread_id = thread_id
        self.priority = priority
        self.uninterruptible = uninterruptible
        self._internal_status: ThreadInternalStatus = ThreadInternalStatus.READY
        self.hooks = hooks or DefaultThreadHooks()
        self.metadata = metadata or {}

        # Generate unique correlation_id for this thread execution instance
        # Format: thread_id-uuid allows tracking all messages from this thread instance
        self.correlation_id = f"{thread_id}-{str(uuid.uuid4())[-10:]}"

        self.current_task: Task | None = None
        # queue of tasks to execute
        self.task_queue: deque[Task] = deque()
        # store tasks for later execution
        self.wait_queue: deque[Task] = deque()

    def enqueue_task(self, task: Task) -> None:
        """Add task to this thread's queue and inject correlation_id"""
        task.correlation_id = self.correlation_id
        task.enqueue(correlation_id=self.correlation_id)
        self.task_queue.append(task)

    def step(self, ctx: Context) -> ThreadStatus:
        """Execute one step. Return True if thread completed"""

        # so we shouldn't be stepping if we have no current task
        # every thread transition should handle advancing a task onto the queue
        # or the queue is empty and the current task is None
        if not self.current_task and self.task_queue:
            raise RuntimeError(f"Thread {self.thread_id} has no current task but has tasks queued.")

        if not self.current_task:
            match self._internal_status:
                case ThreadInternalStatus.READY:
                    raise RuntimeError(
                        f"Thread {self.thread_id} is in READY state but step was called."
                    )
                case ThreadInternalStatus.CANCELING:
                    # done with on_cancel tasks, return CANCELED
                    self.uninterruptible = False
                    self.transition_to(ThreadInternalStatus.CANCELLED)
                    return self.status
                case ThreadInternalStatus.SUSPENDING:
                    # done with on_suspend tasks, return SUSPENDED
                    self.uninterruptible = False
                    self.transition_to(ThreadInternalStatus.SUSPENDED)
                    return self.status
                case ThreadInternalStatus.RESUMING:
                    self.uninterruptible = False
                    while self.wait_queue:
                        self.task_queue.append(self.wait_queue.popleft())
                    self._advance_to_next_task(ctx)
                    # This not working because advance_to_next already set READY
                    # if self.current_task:
                    #     self.current_task.resume(ctx)
                    self.transition_to(ThreadInternalStatus.RUNNING)
                    return self.status
                case ThreadInternalStatus.RUNNING:
                    self.transition_to(ThreadInternalStatus.COMPLETED)
                    return self.status
                case _:
                    inspect(self)
                    raise RuntimeError(f"Unexpected thread status {self._internal_status} in thread {self.thread_id} while current_task is None")

        if self.status.is_active:
            current_task_status = self.current_task.step(ctx)

            if current_task_status == TaskStatus.RUNNING:
                return ThreadStatus.RUNNING
            elif current_task_status == TaskStatus.SUCCESS:
                self.current_task.exit(ctx, current_task_status)
                self._advance_to_next_task(ctx)
                return ThreadStatus.RUNNING
            elif current_task_status == TaskStatus.FAILED:
                inspect(self.current_task)
                self.current_task.exit(ctx, current_task_status)
                self._handle_failure(ctx)
                return ThreadStatus.FAILED
            elif current_task_status == TaskStatus.CANCELLED:
                self.current_task.exit(ctx, current_task_status)
                self._advance_to_next_task(ctx)
                return ThreadStatus.RUNNING
            elif current_task_status == TaskStatus.SUSPENDED:
                self.current_task.exit(ctx, current_task_status)
                self._advance_to_next_task(ctx)
                return ThreadStatus.RUNNING

            # Currently if we tey to step anything else, its a failure
            # @TODO move this to proper state machine
            raise RuntimeError(f"Unexpected task status {current_task_status} in thread {self.thread_id}")
        raise RuntimeError(f"Thread {self.thread_id} is not active but step was called.")

    @property
    def status(self) -> ThreadStatus:
        """Public status for the parent Thread/Scheduler."""
        return self._internal_status.external

    def start(self, ctx: Context) -> None:
        """Begin execution of this thread"""
        self._advance_to_next_task(ctx)
        self.transition_to(ThreadInternalStatus.RUNNING)

    def suspend(self, ctx: Context) -> None:
        """Capture suspension point"""

        self.transition_to(ThreadInternalStatus.SUSPENDING)
        self.uninterruptible = True

        if self.current_task:
            self.current_task.suspend(ctx)
            self.wait_queue.appendleft(self.current_task)
            self.current_task.clone()
            # let current task handle its own suspension
            # self.current_task = None

        # move the remaining task queue to the wait queue
        while self.task_queue:
            self.wait_queue.append(self.task_queue.popleft())

        # enqueue on_suspend uninterruptible tasks
        for task in self.on_suspend_provider.get_tasks(self):
            self.enqueue_task(task)

        if not self.current_task:
            self._advance_to_next_task(ctx)

    def resume(self, ctx: Context) -> None:
        """Resume from suspension, potentially with different task strategy"""

        self.transition_to(ThreadInternalStatus.RESUMING)
        self.uninterruptible = True

        for task in self.on_resume_provider.get_tasks(self):
            self.enqueue_task(task)

        if not self.current_task:
            self._advance_to_next_task(ctx)

    def cancel(self, ctx: Context) -> None:
        """Cancel this thread - execute cleanup tasks and mark as cancelled"""
        self.transition_to(ThreadInternalStatus.CANCELING)
        self.uninterruptible = True

        # Cancel current task if any
        if self.current_task:
            self.current_task.cancel(ctx)

        # Clear remaining tasks, no more main tasks should run after cancel
        self.task_queue.clear()

        for task in self.on_cancel_provider.get_tasks(self):
            self.enqueue_task(task)

        if not self.current_task:
            self._advance_to_next_task(ctx)

    def _handle_failure(self, ctx: Context) -> None:
        """Handle task failure by clearing queue and running on_failed tasks"""

        logger.warning(f"Thread {self.thread_id} task failed. Clearing queue.")

        # Clear remaining tasks
        self.task_queue.clear()

        self.cancel(ctx)

        # Move to first on_failed task if any were added
        if self.current_task is None and self.task_queue:
            self._advance_to_next_task(ctx)

    # @trace
    def _advance_to_next_task(self, ctx: Context) -> None:
        """Move to next task in queue"""
        if self.task_queue:
            self.current_task = self.task_queue.popleft()
            rprint(self.current_task)
            self.current_task.enter(ctx)
        else:
            self.current_task = None

    # def on_suspend(self, ctx: Context) -> list[Task]:
    #     tasks: list[Task] = []
    #     for step in self.on_suspend_steps:
    #         tasks.append(TaskFactory.create(step.to_dict()))
    #     return tasks

    def transition_to(self, next_state: ThreadInternalStatus):
        """Enforces validity and updates the internal state."""
        # Use the transition map logic here
        self._internal_status = self._internal_status.transition_to(next_state)


    def __lt__(self, other: "TaskThreadBase") -> bool:
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.thread_id < other.thread_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskThreadBase):
            return NotImplemented
        return self.thread_id == other.thread_id

    def to_dict(self) -> dict:
        """Return a dictionary representation of the thread state."""
        return {
            "thread_id": self.thread_id,
            "state": self._internal_status.name,
            "task_queue_len": len(self.task_queue),
            "wait_queue_len": len(self.wait_queue),
            "priority": self.priority.name,
            "correlation_id": self.correlation_id,
            "current_task": self.current_task.to_dict() if self.current_task and hasattr(self.current_task,
                                                                                         "to_dict") else str(
                self.current_task),
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "correlation_id", self.correlation_id
        yield "priority", self.priority.name
        yield "status", self.status.value
        yield "uninterruptible", self.uninterruptible
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        yield "task_queue_len", len(self.task_queue)
        yield "on_suspend_provider", self.on_suspend
        yield "on_resume_provider", self.on_resume
        yield "on_cancel_provider", self.on_cancel
        yield "on_failed_provider", self.on_failed
