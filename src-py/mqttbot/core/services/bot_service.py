import uuid
from typing import Optional

from mqttbot import MessageData
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import MessageService


class BotService(MessageService):
    """Unified service for managing all bot operations (baritone, sleep, warp)"""

    def __init__(self, ctx: Context):
        super().__init__(ctx, "bot")

    def send_goto(self, x: int, y: int, z: int) -> str:
        """
        Send baritone goto request, return request_id immediately (non-blocking).

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            z: Target Z coordinate

        Returns:
            The request_id of the sent message
        """
        request_id = str(uuid.uuid4())

        message_data = MessageData(
            **{
                "service": "baritone",
                "method": "goto",
                "request_id": request_id,
                "params": {"x": x, "y": y, "z": z},
            }
        )
        return self.send_message(message_data)

    def sleep(self, radius: Optional[int] = None) -> str:
        """
        Send sleep request, return request_id immediately (non-blocking).

        Args:
            radius: Optional scan radius for finding beds (defaults to server default)

        Returns:
            The request_id of the sent message
        """
        request_id = str(uuid.uuid4())

        params = {}
        if radius is not None:
            params["radius"] = radius

        message_data = MessageData(
            **{
                "service": "sleep",
                "method": "start",
                "request_id": request_id,
                "params": params,
            }
        )
        return self.send_message(message_data)

    def teleport(
        self,
        name: str,
        target_x: float,
        target_y: float,
        target_z: float,
        radius: Optional[int] = None,
        command_template: Optional[str] = None,
    ) -> str:
        """
        Send warp/teleport request, return request_id immediately (non-blocking).

        Args:
            name: Warp destination name (required)
            target_x: Expected destination X coordinate (required)
            target_y: Expected destination Y coordinate (required)
            target_z: Expected destination Z coordinate (required)
            radius: Optional radius for position checking (defaults to server default, typically 5)
            command_template: Optional command template (defaults to "warp {name}")

        Returns:
            The request_id of the sent message
        """
        request_id = str(uuid.uuid4())

        params = {
            "name": name,
            "target": {
                "x": target_x,
                "y": target_y,
                "z": target_z,
            },
        }

        if radius is not None:
            params["radius"] = radius

        if command_template is not None:
            params["command_template"] = command_template

        message_data = MessageData(
            **{
                "service": "warp",
                "method": "teleport",
                "request_id": request_id,
                "params": params,
            }
        )
        return self.send_message(message_data)
