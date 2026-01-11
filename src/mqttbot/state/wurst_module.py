from typing import Any

from mqttbot import MessageData
from mqttbot.state.state_module import StateModule
from mqttbot.state.wurst_state import WurstState


class WurstModule(StateModule[WurstState]):
    def __init__(self):
        self._state = WurstState()

    def handle_event(self, event: MessageData) -> None:
        ...

    def get_state(self) -> WurstState:
        return self._state

    def reset_state(self) -> None:
        self._state = WurstState()
