from dataclasses import dataclass, field
from typing import Any


@dataclass
class Settings:
    """Configuration settings for the MQTT bot client."""

    broker: str
    port: int
    client_id: str
    expected_player_name: str
    topic_base: str
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    cmd_tpl_name: str
    cmd_tpl_xyz: str
    log_level: str = "INFO"
    log_file_level: str = "DEBUG"
    log_dir: str = "logs"
    log_mqtt_to_file: bool = True
    log_package_levels: dict[str, str] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)
    events: dict[str, Any] = field(default_factory=dict)
