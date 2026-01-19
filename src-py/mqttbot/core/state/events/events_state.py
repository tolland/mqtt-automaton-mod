from dataclasses import dataclass
from typing import Optional

from mqttbot import ServiceMessage


@dataclass
class EventsState:
    message: Optional[ServiceMessage] = None
    player_joined: bool = False
