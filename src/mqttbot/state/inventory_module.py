from typing import Any

from mqttbot import MessageData
from mqttbot.core.models.inventory_item import InventoryItem
from mqttbot.state.inventory_state import InventoryState
from mqttbot.state.state_module import StateModule


class InventoryModule(StateModule[InventoryState]):
    def __init__(self):
        self._state = InventoryState()

    def handle_event(self, event: MessageData) -> None:


        if event.method == "inventory_open":
            self._state.open = True
            self._state.current_container = event.get("container", "main")

        elif event.method  == "inventory_close":
            self._state.open = False

        elif event.method  == "item_update":
            items = event.get("items", [])
            container = event.get("container", "main")
            target = self._state.main_items
            target.clear()
            for item_data in items:
                item = InventoryItem(**item_data)
                target[item.slot] = item

    def get_state(self) -> InventoryState:
        return self._state

    def reset_state(self) -> None:
        self._state = InventoryState()
