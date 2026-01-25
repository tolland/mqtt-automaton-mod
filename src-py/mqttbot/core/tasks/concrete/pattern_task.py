from mqttbot.core.tasks.concrete import GotoTask
from mqttbot.core.tasks.task_base import task


@task("pattern")
class PatternTask(GotoTask):
    pass
