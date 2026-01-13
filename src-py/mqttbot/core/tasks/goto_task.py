import time
from enum import Enum
from typing import Optional, Any

from mqttbot.core.services.message_service import RequestStatus
from mqttbot.core.tasks.task import Task
from mqttbot.core.tasks.task_priority import TaskStatus

from mqttbot.core.context import Context
from mqttbot.core.service_config import ServiceConfig


class GotoTaskState(Enum):
    INIT = "init"
    SENT = "sent"
    WAITING = "waiting"
    DONE = "done"


class GotoTask(Task):

    def __init__(
        self,
        service: str = None,
        method: str = None,
        params: dict[str, Any] = None,
        service_config: Optional[ServiceConfig] = None,
    ):
        super().__init__()
        # inspect(params)
        x = params["target"]["x"]
        y = params["target"]["y"]
        z = params["target"]["z"]
        self.target = (x, y, z)
        self.service_config = service_config
        self.request_id: Optional[str] = None
        self.result = None
        self._state = GotoTaskState.INIT
        self._timeout = 60.0
        self._sent_time = 0.0

    @classmethod
    def create(
        cls, x: int, y: int, z: int, service_config: Optional[ServiceConfig] = None
    ) -> "GotoTask":
        """Factory method to create a GotoTask"""
        params: dict[str, Any] = {"target": {"x": x, "y": y, "z": z}}
        service = "baritone"
        method = "goto"
        return cls(service, method, params)

    def _enter(self, ctx: Context) -> None:
        """Initialize the task"""
        print(f"[GotoTask] Starting navigation to {self.target}")

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

    def _suspend(self) -> None:
        """Suspend - save state for resumption"""
        print(f"[GotoTask] Suspended at {self.target}")


    def _resume(self, ctx: Context) -> None:
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

    def _exit(self, ctx: Context, status: TaskStatus) -> None:
        """Clean shutdown"""
        print(f"[GotoTask] Exiting {self.target} with status {status}")
        # Could cancel pending request here if needed
        pass
