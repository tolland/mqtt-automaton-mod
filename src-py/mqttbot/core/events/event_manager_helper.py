
from mqttbot import ServiceMessage
from mqttbot.core.events.event_manager import EventHandlerConfig
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.core.threads.thread_helper import ThreadHelper


class EventManagerHelper:
    """
    Helper methods for EventManager when working with TaskThreads
    """

    @staticmethod
    async def _build_thread_from_config(
        thread_id: str, handler_config: EventHandlerConfig, trigger_msg: ServiceMessage
    ) -> TaskThread | None:
        """Build a TaskThread from event handler config"""

        thread = TaskThread(thread_id, TaskPriority.HIGH)

        for step in handler_config.steps:
            task = ThreadHelper._create_task_from_step(step, trigger_msg)
            if task:
                thread.enqueue_task(task)

        return thread
