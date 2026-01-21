from loguru import logger
from mqttbot import ServiceMessage
from mqttbot.core.state.events.events_state import EventsState
from mqttbot.core.state.state_module import StateModule


class EventsModule(StateModule[EventsState]):
    def __init__(self):
        self._state = EventsState()

    def handle_event(self, message_data: ServiceMessage) -> None:
        logger.debug(f"EventsModule handling event: {message_data.service}:{message_data.method}")
        if message_data.method == "chat_message":
            self._state.message = message_data
        elif message_data.service == "events" and message_data.method == "player_join":
            self._state.player_joined = True
        elif message_data.service == "events" and message_data.method == "heartbeat":
            self._state.player_joined = True

    def get_state(self) -> EventsState:
        return self._state

    def reset_state(self) -> None:
        self._state = EventsState()
