import os
import sys
import threading
import time
import uuid
from typing import Any, Dict, Tuple

import yaml
from paho.mqtt import client as mqtt

from mqttbot import MessageData
from mqttbot.scripts.behaviors.emergency_behavior import EmergencyBehavior
from mqttbot.scripts.behaviors.farming_behavior import FarmingBehavior
from mqttbot.scripts.core.behavior_engine import BehaviorEngine
from mqttbot.scripts.patterns.pattern_engine import PatternEngine

"""
Modular bot client using the new behavior-based architecture
"""

# Add scripts directory to Python path
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)



class ModularBotClient:
    """
    Modular bot client that uses behavior-based architecture.

    This client:
    - Manages MQTT communication
    - Orchestrates behaviors through the behavior engine
    - Handles events and context updates
    - Provides a clean interface for bot operations
    """

    def __init__(self, config_path: str):
        """Initialize the modular bot client"""
        self.config = self._load_config(config_path)
        self.behavior_engine = BehaviorEngine()
        self.pattern_engine = None
        self.mqtt_client = None
        self.running = False

        # MQTT state
        self._mqtt_connected = False
        self._last_position = None
        self._last_event = None
        self._lock = threading.Lock()

        # Initialize components
        self._setup_mqtt()
        self._setup_pattern_engine()
        self._setup_behaviors()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _setup_mqtt(self) -> None:
        """Setup MQTT client"""
        client_id = self.config.get("client_id", "modular_bot")
        broker = self.config.get("broker", "127.0.0.1")
        port = self.config.get("port", 1883)

        self.mqtt_client = mqtt.Client(client_id=f"modular-bot-{int(time.time())}")
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

        # Store topic information
        self.topic_cmd = f"mqttbot/{client_id}/command"
        self.topic_reply = (
            f"mqttbot/{self.config.get('expected_player_name', client_id)}/reply"
        )
        self.topic_pos = (
            f"mqttbot/{self.config.get('expected_player_name', client_id)}/pos"
        )

    def _setup_pattern_engine(self) -> None:
        """Setup pattern engine"""
        self.pattern_engine = PatternEngine(
            message_sender=self._send_mqtt_message,
            position_tracker=self._get_current_position,
        )

    def _setup_behaviors(self) -> None:
        """Setup and register behaviors"""
        # Create farming behavior
        farming_config = {
            "waypoints": self.config.get("waypoints", []),
            "patterns": self.config.get("patterns", {}),
            "priority": 5,
        }
        farming_behavior = FarmingBehavior("farming", farming_config)
        farming_behavior.set_pattern_engine(self.pattern_engine)
        self.behavior_engine.add_behavior(farming_behavior)

        # Create emergency behavior
        emergency_config = {"priority": 1, "interruptible": False}
        emergency_behavior = EmergencyBehavior("emergency", emergency_config)
        self.behavior_engine.add_behavior(emergency_behavior)

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc != 0:
            print(f"[mqtt] Connect failed rc={rc}", file=sys.stderr)
            return

        print(f"[mqtt] Connected → subscribing {self.topic_reply}")
        self.mqtt_client.subscribe(self.topic_reply, qos=0)
        self.mqtt_client.subscribe(self.topic_pos, qos=0)
        self._mqtt_connected = True

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        print(f"[mqtt] Disconnected rc={rc}")
        self._mqtt_connected = False

    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        payload = msg.payload.decode("utf-8", errors="replace").strip()

        try:
            # Parse as structured MessageData
            message_data = MessageData.from_json(payload)
            if message_data:
                self._process_message(message_data)
        except Exception as e:
            print(f"[mqtt] Error processing message: {e}")

    def _process_message(self, message_data: MessageData) -> None:
        """Process incoming message and update context"""
        with self._lock:
            self._last_event = {
                "service": message_data.service,
                "method": message_data.method,
                "params": message_data.params,
                "response": message_data.response,
            }

            # Update position if available
            if message_data.response:
                x = message_data.response.get("x")
                y = message_data.response.get("y")
                z = message_data.response.get("z")
                if (
                        isinstance(x, (int, float))
                        and isinstance(y, (int, float))
                        and isinstance(z, (int, float))
                ):
                    self._last_position = (float(x), float(y), float(z))

        # Update behavior engine context
        context_updates = {
            "current_position": self._last_position,
            "last_event": self._last_event,
        }

        # Check for emergency conditions
        if message_data.service == "events":
            event_type = (
                message_data.response.get("event") if message_data.response else None
            )
            if event_type == "pillager_attack":
                context_updates["pillager_attack"] = True
                context_updates["pillager_data"] = message_data.response
            elif event_type == "player_detected":
                context_updates["player_detected"] = True
                context_updates["player_data"] = message_data.response
            elif event_type == "low_health":
                context_updates["low_health"] = True
                context_updates["health_data"] = message_data.response

        self.behavior_engine.update_context(context_updates)

    def _send_mqtt_message(self, message: str) -> None:
        """Send MQTT message"""
        print(f"[mqtt] → {self.topic_cmd}: {message}")
        self.mqtt_client.publish(self.topic_cmd, message, qos=0, retain=False)

    def _get_current_position(self) -> Tuple[float, float, float]:
        """Get current bot position"""
        return self._last_position or (0.0, 0.0, 0.0)

    def connect(self) -> None:
        """Connect to MQTT broker"""
        broker = self.config.get("broker", "127.0.0.1")
        port = self.config.get("port", 1883)

        self.mqtt_client.connect(broker, port, keepalive=60)
        self.mqtt_client.loop_start()

        # Wait for connection
        print(f"[mqtt] Connecting to {broker}:{port}...")
        timeout = 10
        start_time = time.time()
        while not self._mqtt_connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self._mqtt_connected:
            raise Exception(
                f"Failed to connect to MQTT broker within {timeout} seconds"
            )

        print(f"[mqtt] Connection established successfully")

    def start(self) -> None:
        """Start the bot"""
        print(f"[bot] Starting modular bot client")

        # Set correlation ID for this session
        correlation_id = str(uuid.uuid4())
        self.pattern_engine.set_correlation_id(correlation_id)

        # Start behavior engine
        self.behavior_engine.start()

        # Queue farming behavior if waypoints are configured
        if self.config.get("waypoints"):
            farming_behavior = None
            for behavior in self.behavior_engine.behaviors:
                if behavior.name == "farming":
                    farming_behavior = behavior
                    break

            if farming_behavior:
                self.behavior_engine.queue_behavior(farming_behavior)
                print(f"[bot] Queued farming behavior")

        self.running = True
        print(f"[bot] Bot started successfully")

    def stop(self) -> None:
        """Stop the bot"""
        print(f"[bot] Stopping modular bot client")

        self.running = False
        self.behavior_engine.stop()

        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

        print(f"[bot] Bot stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            "running": self.running,
            "mqtt_connected": self._mqtt_connected,
            "current_position": self._last_position,
            "behavior_engine": self.behavior_engine.get_status(),
        }

    def run(self) -> int:
        """Run the bot (main execution loop)"""
        try:
            self.connect()
            self.start()

            # Keep running until interrupted
            while self.running:
                time.sleep(1)

                # Print status periodically
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    status = self.get_status()
                    print(f"[bot] Status: {status}")

            return 0

        except KeyboardInterrupt:
            print(f"\n[bot] Interrupted by user")
            return 130
        except Exception as e:
            print(f"[bot] Error: {e}")
            return 1
        finally:
            self.stop()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Modular Minecraft Bot Client")
    parser.add_argument("config", help="Path to YAML configuration file")
    args = parser.parse_args()

    try:
        client = ModularBotClient(args.config)
        return client.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
