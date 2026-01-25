"""MQTT-based Minecraft bot automation with Baritone integration."""

__app_name__ = "mqttbot"
__version__ = "0.1.0"

from mqttbot.config.settings.settings import Settings
from mqttbot.model.messaging.service_message import ServiceMessage

__all__ = ["ServiceMessage", "Settings", "__version__"]
