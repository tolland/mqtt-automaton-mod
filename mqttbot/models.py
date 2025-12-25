"""Data models for MQTT bot communication."""

import json
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MessageData:
    """Python equivalent of the Java MessageData class for structured MQTT communication."""

    service: str
    method: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    identity: str = "python_client"
    message: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string matching Java MessageData format."""
        data = {
            "service": self.service,
            "method": self.method,
            "requestId": self.request_id,
            "correlationId": self.correlation_id,
            "params": self.params,
            "response": self.response,
            "identity": self.identity,
            "message": self.message,
        }
        # Remove None values to keep JSON clean
        return json.dumps({k: v for k, v in data.items() if v is not None})

    @classmethod
    def from_json(cls, json_str: str) -> Optional["MessageData"]:
        """Parse JSON string into MessageData object."""
        try:
            data = json.loads(json_str)
            return cls(
                service=data.get("service"),
                method=data.get("method"),
                request_id=data.get("requestId", str(uuid.uuid4())),
                correlation_id=data.get("correlationId"),
                params=data.get("params", {}),
                response=data.get("response", {}),
                identity=data.get("identity", "unknown"),
                message=data.get("message"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse MessageData from JSON: {e}", file=sys.stderr)
            return None


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
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    cmd_tpl_name: str
    cmd_tpl_xyz: str
    services: dict[str, Any] = field(default_factory=dict)
    events: dict[str, Any] = field(default_factory=dict)
