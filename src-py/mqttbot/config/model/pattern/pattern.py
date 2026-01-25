from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict

from mqttbot.config.model.pattern.pattern_step import PatternStep
from mqttbot.config.model.step.steps_discriminator import Step


class Pattern(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    pattern_id: str | None = None
    steps: list[Step]
    # Hooks
    on_pattern_start_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_start")
    on_pattern_end_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_end")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("steps", mode="before")
    def normalize_steps(cls, v):
        """Convert raw strings like '~ ~ ~5' into PatternStep automatically."""
        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append(PatternStep.from_string(item))
            else:
                normalized.append(item)
        return normalized
