from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Any

import rich
from rich.repr import rich_repr

from mqttbot.config.model.step.step_base import StepBase


class PatternStep(StepBase):
    type: Literal["pattern"] = "pattern"
    coords: Coords

    @classmethod
    def from_string(cls, step_str: str) -> "PatternStep":
        tokens = step_str.split()
        if len(tokens) != 3:
            raise ValueError(f"Invalid pattern step string: {step_str}")
        x = CoordAxis.create(tokens[0])
        y = CoordAxis.create(tokens[1])
        z = CoordAxis.create(tokens[2])
        return cls(type="pattern", coords=Coords(x, y, z))

    @property
    def relative_coords(self) -> tuple[float, float, float]:
        """Return the raw numeric offsets for the step axes (useful for tests).

        Returns offsets as integers for x,y,z (for relative tokens these are the offsets, for absolute tokens they are the absolute values).
        """
        return self.coords.x.value, self.coords.y.value, self.coords.z.value

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
        return data


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

    def __rich_repr__(self) -> rich.repr.Result:
        yield "frame", self.frame
        yield "value", self.value


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

    def __rich_repr__(self) -> rich.repr.Result:
        yield "x", f"{self.x.frame[0:3]}[{self.x.value}]"
        yield "y", f"{self.y.frame[0:3]}[{self.y.value}]"
        yield "z", f"{self.z.frame[0:3]}[{self.z.value}]"
