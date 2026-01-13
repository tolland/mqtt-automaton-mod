from typing import Optional, Any



from mqttbot import MessageData
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.state.events.events_state import EventsState
from mqttbot.core.tasks.goto_task import GotoTaskState
from mqttbot.core.tasks.task import Task
from mqttbot.core.tasks.task_priority import TaskStatus


class CommandToChatTask(Task):
    """
    A Task that sends a command to a chat service and waits for the response.
    in the chat and filter based on params
    """

    def __init__(self, service: str, method: str, params: dict[str, Any], timeout: int = 15):
        super().__init__()
        self.timeout = timeout
        self.request_id: Optional[str] = None
        self.result: Optional[RequestResult] = None
        self._state = GotoTaskState.INIT
        self.service = service
        self.method = method
        self.params = params
        self.found = False

    def _enter(self, ctx: Context) -> None:
        """Initialize the task"""
        print(f"[CommandToChatTask] Starting ")

        ctx.blackboard.subscribe("events", self._handler)

        self._state = GotoTaskState.INIT

    def _handler(self, event_state: EventsState):
        print(f"[CommandToChatTask] Event received: {event_state}")
        if isinstance(event_state, EventsState):
            if "clean_message" in event_state.message.response:
                clean_message = event_state.message.response["clean_message"]
                print(f"[CommandToChatTask] Clean message: {clean_message}")
                if '[Wurst] All items sold successfully' in clean_message:
                    print(f"[CommandToChatTask] Detected successful sell message.")
                    self.found = True

    def _step(self, ctx: Context) -> TaskStatus:
        if self._state == GotoTaskState.INIT:
            # Send warp request
            print(f"[CommandToChatTask] stepping and sending message")
            message = MessageData(
                service=self.service,
                method=self.method,
                params=self.params,
            )
            # Send via context mqtt direct, don't want bot_service to
            # track requestId
            ctx.message_sender(message)
            self.request_id = message.request_id
            self._state = GotoTaskState.WAITING
            return TaskStatus.RUNNING

        elif self._state == GotoTaskState.WAITING:
            if self.found:
                return TaskStatus.SUCCESS

            return TaskStatus.RUNNING

        return TaskStatus.FAILED

    def _exit(self, ctx: Any, status: Any) -> None:
        print(f"[CommandToChatTask] exiting ")

        ctx.blackboard.unsubscribe("events", self._handler)

        self._state = GotoTaskState.DONE
