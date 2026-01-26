from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, field_validator, Field

from mqttbot.config.model.pattern.coords import Coords
from mqttbot.config.model.pattern.coords_axis import CoordAxis
from mqttbot.config.model.step.step_base import StepBase


class CollectParams(BaseModel):
    block: str
    range: int = 5
    origin: Coords = Field(default_factory=lambda: Coords(x=CoordAxis(), y=CoordAxis(), z=CoordAxis()))

    @field_validator("origin", mode="before")
    @classmethod
    def validate_origin(cls, v: dict | str | Coords) -> Coords:
        if isinstance(v, Coords):
            return v

        if isinstance(v, str):
            return Coords.from_string(v)

        if isinstance(v, dict):
            return Coords(**v)

        raise ValueError(f"Invalid origin format: {v}")


class CollectStep(StepBase):
    type: Literal["collect"] = "collect"
    params: CollectParams

    @property
    def relative_coords(self) -> tuple[float, float, float]:
        """Return the raw numeric offsets for the step axes (useful for tests).

        Returns offsets as integers for x,y,z (for relative tokens these are the offsets, for absolute tokens they are the absolute values).
        """
        return self.coords.x.value, self.coords.y.value, self.coords.z.value

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
