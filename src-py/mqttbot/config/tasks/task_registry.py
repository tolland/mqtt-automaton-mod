from typing import Type, Dict

from mqttbot.core.tasks.task_base import TaskBase


class TaskRegistry:
    _registry: Dict[str, Type[TaskBase]] = {}

    @classmethod
    def register(cls, name: str, task_cls: Type[TaskBase]) -> None:
        cls._registry[name] = task_cls

    @classmethod
    def get(cls, name: str) -> Type[TaskBase]:
        return cls._registry[name]
