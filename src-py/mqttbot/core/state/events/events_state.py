from dataclasses import dataclass

from mqttbot import ServiceMessage


@dataclass
class EventsState:
    message: ServiceMessage | None = None
    player_joined: bool = False
