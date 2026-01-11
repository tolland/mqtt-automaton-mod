import asyncio
import os
import sys
import threading
import time
from typing import Any

import yaml
from paho.mqtt import client as mqtt
from rich.pretty import pprint

from mqttbot import MessageData
from mqttbot.core.config_parser import ConfigParser
from mqttbot.core.context import Context
from mqttbot.core.scheduler import Scheduler
from mqttbot.core.task_thread import TaskThread
from mqttbot.core.thread_config import ThreadConfig
from mqttbot.models.settings import Settings
from mqttbot.state.baritone.baritone_module import BaritoneModule
from mqttbot.state.baritone.service import BaritoneService
from mqttbot.state.blackboard import TypedBlackboard
from mqttbot.state.date_time_module import DateTimeModule
from mqttbot.state.inventory_module import InventoryModule
from mqttbot.state.position_module import PositionModule
from mqttbot.state.wurst_module import WurstModule
from mqttbot.tasks.goto_task import GotoTask
from mqttbot.tasks.task import Task

"""
Modular bot client using the new behavior-based architecture
"""

# Add scripts directory to Python path
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


def _load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class ModularBotClient:
    """
    Modular bot client that uses behavior-based architecture.

    This client:
    - Manages MQTT communication
    - Orchestrates behaviors through the behavior engine
    - Handles events and context updates
    - Provides a clean interface for bot operations
    """

    def __init__(self, settings: Settings, config_path: str):
        """Initialize the modular bot client
        
        Args:
            settings: Settings object containing MQTT and connection configuration
            config_path: Path to YAML config file containing waypoints, patterns, and behaviors
        """
        self.settings = settings
        self.config = _load_config(config_path)
        self.mqtt_client = None
        self.running = False

        # Set Task log level from settings
        Task.set_log_level(settings.log_level)

        # MQTT state
        self._mqtt_connected = False
        self._last_position = None
        self._last_event = None
        self._lock = threading.Lock()

        # Initialize components
        self._setup_mqtt()

        # Now with type safety, you can do:
        self.blackboard = TypedBlackboard()
        self.blackboard.register_module("baritone", BaritoneModule())
        self.blackboard.register_module("events", DateTimeModule())
        self.blackboard.register_module("inventory", InventoryModule())
        self.blackboard.register_module("position", PositionModule())
        self.blackboard.register_module("wurst", WurstModule())

        self.ctx = Context(** {
            "message_sender": self.send_mqtt_message,
            "blackboard": self.blackboard,
            "baritone_service": None
        })

        self.baritone_service = BaritoneService(self.ctx)
        self.ctx.baritone_service = self.baritone_service

        self._scheduler = Scheduler()

    def _setup_mqtt(self) -> None:
        """Setup MQTT client using Settings"""
        self.mqtt_client = mqtt.Client(client_id=f"modular-bot-{int(time.time())}")
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

        # Store topic information from Settings
        self.topic_cmd = self.settings.topic_cmd
        self.topic_reply = self.settings.topic_reply
        self.topic_pos = self.settings.topic_pos

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

        print(f"[mqtt] < {self.topic_cmd}: {payload}")

        try:
            # Parse as structured MessageData
            message_data = MessageData.from_json(payload)
            if message_data:
                self._process_message(message_data)
        except Exception as e:
            print(f"[mqtt] Error processing message: {e}")
            raise

    def _process_message(self, message_data):
        if message_data.service == "baritone":
            self.baritone_service.handle_response(message_data)
        else:
            self.blackboard.emit_event(message_data.service, message_data)

    def _send_mqtt_message(self, message: str) -> None:
        """Send MQTT message"""
        print(f"[mqtt] → {self.topic_cmd}: {message}")
        self.mqtt_client.publish(self.topic_cmd, message, qos=0, retain=False)

    def send_mqtt_message(self, message: MessageData) -> None:
        """Public method to send MQTT message"""
        self._send_mqtt_message(message.to_json())

    def connect(self) -> None:
        """Connect to MQTT broker using Settings"""
        self.mqtt_client.connect(self.settings.broker, self.settings.port, keepalive=60)
        self.mqtt_client.loop_start()

        # Wait for connection
        print(f"[mqtt] Connecting to {self.settings.broker}:{self.settings.port}...")
        timeout = 10
        start_time = time.time()
        while not self._mqtt_connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self._mqtt_connected:
            raise Exception(
                f"Failed to connect to MQTT broker within {timeout} seconds"
            )

        print(f"[mqtt] Connection established successfully")

    def stop(self) -> None:
        """Stop the bot"""
        print(f"[bot] Stopping modular bot client")

        self.running = False

        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

        print(f"[bot] Bot stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current bot status"""
        return {
            "running": self.running,
            "mqtt_connected": self._mqtt_connected,
            "current_position": self._last_position,
        }

    def start(self) -> None:
        """Start the bot by initializing threads from config"""
        print(f"[bot] Starting modular bot client")

        # Parse thread configurations
        thread_configs = ConfigParser.from_yaml(self.config)
        print(f"[bot] Loaded {len(thread_configs)} thread configuration(s)")

        # Create and register threads
        for thread_config in thread_configs:
            thread = self._create_thread_from_config(thread_config)
            self._scheduler.register_thread(thread)
            print(f"[bot] Registered thread: {thread_config.thread_id}")

        self.running = True
        print(f"[bot] Bot started successfully")

    def _create_thread_from_config(self, config: ThreadConfig) -> TaskThread:
        """Create a TaskThread from a ThreadConfig"""

        # Create callbacks for on_suspend and on_resume (if configured)
        async def on_suspend(thread: TaskThread) -> None:
            # Execute suspend tasks
            for task_spec in config.on_suspend_tasks:
                service = task_spec.get("service")
                method = task_spec.get("method")
                params = task_spec.get("params", {})
                print(f"[thread] {config.thread_id} suspending: {service}.{method}")
                # TODO: Route to appropriate service

        async def on_resume(thread: TaskThread, ctx) -> None:
            # Execute resume tasks
            for task_spec in config.on_resume_tasks:
                service = task_spec.get("service")
                method = task_spec.get("method")
                params = task_spec.get("params", {})
                print(f"[thread] {config.thread_id} resuming: {service}.{method}")
                # TODO: Route to appropriate service

        thread = TaskThread(
            thread_id=config.thread_id,
            priority=config.priority,
            on_suspend=on_suspend,
            on_resume=on_resume,
        )

        # Enqueue tasks for each waypoint
        for waypoint in config.waypoints:
            # Create goto task
            goto_task = GotoTask(waypoint.x, waypoint.y, waypoint.z)
            goto_task.service_config = config.services.get("baritone")
            thread.enqueue_task(goto_task)

            # TODO: Create pattern execution tasks for each pattern
            # for pattern_name in waypoint.patterns:
            #     pattern_task = PatternTask(pattern_name, self.patterns)
            #     thread.enqueue_task(pattern_task)

            # Add dwell if configured
            if waypoint.dwell_seconds > 0:
                # TODO: Create DwellTask
                pass

        # Store config in thread metadata for tasks to access
        thread.metadata = config

        return thread

    async def run(self) -> int:
        """Run the bot (main execution loop)"""
        try:
            self.connect()
            self.start()

            while self.running:
                await asyncio.sleep(1)

                pprint(self._scheduler)
                all_complete = await self._scheduler.step(self.ctx)

                # if all_complete:
                #     print(f"[bot] All tasks completed, exiting")
                #     self.running = False
                #     break

                # Print status periodically
                if int(time.time()) % 30 == 0:
                    status = self.get_status()
                    print(f"[bot] Status: {status}")

            return 0

        except KeyboardInterrupt:
            print(f"\n[bot] Interrupted by user")
            return 130
        except Exception as e:
            print(f"[bot] Error: {e}")
            raise
        finally:
            self.stop()
