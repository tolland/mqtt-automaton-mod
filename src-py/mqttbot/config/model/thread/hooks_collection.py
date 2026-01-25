from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field

from mqttbot.config.model.thread.hook_definition import HookDefinition


class HooksCollection(BaseModel):
    on_suspend: HookDefinition = Field(default_factory=HookDefinition)
    on_resume: HookDefinition = Field(default_factory=HookDefinition)
    on_cancel: HookDefinition = Field(default_factory=HookDefinition)
    on_failed: HookDefinition = Field(default_factory=HookDefinition)
