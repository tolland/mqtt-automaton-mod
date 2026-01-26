from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import rich
from pydantic import BaseModel


class CoordAxis(BaseModel):
    frame: Literal["absolute", "relative"] = "relative"
    value: float = 0

    @staticmethod
    def create(token: str) -> "CoordAxis":
        if token.startswith("~"):
            offset = int(token[1:]) if token[1:] else 0
            return CoordAxis(frame="relative", value=offset)
        return CoordAxis(frame="absolute", value=int(token))

    def __rich_repr__(self) -> rich.repr.Result:
        yield "frame", self.frame
        yield "value", self.value
