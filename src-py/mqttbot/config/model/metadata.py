from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class Metadata(BaseModel):
    fail_me: bool | None = None
    note: str | None = None
    tags: list[str] | None = None
    pattern: Any | None = None

    model_config = ConfigDict(extra="allow")

class WithMetadata(BaseModel):
    metadata: Optional[Metadata] = None

    model_config = ConfigDict(
        extra="forbid",

    )
