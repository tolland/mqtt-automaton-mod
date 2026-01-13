from typing import Optional, Any

from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.tasks.task import Task
from mqttbot.core.tasks.task_priority import TaskStatus

from mqttbot import MessageData
from mqttbot.core.context import Context


class OneShotTask(Task):
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
            print(f"[OneShotTask] Sending message")
            message = MessageData(
                service=self.service,
                method=self.method,
                params=self.params,
            )
            # Send via context
            ctx.message_sender(message)
            self.request_id = message.request_id
            self._state = "waiting"
            return TaskStatus.RUNNING

        elif self._state == "waiting":
            self._state = "done"
            return TaskStatus.SUCCESS

        return TaskStatus.RUNNING
