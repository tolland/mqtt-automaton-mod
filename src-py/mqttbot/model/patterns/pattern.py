from dataclasses import dataclass
from dataclasses import field
from typing import Any, Iterator, Optional
from typing import Literal

import rich
from rich.repr import rich_repr

from mqttbot.model.patterns.step import StepBase


@dataclass(frozen=True)
class CoordAxis:
    frame: Literal["absolute", "relative"]
    value: float = 0

    @staticmethod
    def create(token: str) -> "CoordAxis":
        if token.startswith("~"):
            offset = int(token[1:]) if token[1:] else 0
            return CoordAxis("relative", offset)
        return CoordAxis("absolute", int(token))

@dataclass(frozen=True)
class Coords:
    x: CoordAxis
    y: CoordAxis
    z: CoordAxis

    def resolve(self, origin: tuple[float, float, float]) -> tuple[float, float, float]:
        ox, oy, oz = origin

        def axis(a: CoordAxis, o: float) -> float:
            if a.frame == "absolute":
                return a.value
            return o + a.value

        return (
            axis(self.x, ox),
            axis(self.y, oy),
            axis(self.z, oz),
        )

@dataclass
class PatternStep(StepBase):
    """A single step in a pattern"""

    type: str
    coords: Coords
    dwell_seconds: Optional[float] = None

    @classmethod
    def from_string(cls, step_str: str) -> "PatternStep":
        tokens = step_str.split()
        if len(tokens) != 3:
            raise ValueError(f"Invalid pattern step string: {step_str}")
        x = CoordAxis.create(tokens[0])
        y = CoordAxis.create(tokens[1])
        z = CoordAxis.create(tokens[2])
        return cls(type="goto", coords=Coords(x, y, z))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "params": {
                "target": {
                    "x": self.coords.x.value,
                    "y": self.coords.y.value,
                    "z": self.coords.z.value,
                    "frame": self.coords.x.frame,  # assuming all axes have same frame
                }
            },
        }
        if self.dwell_seconds is not None:
            data["params"]["dwell_seconds"] = self.dwell_seconds
        return data


@rich_repr
@dataclass
class Pattern:
    """Configuration for a Patterns Section"""

    pattern_id: str
    steps: list[StepBase]
    on_pattern_start_tasks: list[StepBase] = field(default_factory=list)
    on_pattern_end_tasks: list[StepBase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __iter__(self) -> Iterator[Any]:
        yield from self.on_pattern_start_tasks
        yield from self.steps
        yield from self.on_pattern_end_tasks

    def __rich_repr__(self) -> rich.repr.Result:
        yield "pattern_id", self.pattern_id
        if self.on_pattern_start_tasks:
            yield "on_pattern_start_tasks", self.on_pattern_start_tasks
        yield "steps", self.steps
        if self.on_pattern_end_tasks:
            yield "on_pattern_end_tasks", self.on_pattern_end_tasks
        if self.metadata:
            yield "metadata", self.metadata
