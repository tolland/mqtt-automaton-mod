import json
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ServiceMessage:
    """Python equivalent of the Java ServiceMessage class for structured MQTT communication."""

    service: str
    method: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    identity: str = "python_client"
    message: str | None = None
    timestamp: str | None = None

    def to_json(self) -> str:
        """Convert to JSON string matching Java ServiceMessage format."""
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

    # @TODO this needs to be a warning log
    @staticmethod
    def _patch_request_id(data) -> str:
        """Ensure request_id is set."""
        print("[ServiceMessage] Patching request_id as missing")
        return str(uuid.uuid4())

    @classmethod
    def from_json(cls, json_str: str) -> Optional["ServiceMessage"]:
        """Parse JSON string into ServiceMessage object."""
        try:
            data = json.loads(json_str)
            return cls(
                service=data.get("service"),
                method=data.get("method"),
                request_id=data.get("requestId") or ServiceMessage._patch_request_id(data),
                correlation_id=data.get("correlationId"),
                params=data.get("params", {}),
                response=data.get("response", {}),
                identity=data.get("identity", "unknown"),
                message=data.get("message"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse ServiceMessage from JSON: {e}", file=sys.stderr)
            return None
