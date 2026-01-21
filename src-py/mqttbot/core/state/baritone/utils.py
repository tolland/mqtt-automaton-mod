from loguru import logger


def dump_baritone_state(state):
    """Callback to dump baritone state to log (debug level)"""
    lines = ["\nBaritone State Update:", "=" * 60]

    if state.current_state:
        lines.append(f"Phase: {state.current_state.phase}")
        lines.append(f"Has Active Request: {state.current_state.has_active_request}")

    if state.history_stats:
        lines.append("\nHistory Stats:")
        lines.append(f"  Total Requests: {state.history_stats.total_requests}")
        lines.append(f"  Successful: {state.history_stats.successful}")
        lines.append(f"  Failed: {state.history_stats.failed}")
        lines.append(f"  Stuck: {state.history_stats.stuck}")
        lines.append(f"  Cancelled: {state.history_stats.cancelled}")
        lines.append(f"  Avg Duration: {state.history_stats.avg_duration_seconds:.2f}s")

    if state.request_history:
        lines.append(f"\nRecent Requests ({len(state.request_history)}):")
        for i, req in enumerate(state.request_history[-3:], 1):  # Show last 3
            lines.append(f"  [{i}] {req.request_id[:8]}... - {req.phase}")
            if req.target_x is not None:
                lines.append(f"      Target: ({req.target_x}, {req.target_y}, {req.target_z})")
            if req.failure_reason:
                lines.append(f"      Failure: {req.failure_reason}")

    if state.current_request_timeline:
        lines.append(f"\nCurrent Request Timeline ({len(state.current_request_timeline)} events):")
        for event in state.current_request_timeline[-5:]:  # Show last 5 events
            lines.append(f"  {event}")

    lines.append("=" * 60)

    logger.debug("\n".join(lines))
