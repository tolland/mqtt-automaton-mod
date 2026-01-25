import heapq
from typing import Any

from loguru import logger
from rich import inspect
from rich.repr import rich_repr
from rich import print as rprint

from mqttbot.core.protocol.thread_status import ThreadStatus
from mqttbot.core.protocol.scheduler import Scheduler
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.threads.dispatcher import Dispatcher
from mqttbot.core.threads.scheduler_context import Context


@rich_repr
class SchedulerBase(Scheduler):
    """Manages thread-level preemption"""

    def __init__(self) -> None:
        """

        :rtype: None
        """
        # self.ready_threads: list[ThreadInterface] = []
        # # the dispatcher puts items here when done
        # self.done_queue: list[ThreadInterface] = []
        self.dispatcher = Dispatcher(
            [],
            [],
        )
        # For MQTT state diff publishing
        self.old_state: dict[str, Any] | None = None

    """
    To match behaviour for before the scheduler was split out, we are using these property setters and getters to keep tests working
    """

    @property
    def current_thread(self) -> ThreadInterface | None:
        """Get the currently executing thread, if any."""
        return self.dispatcher.current_thread

    @current_thread.setter
    def current_thread(self, thread: ThreadInterface | None) -> None:
        """Set the currently executing thread."""
        self.dispatcher.current_thread = thread

    @property
    def done_threads(self) -> list[ThreadInterface] | None:
        """Get the currently executing thread, if any."""
        return self.dispatcher.done_threads

    @property
    def ready_threads(self) -> list[ThreadInterface] | None:
        """Get the currently executing thread, if any."""
        return self.dispatcher.ready_queue

    def register_thread(self, thread: ThreadInterface) -> None:
        """Register a thread (typically at startup)"""
        heapq.heappush(self.ready_threads, thread)

    def enqueue_thread(self, thread: ThreadInterface, singleton: bool = False) -> bool:
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
                logger.debug(f"Thread {thread.thread_id} already active, skipping")
                return False

        heapq.heappush(self.ready_threads, thread)
        logger.debug(f"Enqueued thread: {thread.thread_id}")
        return True

    def _thread_id_exists(self, thread_id: str) -> bool:
        """Check if a thread with this ID exists in any queue"""
        # Check current thread
        if self.current_thread and self.current_thread.thread_id == thread_id:
            return True

        # Check ready queue
        if any(t.thread_id == thread_id for t in self.ready_threads):
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
        )

    async def step(self, ctx: Context) -> bool:
        """Execute one scheduler tick."""
        self._publish_state(ctx)  # for debugging hung schedulers

        # move done threads done due to suspension back to ready queue
        remaining_done_queue = []
        for thread in self.done_threads:
            if thread.status == ThreadStatus.SUSPENDED:
                logger.debug(f"Thread {thread.thread_id} suspended, moving to ready_threads stack")
                self.ready_threads.append(thread)
            else:
                remaining_done_queue.append(thread)
        # Maintain the same list object that Dispatcher holds by mutating in-place
        self.done_threads[:] = remaining_done_queue

        # Check if any ready thread should preempt current thread
        if self.ready_threads and self._should_preempt():
            await self._preempt(ctx)
            return False

        # Return True if all work is done
        try:
            return await self.dispatcher.step(ctx)
        except Exception as e:
            rprint(self)
            raise e

    def _should_preempt(self) -> bool:
        """
        Compares the current thread's priority against the highest-priority ready thread.

        :return:
        :rtype:
        """
        if not self.current_thread or not self.ready_threads:
            return False

        # Cannot preempt uninterruptible threads
        if self.current_thread.uninterruptible:
            return False

        return any(
            [
                thread.priority.value < self.current_thread.priority.value
                for thread in self.ready_threads
            ]
        )

    async def _preempt(self, ctx: Context) -> None:
        """Suspend current thread, switch to higher priority"""
        assert self.current_thread is not None

        self.current_thread.suspend(ctx)

    async def shutdown(self, ctx: Context) -> None:
        """Gracefully shutdown scheduler - cancel all threads and execute on_cancel tasks"""
        logger.info("Shutting down - cancelling all threads")

        # Cancel current thread
        if self.current_thread:
            logger.info(f"Cancelling current thread: {self.current_thread.thread_id}")
            self.current_thread.cancel(ctx)

        # @TODO are there any circumstances where we want to cancel suspended threads?
        # Cancel all ready threads
        # while self.ready_threads:
        #     thread = heapq.heappop(self.ready_threads)
        #     logger.debug(f"Cancelling ready thread: {thread.thread_id}")
        #     await thread.cancel(ctx)

        logger.info("Shutdown complete")

    def _publish_state(self, ctx: Context) -> None:
        """Publish state to MQTT"""
        if ctx.mqtt:
            if self.to_dict() != self.old_state:
                self.old_state = self.to_dict()
                topic = f"{ctx.mqtt.topic_base}/scheduler/state"
                ctx.mqtt.send(topic, self.to_json())

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_thread": self.current_thread.to_dict() if self.current_thread else None,
            "ready_threads": [
                (
                    t.thread_id,
                    t.priority,
                )
                for t in self.ready_threads
            ],
            "done_queue": [t.to_dict() for t in self.done_threads],
        }

    def to_json(self) -> str:
        from mqttbot import ServiceMessage

        return ServiceMessage(service="scheduler", method="state", params=self.to_dict()).to_json()

    def __rich_repr__(self):
        yield "is_complete", self.is_complete()
        yield "ready_threads", [
            (
                t.thread_id,
                t.priority,
            )
            for t in self.ready_threads
        ]
        yield self.dispatcher


def create(*args, **kwargs) -> Scheduler:
    """Entry point to get a scheduler instance."""
    return SchedulerBase(*args, **kwargs)
