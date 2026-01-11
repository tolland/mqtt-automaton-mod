from mqttbot import MessageData


def _get_current_position(self) -> tuple[float, float, float]:
    """Get current bot position"""
    return self._last_position or (0.0, 0.0, 0.0)

def _process_message(self, message_data: MessageData) -> None:
    """Process incoming message and update context"""
    with self._lock:
        self._last_event = {
            "service": message_data.service,
            "method": message_data.method,
            "params": message_data.params,
            "response": message_data.response,
        }

        # Update position if available
        if message_data.response:
            x = message_data.response.get("x")
            y = message_data.response.get("y")
            z = message_data.response.get("z")
            if (
                    isinstance(x, (int, float))
                    and isinstance(y, (int, float))
                    and isinstance(z, (int, float))
            ):
                self._last_position = (float(x), float(y), float(z))

    # Check for arrival events (baritone goto completion)
    self._check_arrival(message_data)

    # Update behavior engine context
    context_updates = {
        "current_position": self._last_position,
        "last_event": self._last_event,
    }

    # Check for emergency conditions
    if message_data.service == "events":
        event_type = (
            message_data.response.get("event") if message_data.response else None
        )
        if event_type == "pillager_attack":
            context_updates["pillager_attack"] = True
            context_updates["pillager_data"] = message_data.response
        elif event_type == "player_detected":
            context_updates["player_detected"] = True
            context_updates["player_data"] = message_data.response
        elif event_type == "low_health":
            context_updates["low_health"] = True
            context_updates["health_data"] = message_data.response

    # Check for inventory events
    elif message_data.service == "inventory":
        event_type = (
            message_data.response.get("event") if message_data.response else None
        )
        if event_type == "inventory_full":
            print(f"[mqtt] Inventory full event detected")
            context_updates["inventory_full"] = True
            context_updates["inventory_data"] = message_data.response

            # Queue inventory management behavior if not already queued/running
            for behavior in self.behavior_engine.behaviors:
                if behavior.name == "inventory_management":
                    # Check if already running or queued
                    if behavior.state.value == "running":
                        print(f"[mqtt] Inventory management already running, skipping queue")
                        break
                    if behavior in self.behavior_engine.behavior_queue:
                        print(f"[mqtt] Inventory management already queued, skipping")
                        break
                    # Only queue if idle and not in queue
                    if behavior.state.value == "idle":
                        print(f"[mqtt] Queuing inventory management behavior")
                        self.behavior_engine.queue_behavior(behavior)
                    break

    self.behavior_engine.update_context(context_updates)

def _check_arrival(self, message_data: MessageData) -> None:
    """Check if message indicates arrival at destination"""
    if not message_data.response:
        return

    # Check for baritone arrival indicators
    is_arrival = False

    # Check for success status with coordinates
    if message_data.response.get("status") == "success":
        if all(k in message_data.response for k in ("x", "y", "z")):
            is_arrival = True

    # Check for traditional arrival keys
    if message_data.response.get("type") in ("arrived", "reached"):
        is_arrival = True

    if is_arrival:
        print(f"[mqtt] Arrival detected: {message_data.response}")
        # Signal pattern engine
        if self.pattern_engine:
            self.pattern_engine.signal_arrival()
