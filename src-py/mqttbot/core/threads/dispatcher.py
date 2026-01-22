import heapq

from loguru import logger

from mqttbot.config.threads.thread_status import ThreadStatus
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.task_thread_base import TaskThreadBase


class Dispatcher:
    def __init__(self,
                 ready_queue: list[TaskThreadBase],
                 done_queue: list[TaskThreadBase],
                 ):
        """

        :rtype: None
        """
        self.ready_queue: list[TaskThreadBase] = ready_queue
        self.done_queue: list[TaskThreadBase] = done_queue
        self.current_thread: TaskThreadBase | None = None

    async def step(self, ctx: Context) -> bool:
        """Execute one dispatcher tick.

        Returns:
            True if all tasks are complete (scheduler is empty), False otherwise.
        """

        # Execute current thread
        if self.current_thread:
            current = self.current_thread
            try:
                status = await current.step(ctx)
                if status == ThreadStatus.RUNNING:
                    return False
                else:
                    self.done_queue.append(current)
                    self.current_thread = None
            except Exception as e:
                logger.error(f"Thread {current.thread_id} failed with exception: {e}")
                raise e
        elif self.ready_queue:
            await self._start_next_thread(ctx)

        # Return True if all work is done
        return self.is_complete()

    async def _start_next_thread(self, ctx: Context) -> None:
        """Pop highest-priority ready thread"""
        if not self.ready_queue:
            self.current_thread = None
            return

        thread = heapq.heappop(self.ready_queue)
        self.current_thread = thread

        if thread.state == ThreadStatus.READY:
            await thread.start(ctx)
        elif thread.state == ThreadStatus.SUSPENDED:
            await thread.resume(ctx)

    def is_complete(self) -> bool:
        """Check if dispatcher has consumed all threads."""
        return (
            len(self.ready_queue) == 0
            and self.current_thread is None)
