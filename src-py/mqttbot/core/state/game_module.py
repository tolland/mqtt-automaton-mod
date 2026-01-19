from mqttbot import ServiceMessage
from mqttbot.core.state.game_state import GameState
from mqttbot.core.state.state_module import StateModule


class GameModule(StateModule[GameState]):
    def __init__(self):
        self._state = GameState()

    def handle_event(self, event: ServiceMessage) -> None: ...

    def get_state(self) -> GameState:
        return self._state

    def reset_state(self) -> None:
        self._state = GameState()
