from typing import Optional, Any

from mqttbot import MessageData
from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult, RequestStatus
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus


@task("command")
class CommandTask(TaskBase):
    """Run arbitrary command"""

    def __init__(self, service: str, method: str, params: dict[str, Any], timeout: int = 15):
        super().__init__()
        self.timeout = timeout
        self.request_id: Optional[str] = None
        self.result: Optional[RequestResult] = None
        self._state = "init"
        self.service = service
        self.method = method
        self.params = params

    def _step(self, ctx: Context) -> TaskStatus:
        if self._state == "init":
            # Send warp request
            print(f"[CommandTask] Sending message")
            message = MessageData(
                service=self.service,
                method=self.method,
                params=self.params,
                correlation_id=ctx.correlation_id,
            )
            # Send via context
            ctx.bot_service.send_message(message)
            self.request_id = message.request_id
            self._state = "waiting"
            return TaskStatus.RUNNING

        elif self._state == "waiting":
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
