from typing import Protocol, List, runtime_checkable, Iterator

from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.thread import ThreadInterface


@runtime_checkable
class TaskProvider(Protocol):
    """Common interface for anything that yields tasks based on thread state."""
    def get_tasks(self, thread: "ThreadInterface") -> Iterator["Task"]: ...

    # def get_next_batch(self, thread: "ThreadInterface") -> list["Task"]: ...
    #
    # def is_exhausted(self) -> bool: ...
