import uuid
from collections import deque
from collections.abc import Callable
from functools import total_ordering

from loguru import logger
from rich.repr import rich_repr

from mqttbot.config.threads.thread_status import ThreadStatus, ThreadInternalStatus
from mqttbot.core.protocol.task import Task
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.core.tasks.task_status import TaskStatus
from mqttbot.core.threads.scheduler_context import Context


@total_ordering
@rich_repr
class TaskThreadBase:
    """
    A thread of execution: manages a sequence of tasks that need to be completed
    as a set. A TaskThread can be interrupted and suspended and later resumed.
    The TaskThread implementation

    """

    def __init__(
        self,
        thread_id: str,
        priority: TaskPriority,
        on_suspend: Callable[["TaskThreadBase", "Context"], list[Task]] | None = None,
        on_resume: Callable[["TaskThreadBase", "Context"], list[Task]] | None = None,
        on_cancel: Callable[["TaskThreadBase", "Context"], list[Task]] | None = None,
        on_failed: Callable[["TaskThreadBase", "Context"], list[Task]] | None = None,
        uninterruptible: bool = False,
    ) -> None:
        self.thread_id = thread_id
        self.priority = priority
        self.uninterruptible = uninterruptible
        self._status: ThreadInternalStatus = ThreadInternalStatus.READY

        # Generate unique correlation_id for this thread execution instance
        # Format: thread_id-uuid allows tracking all messages from this thread instance
        self.correlation_id = f"{thread_id}-{uuid.uuid4()}"

        self.current_task: Task | None = None
        # queue of tasks to execute
        self.task_queue: deque[Task] = deque()
        # store tasks for later execution
        self.wait_queue: deque[Task] = deque()

        # Injected callbacks
        self._on_suspend = on_suspend
        self._on_resume = on_resume
        self._on_cancel = on_cancel
        self._on_failed = on_failed

    def enqueue_task(self, task: Task) -> None:
        """Add task to this thread's queue and inject correlation_id"""
        task.correlation_id = self.correlation_id
        self.task_queue.append(task)

    async def step(self, ctx: Context) -> ThreadStatus:
        """Execute one step. Return True if thread completed"""

        # # so we shouldn't be stepping if we have no current task
        # if not self.current_task and (self.task_queue or self.wait_queue):
        #     raise RuntimeError(f"Thread {self.thread_id} has no current task but has tasks queued.")

        if not self.current_task:
            match self._status:
                case ThreadInternalStatus.READY:
                    raise RuntimeError(f"Thread {self.thread_id} is in READY state but step was called.")
                case ThreadInternalStatus.SUSPENDING:
                    # done with on_suspend tasks, return SUSPENDED
                    self.uninterruptible = False
                    self._status = self._status.transition_to(ThreadInternalStatus.SUSPENDED)
                    return self.state
                case ThreadInternalStatus.RESUMING:
                    # resume complete, move to running
                    self.uninterruptible = False
                    while self.wait_queue:
                        self.task_queue.append(self.wait_queue.popleft())
                    await self._advance_to_next_task(ctx)
                    self._status = self._status.transition_to(ThreadInternalStatus.RUNNING)
                    return self.state
                case ThreadInternalStatus.RUNNING:
                    self._status = self._status.transition_to(ThreadInternalStatus.COMPLETED)
                    return self.state

        if self._status.is_active:
            status = self.current_task.step(ctx)

            if status == TaskStatus.SUCCESS:
                self.current_task.exit(ctx, status)
                await self._advance_to_next_task(ctx)
                return ThreadStatus.RUNNING
            elif status == TaskStatus.FAILED:
                self.current_task.exit(ctx, status)
                await self._handle_failure(ctx)
                return ThreadStatus.FAILED
            elif status == TaskStatus.RUNNING:
                return ThreadStatus.RUNNING

        # Currently if we tey to step anything else, its a failure
        # @TODO move this to proper state machine
        raise RuntimeError(f"Unexpected task status {status} in thread {self.thread_id}")

    @property
    def state(self) -> ThreadStatus:
        """Return internal status of this thread"""
        match self._status:
            case ThreadInternalStatus.READY:
                return ThreadStatus.READY
            case ThreadInternalStatus.RUNNING:
                return ThreadStatus.RUNNING
            case ThreadInternalStatus.SUSPENDING:
                return ThreadStatus.RUNNING
            case ThreadInternalStatus.SUSPENDED:
                return ThreadStatus.SUSPENDED
            case ThreadInternalStatus.RESUMING:
                return ThreadStatus.RUNNING
            case ThreadInternalStatus.CANCELING:
                return ThreadStatus.RUNNING
            case ThreadInternalStatus.COMPLETED:
                return ThreadStatus.COMPLETED
            case ThreadInternalStatus.FAILED:
                return ThreadStatus.FAILED
            case ThreadInternalStatus.CANCELLED:
                return ThreadStatus.CANCELLED
        raise RuntimeError(f"Thread {self.thread_id} in unexpected internal status {self._status}")

    async def start(self, ctx: Context) -> None:
        """Begin execution of this thread"""
        self._status = self._status.transition_to(ThreadInternalStatus.RUNNING)
        await self._advance_to_next_task(ctx)

    async def suspend(self, ctx: Context) -> None:
        """Capture suspension point"""
        if self._status != ThreadInternalStatus.RUNNING:
            raise RuntimeError(f"Cannot suspend thread {self.thread_id} in status {self._status}")

        self._status = self._status.transition_to(ThreadInternalStatus.SUSPENDING)
        self.uninterruptible = True

        # move the current task back to the wait queue
        while self.task_queue:
            self.wait_queue.append(self.task_queue.popleft())

        if self._on_suspend:
            self.task_queue.extend(self._on_suspend(self, ctx))

        if not self.current_task:
            await self._advance_to_next_task(ctx)

    async def resume(self, ctx: Context) -> None:
        """Resume from suspension, potentially with different task strategy"""
        if self._status != ThreadInternalStatus.SUSPENDED:
            raise RuntimeError(f"Cannot resume thread {self.thread_id} in status {self._status}")

        self._status = self._status.transition_to(ThreadInternalStatus.RESUMING)
        self.uninterruptible = True

        if self._on_resume:
            self.task_queue.extend(self._on_resume(self, ctx))

    async def cancel(self, ctx: Context) -> None:
        """Cancel this thread - execute cleanup tasks and mark as cancelled"""
        self._status = self._status.transition_to(ThreadInternalStatus.CANCELING)
        self.uninterruptible = True

        # Cancel current task if any
        if self.current_task:
            self.current_task.suspend(ctx)

        if self._on_cancel:
            self.task_queue.extend(self._on_cancel(self, ctx))

        # Clear remaining tasks - thread is dead after cancellation
        self.task_queue.clear()
        self.current_task = None

    async def _handle_failure(self, ctx: Context) -> None:
        """Handle task failure by clearing queue and running on_failed tasks"""

        logger.warning(f"Thread {self.thread_id} task failed. Clearing queue.")

        # Clear remaining tasks
        self.task_queue.clear()
        self.current_task = None

        # Execute on_failed tasks if any
        if self._on_failed:
            await self._on_failed(self, ctx)

        # Move to first on_failed task if any were added
        if self.current_task is None and self.task_queue:
            await self._advance_to_next_task(ctx)

    async def _advance_to_next_task(self, ctx: Context) -> None:
        """Move to next task in queue"""
        if self.task_queue:
            self.current_task = self.task_queue.popleft()
            self.current_task.enter(ctx)
        else:
            self.current_task = None

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
            "state": self.state.name,
            "status": self._status.name,
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
        yield "state", self.state.value
        yield "_status", self._status.value
        yield "uninterruptible", self.uninterruptible
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        yield "task_queue_len", len(self.task_queue)
        yield "on_suspend", self._on_suspend
        yield "on_resume", self._on_resume
        yield "on_cancel", self._on_cancel
        yield "on_failed", self._on_failed
