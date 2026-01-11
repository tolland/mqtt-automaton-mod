
from mqttbot.state.baritone.baritone_state import BaritoneState
from mqttbot.tasks.task import Task


def execute_movement(ctx) -> None:
    """Execute a movement to the given coordinates"""

    # Create a structured JSON command for movement
    message_data = {
        "service": "wurst",
        "method": "command",
        # "correlationId": self.correlation_id,
        "params": {"command": "t", "args": ["autofarm", "on"]},
    }

    cmd = str(message_data).replace("'", '"')  # Simple JSON conversion
    print(f"[pattern] Wurst: action")
    ctx.message_sender(cmd)


class WurstToggle(Task):
    def __init__(self, hack: str, state: bool):
        self.hack = hack
        self.state = state

    def step(self, ctx):
        execute_movement(ctx)
        return TaskStatus.SUCCESS

        # if self._state.status == BaritoneStatus.FAILED:
        #     return TaskStatus.FAILED
        #
        # return TaskStatus.RUNNING

    def _suspend(self, ctx) -> None:
        print(f"Wurst action Suspended: {self.state}")

    def _resume(self, ctx) -> None:
        print(f"Wurst action Resumed: {self.state}")


    def state(self, pos: BaritoneState):
        print(f"Wurst Update: {self.state} → {pos}")

    def _exit(self, ctx, status: TaskStatus):
        print(f"Wurst action Done: {self.state}")
