from typing import Optional, Any

from mqttbot.model.tasks.task_step_config import TaskStepConfig
from mqttbot.core.patterns.pattern_thread import PatternThread
from mqttbot.core.tasks.task import Task, create_task

from mqttbot import MessageData
from mqttbot.config.threads.thread_config import ThreadConfig
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.patterns_config import PatternsConfig


class ThreadHelper:
    """Helper class for thread management."""

    @staticmethod
    def is_thread_alive(thread) -> bool:
        """Check if a thread is alive.

        Args:
            thread: The thread to check.

        Returns:
            bool: True if the thread is alive, False otherwise.
        """
        return thread.is_alive()

    @staticmethod
    def _create_task_from_step(step: TaskStepConfig, trigger_msg: MessageData) -> Optional[Task]:
        """Create a task from a step definition"""

        return create_task(step.to_dict())

    @staticmethod
    def _create_thread_from_thread_config(
        config: ThreadConfig, patterns: dict[str, Any], patterns_config: PatternsConfig
    ) -> TaskThread:
        """Create a TaskThread from a ThreadConfig"""

        # Create callbacks for on_suspend and on_resume (if configured)
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
            patterns_config=patterns_config,
            on_suspend=on_suspend,
            on_resume=on_resume,
        )

        thread.build_task_sequence()

        return thread
