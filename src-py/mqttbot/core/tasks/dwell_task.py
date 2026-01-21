import time
from typing import Any

from loguru import logger

from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState


@task("dwell")
class DwellTask(TaskBase):
    """Client-side pause/wait for a specified duration

    This is a pure client-side task - it doesn't send any messages or
    interact with services. It's useful for:
    - Pattern timing (wait between farming operations)
    - Crop growth (dwell before harvesting again)
    - Speed control (delay between pathfinding operations)
    - Bot stabilization (brief pause after reaching a waypoint)

    Can be used in patterns, events, or any other thread that needs timing control.
    """

    def __init__(
        self,
        service: str = None,
        method: str = None,
        params: dict[str, Any] = None,
    ):
        """Initialize dwell task

        Args:
            seconds: How long to dwell
            reason: Optional description (for logging)
        """
        super().__init__()
        # Support both legacy 'period' key and normalized 'dwell_seconds' from pattern parsing
        if params is None:
            params = {}
        self.duration = params.get("period", params.get("dwell_seconds"))
        if self.duration is None:
            raise KeyError("DwellTask requires a 'period' or 'dwell_seconds' parameter")
        self.duration = float(self.duration)
        self.reason = params.get("reason", "")
        self.start_time: float = 0.0
        self._state = TaskState.INIT

    def _enter(self, ctx: Context) -> None:
        """Initialize dwell"""
        reason_str = f" ({self.reason})" if self.reason else ""
        logger.debug(f"Dwelling for {self.duration}s{reason_str}")
        self.start_time = time.time()
        self._state = TaskState.WAITING

    def _step(self, ctx: dict) -> TaskStatus:
        """Check if dwell time has elapsed"""
        elapsed = time.time() - self.start_time

        if elapsed >= self.duration:
            logger.debug("Dwell completed")
            self._state = TaskState.DONE
            return TaskStatus.SUCCESS

        # Still waiting (don't log every tick to avoid spam)
        return TaskStatus.RUNNING

    def _suspend(self, ctx: Context) -> None:
        """Suspend - save remaining time"""
        elapsed = time.time() - self.start_time
        remaining = self.duration - elapsed
        logger.debug(f"Dwell suspended: {remaining:.1f}s remaining")
        self._state = TaskState.SUSPENDED

    def _resume(self, ctx: Context) -> None:
        """Resume - adjust start time to account for remaining duration"""
        # Note: In real system, remaining_seconds would be passed via metadata or similar
        # If not present, we use current duration as default (start fresh)
        remaining = ctx.metadata.get("remaining_seconds", self.duration)
        logger.debug(f"Dwell resumed: {remaining:.1f}s remaining")

        # Adjust start time so elapsed calculation gives correct result
        self.start_time = time.time() - (self.duration - remaining)
        self._state = TaskState.WAITING

    def _exit(self, ctx: Context, status: TaskStatus) -> None:
        """Clean shutdown"""
        logger.debug(f"Exiting dwell: {status.name}")
