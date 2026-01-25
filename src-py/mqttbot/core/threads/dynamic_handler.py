from typing import Iterator

from mqttbot.config.model.step.steps_discriminator import Step
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_compiler_protocol import TaskCompilerProtocol
from mqttbot.core.protocol.thread import ThreadInterface


class DynamicHandler:
    def __init__(self, steps: list[Step], compiler: "TaskCompilerProtocol"):
        self.steps = steps
        self.compiler = compiler

    def get_tasks(self, thread: "ThreadInterface") -> Iterator["Task"]:
        # Grabs live position for relative math at the moment of the event
        yield from (self.decorate(x) for x in self.build_task_sequence())
        return None

    def decorate(self, task: Task) -> Task:
        # Attach waypoint metadata to the task for traceability
        # task.metadata["waypoint_index"] = self.index - 1
        return task

    def build_task_sequence(
        self,
    ) -> Iterator[Task]:

        for step in self.steps:
           yield from self.compiler.compile_step(step)
        return

    def __rich_repr__(self) -> "rich.repr.Result":
        yield "steps", self.steps
