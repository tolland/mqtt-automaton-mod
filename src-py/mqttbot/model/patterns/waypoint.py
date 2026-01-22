from dataclasses import dataclass, field
from typing import Any

from rich.repr import rich_repr


@rich_repr
@dataclass
class Waypoint:
    """A waypoint definition"""

    x: int
    y: int
    z: int
    patterns: list[str] = field(default_factory=list)  # Pattern names to run
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the Waypoint to a JSON-serializable dictionary"""
        data: dict[str, Any] = {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
        if self.patterns:
            data["patterns"] = self.patterns
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def __rich_repr__(self):
        yield "x", self.x
        yield "y", self.y
        yield "z", self.z
        if self.patterns:
            yield "patterns", self.patterns
        if self.metadata:
            yield "metadata", self.metadata
