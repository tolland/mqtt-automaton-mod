from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mqttbot.config.model.step.step_base import StepBase


class GotoStep(StepBase):
    type: Literal["goto"] = "goto"
    params: GotoParams = Field(description="Goto step parameters")

class GotoParams(BaseModel):
    target: GotoCoords = Field(description="Target coordinates for the goto step")

class GotoCoords(BaseModel):
    x: float
    y: float
    z: float
