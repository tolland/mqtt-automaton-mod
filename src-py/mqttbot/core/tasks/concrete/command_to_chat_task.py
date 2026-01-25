from typing import Any

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.core.protocol.task_status import TaskInternalState, TaskStatus
from mqttbot.core.services.message_service import RequestResult
from mqttbot.core.state.events.events_state import EventsState
from mqttbot.core.tasks.task_base import task, TaskBase
from mqttbot.core.threads.scheduler_context import Context


@task("commandtochat")
class CommandToChatTask(TaskBase):
    """
    A Task that sends a command to a chat service and waits for the response.
    in the chat and filter based on params
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
        self.found = False

    def _enter(self, ctx: Context) -> None:
        """Initialize the task"""
        logger.debug("Starting CommandToChatTask")

        ctx.blackboard.subscribe("events", self._handler)

        self._state = TaskInternalState.READY

    def _handler(self, event_state: EventsState):
        logger.debug(f"Event received: {event_state}")
        if isinstance(event_state, EventsState):
            if "clean_message" in event_state.message.response:
                clean_message = event_state.message.response["clean_message"]
                logger.debug(f"Clean message: {clean_message}")
                if "[Wurst] All items sold successfully" in clean_message:
                    logger.debug("Detected successful sell message")
                    self.found = True

    def _step(self, ctx: Context) -> TaskStatus:
        if self._state == TaskInternalState.READY:
            # Send warp request
            logger.debug("Stepping and sending message")
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
            self._state = TaskInternalState.WAITING
            return TaskStatus.RUNNING

        elif self._state == TaskInternalState.WAITING:
            if self.found:
                return TaskStatus.SUCCESS

            return TaskStatus.RUNNING

        return TaskStatus.FAILED

    def _exit(self, ctx: Any, status: TaskStatus) -> None:
        logger.debug("CommandToChatTask exiting")

        ctx.blackboard.unsubscribe("events", self._handler)

        self._state = TaskInternalState.DONE
