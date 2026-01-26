from __future__ import annotations

from typing import Literal, Any

from mqttbot.config.model.pattern.coords_axis import CoordAxis
from mqttbot.config.model.pattern.coords import Coords
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
        return cls(type="pattern", coords=Coords(x=x, y=y, z=z), metadata={})

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
            "metadata": self.metadata.model_dump() if self.metadata else {},
        }
        return data
