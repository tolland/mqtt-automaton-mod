from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass
class PatternStepConfig:
    name: str
    enabled: bool = True
    retries: int = 0
    timeout: Optional[float] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Placeholder: return a dict representation. Customize serialization if needed."""
        return asdict(self)

    def __repr__(self) -> str:
        """Rich, human-friendly representation (falls back to a simple repr on error)."""
        try:
            import json
            return json.dumps(self.to_dict(), indent=2, sort_keys=True)
        except Exception:
            return (
                f"PatternStepConfig(name={self.name!r}, enabled={self.enabled!r}, "
                f"retries={self.retries!r}, timeout={self.timeout!r}, params={self.params!r})"
            )
