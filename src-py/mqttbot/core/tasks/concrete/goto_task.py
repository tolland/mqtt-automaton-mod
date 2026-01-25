import time
from typing import Any

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.config.service_config import ServiceConfig
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_status import TaskInternalState, TaskStatus
from mqttbot.core.services.message_service import RequestStatus
from mqttbot.core.tasks.task_base import task, TaskBase
from mqttbot.core.threads.scheduler_context import Context


@task("goto")
class GotoTask(TaskBase):

    def __init__(
        self,
        service: str = None,
        method: str = None,
        params: dict[str, Any] = None,
        service_config: ServiceConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(metadata)
        # inspect(params)
        x = params["target"]["x"]
        y = params["target"]["y"]
        z = params["target"]["z"]
        self.target = (x, y, z)
        self.result = None
        self._timeout = 60.0
        self._sent_time = 0.0
        self.metadata = metadata
        self.params = params
        self.service_config = service_config
        self.service = service
        self.method = method

    @classmethod
    def create(
        cls,
        x: int,
        y: int,
        z: int,
        service_config: ServiceConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "GotoTask":
        """Factory method to create a GotoTask"""
        params: dict[str, Any] = {"target": {"x": x, "y": y, "z": z}}
        service = "baritone"
        method = "goto"
        return cls(service, method, params)

    def _step(self, ctx: Context) -> TaskStatus:
        bot_service = ctx.bot_service

        if self._internal_status == TaskInternalState.READY:
            # Send request
            logger.info(f"[GotoTask] Sending goto {self.target}")

            message_data = ServiceMessage(
                service="baritone",
                method="goto",
                request_id=self.request_id,
                correlation_id=self.correlation_id,
                params={"x": self.target[0], "y": self.target[1], "z": self.target[2]},
            )
            bot_service.send_message(message_data)

            self._sent_time = time.time()
            self.transition_to(TaskInternalState.SENT)

        elif self._internal_status == TaskInternalState.SENT:
            # Check if response arrived (non-blocking)
            result = bot_service.get_result(self.request_id)
            if result is not None:
                self.result = result
                self.transition_to(TaskInternalState.WAITING)
            # Check timeout
            elif time.time() - self._sent_time > self._timeout:
                logger.info(f"[GotoTask] Timeout waiting for goto {self.target}")
                self.transition_to(TaskInternalState.DONE)

        elif self._internal_status == TaskInternalState.WAITING:
            if self.result.status == RequestStatus.SUCCESS:
                logger.debug(f"Reached {self.target}")
                self.transition_to(TaskInternalState.DONE)
            else:
                logger.warning(f"Failed to reach {self.target}: {self.result.error}")
                self.transition_to(TaskInternalState.FAILED)

        elif self._internal_status in [TaskInternalState.CANCELING]:
            self.handle_cancel(ctx)
            self.transition_to(TaskInternalState.CANCELLED)

        elif self._internal_status in [TaskInternalState.SUSPENDING]:
            self.handle_cancel(ctx)
            self.transition_to(TaskInternalState.SUSPENDED)

        else:
            raise NotImplementedError(f"GotoTask: Unhandled internal state {self._internal_status}")

        return self.status

    def handle_cancel(self, ctx: Context) -> None:
        """Handle cancellation of the task"""
        if not self.request_id:
            raise ValueError("Cannot cancel GotoTask without a valid request_id")

        logger.info(f"[GotoTask] target: {self.target}, cancelling request {self.request_id}")
        cancel_msg = ServiceMessage(
            service="baritone",
            method="cancel",
            request_id=self.request_id,
            correlation_id=self.correlation_id,
            params={"request_id": self.request_id, "reason": "preempted"},
        )
        ctx.bot_service.send_message(cancel_msg)

    def clone(self) -> "Task":
        """Create a copy of this task"""
        new_task = GotoTask(
            service=self.service,
            method=self.method,
            params=self.params,
            service_config=self.service_config,
            metadata=self.metadata,
        )
        return new_task
