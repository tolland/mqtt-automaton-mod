"""
MQTT Device Presence Library

Generic library for detecting device liveness/readiness following Home Assistant
MQTT discovery pattern.

Usage:
    monitor = DevicePresenceMonitor(device_id="SandyFire", mqtt_client=client)

    # Wait for device to be available and ready
    await monitor.wait_for_available(timeout=30.0)
    await monitor.wait_for_ready(timeout=30.0)

    # Subscribe to state changes
    monitor.on_availability_change(lambda available: print(f"Available: {available}"))
    monitor.on_readiness_change(lambda ready: print(f"Ready: {ready}"))
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class AvailabilityState(Enum):
    """Device availability (liveness)"""
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass
class DeviceConfig:
    """Device configuration and capabilities"""
    device_id: str
    name: str
    model: str
    manufacturer: str
    sw_version: str
    services: list[str]
    capabilities: Dict[str, Any]
    topics: Dict[str, str]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "DeviceConfig":
        """Parse from MQTT config message"""
        device = data.get("device", {})
        identifiers = device.get("identifiers", [])
        device_id = identifiers[0] if identifiers else "unknown"

        return cls(
            device_id=device_id,
            name=device.get("name", "Unknown"),
            model=device.get("model", "Unknown"),
            manufacturer=device.get("manufacturer", "Unknown"),
            sw_version=device.get("sw_version", "Unknown"),
            services=data.get("services", []),
            capabilities=data.get("capabilities", {}),
            topics=data.get("topics", {})
        )


@dataclass
class ReadinessState:
    """Device readiness (operational state)"""
    ready: bool
    state: str
    can_accept_tasks: bool
    reason: str
    additional_data: Dict[str, Any]
    timestamp: datetime

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ReadinessState":
        """Parse from MQTT readiness message"""
        return cls(
            ready=data.get("ready", False),
            state=data.get("state", "UNKNOWN"),
            can_accept_tasks=data.get("can_accept_tasks", False),
            reason=data.get("reason", ""),
            additional_data={k: v for k, v in data.items()
                           if k not in ["ready", "state", "can_accept_tasks", "reason", "timestamp"]},
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        )


class HeartbeatMonitor:
    """Monitor device heartbeat for fast liveness detection"""

    def __init__(self, timeout: float = 1.5):
        """
        Args:
            timeout: Seconds without heartbeat before considering device dead
        """
        self._timeout = timeout
        self._last_heartbeat: Optional[float] = None
        self._last_sequence: Optional[int] = None
        self._is_alive = False
        self._callbacks: list[Callable[[bool], None]] = []
        self._monitor_task: Optional[asyncio.Task] = None

    def on_heartbeat(self, data: Dict[str, Any]):
        """Called when heartbeat message received"""
        self._last_heartbeat = time.time()
        self._last_sequence = data.get("sequence")

        if not self._is_alive:
            self._is_alive = True
            self._notify_callbacks(True)

    def on_state_change(self, callback: Callable[[bool], None]):
        """Subscribe to alive/dead transitions"""
        self._callbacks.append(callback)

    async def start_monitoring(self):
        """Start background monitoring task"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop background monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_loop(self):
        """Background task to detect timeout"""
        while True:
            await asyncio.sleep(0.1)  # Check every 100ms

            if self._last_heartbeat is None:
                continue

            elapsed = time.time() - self._last_heartbeat
            if elapsed > self._timeout and self._is_alive:
                self._is_alive = False
                self._notify_callbacks(False)
                logger.warning(f"Heartbeat timeout ({elapsed:.2f}s > {self._timeout}s)")

    def _notify_callbacks(self, is_alive: bool):
        """Notify all callbacks of state change"""
        for callback in self._callbacks:
            try:
                callback(is_alive)
            except Exception as e:
                logger.error(f"Error in heartbeat callback: {e}")

    @property
    def is_alive(self) -> bool:
        """Check if device is alive based on heartbeat"""
        return self._is_alive


class DevicePresenceMonitor:
    """
    Monitor MQTT device presence (availability, readiness, heartbeat).

    Follows Home Assistant MQTT discovery pattern.
    """

    def __init__(self, device_id: str, mqtt_client, base_topic: str = "mqttbot"):
        """
        Args:
            device_id: Unique device identifier (e.g., player name)
            mqtt_client: Paho MQTT client instance
            base_topic: Base topic prefix (default: "mqttbot")
        """
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.base_topic = f"{base_topic}/{device_id}"

        # Topics
        self.availability_topic = f"{self.base_topic}/availability"
        self.config_topic = f"{self.base_topic}/config"
        self.readiness_topic = f"{self.base_topic}/readiness"
        self.state_topic = f"{self.base_topic}/state"
        self.heartbeat_topic = f"{self.base_topic}/heartbeat"

        # State
        self._availability: AvailabilityState = AvailabilityState.UNKNOWN
        self._config: Optional[DeviceConfig] = None
        self._readiness: Optional[ReadinessState] = None
        self._heartbeat_monitor = HeartbeatMonitor(timeout=1.5)

        # Events
        self._availability_event = asyncio.Event()
        self._config_event = asyncio.Event()
        self._readiness_event = asyncio.Event()

        # Callbacks
        self._availability_callbacks: list[Callable[[AvailabilityState], None]] = []
        self._readiness_callbacks: list[Callable[[ReadinessState], None]] = []
        self._config_callbacks: list[Callable[[DeviceConfig], None]] = []

        # Subscribe to heartbeat state changes
        self._heartbeat_monitor.on_state_change(self._on_heartbeat_state_change)

    def subscribe(self):
        """Subscribe to all device topics"""
        topics = [
            (self.availability_topic, 1),  # QoS 1
            (self.config_topic, 1),
            (self.readiness_topic, 1),
            (self.state_topic, 0),
            (self.heartbeat_topic, 0),
        ]

        for topic, qos in topics:
            self.mqtt_client.subscribe(topic, qos=qos)
            logger.debug(f"Subscribed to {topic} (QoS {qos})")

        # Register message callback
        self.mqtt_client.message_callback_add(self.availability_topic, self._on_availability_message)
        self.mqtt_client.message_callback_add(self.config_topic, self._on_config_message)
        self.mqtt_client.message_callback_add(self.readiness_topic, self._on_readiness_message)
        self.mqtt_client.message_callback_add(self.heartbeat_topic, self._on_heartbeat_message)

    def unsubscribe(self):
        """Unsubscribe from all device topics"""
        topics = [
            self.availability_topic,
            self.config_topic,
            self.readiness_topic,
            self.state_topic,
            self.heartbeat_topic,
        ]

        for topic in topics:
            self.mqtt_client.unsubscribe(topic)
            self.mqtt_client.message_callback_remove(topic)

    # Message handlers

    def _on_availability_message(self, client, userdata, msg):
        """Handle availability (online/offline) message"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            state_str = data.get("state", "unknown")

            old_state = self._availability
            self._availability = AvailabilityState(state_str)

            if old_state != self._availability:
                logger.info(f"[{self.device_id}] Availability: {old_state.value} → {self._availability.value}")
                self._availability_event.set()
                self._notify_availability_callbacks()
        except Exception as e:
            logger.error(f"Error parsing availability message: {e}")

    def _on_config_message(self, client, userdata, msg):
        """Handle device config message"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            self._config = DeviceConfig.from_json(data)

            logger.info(f"[{self.device_id}] Config received: {len(self._config.services)} services, v{self._config.sw_version}")
            self._config_event.set()
            self._notify_config_callbacks()
        except Exception as e:
            logger.error(f"Error parsing config message: {e}")

    def _on_readiness_message(self, client, userdata, msg):
        """Handle readiness state message"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            old_readiness = self._readiness
            self._readiness = ReadinessState.from_json(data)

            # Log if changed
            if old_readiness is None or old_readiness.state != self._readiness.state:
                logger.info(f"[{self.device_id}] Readiness: {self._readiness.state} "
                          f"(can_accept_tasks={self._readiness.can_accept_tasks}, reason={self._readiness.reason})")

            self._readiness_event.set()
            self._notify_readiness_callbacks()
        except Exception as e:
            logger.error(f"Error parsing readiness message: {e}")

    def _on_heartbeat_message(self, client, userdata, msg):
        """Handle heartbeat message"""
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            self._heartbeat_monitor.on_heartbeat(data)
        except Exception as e:
            logger.error(f"Error parsing heartbeat message: {e}")

    def _on_heartbeat_state_change(self, is_alive: bool):
        """Called when heartbeat monitor detects alive/dead transition"""
        if is_alive:
            logger.info(f"[{self.device_id}] Heartbeat detected - device alive")
        else:
            logger.warning(f"[{self.device_id}] Heartbeat timeout - device may be dead")

    # Callbacks

    def on_availability_change(self, callback: Callable[[AvailabilityState], None]):
        """Subscribe to availability changes"""
        self._availability_callbacks.append(callback)

    def on_readiness_change(self, callback: Callable[[ReadinessState], None]):
        """Subscribe to readiness changes"""
        self._readiness_callbacks.append(callback)

    def on_config_change(self, callback: Callable[[DeviceConfig], None]):
        """Subscribe to config changes"""
        self._config_callbacks.append(callback)

    def _notify_availability_callbacks(self):
        for callback in self._availability_callbacks:
            try:
                callback(self._availability)
            except Exception as e:
                logger.error(f"Error in availability callback: {e}")

    def _notify_readiness_callbacks(self):
        if self._readiness:
            for callback in self._readiness_callbacks:
                try:
                    callback(self._readiness)
                except Exception as e:
                    logger.error(f"Error in readiness callback: {e}")

    def _notify_config_callbacks(self):
        if self._config:
            for callback in self._config_callbacks:
                try:
                    callback(self._config)
                except Exception as e:
                    logger.error(f"Error in config callback: {e}")

    # Wait methods

    async def wait_for_available(self, timeout: float = 30.0) -> bool:
        """
        Wait for device to be available (online).

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if device became available, False if timeout
        """
        if self._availability == AvailabilityState.ONLINE:
            return True

        logger.info(f"[{self.device_id}] Waiting for device to be available...")

        try:
            await asyncio.wait_for(self._availability_event.wait(), timeout=timeout)
            return self._availability == AvailabilityState.ONLINE
        except asyncio.TimeoutError:
            logger.error(f"[{self.device_id}] Timeout waiting for availability after {timeout}s")
            return False

    async def wait_for_config(self, timeout: float = 30.0) -> Optional[DeviceConfig]:
        """
        Wait for device config to be received.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            DeviceConfig if received, None if timeout
        """
        if self._config is not None:
            return self._config

        logger.info(f"[{self.device_id}] Waiting for device config...")

        try:
            await asyncio.wait_for(self._config_event.wait(), timeout=timeout)
            return self._config
        except asyncio.TimeoutError:
            logger.error(f"[{self.device_id}] Timeout waiting for config after {timeout}s")
            return None

    async def wait_for_ready(self, timeout: float = 60.0) -> bool:
        """
        Wait for device to be ready (can_accept_tasks=True).

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if device became ready, False if timeout
        """
        if self._readiness and self._readiness.can_accept_tasks:
            return True

        logger.info(f"[{self.device_id}] Waiting for device to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                await asyncio.wait_for(self._readiness_event.wait(), timeout=1.0)
                if self._readiness and self._readiness.can_accept_tasks:
                    logger.info(f"[{self.device_id}] Device ready: {self._readiness.state}")
                    return True
                else:
                    # Got readiness update but not ready yet, keep waiting
                    self._readiness_event.clear()
            except asyncio.TimeoutError:
                # Check again
                continue

        logger.error(f"[{self.device_id}] Timeout waiting for ready state after {timeout}s")
        if self._readiness:
            logger.error(f"  Last state: {self._readiness.state} (can_accept_tasks={self._readiness.can_accept_tasks})")
        return False

    # Properties

    @property
    def is_available(self) -> bool:
        """Check if device is currently available (online)"""
        return self._availability == AvailabilityState.ONLINE

    @property
    def is_ready(self) -> bool:
        """Check if device is currently ready (can accept tasks)"""
        return self._readiness is not None and self._readiness.can_accept_tasks

    @property
    def availability(self) -> AvailabilityState:
        """Current availability state"""
        return self._availability

    @property
    def config(self) -> Optional[DeviceConfig]:
        """Current device config"""
        return self._config

    @property
    def readiness(self) -> Optional[ReadinessState]:
        """Current readiness state"""
        return self._readiness

    async def start_heartbeat_monitoring(self):
        """Start monitoring heartbeat for fast liveness detection"""
        await self._heartbeat_monitor.start_monitoring()

    async def stop_heartbeat_monitoring(self):
        """Stop monitoring heartbeat"""
        await self._heartbeat_monitor.stop_monitoring()
