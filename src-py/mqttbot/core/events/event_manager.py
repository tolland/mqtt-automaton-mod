from dataclasses import dataclass
from typing import Any

from loguru import logger
from rich import inspect

from mqttbot import ServiceMessage
from mqttbot.core.threads.task_thread import TaskThread
from mqttbot.model.patterns.step import TaskStep


@dataclass
class EventHandlerConfig:
    """Configuration for an event handler"""

    enabled: bool
    steps: list[TaskStep]


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
                    try:
                        step = TaskStep(
                            type=step_def.get("type", "command"),
                            service=step_def["service"],
                            method=step_def["method"],
                            params=step_def.get("params", {}),
                        )
                    except:
                        inspect(step_def)
                        raise
                    steps.append(step)

                key = (service_name, method_name)
                self.handlers[key] = EventHandlerConfig(enabled=True, steps=steps)
                logger.info(
                    f"Registered event handler: {service_name}:{method_name} ({len(steps)} steps)"
                )

    def get_handler_config(self, service: str, method: str) -> EventHandlerConfig | None:
        """Look up handler config for a service:method pair"""
        return self.handlers.get((service, method))

    async def handle_message(self, message_data: ServiceMessage) -> TaskThread | None:
        for pattern, callbacks in self.handlers.items():
            for callback in callbacks:
                if pattern[0] == message_data.service and pattern[1] == message_data.method:
                    result = await callback(message_data)
                    if result:
                        return result
        logger.debug(f"No handler found for {message_data.service}:{message_data.method}")
        return None
