"""DwellTask - pause/wait for a specified duration

Client-side task that doesn't require any server communication.
Used for timing-based control (e.g., allowing crops to grow, waiting for
Baritone to stabilize, throttling farming speed).

Can be used in patterns, events, or any other thread that needs timing control.
"""
import time
from typing import Optional

from mqttbot.core.task.task import TaskContext, TaskStatus
from mqttbot.tasks.task import Task


class DwellTask(Task):
    """Client-side pause/wait for a specified duration

    This is a pure client-side task - it doesn't send any messages or
    interact with services. It's useful for:
    - Pattern timing (wait between farming operations)
    - Crop growth (dwell before harvesting again)
    - Speed control (delay between pathfinding operations)
    - Bot stabilization (brief pause after reaching a waypoint)
    """

    def __init__(self, seconds: float, reason: Optional[str] = None):
        """Initialize dwell task

        Args:
            seconds: How long to dwell
            reason: Optional description (for logging)
        """
        super().__init__()
        self.duration = seconds
        self.reason = reason or ""
        self.start_time: float = 0.0

    def _enter(self, ctx: TaskContext) -> None:
        """Initialize dwell"""
        reason_str = f" ({self.reason})" if self.reason else ""
        print(f"[DwellTask] Dwelling for {self.duration}s{reason_str}")
        self.start_time = time.time()

    def _step(self, ctx: dict) -> TaskStatus:
        """Check if dwell time has elapsed"""
        elapsed = time.time() - self.start_time

        if elapsed >= self.duration:
            print(f"[DwellTask] Dwell completed")
            return TaskStatus.SUCCESS

        # Still waiting (don't log every tick to avoid spam)
        return TaskStatus.RUNNING

    def _suspend(self) -> TaskContext:
        """Suspend - save remaining time"""
        elapsed = time.time() - self.start_time
        remaining = self.duration - elapsed
        print(f"[DwellTask] Suspended with {remaining:.1f}s remaining")

        return TaskContext(
            step_index=0,
            metadata={"remaining_seconds": remaining}
        )

    def _resume(self, ctx: TaskContext) -> None:
        """Resume - adjust start time to account for remaining duration"""
        remaining = ctx.metadata.get("remaining_seconds", self.duration)
        print(f"[DwellTask] Resumed - {remaining:.1f}s remaining")

        # Adjust start time so elapsed calculation gives correct result
        # If we slept for 2s and had 3s remaining, we need elapsed to be 2s when resumed
        self.start_time = time.time() - (self.duration - remaining)

    def _exit(self, ctx, status: TaskStatus) -> None:
        """Clean shutdown"""
        print(f"[DwellTask] Exiting with status {status}")
