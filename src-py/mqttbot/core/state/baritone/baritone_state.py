from dataclasses import dataclass, field
from typing import Optional


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
    correlation_id: Optional[str] = None
    target_x: Optional[int] = None
    target_y: Optional[int] = None
    target_z: Optional[int] = None
    phase: str = "IDLE"
    start_time: Optional[str] = None
    elapsed_seconds: float = 0.0
    completion_time: Optional[str] = None
    duration_seconds: float = 0.0
    failure_reason: Optional[str] = None
    last_x: Optional[int] = None
    last_y: Optional[int] = None
    last_z: Optional[int] = None
    timeline: list[str] = field(default_factory=list)


@dataclass
class BaritoneState:
    """Complete baritone state including current state, history, and statistics"""
    state_type: str = "baritoneState"
    current_state: Optional[PathingStateInfo] = None
    request_history: list[PathingRequest] = field(default_factory=list)
    history_stats: Optional[HistoryStats] = None
    current_request_timeline: list[str] = field(default_factory=list)
