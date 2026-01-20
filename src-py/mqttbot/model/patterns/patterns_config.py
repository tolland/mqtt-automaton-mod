from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from rich.repr import rich_repr

from mqttbot.model.patterns.pattern import Pattern


@rich_repr
@dataclass
class PatternsConfig:
    """Configuration for a Patterns Section"""

    patterns: list[Pattern]
    on_patterns_start_tasks: list[dict[str, Any]] = field(default_factory=list)
    on_patterns_end_tasks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __contains__(self, item: str | Pattern) -> bool:
        if isinstance(item, Pattern):
            return item in self.patterns
        return any(getattr(p, "pattern_id", None) == item for p in self.patterns)

    def __iter__(self) -> Iterator[Pattern]:
        return iter(self.patterns)

    def __len__(self) -> int:
        return len(self.patterns)

    def __getitem__(self, key):
        return next((x for x in self.patterns if x.pattern_id == key), None)

    def __repr__(self) -> str:
        """Return a string representation of PatternsConfig."""
        parts = [
            f"patterns={len(self.patterns)}",
            f"on_patterns_start_tasks={len(self.on_patterns_start_tasks)}",
            f"on_patterns_end_tasks={len(self.on_patterns_end_tasks)}",
        ]
        if self.metadata:
            parts.append(f"metadata={self.metadata}")
        return f"PatternsConfig({', '.join(parts)})"

    def __rich_repr__(self):
        if self.on_patterns_start_tasks:
            yield "on_patterns_start_tasks", self.on_patterns_start_tasks
        yield "patterns", self.patterns
        if self.on_patterns_end_tasks:
            yield "on_patterns_end_tasks", self.on_patterns_end_tasks
        if self.metadata:
            yield "metadata", self.metadata
