"""MQTT-based Minecraft bot automation with Baritone integration."""

__version__ = "0.1.0"

from mqttbot.model.messaging.message_data import MessageData
from mqttbot.model.settings.settings import Settings

__all__ = ["MessageData", "Settings", "__version__"]
