from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from mqttbot.config.model.thread.hook_definition import HookDefinition


class HooksCollection(BaseModel):
    on_suspend: HookDefinition = Field(default_factory=HookDefinition)
    on_resume: HookDefinition = Field(default_factory=HookDefinition)
    on_cancel: HookDefinition = Field(default_factory=HookDefinition)
    on_failed: HookDefinition = Field(default_factory=HookDefinition)
    on_waypoints_start: HookDefinition = Field(default_factory=HookDefinition)
    on_waypoints_end: HookDefinition = Field(default_factory=HookDefinition)
    on_waypoint_start: HookDefinition = Field(default_factory=HookDefinition)
    on_waypoint_end: HookDefinition = Field(default_factory=HookDefinition)
    on_pattern_start: HookDefinition = Field(default_factory=HookDefinition)
    on_pattern_end: HookDefinition = Field(default_factory=HookDefinition)
    on_patterns_end: HookDefinition = Field(default_factory=HookDefinition)
    on_patterns_start: HookDefinition = Field(default_factory=HookDefinition)


    def __rich_repr__(self):
        for name, hook in self.__dict__.items():
            # suppress empty hooks
            if getattr(hook, "steps", None):
                if len(hook.steps) > 0:
                    yield name, hook
