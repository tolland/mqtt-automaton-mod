from typing import Any

from mqttbot import ServiceMessage
from mqttbot.config.tasks.task_decorator import task
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.state.events.events_state import EventsState
from mqttbot.core.tasks.task_base import TaskBase
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState


@task("commandtochat")
class CommandToChatTask(TaskBase):
    """
    A Task that sends a command to a chat service and waits for the response.
    in the chat and filter based on params
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
        self.found = False

    def _enter(self, ctx: Context) -> None:
        """Initialize the task"""
        print("[CommandToChatTask] Starting ")

        ctx.blackboard.subscribe("events", self._handler)

        self._state = TaskState.INIT

    def _handler(self, event_state: EventsState):
        print(f"[CommandToChatTask] Event received: {event_state}")
        if isinstance(event_state, EventsState):
            if "clean_message" in event_state.message.response:
                clean_message = event_state.message.response["clean_message"]
                print(f"[CommandToChatTask] Clean message: {clean_message}")
                if "[Wurst] All items sold successfully" in clean_message:
                    print("[CommandToChatTask] Detected successful sell message.")
                    self.found = True

    def _step(self, ctx: Context) -> TaskStatus:
        if self._state == TaskState.INIT:
            # Send warp request
            print("[CommandToChatTask] stepping and sending message")
            message = ServiceMessage(
                service=self.service,
                method=self.method,
                params=self.params,
                correlation_id=self.correlation_id,
            )
            # Send via context mqtt direct, don't want bot_service to
            # track requestId
            ctx.message_sender(message)
            self.request_id = message.request_id
            self._state = TaskState.WAITING
            return TaskStatus.RUNNING

        elif self._state == TaskState.WAITING:
            if self.found:
                return TaskStatus.SUCCESS

            return TaskStatus.RUNNING

        return TaskStatus.FAILED

    def _exit(self, ctx: Any, status: TaskStatus) -> None:
        print("[CommandToChatTask] exiting ")

        ctx.blackboard.unsubscribe("events", self._handler)

        self._state = TaskState.DONE
