from dataclasses import dataclass, field
from typing import Any

from mqttbot.config.service_method_config import ServiceMethodConfig


@dataclass
class ServiceConfig:
    """Configuration for a service (baritone, wurst, sleep, etc)"""

    name: str
    timeout: int = 60
    methods: dict[str, ServiceMethodConfig] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
