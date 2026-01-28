"""
World state module - integrates WorldStateCache with the blackboard system.
"""

from typing import Any

from mqttbot.core.state.state_module import StateModule
from mqttbot.core.state.world_cache import WorldStateCache
from mqttbot.model.world.scan_result import ScanResult


class WorldModule(StateModule[WorldStateCache]):
    """
    State module for world data (entities, blocks, containers).

    Handles scan result events and maintains world cache.
    """

    def __init__(self):
        self.cache = WorldStateCache()

    def handle_event(self, event: dict[str, Any]) -> None:
        """
        Handle incoming events (scan results from mod).

        Expected event format:
        {
            "type": "scan_result",
            "data": {
                "scan_type": "container_scan",
                "timestamp": 1234567890,
                "center": [100, 64, -200],
                "radius": 64,
                "entities": [...],
                "blocks": [...]
            }
        }
        """
        if event.get("type") == "scan_result":
            scan = ScanResult.from_dict(event["data"])
            self.cache.update_from_scan(scan)

    def get_state(self) -> WorldStateCache:
        """Get the world cache"""
        return self.cache

    def reset_state(self) -> None:
        """Reset/clear the cache"""
        self.cache.clear()
