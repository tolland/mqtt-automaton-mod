from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict

from mqttbot.config.model.metadata import WithMetadata
from mqttbot.config.model.step.pattern_step import PatternStep
from mqttbot.config.model.step.steps_discriminator import Step
from mqttbot.config.model.thread.hooks_collection import HooksCollection


class Pattern(WithMetadata):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="allow")

    pattern_id: str | None = None
    steps: list[Step]
    # Hooks
    hooks: HooksCollection = Field(default_factory=HooksCollection)
    on_pattern_start_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_start")
    on_pattern_end_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_end")

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

    # def __rich_repr__(self) -> "rich.repr.Result":
    #     yield "pattern_id", self.pattern_id
    #     yield "steps", f"[{len(self.steps)} steps]"
    #     yield "hooks", self.hooks
