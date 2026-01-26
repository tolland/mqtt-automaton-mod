from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mqttbot.config.model.pattern.pattern import Pattern
from mqttbot.config.model.step.steps_discriminator import Step


class PatternConfig(BaseModel):
    steps: list[Step]


class PatternsConfig(BaseModel):
    patterns: list[Pattern] = Field(default_factory=list)
    on_pattern_start_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_start")
    on_pattern_end_tasks: list[Step] = Field(default_factory=list, alias="on_pattern_end")
    on_patterns_start_tasks: list[Step] = Field(default_factory=list, alias="on_patterns_start")
    on_patterns_end_tasks: list[Step] = Field(default_factory=list, alias="on_patterns_end")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)

    def get(self, pattern_id: str) -> Pattern | None:
        """Get a Pattern by its ID."""
        return next(
            (p for p in self.patterns
             if p.pattern_id == pattern_id),
            None
        )

    # @model_validator(mode="before")
    # @classmethod
    # def root_validator(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         # If the dict contains any of the known pattern fields, it's already a PatternsConfig object
    #         # otherwise if it's a dict where values look like patterns, we wrap it.
    #         known_keys = {"patterns", "on_pattern_start", "on_pattern_end", "on_patterns_start", "on_patterns_end",
    #                       "on_failed", "metadata"}
    #         if not any(k in data for k in known_keys):
    #             # Check if it looks like a dict of patterns
    #             if any(isinstance(v, dict) and "steps" in v for v in data.values()):
    #                 data = {"patterns": data}
    #
    #         # If 'patterns' is a dict, we need to convert it to a list of Pattern objects/dicts
    #         if "patterns" in data and isinstance(data["patterns"], dict):
    #             data = dict(data)
    #             patterns_dict = data["patterns"]
    #             normalized = []
    #             for pattern_id, pattern_data in patterns_dict.items():
    #                 if isinstance(pattern_data, dict):
    #                     d = dict(pattern_data)
    #                     d.setdefault("pattern_id", pattern_id)
    #                     normalized.append(d)
    #                 else:
    #                     normalized.append(pattern_data)
    #             data["patterns"] = normalized
    #     return data
