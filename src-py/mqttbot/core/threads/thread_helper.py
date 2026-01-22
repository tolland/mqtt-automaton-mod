from rich import inspect

from mqttbot import ServiceMessage
from mqttbot.config.threads.thread_config import ThreadConfig
from mqttbot.core.patterns.pattern_thread import PatternThread, PatternThreadHelper
from mqttbot.core.protocol.task import Task
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.task_thread_base import TaskThreadBase
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.patterns.step import TaskStep, StepBase
from mqttbot.model.tasks.task import TaskFactory


class ThreadHelper:
    """Helper class for thread management."""

    @staticmethod
    def _create_task_from_step(step: TaskStep, trigger_msg: ServiceMessage | None = None) -> Task | None:
        """Create a task from a step definition"""

        return TaskFactory.create(step.to_dict())

    @staticmethod
    def _parse_task_steps(specs: list[StepBase]) -> list[TaskStep]:
        """Parse a list of task-spec dicts into TaskStep objects.

        Keeps the same inspect-and-raise behavior on failure.
        """
        steps: list[TaskStep] = []
        for task_spec in specs:
            try:
                step = TaskStep(
                    type=task_spec.get("type", "command"),
                    service=task_spec["service"],
                    method=task_spec["method"],
                    params=task_spec.get("params", {}),
                )
                steps.append(step)
            except Exception:
                inspect(task_spec)
                raise
        return steps

    @staticmethod
    def _tasks_from_steps(steps: list[TaskStep], correlation_id: str) -> list[Task]:
        """Convert TaskStep objects into Task instances and stamp correlation_id."""
        tasks: list[Task] = []
        for step in steps:
            task = TaskFactory.create(step.to_dict())
            task.correlation_id = correlation_id
            tasks.append(task)
        return tasks

    @staticmethod
    def _create_thread_from_thread_config(
        config: ThreadConfig,
        patterns: PatternsConfig
    ) -> TaskThreadBase:
        """
        Materialises a TaskThread from a ThreadConfig
        """

        # Parse suspend/resume/cancel tasks into TaskStep objects (shared helper)
        suspend_steps = ThreadHelper._parse_task_steps(config.on_suspend_tasks)
        resume_steps = ThreadHelper._parse_task_steps(config.on_resume_tasks)
        cancel_steps = ThreadHelper._parse_task_steps(config.on_cancel_tasks)
        failed_steps = ThreadHelper._parse_task_steps(config.on_failed_tasks)

        def on_suspend(thread: TaskThreadBase, ctx: Context) -> list[Task]:
            """Execute suspend tasks (return list of Task instances)."""
            return ThreadHelper._tasks_from_steps(suspend_steps, thread.correlation_id)

        def on_resume(thread: TaskThreadBase, ctx: Context) -> list[Task]:
            """Execute resume tasks (return list of Task instances)."""
            return ThreadHelper._tasks_from_steps(resume_steps, thread.correlation_id)

        def on_cancel(thread: TaskThreadBase, ctx: Context) -> list[Task]:
            """Execute cancel tasks (return list of Task instances)."""
            return ThreadHelper._tasks_from_steps(cancel_steps, thread.correlation_id)

        def on_failed(thread: TaskThreadBase, ctx: Context) -> list[Task]:
            """Execute failed tasks (return list of Task instances)."""
            return ThreadHelper._tasks_from_steps(failed_steps, thread.correlation_id)

        thread = PatternThread(
            thread_id=config.thread_id,
            priority=config.priority,
            waypoints=[x.to_dict() for x in config.waypoints],
            patterns=patterns,
            on_suspend=on_suspend,
            on_resume=on_resume,
            on_cancel=on_cancel,
            on_failed=on_failed,
            on_waypoint_start=config.on_waypoint_start_tasks,
            on_waypoint_end=config.on_waypoint_end_tasks,
            on_waypoints_start=config.on_waypoints_start_tasks,
            on_waypoints_end=config.on_waypoints_end_tasks,
        )

        PatternThreadHelper.build_task_sequence(thread)

        return thread
