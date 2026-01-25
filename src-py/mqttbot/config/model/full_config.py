from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from mqttbot.config.model.events.events_config import EventsConfig
from mqttbot.config.model.pattern.pattern_config import PatternsConfig
from mqttbot.config.model.thread.threads_config import ThreadConfig


class FullConfig(BaseModel):
    thread_config: ThreadConfig = Field(default_factory=ThreadConfig)
    pattern_config: PatternsConfig = Field(default_factory=PatternsConfig)
    event_handlers: EventsConfig = Field(default_factory=lambda: EventsConfig(root={}))

    def __rich_repr__(self) -> "rich.repr.Result":
        yield self.thread_config
        yield "pattern_config", self.pattern_config
        yield "event_handlers", self.event_handlers


def load_full_config(path: str | Path) -> FullConfig:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return FullConfig.model_validate(data)
