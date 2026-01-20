from dataclasses import dataclass
from typing import Callable, Optional

from mqttbot import ServiceMessage


@dataclass
class Context:
    message_sender: Callable[[ServiceMessage], None]
    blackboard: "TypedBlackboard"
    bot_service: "BotService"
    mqtt: Optional["MqttBotClient"] = None
