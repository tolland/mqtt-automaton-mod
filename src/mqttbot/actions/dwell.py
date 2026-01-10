from mqttbot.actions.action import Action


class DwellAction(Action):
    def __init__(self, dwell_time: float):
        self.dwell_time = dwell_time
        self.start_time = None

    def execute(self, *args, **kwargs):
        import time

        if self.start_time is None:
            self.start_time = time.time()

    def can_start(self) -> bool:
        return True

    def is_complete(self) -> bool:
        import time

        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.dwell_time

    def reset(self):
        self.start_time = None
