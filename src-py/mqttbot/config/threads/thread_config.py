from dataclasses import dataclass, field
from typing import Any

from mqttbot.core.tasks.task_priority import TaskPriority
from rich.repr import rich_repr

from mqttbot.core.service_config import ServiceConfig
from mqttbot.core.waypoint import Waypoint


@rich_repr
@dataclass
class ThreadConfig:
    """Configuration for a TaskThread"""

    thread_id: str
    priority: TaskPriority
    waypoints: list[Waypoint] = field(default_factory=list)
    services: dict[str, ServiceConfig] = field(default_factory=dict)
    on_suspend_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_resume_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_waypoint_start_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_waypoint_end_tasks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "priority", (
            self.priority.name if hasattr(self.priority, "name") else str(self.priority)
        )
        yield "waypoints", len(self.waypoints)
        yield "services", list(self.services.keys())
        yield "on_suspend_tasks", len(self.on_suspend_tasks)
        yield "on_resume_tasks", len(self.on_resume_tasks)
        if self.metadata:
            yield "metadata", self.metadata
