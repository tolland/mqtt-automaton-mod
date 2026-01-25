from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from mqttbot.config.model.step.steps_discriminator import Step


class HookDefinition(BaseModel):
    steps: List[Step] = Field(default_factory=list)
