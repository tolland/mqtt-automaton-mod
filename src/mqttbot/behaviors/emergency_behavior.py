from typing import Dict, Any

from mqttbot.behaviors.base_behavior import BaseBehavior

"""
Emergency behavior for handling urgent situations like pillager attacks
"""


class EmergencyBehavior(BaseBehavior):
    """
    High-priority behavior for emergency situations.

    This behavior handles:
    - Pillager attacks
    - Player detection
    - Low health situations
    - Other urgent threats
    """

    def __init__(self, name: str = "emergency", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.priority = 1  # Highest priority
        self.interruptible = False  # Cannot be interrupted
        self.emergency_type = None
        self.emergency_data = None

    def can_start(self, context: Dict[str, Any]) -> bool:
        """Check if emergency behavior should start"""
        # Check for various emergency conditions
        if context.get("pillager_attack", False):
            self.emergency_type = "pillager_attack"
            self.emergency_data = context.get("pillager_data", {})
            return True

        if context.get("player_detected", False):
            self.emergency_type = "player_detected"
            self.emergency_data = context.get("player_data", {})
            return True

        if context.get("low_health", False):
            self.emergency_type = "low_health"
            self.emergency_data = context.get("health_data", {})
            return True

        return False

    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute emergency response"""
        print(f"[emergency] Executing emergency response for: {self.emergency_type}")

        try:
            if self.emergency_type == "pillager_attack":
                return self._handle_pillager_attack(context)
            elif self.emergency_type == "player_detected":
                return self._handle_player_detection(context)
            elif self.emergency_type == "low_health":
                return self._handle_low_health(context)
            else:
                print(f"[emergency] Unknown emergency type: {self.emergency_type}")
                return False

        except Exception as e:
            print(f"[emergency] Error during emergency response: {e}")
            return False

    def _handle_pillager_attack(self, context: Dict[str, Any]) -> bool:
        """Handle pillager attack emergency"""
        print(f"[emergency] Handling pillager attack")

        # 1. Immediately stop all farming activities
        self._stop_farming_activities()

        # 2. Try to escape to a safe location
        safe_location = self._find_safe_location(context)
        if safe_location:
            print(f"[emergency] Escaping to safe location: {safe_location}")
            if not self._escape_to_location(safe_location):
                print(f"[emergency] Failed to escape to safe location")
                return False

        # 3. Wait for threat to pass
        print(f"[emergency] Waiting for threat to pass...")
        # In real implementation, this would monitor for threat clearance

        # 4. Return to farming after threat is cleared
        print(f"[emergency] Threat cleared, resuming normal operations")
        return True

    def _handle_player_detection(self, context: Dict[str, Any]) -> bool:
        """Handle player detection emergency"""
        player_data = self.emergency_data
        player_name = player_data.get("name", "unknown")
        print(f"[emergency] Player detected: {player_name}")

        # 1. Stop farming activities
        self._stop_farming_activities()

        # 2. Move to a discrete location
        discrete_location = self._find_discrete_location(context)
        if discrete_location:
            print(f"[emergency] Moving to discrete location: {discrete_location}")
            self._escape_to_location(discrete_location)

        # 3. Wait for player to leave
        print(f"[emergency] Waiting for player to leave...")
        # In real implementation, this would monitor player proximity

        return True

    def _handle_low_health(self, context: Dict[str, Any]) -> bool:
        """Handle low health emergency"""
        health_data = self.emergency_data
        current_health = health_data.get("health", 0)
        print(f"[emergency] Low health detected: {current_health}")

        # 1. Stop all activities
        self._stop_farming_activities()

        # 2. Try to eat food
        self._attempt_healing()

        # 3. Move to safe location if still low health
        if current_health < 10:  # Still critically low
            safe_location = self._find_safe_location(context)
            if safe_location:
                print(f"[emergency] Moving to safe location due to low health")
                self._escape_to_location(safe_location)

        return True

    def _stop_farming_activities(self) -> None:
        """Stop all farming activities"""
        print(f"[emergency] Stopping all farming activities")

        stop_cmd = {
            "service": "wurst",
            "method": "command",
            "params": {"command": "t", "args": ["autofarm", "off"]},
        }

        # In real implementation, this would send the actual command
        print(f"[emergency] Sent stop farming command")

    def _find_safe_location(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find a safe location to escape to"""
        # Look for configured safe locations
        safe_locations = context.get("safe_locations", [])
        if safe_locations:
            return safe_locations[0]  # Return first safe location

        # Default safe location (home)
        return {"name": "home", "x": 345, "y": 64, "z": -2493}

    def _find_discrete_location(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find a discrete location to hide"""
        # Look for configured discrete locations
        discrete_locations = context.get("discrete_locations", [])
        if discrete_locations:
            return discrete_locations[0]

        # Default to a nearby but hidden location
        current_pos = context.get("current_position", (0, 64, 0))
        return {"x": current_pos[0] + 50, "y": current_pos[1], "z": current_pos[2] + 50}

    def _escape_to_location(self, location: Dict[str, Any]) -> bool:
        """Escape to the specified location"""
        print(f"[emergency] Escaping to location: {location}")

        if "name" in location:
            escape_cmd = {
                "service": "warp",
                "method": "teleport",
                "params": {
                    "name": location["name"],
                    "radius": 5,
                    "command_template": "home tp {name}",
                    "target": {
                        "x": location.get("x", 0),
                        "y": location.get("y", 64),
                        "z": location.get("z", 0),
                    },
                },
            }
        else:
            escape_cmd = {
                "service": "baritone",
                "method": "goto",
                "params": {"x": location["x"], "y": location["y"], "z": location["z"]},
            }

        # In real implementation, this would send the actual command
        print(f"[emergency] Sent escape command")
        return True

    def _attempt_healing(self) -> None:
        """Attempt to heal by eating food"""
        print(f"[emergency] Attempting to heal")

        heal_cmd = {
            "service": "wurst",
            "method": "command",
            "params": {"command": "t", "args": ["eat", "on"]},
        }

        # In real implementation, this would send the actual command
        print(f"[emergency] Sent healing command")

    def cleanup(self, context: Dict[str, Any]) -> None:
        """Clean up after emergency behavior"""
        print(f"[emergency] Emergency behavior cleanup")

        # Reset emergency state
        self.emergency_type = None
        self.emergency_data = None

        # Clear emergency flags in context
        context["emergency_state"] = False
        context["pillager_attack"] = False
        context["player_detected"] = False
        context["low_health"] = False
