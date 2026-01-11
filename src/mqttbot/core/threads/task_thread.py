from collections import deque
from functools import total_ordering
from typing import Callable, Awaitable, Optional

from rich.repr import rich_repr

from mqttbot.core.task.task import TaskPriority, TaskContext, TaskStatus
from mqttbot.core.threads.thread_status import ThreadStatus
from mqttbot.tasks.task import Task


@total_ordering
@rich_repr
class TaskThread:
    """A thread of execution: manages a sequence of tasks and resumption"""

    def __init__(
            self,
            thread_id: str,
            priority: TaskPriority,
            on_suspend: Optional[Callable[["TaskThread"], Awaitable[None]]] = None,
            on_resume: Optional[Callable[["TaskThread", TaskContext], Awaitable[None]]] = None,
    ) -> None:
        self.thread_id = thread_id
        self.priority = priority
        self.state = ThreadStatus.READY

        self.current_task: Optional[Task] = None
        self.task_queue: deque[Task] = deque()
        self.suspended_context: Optional[TaskContext] = None

        # Injected callbacks
        self._on_suspend = on_suspend
        self._on_resume = on_resume

    def enqueue_task(self, task: Task) -> None:
        """Add task to this thread's queue"""
        self.task_queue.append(task)

    async def start(self) -> None:
        """Begin execution of this thread"""
        self.state = ThreadStatus.RUNNING
        await self._advance_to_next_task()

    async def suspend(self) -> TaskContext:
        """Capture suspension point"""
        self.state = ThreadStatus.SUSPENDED

        if self.current_task:
            self.suspended_context = self.current_task.suspend()

        if self._on_suspend:
            await self._on_suspend(self)

        return self.suspended_context or TaskContext(0, {})

    async def resume(self, ctx: TaskContext) -> None:
        """Resume from suspension, potentially with different task strategy"""
        self.state = ThreadStatus.RUNNING
        self.suspended_context = ctx

        if self._on_resume:
            await self._on_resume(self, ctx)

        if self.current_task and self.current_task.state == TaskStatus.SUSPENDED:
            await self.current_task.resume(ctx)
        else:
            await self._advance_to_next_task()

    async def step(self, ctx) -> bool:
        """Execute one step. Return True if thread completed"""
        if not self.current_task:
            return True

        # step() is synchronous, returns immediately
        status = self.current_task.step(ctx)

        if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
            self.current_task.exit(ctx, status)
            await self._advance_to_next_task()

        return self.current_task is None

    async def _advance_to_next_task(self) -> None:
        """Move to next task in queue"""
        if self.task_queue:
            self.current_task = self.task_queue.popleft()
            ctx = TaskContext(
                step_index=0,
                metadata={}
            )
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
        yield "priority", self.priority.name
        yield "state", self.state.value
        yield "current_task", type(self.current_task).__name__ if self.current_task else None
        yield "task_queue_len", len(self.task_queue)
        if self.suspended_context:
            yield "suspended_context", {
                "step_index": self.suspended_context.step_index,
                "metadata": self.suspended_context.metadata,
            }
