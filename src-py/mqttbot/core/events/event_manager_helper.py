from mqttbot import ServiceMessage
from mqttbot.core.events.event_manager import EventHandlerConfig, EventManager
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.core.threads.dynamic_handler import DynamicHandler
from mqttbot.core.threads.thread import TaskThread
from mqttbot.core.threads.thread_base import TaskThreadBase


class EventManagerHelper:
    """
    Helper methods for EventManager when working with TaskThreads
    """

    @staticmethod
    def build_thread_from_config(
        full_config,
    ) -> "TaskThread":

        patterns_configs = full_config.pattern_config
        thread_configs = full_config.thread_config
        event_configs = full_config.event_handlers

        event_manager = EventManager(event_configs)

        handler_config = event_manager.get_handler_config("inventory", "inventory_full")

        task_compiler = TaskCompiler(patterns_configs)
        event_thread = TaskThread(
            thread_id="event-thread-1",
            main_source_provider=DynamicHandler(handler_config.steps, task_compiler),
            on_suspend_provider=DynamicHandler([], task_compiler),
            on_resume_provider=DynamicHandler([], task_compiler),
            on_cancel_provider=DynamicHandler([], task_compiler),
            on_failed_provider=DynamicHandler([], task_compiler),
            priority=ThreadPriority.HIGH,
        )
        return event_thread
