
from mqttbot.core.tasks.task_base import TaskBase


class TaskRegistry:
    _registry: dict[str, type[TaskBase]] = {}

    @classmethod
    def register(cls, name: str, task_cls: type[TaskBase]) -> None:
        cls._registry[name] = task_cls

    @classmethod
    def get(cls, name: str) -> type[TaskBase]:
        return cls._registry[name]
