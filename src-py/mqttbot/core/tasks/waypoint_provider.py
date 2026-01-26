from typing import Iterator

from mqttbot.config.model.pattern.waypoint import Waypoint
from mqttbot.config.model.thread.thread_definition import ThreadDefinition
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_compiler_protocol import TaskCompilerProtocol
from mqttbot.core.protocol.task_provider import TaskProvider
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.tasks.concrete import GotoTask


class WaypointTaskSource(TaskProvider):
    """
    Waypoint Tasks are an initial Goto x,y,z followed by a series of steps
    which may include Patterns which are relative coordinates incrementally
    calculated from the last position.
    """

    def __init__(self, definition: ThreadDefinition, compiler: "TaskCompilerProtocol"):
        self.definition = definition
        self.index = 0
        self.compiler = compiler

    def get_tasks(self, thread: "ThreadInterface") -> Iterator[Task]:
        if self.index >= len(self.definition.waypoints):
            return []

        wp = self.definition.waypoints[self.index]
        self.index += 1

        # Expand the waypoint into a batch of Goto and Pattern tasks
        # Note: We use the waypoint's static XYZ as the anchor for its patterns
        yield from (self.decorate(x) for x in self.build_task_sequence())
        return None

    def decorate(self, task: Task) -> Task:
        # Attach waypoint metadata to the task for traceability
        # task.metadata["waypoint_index"] = self.index - 1
        return task

    def build_task_sequence(
        self,
    ) -> Iterator[Task]:

        for step in self.definition.hooks.on_waypoints_start.steps:
            yield from self.compiler.compile_step(step)

        for wp in self.definition.waypoints:

            for step in self.definition.hooks.on_waypoint_start.steps:
                yield from self.compiler.compile_step(step)

            wp_pos = (wp.x, wp.y, wp.z)

            yield GotoTask.create(*wp_pos)

            # Expand and add pattern tasks
            pattern_names = wp.patterns
            for p_name in pattern_names:
                for task in self.compiler.compile_pattern(p_name, wp_pos):
                    wp_pos = self.compiler.current_pos
                    yield task

            for step in self.definition.hooks.on_waypoint_end.steps:
                yield from self.compiler.compile_step(step)

        for step in self.definition.hooks.on_waypoints_end.steps:
            yield from self.compiler.compile_step(step)

        return

        # for _step in pt.on_waypoints_end_steps:
        #     buff = PatternThreadHelper._create_task_from_step(_step)
        #     pt.enqueue_task(buff)

    def __rich_repr__(self):
        yield "waypoints_count", len(self.definition.waypoints)
        yield "index", self.index
