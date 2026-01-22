from mqttbot.core.services.message_service import MessageService
from mqttbot.core.threads.scheduler_context import Context


class BotService(MessageService):
    """Unified service for managing all bot operations (baritone, sleep, warp)"""

    def __init__(self, ctx: Context):
        super().__init__(ctx, "bot")
