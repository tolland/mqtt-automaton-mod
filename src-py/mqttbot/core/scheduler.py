import heapq
from collections import deque
from dataclasses import dataclass
from typing import Any

from rich.repr import rich_repr

from mqttbot.config.threads.thread_status import ThreadStatus
from mqttbot.core.context import Context
from mqttbot.core.threads.task_thread import TaskThread


@dataclass
class SchedulerState:
    current_thread_id: int | None
    current_thread_state: str | None
    current_correlation_id: str | None
    ready_threads: list[str]
    suspended_stack: list[str]

@rich_repr
class Scheduler:
    """Manages thread-level preemption"""

    def __init__(self) -> None:
        self.ready_threads: list[TaskThread] = []
        self.current_thread: TaskThread | None = None
        self.suspended_stack: deque[TaskThread] = deque()
        self.old_state: dict[str, Any] | None = None

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
        # Publish state to MQTT
        if ctx.mqtt:
            if self.to_dict() != self.old_state:
                self.old_state = self.to_dict()
                topic = f"{ctx.mqtt.topic_base}/scheduler/state"
                ctx.mqtt.send(topic, self.to_json())

        # Check preemption
        if self.ready_threads and self._should_preempt():
            await self._preempt(ctx)
            return False

        # Execute current thread
        if self.current_thread:
            current = self.current_thread
            try:
                completed = await current.step(ctx)
                if completed:
                    current.state = ThreadStatus.COMPLETED
                    if self.current_thread == current:
                        self.current_thread = None
                        await self._resume_suspended(ctx)
            except Exception as e:
                current.state = ThreadStatus.FAILED
                if self.current_thread == current:
                    self.current_thread = None
                raise e
        elif self.ready_threads:
            await self._start_next_thread(ctx)

        # Return True if all work is done
        return self.is_complete()

    def _should_preempt(self) -> bool:
        if not self.current_thread or not self.ready_threads:
            return False

        # Cannot preempt uninterruptible threads
        if self.current_thread.uninterruptible:
            return False

        next_priority = self.ready_threads[0].priority.value
        return next_priority < self.current_thread.priority.value

    async def _preempt(self, ctx: Context) -> None:
        """Suspend current thread, switch to higher priority"""
        assert self.current_thread is not None

        await self.current_thread.suspend(ctx)
        self.suspended_stack.append(self.current_thread)
        self.current_thread = None

        await self._start_next_thread(ctx)

    async def _start_next_thread(self, ctx: Context) -> None:
        """Pop highest-priority ready thread"""
        if not self.ready_threads:
            self.current_thread = None
            return

        thread = heapq.heappop(self.ready_threads)
        self.current_thread = thread

        if thread.state == ThreadStatus.READY:
            await thread.start(ctx)
        elif thread.state == ThreadStatus.SUSPENDED:
            await thread.resume(ctx)

    async def _resume_suspended(self, ctx: Context) -> None:
        """Resume most recently preempted thread"""
        if not self.suspended_stack:
            return

        thread = self.suspended_stack.pop()
        await thread.resume(ctx)
        self.current_thread = thread

    async def shutdown(self, ctx: Context) -> None:
        """Gracefully shutdown scheduler - cancel all threads and execute on_cancel tasks"""
        print("[scheduler] Shutting down - cancelling all threads")

        # Cancel current thread
        if self.current_thread:
            print(f"[scheduler] Cancelling current thread: {self.current_thread.thread_id}")
            await self.current_thread.cancel(ctx)
            self.current_thread = None

        # Cancel all ready threads
        while self.ready_threads:
            thread = heapq.heappop(self.ready_threads)
            print(f"[scheduler] Cancelling ready thread: {thread.thread_id}")
            await thread.cancel(ctx)

        # Cancel all suspended threads
        while self.suspended_stack:
            thread = self.suspended_stack.pop()
            print(f"[scheduler] Cancelling suspended thread: {thread.thread_id}")
            await thread.cancel(ctx)

        print("[scheduler] Shutdown complete")

    def __rich_repr__(self):
        yield "current_thread", self.current_thread.thread_id if self.current_thread else None
        yield "ready_threads", [t.thread_id for t in self.ready_threads]
        yield "suspended_stack", [t.thread_id for t in self.suspended_stack]

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_thread": self.current_thread.to_dict() if self.current_thread else None,
            "ready_threads": [t.thread_id for t in self.ready_threads],
            "suspended_stack": [t.thread_id for t in self.suspended_stack],
        }

    def to_json(self) -> str:
        from mqttbot import ServiceMessage
        return ServiceMessage(
            service="scheduler",
            method="state",
            params=self.to_dict()
        ).to_json()
