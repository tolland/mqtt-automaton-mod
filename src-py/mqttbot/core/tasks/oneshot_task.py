from typing import Any

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState


@task("oneshot")
class OneShotTask(TaskBase):
    """
    Run arbitrary command and don't wait for any reply

    This is a task type used when we have not fully implemented the response handling to confirm task completion on the remote side. It should typically be only used for tasks that can be executed immediately and have little chance of failing, or that would cause problems if it failed remotely.
    """

    def __init__(self, service: str, method: str, params: dict[str, Any], timeout: int = 15):
        super().__init__()
        self.timeout = timeout
        self.request_id: str | None = None
        self.result: RequestResult | None = None
        self._state = TaskState.INIT
        self.service = service
        self.method = method
        self.params = params

    def _step(self, ctx: Context) -> TaskStatus:
        if self._state == TaskState.INIT:
            # Send warp request
            logger.debug("OneShotTask: Sending message")
            message = ServiceMessage(
                service=self.service,
                method=self.method,
                params=self.params,
                correlation_id=self.correlation_id,
            )
            # Send via context
            ctx.message_sender(message)
            self.request_id = message.request_id
            self._state = TaskState.WAITING
            return TaskStatus.RUNNING

        elif self._state == TaskState.WAITING:
            self._state = TaskState.DONE
            return TaskStatus.SUCCESS

        return TaskStatus.RUNNING
