
from mqttbot import ServiceMessage
from mqttbot.core.events.event_manager import EventHandlerConfig
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.threads.thread_base import TaskThreadBase


class EventManagerHelper:
    """
    Helper methods for EventManager when working with TaskThreads
    """

    @staticmethod
    async def _build_thread_from_config(
        thread_id: str, handler_config: EventHandlerConfig, trigger_msg: ServiceMessage
    ) -> TaskThreadBase | None:
        """Build a TaskThread from event handler config"""

        thread = TaskThreadBase(thread_id, ThreadPriority.HIGH)

        for step in handler_config.steps:
            task = PatternThreadHelper._create_task_from_step(step, trigger_msg)
            if task:
                thread.enqueue_task(task)

        return thread
