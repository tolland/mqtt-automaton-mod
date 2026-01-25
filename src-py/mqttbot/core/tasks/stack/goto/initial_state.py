import time
import uuid
from typing import Optional

from mqttbot import ServiceMessage
from mqttbot.core.protocol.task_status import TaskStatus
from mqttbot.core.tasks.stack.goto.waiting_for_ack_state import GotoWaitingForAckState



class GotoInitialState:
    external_status = TaskStatus.RUNNING

    def on_enter(self, task: "GotoTask", ctx: "Context") -> None:
        # 1. Generate unique request identity for this specific attempt
        task.request_id = str(uuid.uuid4())

        # 2. Dispatch the MQTT message
        msg = ServiceMessage(
            service="baritone",
            method="goto",
            request_id=task.request_id,
            correlation_id=task.correlation_id,
            params={"x": task.target[0], "y": task.target[1], "z": task.target[2]},
        )
        ctx.bot_service.send_message(msg)
        task.last_sent_time = time.time()

    def step(self, task: "GotoTask", ctx: "Context") -> Optional[TaskState]:
        # Transition immediately to waiting for the ACK
        return GotoWaitingForAckState()

    def handle_suspend(self, task: "GotoTask", ctx: "Context") -> Optional[TaskState]:
        # If suspended before we even move to waiting, just go to suspended
        return GlobalSuspendedState()
