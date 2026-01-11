from mqttbot.core.task.task import TaskStatus
from mqttbot.tasks.task import Task


class PatternTask(Task):
    def __init__(self, task_runner, steps):
        self.steps: list[Task] = steps
        self.index = 0
        self.curr_coords = None
        self.task_runner = task_runner

    def step(self, ctx):
        if self.index >= len(self.steps):
            return TaskStatus.SUCCESS

        step = self.steps[self.index]
        self.task_runner.push(step)
        self.index += 1

        return TaskStatus.RUNNING
