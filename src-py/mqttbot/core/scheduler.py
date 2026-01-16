import heapq
from collections import deque
from typing import Optional

from rich.repr import rich_repr

from mqttbot.config.threads.thread_status import ThreadStatus
from mqttbot.core.context import Context
from mqttbot.core.threads.task_thread import TaskThread


@rich_repr
class Scheduler:
    """Manages thread-level preemption"""

    def __init__(self) -> None:
        self.ready_threads: list[TaskThread] = []
        self.current_thread: Optional[TaskThread] = None
        self.suspended_stack: deque[TaskThread] = deque()

    def register_thread(self, thread: TaskThread) -> None:
        """Register a thread (typically at startup)"""
        heapq.heappush(self.ready_threads, thread)

    def enqueue_thread(self, thread: TaskThread, singleton: bool = False) -> bool:
        """
        Wake a thread (move to ready queue).

        Args:
            thread: The thread to enqueue
            singleton: If True, only allow one instance of this thread_id at a time

        Returns:
            True if enqueued, False if blocked (singleton already active)
        """
        if singleton:
            # Check if a thread with this ID already exists
            if self._thread_id_exists(thread.thread_id):
                print(f"[scheduler] Thread {thread.thread_id} already active, skipping")
                return False

        heapq.heappush(self.ready_threads, thread)
        print(f"[scheduler] Enqueued thread: {thread.thread_id}")
        return True

    def _thread_id_exists(self, thread_id: str) -> bool:
        """Check if a thread with this ID exists in any queue"""
        # Check current thread
        if self.current_thread and self.current_thread.thread_id == thread_id:
            return True

        # Check ready queue
        if any(t.thread_id == thread_id for t in self.ready_threads):
            return True

        # Check suspended stack
        if any(t.thread_id == thread_id for t in self.suspended_stack):
            return True

        return False

    def has_active_thread(self, thread_id: str) -> bool:
        """Public method to check if a thread is active"""
        return self._thread_id_exists(thread_id)

    def is_complete(self) -> bool:
        """Check if scheduler has completed all tasks.

        Returns True if ready_threads, current_thread, and suspended_stack are all empty.
        """
        return (
            len(self.ready_threads) == 0
            and self.current_thread is None
            and len(self.suspended_stack) == 0
        )

    async def step(self, ctx: Context) -> bool:
        """Execute one scheduler tick.

        Returns:
            True if all tasks are complete (scheduler is empty), False otherwise.
        """
        # Check preemption
        if self.ready_threads and self._should_preempt():
            await self._preempt(ctx)

        # Execute current thread
        if self.current_thread:
            try:
                # Set correlation_id from current thread before stepping
                ctx.correlation_id = self.current_thread.correlation_id
                completed = await self.current_thread.step(ctx)
                if completed:
                    self.current_thread.state = ThreadStatus.COMPLETED
                    self.current_thread = None
                    ctx.correlation_id = None  # Clear when thread completes
                    await self._resume_suspended(ctx)
            except Exception as e:
                self.current_thread.state = ThreadStatus.FAILED
                self.current_thread = None
                ctx.correlation_id = None  # Clear on failure
                raise e
        elif self.ready_threads:
            await self._start_next_thread(ctx)

        # Return True if all work is done
        return self.is_complete()

    def _should_preempt(self) -> bool:
        if not self.current_thread or not self.ready_threads:
            return False

        next_priority = self.ready_threads[0].priority.value
        return next_priority < self.current_thread.priority.value

    async def _preempt(self, ctx: Context) -> None:
        """Suspend current thread, switch to higher priority"""
        assert self.current_thread is not None

        await self.current_thread.suspend()
        self.suspended_stack.append(self.current_thread)
        self.current_thread = None

        await self._start_next_thread(ctx)

    async def _start_next_thread(self, ctx: Context) -> None:
        """Pop highest-priority ready thread"""
        if not self.ready_threads:
            self.current_thread = None
            ctx.correlation_id = None
            return

        thread = heapq.heappop(self.ready_threads)
        self.current_thread = thread

        # Set correlation_id from the thread being started
        ctx.correlation_id = thread.correlation_id

        if thread.state == ThreadStatus.READY:
            await thread.start(ctx)
        elif thread.state == ThreadStatus.SUSPENDED:
            await thread.resume(ctx)

    async def _resume_suspended(self, ctx: Context) -> None:
        """Resume most recently preempted thread"""
        if not self.suspended_stack:
            return

        thread = self.suspended_stack.pop()
        # Set correlation_id from the resumed thread
        ctx.correlation_id = thread.correlation_id
        await thread.resume(ctx)
        self.current_thread = thread

    def __rich_repr__(self):
        yield "current_thread", self.current_thread.thread_id if self.current_thread else None
        yield "ready_threads", [t.thread_id for t in self.ready_threads]
        yield "suspended_stack", [t.thread_id for t in self.suspended_stack]
