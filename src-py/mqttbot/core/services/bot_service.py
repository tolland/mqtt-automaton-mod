import uuid
from typing import Optional

from mqttbot import ServiceMessage
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import MessageService


class BotService(MessageService):
    """Unified service for managing all bot operations (baritone, sleep, warp)"""

    def __init__(self, ctx: Context):
        super().__init__(ctx, "bot")
