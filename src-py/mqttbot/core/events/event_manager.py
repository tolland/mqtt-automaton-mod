from dataclasses import dataclass

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.config.model.events.event_handler import EventHandlerConfig
from mqttbot.config.model.events.events_config import EventsConfig
from mqttbot.core.protocol.thread import ThreadInterface


class EventManager:
    """Config-driven event handling"""

    def __init__(self, config: EventsConfig):
        """Initialize from config"""
        self._enabled: bool = False
        self.config = config
        self.handlers: dict[tuple[str, str], EventHandlerConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Parse config and index handlers by service:method"""
        self.handlers = self.config.root

    def start(self) -> None:
        """Enable the event manager"""
        self._enabled = True
        logger.info("EventManager enabled")

    def stop(self) -> None:
        """Disable the event manager"""
        self._enabled = False
        logger.info("EventManager disabled")

    def get_handler_config(self, service: str, method: str) -> EventHandlerConfig | None:
        """Look up handler config for a service:method pair"""
        return self.handlers.get((service, method))

    async def handle_message(self, message_data: ServiceMessage) -> ThreadInterface | None:
        """Handle an incoming service message by invoking the appropriate handler"""
        if not self._enabled:
            logger.debug("EventManager is disabled; skipping message handling")
            return None
        for pattern, callbacks in self.handlers.items():
            for callback in callbacks:
                if pattern[0] == message_data.service and pattern[1] == message_data.method:
                    result = await callback(message_data)
                    if result:
                        return result
        logger.debug(f"No handler found for {message_data.service}:{message_data.method}")
        return None

    def __rich_repr__(self) -> "rich.repr.Result":
        yield "enabled", self._enabled
        yield "handlers", self.handlers
