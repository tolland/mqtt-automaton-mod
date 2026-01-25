from __future__ import annotations

from typing import List, Any

from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    """
    Represents a waypoint in a three-dimensional space.

    This class is used to define a waypoint with coordinates in 3D space, associated
    patterns, and additional metadata. It provides functionality to convert the waypoint
    into a dictionary for JSON serialization and custom rich representation formatting.

    :ivar x: X-coordinate of the waypoint.
    :ivar y: Y-coordinate of the waypoint.
    :ivar z: Z-coordinate of the waypoint.
    :ivar patterns: A list of string patterns associated with the waypoint.
    :ivar metadata: A dictionary containing additional metadata for the waypoint.
    """
    x: float
    y: float
    z: float
    patterns: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

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

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert the Waypoint to a tuple of coordinates (x, y, z)"""
        return self.x, self.y, self.z

    def __rich_repr__(self) -> "rich.repr.Result":
        yield "x", self.x
        yield "y", self.y
        yield "z", self.z
        if self.patterns:
            yield "patterns", self.patterns
        if self.metadata:
            yield "metadata", self.metadata
