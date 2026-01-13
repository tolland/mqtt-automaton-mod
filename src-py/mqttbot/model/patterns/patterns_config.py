from dataclasses import dataclass, field
from typing import Any

from rich.repr import rich_repr

from mqttbot.model.patterns.pattern_config import PatternConfig


@rich_repr
@dataclass
class PatternsConfig:
    """Configuration for a Patterns Section"""

    patterns: list[PatternConfig]
    on_patterns_start_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_patterns_end_tasks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.patterns)

    def __rich_repr__(self):
        yield "patterns", len(self.patterns)
        yield "on_patterns_start_tasks", len(self.on_patterns_start_tasks)
        yield "on_patterns_end_tasks", len(self.on_patterns_end_tasks)
        if self.metadata:
            yield "metadata", self.metadata
