from dataclasses import dataclass
from typing import Callable, Optional

from mqttbot import MessageData


@dataclass
class Context:
    message_sender: Callable[[MessageData], None]
    blackboard: "TypedBlackboard"
    bot_service: "BotService"
    correlation_id: Optional[str] = None  # Tracks the thread instance for message correlation
