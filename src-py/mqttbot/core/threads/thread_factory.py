from mqttbot.config.model.thread.thread_definition import ThreadDefinition
from mqttbot.core.tasks.waypoint_provider import WaypointTaskSource
from mqttbot.core.threads.dynamic_handler import DynamicHandler
from mqttbot.core.protocol.task_compiler_protocol import TaskCompilerProtocol
from mqttbot.core.protocol.thread import ThreadInterface
from mqttbot.core.threads.thread import TaskThread


class ThreadFactory:
    def __init__(self, compiler: TaskCompilerProtocol):
        self.compiler = compiler

    def create_thread(
        self,
        definition: ThreadDefinition,
    ) -> ThreadInterface:
        # 1. Wrap the main workload into a Source
        main_source = WaypointTaskSource(definition, self.compiler)

        # 2. Wrap the event steps into DynamicHandlers (Providers)
        # We 'bake' the compiler into them here
        # inspect(definition.hooks)
        on_suspend = DynamicHandler(definition.hooks.on_suspend.steps, self.compiler)
        on_resume = DynamicHandler(definition.hooks.on_resume.steps, self.compiler)
        on_cancel = DynamicHandler(definition.hooks.on_cancel.steps, self.compiler)
        on_failed = DynamicHandler(definition.hooks.on_failed.steps, self.compiler)

        # 3. Build the Thread
        return TaskThread(
            thread_id=definition.thread_id,
            main_source_provider=main_source,
            on_suspend_provider=on_suspend,
            on_resume_provider=on_resume,
            on_cancel_provider=on_cancel,
            on_failed_provider=on_failed,
            priority=definition.priority,
            metadata=definition.metadata.model_dump() if definition.metadata else {},
        )
