from dataclasses import dataclass, field
from typing import Any

from rich.repr import rich_repr

from mqttbot.config.service_config import ServiceConfig
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.model.patterns.step import StepBase
from mqttbot.model.patterns.waypoint import Waypoint


@rich_repr
@dataclass
class ThreadConfig:
    """Configuration for a TaskThread

    Attributes:
        priority: The priority of the thread for prioritization.
        waypoints: A list of waypoints that define the thread's path.
        services: A dictionary mapping service names to their configurations.
        on_suspend_tasks: Tasks to execute when the thread is suspended.
        on_resume_tasks: Tasks to execute when the thread is resumed.
        on_cancel_tasks: Tasks to execute when the thread is canceled.
        on_failed_tasks: Tasks to execute when the thread fails.
        on_waypoint_start_tasks: Tasks to execute at the start of each waypoint.
        on_waypoint_end_tasks: Tasks to execute at the end of each waypoint.
        on_waypoints_start_tasks: Tasks to execute at the start of all waypoints.
        on_waypoints_end_tasks: Tasks to execute at the end of all waypoints.
        metadata: Additional metadata for the thread.
    """

    thread_id: str
    priority: TaskPriority
    waypoints: list[Waypoint] = field(default_factory=list)
    services: dict[str, ServiceConfig] = field(default_factory=dict)
    on_suspend_tasks: list[StepBase] = field(default_factory=list)
    on_resume_tasks: list[StepBase] = field(default_factory=list)
    on_cancel_tasks: list[StepBase] = field(default_factory=list)
    on_failed_tasks: list[StepBase] = field(default_factory=list)
    on_waypoint_start_tasks: list[StepBase] = field(default_factory=list)
    on_waypoint_end_tasks: list[StepBase] = field(default_factory=list)
    on_waypoints_start_tasks: list[StepBase] = field(default_factory=list)
    on_waypoints_end_tasks: list[StepBase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "priority", (
            self.priority.name if hasattr(self.priority, "name") else str(self.priority)
        )
        yield "waypoints", self.waypoints
        yield "services", list(self.services.keys())
        yield "on_suspend_tasks", self.on_suspend_tasks, []
        yield "on_resume_tasks", self.on_resume_tasks, []
        yield "on_cancel_tasks", self.on_cancel_tasks, []
        yield "on_failed_tasks", self.on_failed_tasks, []
        yield "on_waypoint_start_tasks", self.on_waypoint_start_tasks, []
        yield "on_waypoint_end_tasks", self.on_waypoint_end_tasks, []
        yield "on_waypoints_start_tasks", self.on_waypoints_start_tasks, []
        yield "on_waypoints_end_tasks", self.on_waypoints_end_tasks, []
        yield "metadata", self.metadata, {}
