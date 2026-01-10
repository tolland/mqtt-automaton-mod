from abc import ABC

from mqttbot.actions.action import Action


class PathCmd(Action):
    def can_start(self) -> bool:
        pass

    def execute(self, bot, command_args):
        if not command_args:
            bot.send_message("Usage: /path <destination>")
            return

        destination = command_args[0]
        bot.send_message(f"Calculating path to {destination}...")
        success = bot.baritone.navigate_to(destination)

        if success:
            bot.send_message(f"Successfully started pathfinding to {destination}.")
        else:
            bot.send_message(f"Failed to find a path to {destination}.")
