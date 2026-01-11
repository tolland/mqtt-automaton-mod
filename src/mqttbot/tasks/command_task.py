from typing import Optional, Any

from mqttbot import MessageData
from mqttbot.core.task.task import TaskStatus
from mqttbot.services.message_service import RequestResult, RequestStatus
from mqttbot.tasks.task import Task


class CommandTask(Task):
    """Run arbitrary command"""

    def __init__(self,
                 service: str,
                 method: str,
                 params: dict[str, Any],
                 timeout: int = 15):
        super().__init__()
        self.timeout = timeout
        self.request_id: Optional[str] = None
        self.result: Optional[RequestResult] = None
        self._state = "init"
        self.service = service
        self.method = method
        self.params = params

    def _step(self, ctx: dict) -> TaskStatus:
        if self._state == "init":
            # Send warp request
            print(f"[CommandTask] Sending message")
            message = MessageData(
                service="warp",
                method="teleport",
                params={
                    "name": self.name,
                    "target": {"x": self.target[0], "y": self.target[1], "z": self.target[2]}
                }
            )
            # Send via context
            ctx["message_sender"](message.to_json())
            self.request_id = message.request_id
            self._state = "waiting"
            return TaskStatus.RUNNING

        elif self._state == "waiting":
            # Check if warp completed
            warp_service = ctx.get("warp_service")
            if warp_service:
                result = warp_service.get_result(self.request_id)
                if result:
                    self.result = result
                    if result.status == RequestStatus.SUCCESS:
                        print(f"[WarpTask] Warped to {self.name}")
                        return TaskStatus.SUCCESS
                    else:
                        print(f"[WarpTask] Warp failed: {result.error}")
                        return TaskStatus.FAILED

            return TaskStatus.RUNNING

        return TaskStatus.FAILED
