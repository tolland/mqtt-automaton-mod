from mqttbot.models.inventory_item import InventoryItem
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Protocol
from abc import ABC, abstractmethod
import json

from mqttbot.state.inventory_state import InventoryState
from mqttbot.state.state_module import StateModule


class InventoryModule(StateModule[InventoryState]):
    def __init__(self):
        self._state = InventoryState()

    def handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")

        if event_type == "inventory_open":
            self._state.open = True
            self._state.current_container = event.get("container", "main")

        elif event_type == "inventory_close":
            self._state.open = False

        elif event_type == "item_update":
            items = event.get("items", [])
            container = event.get("container", "main")
            target = (
                self._state.backpack_items
                if container == "backpack"
                else self._state.main_items
            )
            target.clear()
            for item_data in items:
                item = InventoryItem(**item_data)
                target[item.slot] = item

    def get_state(self) -> InventoryState:
        return self._state
