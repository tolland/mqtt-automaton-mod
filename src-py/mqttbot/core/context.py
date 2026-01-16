from dataclasses import dataclass
from typing import Callable

from mqttbot import MessageData


@dataclass
class Context:
    message_sender: Callable[[MessageData], None]
    blackboard: "TypedBlackboard"
    bot_service: "BotService"
