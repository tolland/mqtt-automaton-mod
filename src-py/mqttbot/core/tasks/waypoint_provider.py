from typing import Iterator

from mqttbot.config.model.pattern.waypoint import Waypoint
from mqttbot.core.protocol.task import Task
from mqttbot.core.protocol.task_compiler_protocol import TaskCompilerProtocol
from mqttbot.core.protocol.task_provider import TaskProvider
from mqttbot.core.protocol.thread import ThreadInterface


class WaypointTaskSource(TaskProvider):

    def __init__(self, waypoints: list[Waypoint], compiler: "TaskCompilerProtocol"):
        self.waypoints = waypoints
        self.index = 0
        self.compiler = compiler

    def get_tasks(self, thread: "ThreadInterface") -> Iterator[Task]:
        if self.index >= len(self.waypoints):
            return []

        wp = self.waypoints[self.index]
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

        for wp in self.waypoints:
            wp_pos = (wp.x, wp.y, wp.z)

            # Expand and add pattern tasks
            pattern_names = wp.patterns
            for p_name in pattern_names:
                for task in self.compiler.compile_pattern(p_name, wp_pos):
                    wp_pos = self.compiler.current_pos
                    yield task
        return

        # for _step in pt.on_waypoints_end_steps:
        #     buff = PatternThreadHelper._create_task_from_step(_step)
        #     pt.enqueue_task(buff)

    def __rich_repr__(self):
        yield "waypoints_count", len(self.waypoints)
        yield "index", self.index
