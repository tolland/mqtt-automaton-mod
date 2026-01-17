from mqttbot import MessageData
from mqttbot.core.state.baritone.baritone_state import BaritoneState, BaritoneStatus
from mqttbot.core.state.state_module import StateModule


def execute_movement(ctx, coordinates: tuple[int, int, int]) -> None:
    """Execute a movement to the given coordinates"""
    x, y, z = coordinates

    # Create a structured JSON command for movement
    message_data = {
        "service": "baritone",
        "method": "goto",
        # "correlationId": self.correlation_id,
        "params": {"x": x, "y": y, "z": z},
    }

    cmd = str(message_data).replace("'", '"')  # Simple JSON conversion
    print(f"[pattern] Movement: goto {x} {y} {z}")
    ctx.message_sender(cmd)


class BaritoneModule(StateModule[BaritoneState]):
    def __init__(self):
        self._state = BaritoneState()

    def handle_event(self, event: MessageData) -> None:
        """
        Routed messages to this module, update state accordingly
        :param event:
        :type event:
        :return:
        :rtype:
        """

        if event.method == "goto":
            data = event.response
            status = data.get("status", "FAILED").upper()
            if status == "SUCCESS":
                self._state.target = None
            self._state.status = BaritoneStatus[status]

    def get_state(self) -> BaritoneState:
        return self._state

    def reset_state(self) -> None:
        self._state = BaritoneState()
