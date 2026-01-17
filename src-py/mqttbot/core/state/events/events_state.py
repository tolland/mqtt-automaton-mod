from dataclasses import dataclass
from typing import Optional

from mqttbot import MessageData


@dataclass
class EventsState:
    message: Optional[MessageData] = None
    player_joined: bool = False
