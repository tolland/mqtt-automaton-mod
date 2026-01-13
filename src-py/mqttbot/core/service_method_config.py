from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceMethodConfig:
    """Configuration for a specific service method"""

    name: str
    timeout: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)
