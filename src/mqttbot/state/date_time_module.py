from mqttbot import MessageData
from mqttbot.state.date_time_state import DateTimeState
from mqttbot.state.state_module import StateModule


class DateTimeModule(StateModule[DateTimeState]):
    def __init__(self):
        self._state = DateTimeState()

    def handle_event(self, event: MessageData) -> None:
        ...
        # if event.method == "goto":
        #     data = event.response
        #     status = data.get("status", "FAILED").upper()
        #     if status == "SUCCESS":
        #         self._state.target = None
        #     self._state.status = BaritoneStatus[status]

    def get_state(self) -> DateTimeState:
        return self._state

    def reset_state(self) -> None:
        self._state = DateTimeState()
