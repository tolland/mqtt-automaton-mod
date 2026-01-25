import time

import pytest

from mqttbot.config.settings.config import build_settings
from mqttbot.core.modular_bot_client import ModularBotClient

# pytestmark = pytest.mark.skip(reason="Requires minecraft client running")

@pytest.mark.requires_server
def test_mqtt_connection(minecraft_client):
    """This test runs only when client is active."""
    settings = build_settings(
        config_path="./configs/threads.yml",
        broker="mosquitto,lan",
        port="1883",
        client_id="mqttbot-minecraft-test",
        timeout=30,
        retries=3,
        retry_delay=5,
        log_level="DEBUG",
    )
    client = ModularBotClient(settings, str("./configs/threads.yml"))
    client.configure()
    time.sleep(30)
    client.run()

@pytest.mark.requires_server
def test_another_feature(minecraft_client):
    """Uses the client fixture."""
    pass
