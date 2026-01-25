import asyncio
import threading
import time
import uuid
from asyncio import Queue
from typing import Any, Optional

from loguru import logger
from rich import inspect
from rich.repr import rich_repr

from mqttbot import ServiceMessage
from mqttbot.config.model.full_config import FullConfig
from mqttbot.config.model.pattern.pattern_config import PatternsConfig
from mqttbot.config.model.thread.threads_config import ThreadConfig
from mqttbot.config.settings.settings import Settings
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.core.events.event_manager_helper import EventManagerHelper
from mqttbot.core.services.bot_service import BotService
from mqttbot.core.state.baritone.baritone_module import BaritoneModule
from mqttbot.core.state.baritone.utils import dump_baritone_state
from mqttbot.core.state.blackboard import TypedBlackboard
from mqttbot.core.state.events.events_module import EventsModule
from mqttbot.core.state.wurst_module import WurstModule
from mqttbot.core.threads import scheduler
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.thread_factory import ThreadFactory
from mqttbot.mqtt.mqtt_client import MqttBotClient
from mqttbot.utils.loader import _load_config

"""
Modular bot client using the new behavior-based architecture
"""


@rich_repr
class ModularBotClient:
    def __init__(self, settings: Settings, config_path: str):
        """Initialize the modular bot client

        Args:
            settings: Settings object containing MQTT and connection configuration
            config_path: Path to YAML config file containing waypoints, patterns, and behaviors
        """
        self.event_manager = None
        self._scheduler = None
        self.threads = None
        self.thread_configs: Optional[ThreadConfig] = None
        self.patterns_configs: Optional[PatternsConfig] = None
        self.settings = settings
        self.config_path = config_path
        self.config = _load_config(config_path)
        self._event_queue: Queue | None = None
        self.running = False
        self._shutdown_requested = False

        # State
        self._last_position = None
        self._last_event = None
        self._lock = threading.Lock()

        # Initialize MQTT client with message callback
        self.mqtt = MqttBotClient(settings, )
        self.mqtt.register_message_callback(
            self._handle_mqtt_message
        )

        # Now with type safety, you can do:
        self.blackboard = TypedBlackboard()
        self.blackboard.register_module("baritone", BaritoneModule())
        self.blackboard.register_module("wurst", WurstModule())
        self.blackboard.register_module("events", EventsModule())

        self.blackboard.subscribe("baritone", dump_baritone_state)

        self.ctx = Context(
            **{
                "message_sender": self.send_mqtt_message,
                "blackboard": self.blackboard,
                "mqtt": self.mqtt,
            }
        )

        self.bot_service = BotService(self.ctx)
        self.ctx.bot_service = self.bot_service

        # Log initialization summary
        logger.debug(
            f"ModularBotClient initialized: broker={settings.broker}:{settings.port}, client_id={settings.client_id}")

    async def connect(self) -> None:
        """Connect to MQTT broker"""
        self.mqtt.connect()

        logger.debug("[bot] Waiting for mod to come online...")
        available = await self.mqtt.device_monitor.wait_for_available(timeout=30.0)
        if not available:
            raise TimeoutError("Mod did not come online")

        logger.debug("[bot] Waiting for mod to come ready...")
        ready = await self.mqtt.device_monitor.wait_for_ready(timeout=30.0)
        if not ready:
            raise TimeoutError("Mod did not become ready")

        logger.info(f"Mod is ready! State: {self.mqtt.device_monitor.readiness.state}")

    def exit(self):
        """Exit the bot gracefully"""
        logger.info("Exit requested - will shutdown gracefully")
        self._shutdown_requested = True
        self.send_mqtt_message(
            ServiceMessage(
                **{
                    "service": "mqttcore",
                    "method": "exit",
                    "request_id": str(uuid.uuid4()),
                    "params": {},
                    "timestamp": time.time(),
                }
            )
        )

    def stop(self) -> None:
        """Stop the bot"""
        logger.info("Stopping modular bot client")
        self._scheduler._publish_state(self.ctx)

        self.running = False
        self.mqtt.disconnect()

        logger.info("Bot stopped")

    def get_status(self) -> dict[str, Any]:
        """Get current bot status"""
        return {
            "running": self.running,
            "mqtt_connected": self.mqtt.is_connected,
            "current_position": self._last_position,
        }

    def configure(self) -> None:
        """Start the bot by initializing threads from config"""
        logger.info("Configuring modular bot client")

        full_config = FullConfig.model_validate(self.config)
        self.patterns_configs = full_config.pattern_config
        logger.info(f"Loaded {len(self.patterns_configs.patterns)} patterns configuration(s)")

        # Parse thread configurations
        # self.thread_configs = PatternThreadConfigParser.from_yaml(self.config)
        self.thread_configs = full_config.thread_config
        logger.info(f"Loaded {len(self.thread_configs.threads)} thread configuration(s)")

        task_compiler = TaskCompiler(self.patterns_configs)
        thread_factory = ThreadFactory(task_compiler)
        self.threads = []
        for thread_config in self.thread_configs.threads:
            thread = thread_factory.create_thread(thread_config)
            self.threads.append(thread)

        inspect(self.threads[0], title="Configured Threads")

        # self.event_manager = EventManager(self.config.get("event_handlers", {}))

    def start(self) -> None:

        self.event_manager.start()
        self._scheduler = scheduler.create()

        """Start the bot by registering threads with the scheduler"""
        for thread_config, thread in zip(self.thread_configs, self.threads, strict=False):
            self._scheduler.register_thread(thread)
            logger.debug(f"Registered thread: {thread_config.thread_id}")

        self.running = True
        logger.info("Bot started successfully")

    async def run(self) -> int:
        """Run the bot (main execution loop)"""
        self._event_queue = asyncio.Queue(maxsize=100)

        try:
            await self.connect()

            self.configure()
            self.start()

            while self.running:
                # Check for shutdown request
                if self._shutdown_requested:
                    logger.info("Processing shutdown request")
                    await self._scheduler.shutdown(self.ctx)
                    self.running = False
                    self.stop()
                    break

                await self._process_event_queue()

                await asyncio.sleep(0.1)

                all_complete = await self._scheduler.step(self.ctx)

                if all_complete:
                    logger.info("All tasks completed, exiting")
                    self.running = False
                    break

                # Log status periodically
                if int(time.time()) % 30 == 0:
                    status = self.get_status()
                    logger.debug(f"Status: {status}")

            return 0

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 130
        # except Exception as e:
        #     logger.error(f"Bot error: {e}")
        #     raise
        finally:
            self.stop()


    def _handle_mqtt_message(self, topic: str, payload: str) -> None:
        """Handle incoming MQTT message payload turn into ServiceMessage

        Args:
            topic: MQTT topic the message was received on
            payload: Message payload string
        """
        try:
            # Parse as structured ServiceMessage
            message_data = ServiceMessage.from_json(payload)
            if message_data:
                self._process_message(topic, message_data)
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            raise

    def _process_message(self, topic: str, message_data):
        """
        Distribute incoming message based on topic routing

        Args:
            topic: MQTT topic the message was received on
            message_data: Parsed ServiceMessage object
        """
        # Route reply messages to bot_service for request/response tracking
        if topic.endswith("reply"):
            self.bot_service.handle_response(message_data)

        # Route baritone state messages to blackboard (even if on topic_reply)
        if message_data.service == "baritone" and message_data.method == "state":
            self.blackboard.emit_event(message_data.service, message_data)

        self.blackboard.emit_event(message_data.service, message_data)

        # Add reply messages to async queue as well (for event processing)
        # This allows reply messages to also trigger event handlers if needed
        if topic.endswith("reply") or topic.endswith("events"):
            if self._event_queue:
                try:
                    self._event_queue.put_nowait(message_data)
                except asyncio.QueueFull:
                    logger.warning(
                        f"Event queue full, dropping {message_data.service}:{message_data.method}"
                    )
                    raise ValueError("Event queue full")

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
                self._scheduler.enqueue_thread(thread, singleton=True)

    def send_mqtt_message(self, message: ServiceMessage) -> None:
        """Public method to send MQTT message"""
        topic = f"mqttbot/{self.settings.client_id}/command"
        self.mqtt.send(topic, message.to_json())


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
