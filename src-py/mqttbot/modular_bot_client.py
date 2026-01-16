import asyncio
import threading
import time
import uuid
from asyncio import Queue
from typing import Any, Optional

import yaml
from rich import inspect, print as rprint
from rich.pretty import pprint
from rich import print
from rich.repr import rich_repr

from mqttbot import MessageData
from mqttbot.config.threads.thread_config_parser import ThreadConfigParser
from mqttbot.core.context import Context
from mqttbot.core.events.event_manager import EventManager
from mqttbot.core.events.event_manager_helper import EventManagerHelper
from mqttbot.core.patterns.patterns_config_parser import PatternsConfigParser
from mqttbot.core.scheduler import Scheduler
from mqttbot.core.services.bot_service import BotService
from mqttbot.core.state.blackboard import TypedBlackboard
from mqttbot.core.state.events.events_module import EventsModule
from mqttbot.core.state.wurst_module import WurstModule
from mqttbot.core.threads.thread_helper import ThreadHelper
from mqttbot.model.settings.settings import Settings
from mqttbot.mqtt.mqtt_client import MqttClient

"""
Modular bot client using the new behavior-based architecture
"""


def _load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@rich_repr
class ModularBotClient:
    def __init__(self, settings: Settings, config_path: str):
        """Initialize the modular bot client

        Args:
            settings: Settings object containing MQTT and connection configuration
            config_path: Path to YAML config file containing waypoints, patterns, and behaviors
        """
        self.threads = None
        self.thread_configs = None
        self.patterns_configs = None
        self.settings = settings
        self.config_path = config_path
        self.config = _load_config(config_path)
        self._event_queue: Optional[Queue] = None
        self.running = False
        self.event_manager = EventManager(self.config.get("event_handlers", {}))

        # State
        self._last_position = None
        self._last_event = None
        self._lock = threading.Lock()

        # Initialize MQTT client with message callback
        self.mqtt = MqttClient(settings, message_callback=self._handle_mqtt_message)

        # Now with type safety, you can do:
        self.blackboard = TypedBlackboard()
        # self.blackboard.register_module("baritone", BaritoneModule())
        # self.blackboard.register_module("events", DateTimeModule())
        # self.blackboard.register_module("inventory", InventoryModule())
        # self.blackboard.register_module("position", PositionModule())
        self.blackboard.register_module("wurst", WurstModule())
        self.blackboard.register_module("events", EventsModule())

        self.ctx = Context(
            **{
                "message_sender": self.send_mqtt_message,
                "blackboard": self.blackboard,
                "bot_service": None,
            }
        )

        self.bot_service = BotService(self.ctx)
        self.ctx.bot_service = self.bot_service

        self._scheduler = Scheduler()

        # Print initialization summary
        pprint(self)

    def _handle_mqtt_message(self, payload: str) -> None:
        """Handle incoming MQTT message payload turn into MessageData"""
        try:
            # Parse as structured MessageData
            message_data = MessageData.from_json(payload)
            if message_data:
                self._process_message(message_data)
        except Exception as e:
            print(f"[mqtt] Error processing message: {e}")
            raise

    def _process_message(self, message_data):
        """
        Distribute incoming message to bot service and event manager
        :param message_data:
        :type message_data:
        :return:
        :rtype:
        """

        self.bot_service.handle_response(message_data)

        self.blackboard.emit_event(message_data.service, message_data)

        if self._event_queue:
            try:
                self._event_queue.put_nowait(message_data)
            except asyncio.QueueFull:
                print(
                    f"[mqtt] Event queue full, dropping {message_data.service}:{message_data.method}"
                )

    async def _handle_event_async(self, message_data):
        """Handle a single event"""
        handler_config = self.event_manager.get_handler_config(
            message_data.service, message_data.method
        )

        if handler_config:
            thread = await EventManagerHelper._build_thread_from_config(
                f"{message_data.service}_{message_data.method}", handler_config, message_data
            )

            if thread:
                inspect(thread)
                self._scheduler.enqueue_thread(thread, singleton=True)

    def send_mqtt_message(self, message: MessageData) -> None:
        """Public method to send MQTT message"""
        self.mqtt.send(message.to_json())

    def connect(self) -> None:
        """Connect to MQTT broker"""
        self.mqtt.connect()

    def exit(self):
        """Exit the bot gracefully"""
        self.send_mqtt_message(
            MessageData(
                **{
                    "service": "mqttcore",
                    "method": "exit",
                    "request_id": str(uuid.uuid4()),
                    "params": {},
                    "timestamp": time.time(),
                }
            )
        )
        # self._scheduler.stop()
        self.stop()

    def stop(self) -> None:
        """Stop the bot"""
        print(f"[bot] Stopping modular bot client")

        self.running = False
        self.mqtt.disconnect()

        print(f"[bot] Bot stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current bot status"""
        return {
            "running": self.running,
            "mqtt_connected": self.mqtt.is_connected,
            "current_position": self._last_position,
        }

    def configure(self) -> None:
        """Start the bot by initializing threads from config"""
        print(f"[bot] Starting modular bot client")

        self.patterns_configs = PatternsConfigParser.from_yaml(self.config)
        print(f"[bot] Loaded {len(self.patterns_configs)} patterns configuration(s)")
        pprint(self.patterns_configs)

        # Parse thread configurations
        self.thread_configs = ThreadConfigParser.from_yaml(self.config)
        print(f"[bot] Loaded {len(self.thread_configs)} thread configuration(s)")

        # Print thread configurations
        for thread_config in self.thread_configs:
            pprint(thread_config)

        self.threads = []
        for thread_config in self.thread_configs:
            thread = ThreadHelper._create_thread_from_thread_config(
                thread_config,
                self.patterns_configs)
            self.threads.append(thread)
            inspect(thread)
            print(thread)


    def start(self) -> None:
        """Start the bot by registering threads with the scheduler"""
        for thread_config, thread in zip(self.thread_configs, self.threads):
            self._scheduler.register_thread(thread)
            print(f"[bot] Registered thread: {thread_config.thread_id}")

        self.running = True
        print(f"[bot] Bot started successfully")

    async def run(self) -> int:
        """Run the bot (main execution loop)"""
        self._event_queue = asyncio.Queue(maxsize=100)

        try:
            self.connect()
            self.configure()
            self.start()

            while self.running:
                await self._process_event_queue()

                await asyncio.sleep(0.1)

                all_complete = await self._scheduler.step(self.ctx)

                if all_complete:
                    print(f"[bot] All tasks completed, exiting")
                    self.running = False
                    break

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

    async def _process_event_queue(self) -> None:
        """Drain event queue and process all pending events"""
        while not self._event_queue.empty():
            try:
                message_data = self._event_queue.get_nowait()
                await self._handle_event_async(message_data)
            except asyncio.QueueEmpty:
                break

    def __rich_repr__(self):
        """Rich representation of the ModularBotClient"""
        yield "config_path", self.config_path
        yield "running", self.running
        yield "mqtt_connected", self.mqtt.is_connected
        if hasattr(self.mqtt, "topic_cmd") and self.mqtt.topic_cmd:
            yield "topic_cmd", self.mqtt.topic_cmd
        if hasattr(self.mqtt, "topic_reply") and self.mqtt.topic_reply:
            yield "topic_reply", self.mqtt.topic_reply
        if hasattr(self.mqtt, "topic_pos") and self.mqtt.topic_pos:
            yield "topic_pos", self.mqtt.topic_pos
        if hasattr(self.blackboard, "_modules") and self.blackboard._modules:
            yield "blackboard_modules", list(self.blackboard._modules.keys())
        if hasattr(self._scheduler, "_threads"):
            yield "scheduler_threads", len(self._scheduler._threads)
        if self.thread_configs is not None:
            yield "thread_configs", len(self.thread_configs)
        if self.patterns_configs is not None:
            yield "patterns_configs", len(self.patterns_configs)
        yield "event_handlers", len(self.event_manager.handlers)

    def __repr__(self) -> str:
        """Return a rich representation of the ModularBotClient"""
        return (
            f"ModularBotClient(\n"
            f"  settings={self.settings!r},\n"
            f"  config_path={self.config_path!r},\n"
            f"  running={self.running},\n"
            f"  mqtt_connected={self.mqtt.is_connected},\n"
            f"  topic_cmd={self.mqtt.topic_cmd!r},\n"
            f"  topic_reply={self.mqtt.topic_reply!r},\n"
            f"  topic_pos={self.mqtt.topic_pos!r},\n"
            f"  blackboard_modules={list(self.blackboard._modules.keys()) if hasattr(self.blackboard, '_modules') else 'N/A'},\n"
            f"  scheduler_threads={len(self._scheduler._threads) if hasattr(self._scheduler, '_threads') else 'N/A'}\n"
            f")"
            f"  event_manager={self.event_manager!r},\n"
            f"  event_manager_handlers={self.event_manager.handlers!r},\n"
            f"  event_manager_handlers_count={len(self.event_manager.handlers)},\n"
        )
