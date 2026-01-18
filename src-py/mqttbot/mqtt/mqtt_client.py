import sys
import time
from typing import Callable, Optional

from paho.mqtt import client as mqtt

from mqttbot.model.settings.settings import Settings


class MqttClient:
    """
    Helper class for MQTT communication.

    Handles connection, disconnection, message sending/receiving,
    and provides a clean interface for MQTT operations.
    """

    def __init__(
        self,
        settings: Settings,
        message_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """Initialize MQTT client

        Args:
            settings: Settings object containing MQTT configuration
            message_callback: Optional callback function to handle incoming messages (topic, payload)
        """
        self.settings = settings
        self.message_callback = message_callback
        self._mqtt_connected = False
        self._client: Optional[mqtt.Client] = None

        # Store topic information from Settings
        self.topic_base = settings.topic_base

    def _setup_client(self) -> None:
        """Setup MQTT client with callbacks"""
        self._client = mqtt.Client(client_id=f"modular-bot-{int(time.time())}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc != 0:
            print(f"[mqtt] Connect failed rc={rc}", file=sys.stderr)
            return

        print(f"[mqtt] Connected → subscribing {self.topic_base}/#")
        self._client.subscribe(f"{self.topic_base}/#", qos=0)
        self._mqtt_connected = True

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        print(f"[mqtt] Disconnected rc={rc}")
        self._mqtt_connected = False

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        print(f"[mqtt] < {topic}: {payload}")

        if self.message_callback:
            try:
                self.message_callback(topic, payload)
            except Exception as e:
                print(f"[mqtt] Error in message callback: {e}")
                raise

    def connect(self) -> None:
        """Connect to MQTT broker"""
        if not self._client:
            self._setup_client()

        self._client.connect(self.settings.broker, self.settings.port, keepalive=60)
        self._client.loop_start()

        # Wait for connection
        print(f"[mqtt] Connecting to {self.settings.broker}:{self.settings.port}...")
        timeout = 10
        start_time = time.time()
        while not self._mqtt_connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self._mqtt_connected:
            raise Exception(f"Failed to connect to MQTT broker within {timeout} seconds")

        print(f"[mqtt] Connection established successfully")

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

        print(f"[mqtt] → {self.topic_base}: {message}")
        self._client.publish(topic, message, qos=0, retain=False)

    @property
    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self._mqtt_connected
