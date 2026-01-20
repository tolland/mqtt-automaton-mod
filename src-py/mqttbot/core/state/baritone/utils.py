

def dump_baritone_state(state):
    """Callback to dump baritone state to console"""
    print("\n[baritone] State Update:")
    print("=" * 60)

    if state.current_state:
        print(f"Phase: {state.current_state.phase}")
        print(f"Has Active Request: {state.current_state.has_active_request}")

    if state.history_stats:
        print("\nHistory Stats:")
        print(f"  Total Requests: {state.history_stats.total_requests}")
        print(f"  Successful: {state.history_stats.successful}")
        print(f"  Failed: {state.history_stats.failed}")
        print(f"  Stuck: {state.history_stats.stuck}")
        print(f"  Cancelled: {state.history_stats.cancelled}")
        print(f"  Avg Duration: {state.history_stats.avg_duration_seconds:.2f}s")

    if state.request_history:
        print(f"\nRecent Requests ({len(state.request_history)}):")
        for i, req in enumerate(state.request_history[-3:], 1):  # Show last 3
            print(f"  [{i}] {req.request_id[:8]}... - {req.phase}")
            if req.target_x is not None:
                print(f"      Target: ({req.target_x}, {req.target_y}, {req.target_z})")
            if req.failure_reason:
                print(f"      Failure: {req.failure_reason}")

    if state.current_request_timeline:
        print(f"\nCurrent Request Timeline ({len(state.current_request_timeline)} events):")
        for event in state.current_request_timeline[-5:]:  # Show last 5 events
            print(f"  {event}")

    print("=" * 60)
    print()
