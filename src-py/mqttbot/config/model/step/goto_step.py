from __future__ import annotations

from typing import Literal

from mqttbot.config.model.step.step_base import StepBase


class GotoStep(StepBase):
    type: Literal["goto"] = "goto"
    raw_coords: str  # e.g., "~ ~ ~-5"
    x: float | None = None
    y: float | None = None
    z: float | None = None
