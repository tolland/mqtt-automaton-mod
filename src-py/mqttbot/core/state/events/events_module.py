from mqttbot import MessageData
from mqttbot.core.state.events.events_state import EventsState
from mqttbot.core.state.state_module import StateModule


class EventsModule(StateModule[EventsState]):
    def __init__(self):
        self._state = EventsState()

    def handle_event(self, message_data: MessageData) -> None:
        if message_data.method == "chat_message":
            self._state.message = message_data

    def get_state(self) -> EventsState:
        return self._state

    def reset_state(self) -> None:
        self._state = EventsState()
