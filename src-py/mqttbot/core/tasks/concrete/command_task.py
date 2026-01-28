import uuid
from typing import Any

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.core.protocol.task_status import TaskInternalState, TaskStatus
from mqttbot.core.services.message_service import RequestResult, RequestStatus
from mqttbot.core.tasks.task_base import task, TaskBase
from mqttbot.core.threads.scheduler_context import Context


@task("command")
class CommandTask(TaskBase):
    """
    Run arbitrary command

    This is a simple mqtt wrapper. The service, method, and params are sent

    """

    def __init__(
        self,
        service: str,
        method: str,
        params: dict[str, Any],
        timeout: int = 15,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(metadata)
        self.timeout = timeout
        self.result: RequestResult | None = None
        self.service = service
        self.method = method
        self.params = params

    def _step(self, ctx: Context) -> TaskStatus:

        logger.info(f"[CommandTask] Sending {self.service}.{self.method} with {self.params}")
        if self._internal_status == TaskInternalState.READY:
            message = ServiceMessage(
                service=self.service,
                method=self.method,
                params=self.params,
                request_id=self.request_id,
                correlation_id=self.correlation_id,
            )
            # Send via context
            ctx.bot_service.send_message(message)
            self.transition_to(TaskInternalState.SENT)
            return TaskStatus.RUNNING

        elif self._internal_status in [TaskInternalState.SENT]:
            self.transition_to(TaskInternalState.WAITING)

        elif self._internal_status == TaskInternalState.WAITING:
            if ctx.bot_service:
                result = ctx.bot_service.get_result(self.request_id)
                if result:
                    self.result = result
                    if result.status == RequestStatus.SUCCESS:
                        logger.debug(f"Success: {self.service}.{self.method}")
                        self.transition_to(TaskInternalState.DONE)
                        return TaskStatus.SUCCESS
                    else:
                        logger.warning(f"Failed: {result.error}")
                        self.transition_to(TaskInternalState.FAILED)
                        return TaskStatus.FAILED

            return TaskStatus.RUNNING
        elif self._internal_status == TaskInternalState.SUSPENDING:
            if self.request_id:
                logger.info(
                    f"[CommandTask] Suspending {self.params}, cancelling request {self.request_id}"
                )
                cancel_msg = ServiceMessage(
                    service="baritone",
                    method="cancel",
                    request_id=str(uuid.uuid4()),
                    correlation_id=self.correlation_id,
                    params={"request_id": self.request_id, "reason": "preempted"},
                )
                ctx.bot_service.send_message(cancel_msg)
            self.transition_to(TaskInternalState.SUSPENDED)
            return TaskStatus.SUSPENDED

        elif self._internal_status in [TaskInternalState.CANCELING]:
            if self.request_id:
                logger.info(
                    f"[CommandTask] Suspending {self.params}, cancelling request {self.request_id}"
                )
                cancel_msg = ServiceMessage(
                    service="baritone",
                    method="cancel",
                    request_id=str(uuid.uuid4()),
                    correlation_id=self.correlation_id,
                    params={"request_id": self.request_id, "reason": "preempted"},
                )
                ctx.bot_service.send_message(cancel_msg)
            self.transition_to(TaskInternalState.CANCELLED)

        elif self._internal_status in [TaskInternalState.SUSPENDING]:
            self.transition_to(TaskInternalState.SUSPENDED)
        return self.status

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} 'id={self.request_id}' status={self._internal_status.name} service={self.service} method={self.method} params={self.params}>"

    def to_dict(self) -> dict[str, Any]:
        """Specific override for CommandTask state."""
        state = super().to_dict()
        state.update(
            {
                "service": self.service,
                "method": self.method,
                "params": self.params,
                "timeout": self.timeout,
            }
        )
        return state
