from typing import Any

from mqttbot import MessageData
from mqttbot.core.state.baritone.baritone_state import (
    BaritoneState,
    HistoryStats,
    PathingRequest,
    PathingStateInfo,
)
from mqttbot.core.state.state_module import StateModule


class BaritoneModule(StateModule[BaritoneState]):
    def __init__(self):
        self._state = BaritoneState()

    def handle_event(self, event: MessageData) -> None:
        """
        Handle incoming baritone state messages.
        
        Args:
            event: MessageData with service="baritone" and method="state"
        """
        if event.service == "baritone" and event.method == "state":
            response = event.response or {}
            
            # Parse current state
            current_state_data = response.get("currentState", {})
            current_state = PathingStateInfo(
                state_type=current_state_data.get("stateType", "pathingState"),
                has_active_request=current_state_data.get("hasActiveRequest", False),
                phase=current_state_data.get("phase", "IDLE"),
            )
            
            # Parse history stats
            history_stats_data = response.get("historyStats", {})
            history_stats = HistoryStats(
                total_requests=history_stats_data.get("totalRequests", 0),
                successful=history_stats_data.get("successful", 0),
                failed=history_stats_data.get("failed", 0),
                stuck=history_stats_data.get("stuck", 0),
                cancelled=history_stats_data.get("cancelled", 0),
                avg_duration_seconds=history_stats_data.get("avgDurationSeconds", 0.0),
            )
            
            # Parse request history
            request_history_data = response.get("requestHistory", [])
            request_history = []
            for req_data in request_history_data:
                req = PathingRequest(
                    request_id=req_data.get("requestId", ""),
                    correlation_id=req_data.get("correlationId"),
                    target_x=req_data.get("targetX"),
                    target_y=req_data.get("targetY"),
                    target_z=req_data.get("targetZ"),
                    phase=req_data.get("phase", "IDLE"),
                    start_time=req_data.get("startTime"),
                    elapsed_seconds=req_data.get("elapsedSeconds", 0.0),
                    completion_time=req_data.get("completionTime"),
                    duration_seconds=req_data.get("durationSeconds", 0.0),
                    failure_reason=req_data.get("failureReason"),
                    last_x=req_data.get("lastX"),
                    last_y=req_data.get("lastY"),
                    last_z=req_data.get("lastZ"),
                    timeline=req_data.get("timeline", []),
                )
                request_history.append(req)
            
            # Parse current request timeline (if active)
            current_request_timeline = response.get("currentRequestTimeline", [])
            
            # Update state
            self._state = BaritoneState(
                state_type=response.get("stateType", "baritoneState"),
                current_state=current_state,
                request_history=request_history,
                history_stats=history_stats,
                current_request_timeline=current_request_timeline,
            )

    def get_state(self) -> BaritoneState:
        return self._state

    def reset_state(self) -> None:
        self._state = BaritoneState()
