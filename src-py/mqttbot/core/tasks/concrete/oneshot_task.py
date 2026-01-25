from typing import Any

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.core.tasks.task_base import task, TaskBase
from mqttbot.core.protocol.task_status import TaskInternalState, TaskStatus
from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.threads.scheduler_context import Context


@task("oneshot")
class OneShotTask(TaskBase):
    """
    Run arbitrary command and don't wait for any reply

    This is a task type used when we have not fully implemented the response handling to confirm task completion on the remote side. It should typically be only used for tasks that can be executed immediately and have little chance of failing, or that would cause problems if it failed remotely.
    """

    def __init__(self, service: str, method: str, params: dict[str, Any], timeout: int = 15):
        super().__init__()
        self.timeout = timeout
        self.result: RequestResult | None = None
        self.service = service
        self.method = method
        self.params = params

    def _step(self, ctx: Context) -> TaskStatus:
        if self._internal_status == TaskInternalState.READY:
            logger.debug("OneShotTask: Sending message")
            message = ServiceMessage(
                service=self.service,
                method=self.method,
                params=self.params,
                request_id=self.request_id,
                correlation_id=self.correlation_id,
            )
            # Send via context
            ctx.message_sender(message)
            self.transition_to(TaskInternalState.SENT)
        elif self._internal_status == TaskInternalState.SENT:
            self.transition_to(TaskInternalState.WAITING)
        elif self._internal_status == TaskInternalState.WAITING:
            self.transition_to(TaskInternalState.DONE)
        elif self._internal_status == TaskInternalState.CANCELING:
            self.transition_to(TaskInternalState.CANCELLED)
        elif self._internal_status == TaskInternalState.SUSPENDING:
            self.transition_to(TaskInternalState.SUSPENDED)
        elif self._internal_status == TaskInternalState.RESUMING:
            self.transition_to(TaskInternalState.RESUMED)
        else:
            # For OneShotTask, we don't wait for a response;
            # we consider it done immediately after sending
            self.transition_to(TaskInternalState.DONE)

        return self.status
