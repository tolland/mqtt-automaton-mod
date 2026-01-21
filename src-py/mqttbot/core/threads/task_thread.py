import uuid
from collections import deque
from collections.abc import Awaitable, Callable
from functools import total_ordering

from rich.repr import rich_repr

from mqttbot.config.threads.thread_status import ThreadStatus
from mqttbot.core.context import Context
from mqttbot.core.tasks.task_priority import TaskPriority, TaskStatus
from mqttbot.model.tasks.task import Task


@total_ordering
@rich_repr
class TaskThread:
    """
    A thread of execution: manages a sequence of tasks that need to be completed
    as a set. A TaskThread can be interrupted and suspended and later resumed.
    The TaskThread implementation

    """

    def __init__(
        self,
        thread_id: str,
        priority: TaskPriority,
        on_suspend: Callable[["TaskThread", "Context"], Awaitable[None]] | None = None,
        on_resume: Callable[["TaskThread", "Context"], Awaitable[None]] | None = None,
        on_cancel: Callable[["TaskThread", "Context"], Awaitable[None]] | None = None,
        uninterruptible: bool = False,
    ) -> None:
        self.thread_id = thread_id
        self.priority = priority
        self.state = ThreadStatus.READY
        self.uninterruptible = uninterruptible

        # Generate unique correlation_id for this thread execution instance
        # Format: thread_id-uuid allows tracking all messages from this thread instance
        self.correlation_id = f"{thread_id}-{uuid.uuid4()}"

        self.current_task: Task | None = None
        self.task_queue: deque[Task] = deque()

        # Injected callbacks
        self._on_suspend = on_suspend
        self._on_resume = on_resume
        self._on_cancel = on_cancel

    def enqueue_task(self, task: Task) -> None:
        """Add task to this thread's queue and inject correlation_id"""
        task.correlation_id = self.correlation_id
        self.task_queue.append(task)

    async def start(self, ctx: Context) -> None:
        """Begin execution of this thread"""
        self.state = ThreadStatus.RUNNING
        await self._advance_to_next_task(ctx)

    async def suspend(self, ctx: Context) -> None:
        """Capture suspension point"""
        self.state = ThreadStatus.SUSPENDED

        if self.current_task:
            self.current_task.suspend(ctx)

        if self._on_suspend:
            await self._on_suspend(self, ctx)

    async def resume(self, ctx: Context) -> None:
        """Resume from suspension, potentially with different task strategy"""
        self.state = ThreadStatus.RUNNING

        if self._on_resume:
            await self._on_resume(self, ctx)

        if self.current_task and self.current_task.status == TaskStatus.SUSPENDED:
            self.current_task.resume(ctx)

        elif self.current_task and not self.current_task.status == TaskStatus.SUSPENDED:
            raise RuntimeError(f"Cannot resume task in status {self.current_task.status}")
        else:
            await self._advance_to_next_task(ctx)

    async def cancel(self, ctx: Context) -> None:
        """Cancel this thread - execute cleanup tasks and mark as cancelled"""
        self.state = ThreadStatus.CANCELLED

        # Cancel current task if any
        if self.current_task:
            self.current_task.suspend(ctx)

        # Execute on_cancel tasks
        if self._on_cancel:
            await self._on_cancel(self, ctx)

        # Clear remaining tasks - thread is dead after cancellation
        self.task_queue.clear()
        self.current_task = None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the thread state."""
        return {
            "thread_id": self.thread_id,
            "state": self.state.name,
            "priority": self.priority.name,
            "correlation_id": self.correlation_id,
            "current_task": self.current_task.to_dict() if self.current_task and hasattr(self.current_task, "to_dict") else str(self.current_task),
            "task_queue_len": len(self.task_queue),
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    async def step(self, ctx: Context) -> bool:
        """Execute one step. Return True if thread completed"""
        if not self.current_task:
            return True

        # step() is synchronous, returns immediately
        status = self.current_task.step(ctx)

        if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
            self.current_task.exit(ctx, status)
            await self._advance_to_next_task(ctx)

        return self.current_task is None

    async def _advance_to_next_task(self, ctx: Context) -> None:
        """Move to next task in queue"""
        if self.task_queue:
            self.current_task = self.task_queue.popleft()
            self.current_task.enter(ctx)
        else:
            self.current_task = None

    def __lt__(self, other: "TaskThread") -> bool:
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.thread_id < other.thread_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskThread):
            return NotImplemented
        return self.thread_id == other.thread_id

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "correlation_id", self.correlation_id
        yield "priority", self.priority.name
        yield "state", self.state.value
        yield "uninterruptible", self.uninterruptible
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        yield "task_queue_len", len(self.task_queue)
        yield "on_suspend", self._on_suspend
        yield "on_resume", self._on_resume
        yield "on_cancel", self._on_cancel
