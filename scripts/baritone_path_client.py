#!/usr/bin/env python3
import argparse
import json
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml  # pip install pyyaml
from paho.mqtt import client as mqtt  # pip install paho-mqtt

ARRIVE_KEYS = [("type", "arrived"), ("status", "reached")]


@dataclass
class MessageData:
    """Python equivalent of the Java MessageData class for structured MQTT communication"""

    service: str
    method: str
    request_id: str = None
    correlation_id: str = None
    params: Dict[str, Any] = None
    response: Dict[str, Any] = None
    identity: str = "python_client"
    message: str = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.params is None:
            self.params = {}
        if self.response is None:
            self.response = {}

    def to_json(self) -> str:
        """Convert to JSON string matching Java MessageData format"""
        data = {
            "service": self.service,
            "method": self.method,
            "requestId": self.request_id,
            "correlationId": self.correlation_id,
            "params": self.params,
            "response": self.response,
            "identity": self.identity,
            "message": self.message,
        }
        # Remove None values to keep JSON clean
        return json.dumps({k: v for k, v in data.items() if v is not None})

    @classmethod
    def from_json(cls, json_str: str) -> Optional["MessageData"]:
        """Parse JSON string into MessageData object"""
        try:
            data = json.loads(json_str)
            return cls(
                service=data.get("service"),
                method=data.get("method"),
                request_id=data.get("requestId"),
                correlation_id=data.get("correlationId"),
                params=data.get("params", {}),
                response=data.get("response", {}),
                identity=data.get("identity", "unknown"),
                message=data.get("message"),
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse MessageData from JSON: {e}", file=sys.stderr)
            return None


@dataclass
class Settings:
    broker: str
    port: int
    client_id: str
    expected_player_name: str  # Actual player name for reply subscription
    topic_cmd: str
    topic_reply: str
    topic_pos: str
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    cmd_tpl_name: str
    cmd_tpl_xyz: str
    services: Dict[str, Any] = None  # Service configuration (command types, timeouts)
    events: Dict[str, Any] = None  # Event handler configuration


class PathingClient:
    def __init__(
        self,
        settings: Settings,
        waypoints: List[Dict[str, Any]],
        patterns: Dict[str, List[str]],
    ):
        self.s = settings
        self.waypoints = waypoints
        self.patterns = patterns

        self._mqtt = mqtt.Client(client_id=f"pathctl-{int(time.time())}")
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_disconnect = self._on_disconnect

        self._arrived_event = threading.Event()
        self._last_event: Optional[Dict[str, Any]] = None
        self._last_pos: Optional[Tuple[float, float, float]] = None
        self._lock = threading.Lock()

        # Event handling state
        self._event_handler_active = False
        self._current_event_steps: List[Dict[str, Any]] = []
        self._current_step_index = 0
        self._step_completion_event = threading.Event()
        self._paused_waypoint_index: Optional[int] = None
        self._waypoint_processing_paused = (
            False  # Flag to pause waypoint processing during events
        )

        # Request tracking for step completion
        self._pending_requests = {}  # request_id -> (timestamp, service, method)
        self._correlation_id = None  # Current correlation ID for waypoint group

        # Lifecycle event completion tracking
        self._lifecycle_events = {}  # event_type -> threading.Event()

    # ---------- MQTT ----------
    def connect(self):
        self._mqtt.connect(self.s.broker, self.s.port, keepalive=60)
        self._mqtt.loop_start()

        # Wait for connection to be established
        print(f"[mqtt] connecting to {self.s.broker}:{self.s.port}...")
        timeout = 10
        start_time = time.time()
        while (
            not hasattr(self, "_mqtt_connected") and time.time() - start_time < timeout
        ):
            time.sleep(0.1)

        if not hasattr(self, "_mqtt_connected"):
            raise Exception(
                f"Failed to connect to MQTT broker within {timeout} seconds"
            )

        print(f"[mqtt] connection established successfully")

    def close(self):
        try:
            self._mqtt.loop_stop()
            self._mqtt.disconnect()
        except Exception:
            pass

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[mqtt] connect failed rc={rc}", file=sys.stderr)
            return
        print(f"[mqtt] connected → subscribing {self.s.topic_reply}")
        self._mqtt.subscribe(self.s.topic_reply, qos=0)
        # subscribe to optional periodic position pings if your mod publishes them
        self._mqtt.subscribe(self.s.topic_pos, qos=0)
        # Mark connection as established
        self._mqtt_connected = True

    def _on_disconnect(self, client, userdata, rc):
        print(f"[mqtt] disconnected rc={rc}")

    # ---------- Event handling ----------
    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace").strip()

        # Parse as structured MessageData
        message_data = MessageData.from_json(payload)
        if message_data and message_data.service in [
            "baritone",
            "events",
            "sleep",
            "warp",
            "commands",
            "wurst",
            "inventory",
        ]:
            data = self._extract_data_from_message(message_data)

            # Check if this is a response to a pending request
            if (
                message_data.request_id
                and message_data.request_id in self._pending_requests
            ):
                print(
                    f"[event] Received response for request {message_data.request_id}"
                )
                # Mark this request as completed
                del self._pending_requests[message_data.request_id]

            # Handle events from "events" service or "inventory" service
            if message_data.service == "events" or message_data.service == "inventory":
                self._handle_event(message_data, data)
                return  # Don't process events as regular messages

        else:
            # Invalid or non-supported message
            print(
                f"[warn] Received non-supported or invalid message: {payload[:100]}..."
            )
            data = {"_raw": payload}

        with self._lock:
            self._last_event = data
            # harvest x/y/z if present (from event or pos topic)
            x = data.get("x")
            y = data.get("y")
            z = data.get("z")
            if (
                isinstance(x, (int, float))
                and isinstance(y, (int, float))
                and isinstance(z, (int, float))
            ):
                self._last_pos = (float(x), float(y), float(z))

        if msg.topic == self.s.topic_pos:
            # quiet log for pos pings
            return

        if self._is_arrival(data):
            print(f"[event] ARRIVED: {data}")
            self._arrived_event.set()
        else:
            kind = data.get("type") or data.get("status") or data.get("_raw")
            print(f"[event] {kind}: {data}")

    def _extract_data_from_message(self, message_data: MessageData) -> Dict[str, Any]:
        """Extract event data from structured MessageData"""
        # Use the structured response field
        if message_data.response:
            return message_data.response

        # Fallback: create a basic event from the structured data
        return {
            "type": message_data.method,
            "service": message_data.service,
            "requestId": message_data.request_id,
        }

    @staticmethod
    def _is_arrival(data: Dict[str, Any]) -> bool:
        # Check traditional arrival keys
        for k, v in ARRIVE_KEYS:
            if data.get(k) == v:
                return True

        # Check for standard success response from baritone goto
        if (
            data.get("status") == "success"
            and "x" in data
            and "y" in data
            and "z" in data
        ):
            return True

        return False

    # ---------- helpers ----------
    def _publish_cmd(self, cmd: str):
        print(f"[cmd] → {self.s.topic_cmd}: {cmd}")
        self._mqtt.publish(self.s.topic_cmd, cmd, qos=0, retain=False)

    def _format_cmd_for_waypoint(self, wp: Dict[str, Any]) -> str:
        """Generate a structured JSON command for waypoint"""
        if "name" in wp and wp["name"]:
            # Named waypoints: Use chat command until we implement waypoint coordinate resolution
            # TODO: Replace with proper waypoint coordinate resolution
            chat_cmd = self.s.cmd_tpl_name.format(name=wp["name"])
            message_data = MessageData(
                service="baritone",
                method="chat",  # Keep chat for named waypoints temporarily
                correlation_id=self._correlation_id,
                params={"message": chat_cmd},
            )
        else:
            # xyz mode - send as structured goto command
            for key in ("x", "y", "z"):
                if key not in wp:
                    raise ValueError(f"waypoint missing '{key}' and no 'name': {wp}")

            message_data = MessageData(
                service="baritone",
                method="goto",
                correlation_id=self._correlation_id,
                params={"x": int(wp["x"]), "y": int(wp["y"]), "z": int(wp["z"])},
            )

        return message_data.to_json()

    def _publish_command(self, cmd: str):
        print(f"[cmd] → {self.s.topic_cmd}: {cmd}")
        self._mqtt.publish(self.s.topic_cmd, cmd, qos=0, retain=False)

    def _wait_for_arrival_or_problem(self) -> bool:
        """
        Wait for either an arrival event or a terminal problem up to timeout.
        On calc_failed / stuck / canceled we return False (caller may retry).
        On timeout we also return False.
        """
        deadline = time.time() + self.s.timeout_seconds
        last_problem = None
        while time.time() < deadline:
            if self._arrived_event.wait(timeout=0.25):
                return True  # arrived!

            # poll recent non-arrival events (optional logic)
            with self._lock:
                ev = self._last_event

            if ev:
                typ = ev.get("type")
                status = ev.get("status")

                # Check for failure conditions
                if typ in ("calc_failed", "stuck", "canceled") or status == "failure":
                    if ev is not last_problem:
                        last_problem = ev
                        reason = ev.get("reason", "unknown")
                        print(f"[problem] {typ or status}: {reason}")
                        # let caller decide to retry
                        return False

        print(f"[timeout] no arrival within {self.s.timeout_seconds}s")
        return False

    # parse a pattern step "a b c" → absolute target from current (x,y,z)
    def _resolve_step(
        self, step: str, base_xyz: Tuple[float, float, float]
    ) -> Tuple[int, int, int]:
        tok = step.split()
        if len(tok) != 3:
            raise ValueError(f"pattern step must have 3 tokens: {step}")
        bx, by, bz = base_xyz

        def resolve_axis(t: str, base: float) -> float:
            t = t.strip()
            if t == "~" or t == "~0" or t == "0":
                return base
            if t.startswith("~"):
                # relative delta (may be like "~-5" or "~10")
                delta = float(t[1:]) if t[1:] else 0.0
                return base + delta
            # else absolute world coord
            return float(t)

        ax = resolve_axis(tok[0], bx)
        ay = resolve_axis(tok[1], by)
        az = resolve_axis(tok[2], bz)
        # use block coords (Baritone #goto typically takes ints)
        return int(round(ax)), int(round(ay)), int(round(az))

    def _parse_dwell_period(self, period_str: str) -> float:
        """Parse dwell period string like '3s', '1.5s', '500ms' into seconds"""
        period_str = period_str.strip().lower()
        if period_str.endswith("ms"):
            return float(period_str[:-2]) / 1000.0
        elif period_str.endswith("s"):
            return float(period_str[:-1])
        else:
            # Assume seconds if no unit specified
            return float(period_str)

    def _execute_dwell(self, dwell_config: Dict[str, Any]) -> bool:
        """Execute a dwell/pause step"""
        period_str = dwell_config.get("period", "1s")
        try:
            period_seconds = self._parse_dwell_period(period_str)
            print(f"[dwell] Pausing for {period_seconds}s ({period_str})")
            time.sleep(period_seconds)
            print(f"[dwell] Dwell completed")
            return True
        except (ValueError, TypeError) as e:
            print(f"[dwell] Error parsing dwell period '{period_str}': {e}")
            return False

    # ---------- main flow ----------
    def run(self) -> int:
        # Trigger waypoints_start event
        self._trigger_lifecycle_event("waypoints_start")

        for i, wp in enumerate(self.waypoints, start=1):
            label = wp.get("name") or f"{wp.get('x')},{wp.get('y')},{wp.get('z')}"
            print(f"\n=== Waypoint {i}/{len(self.waypoints)}: {label} ===")

            # Generate correlation ID for this waypoint group
            self._correlation_id = str(uuid.uuid4())
            print(f"[waypoint] Using correlation ID: {self._correlation_id}")

            # Trigger waypoint_start event
            self._trigger_lifecycle_event("waypoint_start")

            # 1) go to the waypoint
            go_cmd = self._format_cmd_for_waypoint(wp)
            while not self._attempt_until_arrival(go_cmd):
                if self._waypoint_processing_paused:
                    print(
                        f"[waypoint] Waiting for event handler to complete before continuing..."
                    )
                    while self._waypoint_processing_paused:
                        time.sleep(0.5)
                    print(f"[waypoint] Event handler completed, retrying waypoint...")
                else:
                    return 2  # Actual failure, not pause

            # establish starting base for pattern: prefer waypoint coords, else last known pos
            # This ensures patterns start from the correct waypoint position, not a drifted position
            base = None
            if "x" in wp and "y" in wp and "z" in wp:
                base = (float(wp["x"]), float(wp["y"]), float(wp["z"]))
                print(f"[waypoint] Using waypoint coordinates as pattern base: {base}")
            elif self._last_pos is not None:
                base = self._last_pos
                print(f"[waypoint] Using last known position as pattern base: {base}")
            else:
                print("[warn] no position known after arrival; using (0,0,0) as base")
                base = (0.0, 0.0, 0.0)

            # 2) run its patterns (if any), cumulatively relative to current position
            run_list = wp.get("run") or []
            if run_list:
                # Trigger pattern_start event before executing patterns
                self._trigger_lifecycle_event("pattern_start")

            for pname in run_list:
                steps = self.patterns.get(pname)
                if not steps:
                    print(f"[warn] pattern '{pname}' not found; skipping")
                    continue
                print(f"--- pattern: {pname} ({len(steps)} steps) ---")
                cur = base
                for sidx, step in enumerate(steps, start=1):
                    # Check for pause before calculating step coordinates
                    if self._waypoint_processing_paused:
                        print(
                            f"[waypoint] Pattern step {sidx} paused - waiting for event handler to complete..."
                        )
                        while self._waypoint_processing_paused:
                            time.sleep(0.5)
                        print(
                            f"[waypoint] Event handler completed, continuing pattern step {sidx}..."
                        )

                    # Check if this is a dwell step (dictionary with type: dwell)
                    if isinstance(step, dict) and step.get("type") == "dwell":
                        print(f"[step {sidx}/{len(steps)}] dwell: {step}")
                        if not self._execute_dwell(step):
                            print(f"[error] Dwell step {sidx} failed")
                            return 2
                        continue  # Skip movement processing for dwell steps

                    # Handle regular coordinate steps (string format)
                    if not isinstance(step, str):
                        print(
                            f"[error] Pattern step {sidx} must be string coordinates or dwell dict, got: {type(step)}"
                        )
                        return 2

                    tx, ty, tz = self._resolve_step(step, cur)
                    # Create structured JSON command for pattern step
                    message_data = MessageData(
                        service="baritone",
                        method="goto",
                        correlation_id=self._correlation_id,
                        params={"x": tx, "y": ty, "z": tz},
                    )
                    cmd = message_data.to_json()
                    print(f"[step {sidx}/{len(steps)}] {step} → goto {tx} {ty} {tz}")
                    while not self._attempt_until_arrival(cmd):
                        if self._waypoint_processing_paused:
                            print(
                                f"[waypoint] Waiting for event handler to complete before continuing pattern step..."
                            )
                            while self._waypoint_processing_paused:
                                time.sleep(0.5)
                            print(
                                f"[waypoint] Event handler completed, retrying pattern step..."
                            )
                        else:
                            return 2  # Actual failure, not pause
                    # advance base to the new position (cumulative)
                    cur = (tx, ty, tz)  # Use the target coordinates, not last_pos

            # Trigger pattern_end event after all patterns complete
            if run_list:
                self._trigger_lifecycle_event("pattern_end")

            # Trigger waypoint_end event after waypoint and patterns complete
            self._trigger_lifecycle_event("waypoint_end")

        print("\nAll waypoints + patterns completed.")

        # Trigger waypoints_end event and wait for it to complete
        self._trigger_lifecycle_event("waypoints_end")

        # Wait for the final lifecycle event to complete
        print("[lifecycle] Waiting for waypoints_end event to complete...")
        self._wait_for_lifecycle_completion("waypoints_end")

        return 0

    def _attempt_until_arrival(self, cmd: str) -> bool:
        # Check if waypoint processing is paused (event handler active)
        if self._waypoint_processing_paused:
            print(
                f"[waypoint] Skipping command - waypoint processing paused for event handler"
            )
            return False

        attempt = 0
        while attempt <= self.s.max_retries:
            attempt += 1
            self._arrived_event.clear()
            self._publish_cmd(cmd)
            if self._wait_for_arrival_or_problem():
                return True
            if attempt <= self.s.max_retries:
                print(f"[retry] retrying in {self.s.retry_delay_seconds}s…")
                time.sleep(self.s.retry_delay_seconds)
        print("[fail] max retries exhausted")
        return False

    # ---------- Event Handling ----------
    def _handle_event(self, message_data: MessageData, data: Dict[str, Any]):
        """Handle incoming events from the bot"""
        if not self.s.events:
            return

        event_type = data.get("event")
        if not event_type:
            return

        print(f"[event] Received: {event_type} - {data.get('message', '')}")

        # Check if we have a handler for this event
        event_config = self.s.events.get(event_type)
        if not event_config or not event_config.get("enabled", False):
            print(f"[event] No handler or disabled for event: {event_type}")
            return

        # Start event sequence
        steps = event_config.get("steps", [])
        if steps:
            print(
                f"[event] Starting event sequence for {event_type} ({len(steps)} steps)"
            )
            self._start_event_sequence(event_type, steps)

    def _trigger_lifecycle_event(self, event_type: str):
        """Trigger a lifecycle event (waypoints_start, waypoint_start, waypoint_end, waypoints_end)"""
        if not self.s.events:
            return

        event_config = self.s.events.get(event_type)
        if not event_config or not event_config.get("enabled", False):
            print(f"[lifecycle] No handler or disabled for event: {event_type}")
            return

        steps = event_config.get("steps", [])
        if steps:
            print(f"[lifecycle] Triggering {event_type} event ({len(steps)} steps)")
            # Create completion event for tracking
            self._lifecycle_events[event_type] = threading.Event()
            self._start_event_sequence(event_type, steps)
        else:
            print(f"[lifecycle] {event_type} event has no steps configured")

    def _wait_for_lifecycle_completion(self, event_type: str, timeout: int = 60):
        """Wait for a lifecycle event to complete"""
        if event_type not in self._lifecycle_events:
            print(f"[lifecycle] No completion event found for {event_type}")
            return

        print(
            f"[lifecycle] Waiting for {event_type} to complete (timeout: {timeout}s)..."
        )
        if self._lifecycle_events[event_type].wait(timeout=timeout):
            print(f"[lifecycle] {event_type} completed successfully")
            # Clean up the completion event
            del self._lifecycle_events[event_type]
        else:
            print(f"[lifecycle] {event_type} timed out after {timeout}s")
            # Clean up the completion event
            if event_type in self._lifecycle_events:
                del self._lifecycle_events[event_type]

    def _start_event_sequence(self, event_type: str, steps: List[Dict[str, Any]]):
        """Start executing an event sequence"""
        # Check if this is a lifecycle event (should not interrupt waypoint processing)
        is_lifecycle_event = event_type in [
            "waypoints_start",
            "waypoint_start",
            "waypoint_end",
            "waypoints_end",
            "pattern_start",
            "pattern_end",
        ]

        if self._event_handler_active and not is_lifecycle_event:
            print(f"[event] Event handler already active, ignoring {event_type}")
            return

        if is_lifecycle_event:
            print(f"[lifecycle] Executing {event_type} event ({len(steps)} steps)")
            # For lifecycle events, don't set _event_handler_active to True
            # This allows multiple lifecycle events to run in parallel
        else:
            print(
                f"[event] 🚨 INTERRUPTING waypoint processing for {event_type} event!"
            )
            # Pause waypoint processing during non-lifecycle events
            self._waypoint_processing_paused = True
            self._event_handler_active = True

        # Store event state for this specific event
        event_thread = threading.Thread(
            target=self._execute_event_sequence, args=(event_type,), daemon=True
        )
        event_thread.start()

    def _execute_event_sequence(self, event_type: str):
        """Execute event sequence steps"""
        # Get steps for this specific event
        event_config = self.s.events.get(event_type)
        if not event_config:
            print(f"[event] No configuration found for event: {event_type}")
            return

        steps = event_config.get("steps", [])
        if not steps:
            print(f"[event] No steps configured for event: {event_type}")
            return

        try:
            print(f"[event] Executing {len(steps)} steps for {event_type}")

            for i, step in enumerate(steps):
                service = step.get("service")
                method = step.get("method")
                params = step.get("params", {})
                description = step.get("description", f"{service}.{method}")

                print(f"[event] Step {i+1}/{len(steps)}: {description}")

                # Execute step
                success = self._execute_event_step(service, method, params)

                if not success:
                    print(f"[event] Step {i+1} failed, aborting sequence")
                    break

                # Wait for step completion if needed
                command_config = self._get_command_config(service, method)
                if command_config and command_config.get("type") == "reply-expected":
                    timeout = command_config.get("timeout", 30)
                    print(
                        f"[event] Waiting for step {i+1} to complete (timeout: {timeout}s)..."
                    )
                    if not self._wait_for_standard_completion(timeout):
                        print(
                            f"[event] Step {i+1} completion timeout, continuing anyway"
                        )

        except Exception as e:
            print(f"[event] Error executing event sequence: {e}")

        finally:
            # Only update global state for non-lifecycle events
            is_lifecycle_event = event_type in [
                "waypoints_start",
                "waypoint_start",
                "waypoint_end",
                "waypoints_end",
                "pattern_start",
                "pattern_end",
            ]
            if not is_lifecycle_event:
                self._event_handler_active = False
                self._waypoint_processing_paused = False
                self._correlation_id = None  # Reset correlation ID for next sequence
                print(
                    f"[event] ✅ Event sequence for {event_type} completed - resuming waypoint processing"
                )
            else:
                print(f"[lifecycle] ✅ Lifecycle event {event_type} completed")
                # Signal completion for lifecycle events
                if event_type in self._lifecycle_events:
                    self._lifecycle_events[event_type].set()

    def _execute_event_step(
        self, service: str, method: str, params: Dict[str, Any]
    ) -> bool:
        """Execute a single event step"""
        try:
            # Generate correlation ID for this event sequence if not set
            if not self._correlation_id:
                self._correlation_id = str(uuid.uuid4())

            # Create command message with correlation ID
            message_data = MessageData(
                service=service,
                method=method,
                correlation_id=self._correlation_id,
                params=params,
            )

            # Track this request for completion
            request_id = message_data.request_id
            self._pending_requests[request_id] = (time.time(), service, method)

            cmd = message_data.to_json()
            print(f"[event] → {self.s.topic_cmd}: {cmd}")
            self._mqtt.publish(self.s.topic_cmd, cmd, qos=0, retain=False)

            return True

        except Exception as e:
            print(f"[event] Error executing step {service}.{method}: {e}")
            return False

    def _get_command_config(
        self, service: str, method: str
    ) -> Optional[Dict[str, Any]]:
        """Get command configuration from services config"""
        if not self.s.services:
            return None

        service_config = self.s.services.get(service, {})
        commands_config = service_config.get("commands", {})
        return commands_config.get(method)

    def _wait_for_standard_completion(self, timeout: int) -> bool:
        """Wait for standard success/failure response for the current step"""
        if not self._pending_requests:
            print(f"[event] No pending requests to wait for")
            return True

        # Get the most recent request ID (the one we just sent)
        current_request_id = list(self._pending_requests.keys())[-1]
        start_time = time.time()

        print(f"[event] Waiting for request {current_request_id} to complete...")

        while time.time() - start_time < timeout:
            # Check if we received a response for this specific request
            with self._lock:
                if current_request_id not in self._pending_requests:
                    print(f"[event] Request {current_request_id} completed")
                    return True

                # Check if we have a recent event that might be our response
                if self._last_event:
                    # Check if this event is a response to our request
                    # (We'll need to match by request ID or correlation ID)
                    event_request_id = self._last_event.get("requestId")
                    if event_request_id == current_request_id:
                        # Check for standard success/failure responses
                        status = self._last_event.get("status")
                        if status == "success":
                            print(
                                f"[event] Request {current_request_id} completed successfully"
                            )
                            del self._pending_requests[current_request_id]
                            return True
                        elif status == "failure":
                            reason = self._last_event.get("reason", "unknown")
                            print(
                                f"[event] Request {current_request_id} failed: {reason}"
                            )
                            del self._pending_requests[current_request_id]
                            return False

                        # Also check for specific completion indicators
                        event_type = self._last_event.get("type")
                        if event_type in ["reached", "AT_GOAL"]:
                            print(
                                f"[event] Request {current_request_id} completed: {event_type}"
                            )
                            del self._pending_requests[current_request_id]
                            return True
                        elif event_type in ["CALC_FAILED", "sleep_failed"]:
                            print(
                                f"[event] Request {current_request_id} failed: {event_type}"
                            )
                            del self._pending_requests[current_request_id]
                            return False

                        # Check for baritone success with coordinates (arrival)
                        if (
                            self._last_event.get("status") == "success"
                            and "x" in self._last_event
                            and "y" in self._last_event
                            and "z" in self._last_event
                        ):
                            print(
                                f"[event] Request {current_request_id} completed: baritone goal reached"
                            )
                            del self._pending_requests[current_request_id]
                            return True

            time.sleep(0.5)

        print(f"[event] Request {current_request_id} timed out after {timeout}s")
        # Clean up timed out request
        if current_request_id in self._pending_requests:
            del self._pending_requests[current_request_id]
        return False


# ---------- CLI ----------
def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_settings(args, cfg: Dict[str, Any]) -> Settings:
    client_id = args.client_id or cfg.get("client_id")
    if not client_id:
        print("Error: --client-id or YAML client_id required", file=sys.stderr)
        sys.exit(2)

    # Expected player name for replies (defaults to client_id if not specified)
    expected_player_name = cfg.get("expected_player_name") or client_id

    return Settings(
        broker=args.broker,
        port=args.port,
        client_id=client_id,
        expected_player_name=expected_player_name,
        topic_cmd=f"mqttbot/{client_id}/command",
        topic_reply=f"mqttbot/{expected_player_name}/reply",
        topic_pos=f"mqttbot/{expected_player_name}/pos",
        timeout_seconds=int(args.timeout or cfg.get("timeout_seconds", 300)),
        max_retries=int(args.retries or cfg.get("max_retries", 2)),
        retry_delay_seconds=int(args.retry_delay or cfg.get("retry_delay_seconds", 3)),
        cmd_tpl_name=cfg.get("command_template_name", "#wp goto {name}"),
        cmd_tpl_xyz=cfg.get("command_template_xyz", "#goto {x} {y} {z}"),
        services=cfg.get("services", {}),
        events=cfg.get("events", {}),
    )


def main():
    ap = argparse.ArgumentParser(
        description="Baritone pathing client with patterns (MQTT + YAML)"
    )
    ap.add_argument("yaml", help="path to config/waypoints.yaml")
    ap.add_argument("--broker", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--client-id", help="baritone clientId segment in topics")
    ap.add_argument("--timeout", type=int)
    ap.add_argument("--retries", type=int)
    ap.add_argument("--retry-delay", type=int)
    args = ap.parse_args()

    cfg = load_yaml(args.yaml)
    waypoints = cfg.get("waypoints") or []
    patterns = cfg.get("patterns") or {}
    if not waypoints:
        print("Error: YAML missing 'waypoints'", file=sys.stderr)
        sys.exit(2)

    settings = build_settings(args, cfg)
    client = PathingClient(settings, waypoints, patterns)
    try:
        client.connect()
        rc = client.run()
    except KeyboardInterrupt:
        print("\n[ctrl-c] stopping…")
        rc = 130
    finally:
        client.close()
    sys.exit(rc)


if __name__ == "__main__":
    main()
