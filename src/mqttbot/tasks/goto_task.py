import time
from typing import Optional
from enum import Enum

from mqttbot.core.context import Context
from mqttbot.core.service_config import ServiceConfig
from mqttbot.core.task.task import TaskContext
from mqttbot.core.task.task import TaskStatus
from mqttbot.services.message_service import RequestStatus
from mqttbot.tasks.task import Task


class GotoTaskState(Enum):
    INIT = "init"
    SENT = "sent"
    WAITING = "waiting"
    DONE = "done"

class GotoTask(Task):

    def __init__(self, x: int, y: int, z: int, service_config: Optional[ServiceConfig] = None):
        super().__init__()
        self.target = (x, y, z)
        self.service_config = service_config
        self.request_id: Optional[str] = None
        self.result = None
        self._state = GotoTaskState.INIT
        self._timeout = 60.0
        self._sent_time = 0.0

    def _enter(self, ctx: TaskContext) -> None:
        """Initialize the task"""
        print(f"[GotoTask] Starting navigation to {self.target}")

        # Get timeout from service config (from context metadata)
        if not self.service_config:
            thread_config = ctx.metadata.get("thread_config")
            if thread_config:
                self.service_config = thread_config.services.get("baritone")

        if self.service_config:
            self._timeout = self.service_config.timeout

        self._state = GotoTaskState.INIT

    def _step(self, ctx: Context) -> TaskStatus:
        """Synchronous step - returns immediately without blocking"""
        bot_service = ctx.bot_service

        if self._state == GotoTaskState.INIT:
            # Send request
            print(f"[GotoTask] Sending goto {self.target}")
            self.request_id = bot_service.send_goto(*self.target)
            self._sent_time = time.time()
            self._state = GotoTaskState.SENT
            return TaskStatus.RUNNING

        elif self._state == GotoTaskState.SENT:
            # Check if response arrived (non-blocking)
            result = bot_service.get_result(self.request_id)
            if result is not None:
                self.result = result
                self._state = GotoTaskState.WAITING
                return TaskStatus.RUNNING

            # Check timeout
            if time.time() - self._sent_time > self._timeout:
                print(f"[GotoTask] Timeout waiting for goto {self.target}")
                return TaskStatus.FAILED

            return TaskStatus.RUNNING

        elif self._state == GotoTaskState.WAITING:
            if self.result.status == RequestStatus.SUCCESS:
                print(f"[GotoTask] Successfully reached {self.target}")
                return TaskStatus.SUCCESS
            else:
                print(f"[GotoTask] Failed to reach {self.target}: {self.result.error}")
                return TaskStatus.FAILED

        return TaskStatus.FAILED

    def _suspend(self) -> TaskContext:
        """Suspend - save state for resumption"""
        print(f"[GotoTask] Suspended at {self.target}")
        # Save the request ID and current state
        return TaskContext(
            step_index=0,
            metadata={
                "request_id": self.request_id,
                "task_state": self._state.value,
            }
        )

    def _resume(self, ctx: TaskContext) -> None:
        """Resume - restore state"""
        print(f"[GotoTask] Resumed for {self.target}")
        # Restore state from metadata
        self.request_id = ctx.metadata.get("request_id")
        task_state = ctx.metadata.get("task_state")

        if task_state and self.request_id:
            # We were waiting for a response, continue waiting
            self._state = GotoTaskState.SENT
        else:
            # Start fresh
            self._state = GotoTaskState.INIT

    def _exit(self, ctx: TaskContext, status: TaskStatus) -> None:
        """Clean shutdown"""
        print(f"[GotoTask] Exiting {self.target} with status {status}")
        # Could cancel pending request here if needed
        pass
