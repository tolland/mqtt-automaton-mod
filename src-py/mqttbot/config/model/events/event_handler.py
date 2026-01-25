from __future__ import annotations

from pydantic import BaseModel, Field

from mqttbot.config.model.step.steps_discriminator import Step


class EventHandlerConfig(BaseModel):
    """Configuration for an event handler"""
    enabled: bool = True
    steps: list[Step] = Field(default_factory=list)
