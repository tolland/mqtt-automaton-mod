import time
from collections.abc import Callable
from typing import Any

from loguru import logger
from paho.mqtt import client as mqtt
from paho.mqtt.client import MQTTMessage

from mqttbot.config.settings.settings import Settings
from mqttbot.mqtt.device_presence import DevicePresenceMonitor


class MqttBotClient:
    """
    Helper class for MQTT communication.

    Handles connection, disconnection, message sending/receiving,
    and provides a clean interface for MQTT operations.
    """

    def __init__(
        self,
        settings: Settings,
    ):
        """Initialize MQTT client

        Args:
            settings: Settings object containing MQTT configuration
            message_callbacks: Optional list of callback functions to handle incoming messages (topic, payload)
        """
        self.device_monitor: DevicePresenceMonitor | None = None
        self.settings: Settings = settings
        self.message_callbacks: list[Callable[[str, str], None]] = []
        self._mqtt_connected = False
        self._client: mqtt.Client | None = None

        # Store topic information from Settings
        self.topic_base = settings.topic_base

    def _setup_client(self) -> None:
        """Setup MQTT client with callbacks"""
        self._client = mqtt.Client(
            client_id=f"modular-bot-{int(time.time())}",
            clean_session=True
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        # self._client.on_subscribe = self.on_subscribe

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logger.debug(f"Subscribed: mid={mid}, qos={granted_qos}")

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc != 0:
            logger.error(f"MQTT connect failed: rc={rc}")
            return
        # Subscribe to device presence topics
        self.device_monitor.subscribe()

        logger.info("Connected to MQTT broker, subscribing to topics")
        self._client.subscribe(f"{self.topic_base}/reply", qos=0)
        self._client.subscribe(f"{self.topic_base}/events", qos=0)
        self._mqtt_connected = True

    def _on_disconnect(self, _client, _userdata, rc):
        """Handle MQTT disconnection"""
        logger.info(f"Disconnected from MQTT broker: rc={rc}")
        self._mqtt_connected = False

    def _on_message(self, _client: mqtt.Client, _user_data: Any, msg: MQTTMessage) -> None:
        """Handle incoming MQTT messages"""
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()

        logger.bind(mqtt=True).debug(payload)

        for cb in self.message_callbacks:
            try:
                cb(topic, payload)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
                raise

    def connect(self) -> None:
        """Connect to MQTT broker"""
        if not self._client:
            self._setup_client()

        self.device_monitor = DevicePresenceMonitor(self.settings.client_id, self._client)

        self._client.connect(self.settings.broker, self.settings.port, keepalive=60)
        self._client.loop_start()

        # Wait for connection
        logger.info(f"Connecting to {self.settings.broker}:{self.settings.port}...")
        timeout = 10
        start_time = time.time()
        while not self._mqtt_connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self._mqtt_connected:
            raise Exception(f"Failed to connect to MQTT broker within {timeout} seconds")

        logger.info("Connection established successfully")

    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    def send(self, topic: str, message: str) -> None:
        """Send MQTT message

        Args:
            message: Message string to send
            :param message:
            :type message:
            :param topic:
            :type topic:
        """
        if not self._client:
            raise RuntimeError("MQTT client not initialized. Call connect() first.")

        logger.debug(f"Publishing to {topic}: {message[:100]}...")  # Truncate long messages
        logger.bind(mqtt=True).debug(message)
        self._client.publish(topic, message, qos=0, retain=False)

    def register_message_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register an additional message callback (topic, payload)"""
        if not callable(callback):
            raise TypeError("callback must be callable")
        self.message_callbacks.append(callback)

    @property
    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self._mqtt_connected
