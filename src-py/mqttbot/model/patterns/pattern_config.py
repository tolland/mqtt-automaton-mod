from dataclasses import dataclass, field
from typing import Any

from rich.repr import rich_repr

from mqttbot.model.patterns.pattern_step import PatternStep
from mqttbot.model.tasks.task_step_config import TaskStepConfig


@rich_repr
@dataclass
class PatternConfig:
    """Configuration for a Patterns Section"""

    pattern_id: str
    steps: list[PatternStep|TaskStepConfig]
    on_pattern_start_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_pattern_end_tasks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __rich_repr__(self):
        yield "thread_id", self.thread_id
        yield "priority", (
            self.priority.name if hasattr(self.priority, "name") else str(self.priority)
        )
        yield "steps", len(self.steps)
        yield "services", list(self.services.keys())
        yield "on_suspend_tasks", len(self.on_suspend_tasks)
        yield "on_resume_tasks", len(self.on_resume_tasks)
        if self.metadata:
            yield "metadata", self.metadata
