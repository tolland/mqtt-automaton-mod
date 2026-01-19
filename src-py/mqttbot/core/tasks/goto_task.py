import time
from enum import Enum
from typing import Optional, Any

from mqttbot.config.service_config import ServiceConfig
from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestStatus
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState
from mqttbot import ServiceMessage
import uuid
import time
import logging

logger = logging.getLogger(__name__)


@task("goto")
class GotoTask(TaskBase):

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
        self._state = TaskState.INIT
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
        logger.debug(f"[GotoTask] Starting navigation to {self.target}")

        self._state = TaskState.INIT

    def _step(self, ctx: Context) -> TaskStatus:
        """Synchronous step - returns immediately without blocking"""
        bot_service = ctx.bot_service

        if self._state == TaskState.INIT:
            # Send request
            logger.info(f"[GotoTask] Sending goto {self.target}")

            self.request_id = str(uuid.uuid4())
            message_data = ServiceMessage(
                service="baritone",
                method="goto",
                request_id=self.request_id,
                correlation_id=self.correlation_id,
                params={"x": self.target[0], "y": self.target[1], "z": self.target[2]},
            )
            bot_service.send_message(message_data)

            self._sent_time = time.time()
            self._state = TaskState.SENT
            return TaskStatus.RUNNING

        elif self._state == TaskState.SENT:
            # Check if response arrived (non-blocking)
            result = bot_service.get_result(self.request_id)
            if result is not None:
                self.result = result
                self._state = TaskState.WAITING
                return TaskStatus.RUNNING

            # Check timeout
            if time.time() - self._sent_time > self._timeout:
                logger.info(f"[GotoTask] Timeout waiting for goto {self.target}")
                return TaskStatus.FAILED

            return TaskStatus.RUNNING

        elif self._state == TaskState.WAITING:
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
        self._state = TaskState.SUSPENDED

    def _resume(self, ctx: Context) -> None:
        """Resume - restore state"""
        print(f"[GotoTask] Resumed for {self.target}")

        if self._state == TaskState.SUSPENDED:
            # We were suspended, we might need to re-send the request if it was lost
            # or check if it's still valid.
            # For now, if we have a request_id and we were waiting, let's try to resume waiting.
            if self.request_id:
                self._state = TaskState.SENT
            else:
                self._state = TaskState.INIT
        else:
            # Start fresh if not explicitly suspended
            self._state = TaskState.INIT

    def _exit(self, ctx: Context, status: TaskStatus) -> None:
        """Clean shutdown"""
        print(f"[GotoTask] Exiting {self.target} with status {status}")
        # Could cancel pending request here if needed
        pass
