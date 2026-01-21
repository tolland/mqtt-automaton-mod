
from loguru import logger
from rich import inspect

from mqttbot import ServiceMessage
from mqttbot.config.threads.thread_config import ThreadConfig
from mqttbot.core.context import Context
from mqttbot.core.patterns.pattern_thread import PatternThread
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.patterns_config import PatternsConfig
from mqttbot.model.patterns.step import TaskStep
from mqttbot.model.tasks.task import Task, TaskFactory


class ThreadHelper:
    """Helper class for thread management."""

    @staticmethod
    def _create_task_from_step(step: TaskStep, trigger_msg: ServiceMessage) -> Task | None:
        """Create a task from a step definition"""

        return TaskFactory.create(step.to_dict())

    @staticmethod
    def _create_thread_from_thread_config(
            config: ThreadConfig,
            patterns: PatternsConfig
    ) -> TaskThread:
        """Create a TaskThread from a ThreadConfig"""

        # Parse suspend tasks into TaskStep objects
        suspend_steps = []
        for task_spec in config.on_suspend_tasks:
            try:
                step = TaskStep(
                    type=task_spec.get("type", "command"),
                    service=task_spec["service"],
                    method=task_spec["method"],
                    params=task_spec.get("params", {}),
                )
                suspend_steps.append(step)
            except Exception:
                inspect(task_spec)
                raise

        # Parse resume tasks into TaskStep objects
        resume_steps = []
        for task_spec in config.on_resume_tasks:
            try:
                step = TaskStep(
                    type=task_spec.get("type", "command"),
                    service=task_spec["service"],
                    method=task_spec["method"],
                    params=task_spec.get("params", {}),
                )
                resume_steps.append(step)
            except Exception:
                inspect(task_spec)
                raise

        # Parse cancel tasks into TaskStep objects
        cancel_steps = []
        for task_spec in config.on_cancel_tasks:
            try:
                step = TaskStep(
                    type=task_spec.get("type", "command"),
                    service=task_spec["service"],
                    method=task_spec["method"],
                    params=task_spec.get("params", {}),
                )
                cancel_steps.append(step)
            except Exception:
                inspect(task_spec)
                raise

        async def on_suspend(thread: TaskThread, ctx: Context) -> None:
            """Execute suspend tasks"""
            for step in suspend_steps:
                task = TaskFactory.create(step.to_dict())
                task.correlation_id = thread.correlation_id
                task.enter(ctx)

                # Execute task until completion
                while True:
                    status = task.step(ctx)
                    if status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                        task.exit(ctx, status)
                        break

                logger.debug(f"[{config.thread_id}] Suspend task {step.service}.{step.method}: {status.name}")

        async def on_resume(thread: TaskThread, ctx: Context) -> None:
            """Execute resume tasks"""
            for step in resume_steps:
                task = TaskFactory.create(step.to_dict())
                task.correlation_id = thread.correlation_id
                task.enter(ctx)

                # Execute task until completion
                while True:
                    status = task.step(ctx)
                    if status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                        task.exit(ctx, status)
                        break

                logger.debug(f"[{config.thread_id}] Resume task {step.service}.{step.method}: {status.name}")

        async def on_cancel(thread: TaskThread, ctx: Context) -> None:
            """Execute cancel tasks"""
            for step in cancel_steps:
                task = TaskFactory.create(step.to_dict())
                task.correlation_id = thread.correlation_id
                task.enter(ctx)

                # Execute task until completion
                while True:
                    status = task.step(ctx)
                    if status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                        task.exit(ctx, status)
                        break

                logger.debug(f"[{config.thread_id}] Cancel task {step.service}.{step.method}: {status.name}")

        thread = PatternThread(
            thread_id=config.thread_id,
            priority=config.priority,
            waypoints=[x.to_dict() for x in config.waypoints],
            patterns=patterns,
            on_suspend=on_suspend,
            on_resume=on_resume,
            on_cancel=on_cancel,
        )

        thread.build_task_sequence()

        return thread
