from typing import Protocol, Any

from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.task_thread_base import TaskThreadBase


class Scheduler(Protocol):
    """Protocol for the thread scheduler"""

    def register_thread(self, thread: TaskThreadBase) -> None:
        """Register a thread (typically at startup)"""
        ...

    def enqueue_thread(self, thread: TaskThreadBase, singleton: bool = False) -> bool:
        """
        Wake a thread (move to ready queue).

        Args:
            thread: The thread to enqueue
            singleton: If True, only allow one instance of this thread_id at a time

        Returns:
            True if enqueued, False if blocked (singleton already active)
        """
        ...

    def has_active_thread(self, thread_id: str) -> bool:
        """Public method to check if a thread is active"""
        ...

    def is_complete(self) -> bool:
        """Check if scheduler has completed all tasks."""
        ...

    async def step(self, ctx: Context) -> bool:
        """Execute one scheduler tick."""
        ...

    async def shutdown(self, ctx: Context) -> None:
        """Gracefully shutdown scheduler"""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary"""
        ...

    def to_json(self) -> str:
        """Convert state to JSON string"""
        ...
