"""
Inventory management behavior for handling full inventory scenarios
"""

import time
import uuid
from typing import Any, Dict

from mqttbot import MessageData
from mqttbot.scripts.behaviors.base_behavior import BaseBehavior, BehaviorState


class InventoryManagementBehavior(BaseBehavior):
    """
    Handles inventory full situations by navigating to merchants and depositing items.

    This behavior:
    - Triggers when inventory_full event is received
    - Has high priority (2) to interrupt farming
    - Uses baritone to navigate to merchant location
    - Handles item depositing/trading (future: integrate with NPC trading)
    - Returns control to farming after completion
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        config = config or {}
        # Set high priority to interrupt farming (1=highest, 10=lowest)
        config.setdefault("priority", 2)
        config.setdefault("interruptible", False)  # Don't interrupt mid-deposit
        super().__init__(name, config)

        self.merchant_location = config.get("merchant_location", {})
        self.warp_command = config.get("warp_command", "warp merchants")
        self.navigate_to_npc = config.get("navigate_to_npc", True)
        self.npc_coordinates = config.get("npc_coordinates", {})
        self.message_sender = None
        self.pattern_engine = None

        # State tracking
        self.correlation_id = None
        self.warped = False
        self.navigated = False
        self.completed_trade = False

    def set_message_sender(self, sender):
        """Set the MQTT message sender function"""
        self.message_sender = sender

    def set_pattern_engine(self, engine):
        """Set the pattern engine for navigation"""
        self.pattern_engine = engine

    def can_start(self, context: Dict[str, Any]) -> bool:
        """
        Can start when inventory_full event is detected in context
        """
        last_event = context.get("last_event", {})
        if last_event.get("service") == "inventory":
            event_type = last_event.get("response", {}).get("event")
            if event_type == "inventory_full":
                print(
                    f"[{self.name}] Inventory full detected, can start inventory management"
                )
                return True

        return False

    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Execute the inventory management workflow:
        1. Warp to merchant area
        2. Use baritone to navigate to NPC
        3. Handle trading/depositing (placeholder for now)
        4. Return success
        """
        try:
            self.correlation_id = str(uuid.uuid4())
            print(
                f"[{self.name}] Starting inventory management (correlation: {self.correlation_id})"
            )

            # Step 1: Warp to merchant area
            if not self._warp_to_merchants():
                print(f"[{self.name}] Failed to warp to merchants")
                return False

            # Step 2: Navigate to NPC using baritone
            if self.navigate_to_npc and self.npc_coordinates:
                if not self._navigate_to_npc():
                    print(f"[{self.name}] Failed to navigate to NPC")
                    return False
            else:
                print(f"[{self.name}] Skipping NPC navigation (not configured)")

            # Step 3: Handle trading/depositing
            # TODO: Implement actual trading logic when NPC integration is available
            if not self._handle_trading():
                print(f"[{self.name}] Failed to handle trading")
                return False

            print(f"[{self.name}] Inventory management completed successfully")
            return True

        except Exception as e:
            print(f"[{self.name}] Error during execution: {e}")
            return False

    def _warp_to_merchants(self) -> bool:
        """Warp to merchant location"""
        if not self.message_sender:
            print(f"[{self.name}] No message sender configured")
            return False

        print(f"[{self.name}] Warping to merchants...")

        # Create warp command
        message_data = MessageData(
            service="warp",
            method="teleport",
            correlation_id=self.correlation_id,
            params={
                "name": "merchants",
                "command_template": self.warp_command,
                **self.merchant_location,
            },
        )

        # Send warp command
        self.message_sender(message_data.to_json())

        # Wait for warp completion
        # TODO: Implement proper event waiting mechanism
        print(f"[{self.name}] Waiting for warp to complete...")
        time.sleep(3)  # Temporary: wait for warp
        self.warped = True

        return True

    def _navigate_to_npc(self) -> bool:
        """Use baritone to navigate to NPC"""
        if not self.pattern_engine:
            print(f"[{self.name}] No pattern engine configured")
            return False

        if not self.npc_coordinates:
            print(f"[{self.name}] No NPC coordinates configured")
            return False

        print(f"[{self.name}] Navigating to NPC at {self.npc_coordinates}...")

        # Create baritone goto command
        message_data = MessageData(
            service="baritone",
            method="goto",
            correlation_id=self.correlation_id,
            params={
                "x": self.npc_coordinates.get("x"),
                "y": self.npc_coordinates.get("y"),
                "z": self.npc_coordinates.get("z"),
            },
        )

        # Send goto command
        self.message_sender(message_data.to_json())

        # Wait for navigation completion
        # TODO: Implement proper arrival detection
        print(f"[{self.name}] Waiting for navigation to complete...")
        time.sleep(5)  # Temporary: wait for navigation
        self.navigated = True

        return True

    def _handle_trading(self) -> bool:
        """Handle item trading/depositing"""
        print(f"[{self.name}] Handling trading...")

        message_data = MessageData(
            service="wurst",
            method="command",
            correlation_id=self.correlation_id,
            params={"command": "t", "args": ["autoshopgui", "on"]},
        )

        self.message_sender(message_data.to_json())

        # Placeholder: just wait a bit
        print(
            f"[{self.name}] sleeping as placeholder"
        )
        time.sleep(10)
        self.completed_trade = True

        return True

    def cleanup(self, context: Dict[str, Any]) -> None:
        """Clean up after behavior execution"""
        print(f"[{self.name}] Cleaning up inventory management behavior")

        # Reset state for next execution
        self.correlation_id = None
        self.warped = False
        self.navigated = False
        self.completed_trade = False

        # Clear inventory_full flag from context so we don't re-trigger
        if "last_event" in context:
            last_event = context["last_event"]
            if last_event.get("service") == "inventory":
                # Clear the event so it doesn't retrigger
                context["inventory_full_handled"] = True

    def get_status(self) -> Dict[str, Any]:
        """Get current behavior status"""
        status = super().get_status()
        status.update(
            {
                "warped": self.warped,
                "navigated": self.navigated,
                "completed_trade": self.completed_trade,
                "merchant_location": self.merchant_location,
                "npc_coordinates": self.npc_coordinates,
            }
        )
        return status
