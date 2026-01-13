from dataclasses import dataclass
from typing import Optional, Any

from mqttbot import MessageData
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.tasks.task_step_config import TaskStepConfig


@dataclass
class EventHandlerConfig:
    """Configuration for an event handler"""

    enabled: bool
    steps: list[TaskStepConfig]


class EventManager:
    """Config-driven event handling"""

    def __init__(self, config: dict[str, dict[str, Any]]):
        """Initialize from config

        Args:
            config: event_handlers section from YAML
                {
                    "events": {
                        "night_start": {
                            "enabled": True,
                            "steps": [...]
                        }
                    }
                }
        """
        self.config = config
        self.handlers: dict[tuple[str, str], EventHandlerConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Parse config and index handlers by service:method"""
        for service_name, methods in self.config.items():
            for method_name, handler_config in methods.items():
                if not isinstance(handler_config, dict):
                    continue

                if not handler_config.get("enabled", False):
                    continue

                steps = []
                for step_def in handler_config.get("steps", []):
                    step = TaskStepConfig(
                        type=step_def.get("type", "command"),
                        service=step_def["service"],
                        method=step_def["method"],
                        params=step_def.get("params", {}),
                    )
                    steps.append(step)

                key = (service_name, method_name)
                self.handlers[key] = EventHandlerConfig(enabled=True, steps=steps)
                print(
                    f"[config] Registered event handler: {service_name}:{method_name} ({len(steps)} steps)"
                )

    def get_handler_config(self, service: str, method: str) -> Optional[EventHandlerConfig]:
        """Look up handler config for a service:method pair"""
        return self.handlers.get((service, method))

    async def handle_message(self, message_data: MessageData) -> Optional[TaskThread]:
        for pattern, callbacks in self.handlers.items():
            for callback in callbacks:
                if pattern[0] == message_data.service and pattern[1] == message_data.method:
                    result = await callback(message_data)
                    if result:
                        return result
        print(f"[event_manager] No handler found for {message_data.service}:{message_data.method}")
        return None
