from dataclasses import dataclass, field
from typing import Any


@dataclass
class Settings:
    """Configuration settings for the MQTT bot client."""

    broker: str
    port: int
    client_id: str
    expected_player_name: str
    topic_cmd: str
    topic_reply: str
    topic_pos: str
    topic_state: str
    topic_inventory: str
    topic_events: str
    topic_heartbeats: str
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    cmd_tpl_name: str
    cmd_tpl_xyz: str
    log_level: str = "INFO"
    services: dict[str, Any] = field(default_factory=dict)
    events: dict[str, Any] = field(default_factory=dict)
