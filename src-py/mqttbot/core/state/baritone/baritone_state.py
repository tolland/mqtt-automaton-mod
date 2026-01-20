from dataclasses import dataclass, field


@dataclass
class PathingStateInfo:
    """Current pathing state information"""
    state_type: str = "pathingState"
    has_active_request: bool = False
    phase: str = "IDLE"


@dataclass
class HistoryStats:
    """Statistics about request history"""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    stuck: int = 0
    cancelled: int = 0
    avg_duration_seconds: float = 0.0


@dataclass
class PathingRequest:
    """A single pathing request from history"""
    request_id: str = ""
    correlation_id: str | None = None
    target_x: int | None = None
    target_y: int | None = None
    target_z: int | None = None
    phase: str = "IDLE"
    start_time: str | None = None
    elapsed_seconds: float = 0.0
    completion_time: str | None = None
    duration_seconds: float = 0.0
    failure_reason: str | None = None
    last_x: int | None = None
    last_y: int | None = None
    last_z: int | None = None
    timeline: list[str] = field(default_factory=list)


@dataclass
class BaritoneState:
    """Complete baritone state including current state, history, and statistics"""
    state_type: str = "baritoneState"
    current_state: PathingStateInfo | None = None
    request_history: list[PathingRequest] = field(default_factory=list)
    history_stats: HistoryStats | None = None
    current_request_timeline: list[str] = field(default_factory=list)
