from mqttbot import ServiceMessage
from mqttbot.core.state.state_module import StateModule
from mqttbot.core.state.wurst_state import WurstState


class WurstModule(StateModule[WurstState]):
    def __init__(self):
        self._state = WurstState()

    def handle_event(self, event: ServiceMessage) -> None: ...

    def get_state(self) -> WurstState:
        return self._state

    def reset_state(self) -> None:
        self._state = WurstState()
