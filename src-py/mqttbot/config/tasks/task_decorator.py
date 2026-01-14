from typing import Type

from mqttbot.config.tasks.task_registry import TaskRegistry
from mqttbot.core.tasks.task_base import TaskBase


def task(name: str | None = None):
    def decorator(cls: Type[TaskBase]):
        task_name = name or cls.__name__.removesuffix("Task").lower()
        TaskRegistry.register(task_name, cls)
        return cls
    return decorator
