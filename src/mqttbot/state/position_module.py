from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Protocol
from abc import ABC, abstractmethod
import json

from mqttbot.state.entity_state import EntityState
from mqttbot.state.position_state import PositionState
from mqttbot.state.state_module import StateModule


class PositionModule(StateModule[PositionState]):
    def __init__(self):
        self._state = PositionState(player=EntityState(x=0, y=0, z=0))

    def handle_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")

        if event_type == "player_move":
            data = event.get("data", {})
            self._state.player = EntityState(
                x=data["x"],
                y=data["y"],
                z=data["z"],
                yaw=data.get("yaw", 0),
                pitch=data.get("pitch", 0),
            )

        elif event_type == "entity_update":
            entities = event.get("entities", {})
            for eid, edata in entities.items():
                self._state.nearby_entities[eid] = EntityState(
                    x=edata["x"],
                    y=edata["y"],
                    z=edata["z"],
                    yaw=edata.get("yaw", 0),
                    pitch=edata.get("pitch", 0),
                )

    def get_state(self) -> PositionState:
        return self._state
