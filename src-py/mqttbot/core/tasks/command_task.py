import logging
import uuid
from typing import Any

from mqttbot import ServiceMessage
from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult, RequestStatus
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState

logger = logging.getLogger(__name__)


@task("command")
class CommandTask(TaskBase):
    """
    Run arbitrary command

    This is a simple mqtt wrapper. The service, method, and params are sent

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
            print("[CommandTask] Sending message")
            message = ServiceMessage(
                service=self.service,
                method=self.method,
                params=self.params,
                correlation_id=self.correlation_id,
            )
            # Send via context
            ctx.bot_service.send_message(message)
            self.request_id = message.request_id
            self._state = TaskState.WAITING
            return TaskStatus.RUNNING

        elif self._state == TaskState.WAITING:
            if ctx.bot_service:
                result = ctx.bot_service.get_result(self.request_id)
                if result:
                    self.result = result
                    if result.status == RequestStatus.SUCCESS:
                        print(f"[CommandTask] success to {self.service} - {self.method}")
                        return TaskStatus.SUCCESS
                    else:
                        print(f"[CommandTask] failed: {result.error}")
                        return TaskStatus.FAILED

            return TaskStatus.RUNNING
        return TaskStatus.FAILED

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

    def _suspend(self, ctx: Context) -> None:
        """Suspend - cancel remote operation and save state"""
        if self.request_id:
            logger.info(
                f"[CommandTask] Suspending {self.service}:{self.method}, cancelling request {self.request_id}"
            )
            cancel_msg = ServiceMessage(
                service=self.service,
                method="cancel",
                request_id=str(uuid.uuid4()),
                correlation_id=self.correlation_id,
                params={"request_id": self.request_id, "reason": "preempted"},
            )
            ctx.bot_service.send_message(cancel_msg)

        self._state = TaskState.SUSPENDED

    def _resume(self, ctx: Context) -> None:
        """Resume - reset state to trigger a fresh request"""
        logger.info(f"[CommandTask] Resuming for {self.service}:{self.method}")

        # Reset to INIT to force a new request_id and fresh message
        self._state = TaskState.INIT
        self.request_id = None
