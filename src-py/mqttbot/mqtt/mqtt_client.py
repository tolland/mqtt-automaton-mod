import sys
import time
from collections.abc import Callable

from paho.mqtt import client as mqtt

from mqttbot.model.settings.settings import Settings
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
        print("Subscribed:", mid, granted_qos)

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc != 0:
            print(f"[mqtt] Connect failed rc={rc}", file=sys.stderr)
            return
        # Subscribe to device presence topics
        self.device_monitor.subscribe()

        print(f"[mqtt] Connected → subscribing {self.topic_base}/reply and {self.topic_base}/events")
        self._client.subscribe(f"{self.topic_base}/reply", qos=0)
        self._client.subscribe(f"{self.topic_base}/events", qos=0)
        self._mqtt_connected = True

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        print(f"[mqtt] Disconnected rc={rc}")
        self._mqtt_connected = False

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()

        for cb in self.message_callbacks:
            try:
                cb(topic, payload)
            except Exception as e:
                print(f"[mqtt] Error in message callback: {e}")
                raise

    def connect(self) -> None:
        """Connect to MQTT broker"""
        if not self._client:
            self._setup_client()

        self.device_monitor = DevicePresenceMonitor(self.settings.client_id, self._client)

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

        print("[mqtt] Connection established successfully")

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

    def register_message_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register an additional message callback (topic, payload)"""
        if not callable(callback):
            raise TypeError("callback must be callable")
        self.message_callbacks.append(callback)

    @property
    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self._mqtt_connected
