from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from mqttbot.config.model.thread.thread_definition import ThreadDefinition


class ThreadConfig(BaseModel):
    threads: List[ThreadDefinition] = Field(default_factory=list)

    def __rich_repr__(self) -> "rich.repr.Result":
        yield self.threads
