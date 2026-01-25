from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mqttbot.config.model.pattern.waypoint import Waypoint
from mqttbot.config.model.thread.hooks_collection import HooksCollection
from mqttbot.core.protocol.task_priority import ThreadPriority


class ThreadDefinition(BaseModel):
    model_config = ConfigDict(use_enum_values=False, populate_by_name=True)
    thread_id: str | None = Field(default=None)
    priority: ThreadPriority = ThreadPriority.NORMAL

    hooks: HooksCollection = Field(default=None)

    waypoints: List[Waypoint] = Field(default_factory=list)

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> ThreadPriority:
        if isinstance(v, str):
            try:
                return ThreadPriority[v]
            except KeyError:
                # Fallback or let pydantic handle it
                pass
        return v

    # def __rich_repr__(self) -> "rich.repr.Result":
    #     yield "thread_id", self.thread_id
    #     yield "priority", self.priority.name
    #     yield from self.hooks
