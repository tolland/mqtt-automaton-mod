from __future__ import annotations

import rich
from pydantic import BaseModel

from mqttbot.config.model.pattern.coords_axis import CoordAxis


class Coords(BaseModel):
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

    @classmethod
    def from_string(cls, step_str: str) -> "Coords":
        tokens = step_str.split()
        if len(tokens) != 3:
            raise ValueError(f"Invalid pattern step string: {step_str}")
        x = CoordAxis.create(tokens[0])
        y = CoordAxis.create(tokens[1])
        z = CoordAxis.create(tokens[2])
        return cls(x=x, y=y, z=z)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "x", f"{self.x.frame[0:3]}[{self.x.value}]"
        yield "y", f"{self.y.frame[0:3]}[{self.y.value}]"
        yield "z", f"{self.z.frame[0:3]}[{self.z.value}]"
