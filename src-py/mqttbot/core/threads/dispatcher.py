import heapq

from loguru import logger

from mqttbot.core.protocol.thread_status import ThreadStatus
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.threads.scheduler_context import Context


class Dispatcher:
    def __init__(self,
                 ready_queue: list[ThreadInterface],
                 done_threads: list[ThreadInterface],
                 ):
        """

        :rtype: None
        """
        self.ready_queue: list[ThreadInterface] = ready_queue
        self.done_threads: list[ThreadInterface] = done_threads
        self.current_thread: ThreadInterface | None = None

    async def step(self, ctx: Context) -> bool:
        """Execute one dispatcher tick.

        Returns:
            True if all tasks are complete (scheduler is empty), False otherwise.
        """

        # Execute current thread
        if self.current_thread:
            current = self.current_thread
            try:
                status = current.step(ctx)
                if status == ThreadStatus.RUNNING:
                    return False
                else:
                    self.done_threads.append(current)
                    self.current_thread = None
            except Exception as e:
                logger.error(f"Thread {current.thread_id} failed with exception: {e}")
                raise e
        elif self.ready_queue:
            self._start_next_thread(ctx)

        # Return True if all work is done
        return self.is_complete()

    def _start_next_thread(self, ctx: Context) -> None:
        """Pop highest-priority ready thread"""
        if not self.ready_queue:
            self.current_thread = None
            return

        thread = heapq.heappop(self.ready_queue)
        self.current_thread = thread

        if thread.status == ThreadStatus.READY:
            thread.start(ctx)
        elif thread.status == ThreadStatus.SUSPENDED:
            thread.resume(ctx)

    def is_complete(self) -> bool:
        """Check if dispatcher has consumed all threads."""
        return (
            len(self.ready_queue) == 0
            and self.current_thread is None)

    def __rich_repr__(self):
        yield "current_thread", self.current_thread
        yield "ready_queue", self.ready_queue
        yield "done_queue", self.done_threads
