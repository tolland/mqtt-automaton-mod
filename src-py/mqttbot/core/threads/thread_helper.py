from typing import Optional

from mqttbot import ServiceMessage
from mqttbot.config.threads.thread_config import ThreadConfig
from mqttbot.core.patterns.pattern_thread import PatternThread
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.patterns.step import TaskStep
from mqttbot.model.tasks.task import Task, TaskFactory


class ThreadHelper:
    """Helper class for thread management."""

    @staticmethod
    def _create_task_from_step(step: TaskStep, trigger_msg: ServiceMessage) -> Optional[Task]:
        """Create a task from a step definition"""

        return TaskFactory.create(step.to_dict())

    @staticmethod
    def _create_thread_from_thread_config(
        config: ThreadConfig, patterns: PatternsConfig
    ) -> TaskThread:
        """Create a TaskThread from a ThreadConfig"""

        async def on_suspend(thread: TaskThread) -> None:
            # Execute suspend tasks
            for task_spec in config.on_suspend_tasks:
                service = task_spec.get("service")
                method = task_spec.get("method")
                params = task_spec.get("params", {})
                print(f"[thread] {config.thread_id} suspending: {service}.{method}")
                # TODO: Route to appropriate service

        async def on_resume(thread: TaskThread, ctx) -> None:
            # Execute resume tasks
            for task_spec in config.on_resume_tasks:
                service = task_spec.get("service")
                method = task_spec.get("method")
                params = task_spec.get("params", {})
                print(f"[thread] {config.thread_id} resuming: {service}.{method}")
                # TODO: Route to appropriate service

        thread = PatternThread(
            thread_id=config.thread_id,
            priority=config.priority,
            waypoints=[x.to_dict() for x in config.waypoints],
            patterns=patterns,
            on_suspend=on_suspend,
            on_resume=on_resume,
        )

        thread.build_task_sequence()

        return thread
