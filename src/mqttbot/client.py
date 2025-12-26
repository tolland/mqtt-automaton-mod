"""MQTT bot pathing client for Baritone waypoint navigation."""

import sys
import threading
import time
import uuid
from typing import Any, Optional

from paho.mqtt import client as mqtt

from mqttbot.models.message_data import MessageData
from mqttbot.models.settings import Settings

ARRIVE_KEYS = [("type", "arrived"), ("status", "reached")]


class PathingClient:
    """Client for controlling Minecraft bot via MQTT with Baritone integration."""

    def __init__(
            self,
            settings: Settings,
            waypoints: list[dict[str, Any]],
            patterns: dict[str, list[str]],
    ):
        self.s = settings
        self.waypoints = waypoints
        self.patterns = patterns

        self._mqtt = mqtt.Client(client_id=f"pathctl-{int(time.time())}")
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_disconnect = self._on_disconnect

        self._arrived_event = threading.Event()
        self._last_event: Optional[dict[str, Any]] = None
        self._last_pos: Optional[tuple[float, float, float]] = None
        self._lock = threading.Lock()

        # Event handling state
        self._event_handler_active = False
        self._current_event_steps: list[dict[str, Any]] = []
        self._current_step_index = 0
        self._step_completion_event = threading.Event()
        self._paused_waypoint_index: Optional[int] = None
        self._waypoint_processing_paused = False

        # Request tracking for step completion
        self._pending_requests = {}
        self._correlation_id = None

        # Lifecycle event completion tracking
        self._lifecycle_events = {}

    # ---------- MQTT ----------
    def connect(self):
        """Connect to MQTT broker."""
        self._mqtt.connect(self.s.broker, self.s.port, keepalive=60)
        self._mqtt.loop_start()

        # Wait for connection to be established
        print(f"[mqtt] connecting to {self.s.broker}:{self.s.port}...")
        timeout = 10
        start_time = time.time()
        while not hasattr(self, "_mqtt_connected") and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not hasattr(self, "_mqtt_connected"):
            raise Exception(f"Failed to connect to MQTT broker within {timeout} seconds")

        print("[mqtt] connection established successfully")

    def close(self):
        """Close MQTT connection."""
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
        self._mqtt.subscribe(self.s.topic_pos, qos=0)
        self._mqtt_connected = True

    def _on_disconnect(self, client, userdata, rc):
        print(f"[mqtt] disconnected rc={rc}")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace").strip()

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

            if message_data.request_id and message_data.request_id in self._pending_requests:
                print(f"[event] Received response for request {message_data.request_id}")
                del self._pending_requests[message_data.request_id]

            if message_data.service in ("events", "inventory"):
                self._handle_event(message_data, data)
                return

        else:
            print(f"[warn] Received non-supported or invalid message: {payload[:100]}...")
            data = {"_raw": payload}

        with self._lock:
            self._last_event = data
            x = data.get("x")
            y = data.get("y")
            z = data.get("z")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(z, (int, float)):
                self._last_pos = (float(x), float(y), float(z))

        if msg.topic == self.s.topic_pos:
            return

        if self._is_arrival(data):
            print(f"[event] ARRIVED: {data}")
            self._arrived_event.set()
        else:
            kind = data.get("type") or data.get("status") or data.get("_raw")
            print(f"[event] {kind}: {data}")

    def _extract_data_from_message(self, message_data: MessageData) -> dict[str, Any]:
        if message_data.response:
            return message_data.response

        return {
            "type": message_data.method,
            "service": message_data.service,
            "requestId": message_data.request_id,
        }

    @staticmethod
    def _is_arrival(data: dict[str, Any]) -> bool:
        for k, v in ARRIVE_KEYS:
            if data.get(k) == v:
                return True

        if data.get("status") == "success" and all(k in data for k in ("x", "y", "z")):
            return True

        return False

    def _publish_cmd(self, cmd: str):
        print(f"[cmd] → {self.s.topic_cmd}: {cmd}")
        self._mqtt.publish(self.s.topic_cmd, cmd, qos=0, retain=False)

    def _format_cmd_for_waypoint(self, wp: dict[str, Any]) -> str:
        if "name" in wp and wp["name"]:
            chat_cmd = self.s.cmd_tpl_name.format(name=wp["name"])
            message_data = MessageData(
                service="baritone",
                method="chat",
                correlation_id=self._correlation_id,
                params={"message": chat_cmd},
            )
        else:
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

    def _wait_for_arrival_or_problem(self) -> bool:
        deadline = time.time() + self.s.timeout_seconds
        last_problem = None
        while time.time() < deadline:
            if self._arrived_event.wait(timeout=0.25):
                return True

            with self._lock:
                ev = self._last_event

            if ev:
                typ = ev.get("type")
                status = ev.get("status")

                if typ in ("calc_failed", "stuck", "canceled") or status == "failure":
                    if ev is not last_problem:
                        last_problem = ev
                        reason = ev.get("reason", "unknown")
                        print(f"[problem] {typ or status}: {reason}")
                        return False

        print(f"[timeout] no arrival within {self.s.timeout_seconds}s")
        return False

    def _resolve_step(
            self, step: str, base_xyz: tuple[float, float, float]
    ) -> tuple[int, int, int]:
        tok = step.split()
        if len(tok) != 3:
            raise ValueError(f"pattern step must have 3 tokens: {step}")
        bx, by, bz = base_xyz

        def resolve_axis(t: str, base: float) -> float:
            t = t.strip()
            if t in ("~", "~0", "0"):
                return base
            if t.startswith("~"):
                delta = float(t[1:]) if t[1:] else 0.0
                return base + delta
            return float(t)

        ax = resolve_axis(tok[0], bx)
        ay = resolve_axis(tok[1], by)
        az = resolve_axis(tok[2], bz)
        return int(round(ax)), int(round(ay)), int(round(az))

    def _parse_dwell_period(self, period_str: str) -> float:
        period_str = period_str.strip().lower()
        if period_str.endswith("ms"):
            return float(period_str[:-2]) / 1000.0
        elif period_str.endswith("s"):
            return float(period_str[:-1])
        else:
            return float(period_str)

    def _execute_dwell(self, dwell_config: dict[str, Any]) -> bool:
        period_str = dwell_config.get("period", "1s")
        try:
            period_seconds = self._parse_dwell_period(period_str)
            print(f"[dwell] Pausing for {period_seconds}s ({period_str})")
            time.sleep(period_seconds)
            print("[dwell] Dwell completed")
            return True
        except (ValueError, TypeError) as e:
            print(f"[dwell] Error parsing dwell period '{period_str}': {e}")
            return False

    def run(self) -> int:
        """Execute waypoint navigation with patterns."""
        self._trigger_lifecycle_event("waypoints_start")

        for i, wp in enumerate(self.waypoints, start=1):
            label = wp.get("name") or f"{wp.get('x')},{wp.get('y')},{wp.get('z')}"
            print(f"\n=== Waypoint {i}/{len(self.waypoints)}: {label} ===")

            self._correlation_id = str(uuid.uuid4())
            print(f"[waypoint] Using correlation ID: {self._correlation_id}")

            self._trigger_lifecycle_event("waypoint_start")

            go_cmd = self._format_cmd_for_waypoint(wp)
            while not self._attempt_until_arrival(go_cmd):
                if self._waypoint_processing_paused:
                    print("[waypoint] Waiting for event handler to complete before continuing...")
                    while self._waypoint_processing_paused:
                        time.sleep(0.5)
                    print("[waypoint] Event handler completed, retrying waypoint...")
                else:
                    return 2

            base = None
            if all(k in wp for k in ("x", "y", "z")):
                base = (float(wp["x"]), float(wp["y"]), float(wp["z"]))
                print(f"[waypoint] Using waypoint coordinates as pattern base: {base}")
            elif self._last_pos is not None:
                base = self._last_pos
                print(f"[waypoint] Using last known position as pattern base: {base}")
            else:
                print("[warn] no position known after arrival; using (0,0,0) as base")
                base = (0.0, 0.0, 0.0)

            run_list = wp.get("run") or []
            if run_list:
                self._trigger_lifecycle_event("pattern_start")

            for pname in run_list:
                steps = self.patterns.get(pname)
                if not steps:
                    print(f"[warn] pattern '{pname}' not found; skipping")
                    continue
                print(f"--- pattern: {pname} ({len(steps)} steps) ---")
                cur = base
                for sidx, step in enumerate(steps, start=1):
                    if self._waypoint_processing_paused:
                        print(
                            f"[waypoint] Pattern step {sidx} paused - waiting for event handler..."
                        )
                        while self._waypoint_processing_paused:
                            time.sleep(0.5)
                        print(f"[waypoint] Event handler completed, continuing pattern step {sidx}...")

                    if isinstance(step, dict) and step.get("type") == "dwell":
                        print(f"[step {sidx}/{len(steps)}] dwell: {step}")
                        if not self._execute_dwell(step):
                            print(f"[error] Dwell step {sidx} failed")
                            return 2
                        continue

                    if not isinstance(step, str):
                        print(
                            f"[error] Pattern step {sidx} must be string coordinates or dwell dict, got: {type(step)}"
                        )
                        return 2

                    tx, ty, tz = self._resolve_step(step, cur)
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
                                "[waypoint] Waiting for event handler to complete before continuing pattern step..."
                            )
                            while self._waypoint_processing_paused:
                                time.sleep(0.5)
                            print("[waypoint] Event handler completed, retrying pattern step...")
                        else:
                            return 2
                    cur = (tx, ty, tz)

            if run_list:
                self._trigger_lifecycle_event("pattern_end")

            self._trigger_lifecycle_event("waypoint_end")

        print("\nAll waypoints + patterns completed.")

        self._trigger_lifecycle_event("waypoints_end")

        print("[lifecycle] Waiting for waypoints_end event to complete...")
        self._wait_for_lifecycle_completion("waypoints_end")

        return 0

    def _attempt_until_arrival(self, cmd: str) -> bool:
        if self._waypoint_processing_paused:
            print("[waypoint] Skipping command - waypoint processing paused for event handler")
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
    def _handle_event(self, message_data: MessageData, data: dict[str, Any]):
        if not self.s.events:
            return

        event_type = data.get("event")
        if not event_type:
            return

        print(f"[event] Received: {event_type} - {data.get('message', '')}")

        event_config = self.s.events.get(event_type)
        if not event_config or not event_config.get("enabled", False):
            print(f"[event] No handler or disabled for event: {event_type}")
            return

        steps = event_config.get("steps", [])
        if steps:
            print(f"[event] Starting event sequence for {event_type} ({len(steps)} steps)")
            self._start_event_sequence(event_type, steps)

    def _trigger_lifecycle_event(self, event_type: str):
        if not self.s.events:
            return

        event_config = self.s.events.get(event_type)
        if not event_config or not event_config.get("enabled", False):
            print(f"[lifecycle] No handler or disabled for event: {event_type}")
            return

        steps = event_config.get("steps", [])
        if steps:
            print(f"[lifecycle] Triggering {event_type} event ({len(steps)} steps)")
            self._lifecycle_events[event_type] = threading.Event()
            self._start_event_sequence(event_type, steps)
        else:
            print(f"[lifecycle] {event_type} event has no steps configured")

    def _wait_for_lifecycle_completion(self, event_type: str, timeout: int = 60):
        if event_type not in self._lifecycle_events:
            print(f"[lifecycle] No completion event found for {event_type}")
            return

        print(f"[lifecycle] Waiting for {event_type} to complete (timeout: {timeout}s)...")
        if self._lifecycle_events[event_type].wait(timeout=timeout):
            print(f"[lifecycle] {event_type} completed successfully")
            del self._lifecycle_events[event_type]
        else:
            print(f"[lifecycle] {event_type} timed out after {timeout}s")
            if event_type in self._lifecycle_events:
                del self._lifecycle_events[event_type]

    def _start_event_sequence(self, event_type: str, steps: list[dict[str, Any]]):
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
        else:
            print(f"[event] 🚨 INTERRUPTING waypoint processing for {event_type} event!")
            self._waypoint_processing_paused = True
            self._event_handler_active = True

        event_thread = threading.Thread(
            target=self._execute_event_sequence, args=(event_type,), daemon=True
        )
        event_thread.start()

    def _execute_event_sequence(self, event_type: str):
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

                print(f"[event] Step {i + 1}/{len(steps)}: {description}")

                success = self._execute_event_step(service, method, params)

                if not success:
                    print(f"[event] Step {i + 1} failed, aborting sequence")
                    break

                command_config = self._get_command_config(service, method)
                if command_config and command_config.get("type") == "reply-expected":
                    timeout = command_config.get("timeout", 30)
                    print(f"[event] Waiting for step {i + 1} to complete (timeout: {timeout}s)...")
                    if not self._wait_for_standard_completion(timeout):
                        print(f"[event] Step {i + 1} completion timeout, continuing anyway")

        except Exception as e:
            print(f"[event] Error executing event sequence: {e}")

        finally:
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
                self._correlation_id = None
                print(f"[event] ✅ Event sequence for {event_type} completed - resuming waypoint processing")
            else:
                print(f"[lifecycle] ✅ Lifecycle event {event_type} completed")
                if event_type in self._lifecycle_events:
                    self._lifecycle_events[event_type].set()

    def _execute_event_step(self, service: str, method: str, params: dict[str, Any]) -> bool:
        try:
            if not self._correlation_id:
                self._correlation_id = str(uuid.uuid4())

            message_data = MessageData(
                service=service,
                method=method,
                correlation_id=self._correlation_id,
                params=params,
            )

            request_id = message_data.request_id
            self._pending_requests[request_id] = (time.time(), service, method)

            cmd = message_data.to_json()
            print(f"[event] → {self.s.topic_cmd}: {cmd}")
            self._mqtt.publish(self.s.topic_cmd, cmd, qos=0, retain=False)

            return True

        except Exception as e:
            print(f"[event] Error executing step {service}.{method}: {e}")
            return False

    def _get_command_config(self, service: str, method: str) -> Optional[dict[str, Any]]:
        if not self.s.services:
            return None

        service_config = self.s.services.get(service, {})
        commands_config = service_config.get("commands", {})
        return commands_config.get(method)

    def _wait_for_standard_completion(self, timeout: int) -> bool:
        if not self._pending_requests:
            print("[event] No pending requests to wait for")
            return True

        current_request_id = list(self._pending_requests.keys())[-1]
        start_time = time.time()

        print(f"[event] Waiting for request {current_request_id} to complete...")

        while time.time() - start_time < timeout:
            with self._lock:
                if current_request_id not in self._pending_requests:
                    print(f"[event] Request {current_request_id} completed")
                    return True

                if self._last_event:
                    event_request_id = self._last_event.get("requestId")
                    if event_request_id == current_request_id:
                        status = self._last_event.get("status")
                        if status == "success":
                            print(f"[event] Request {current_request_id} completed successfully")
                            del self._pending_requests[current_request_id]
                            return True
                        elif status == "failure":
                            reason = self._last_event.get("reason", "unknown")
                            print(f"[event] Request {current_request_id} failed: {reason}")
                            del self._pending_requests[current_request_id]
                            return False

                        event_type = self._last_event.get("type")
                        if event_type in ["reached", "AT_GOAL"]:
                            print(f"[event] Request {current_request_id} completed: {event_type}")
                            del self._pending_requests[current_request_id]
                            return True
                        elif event_type in ["CALC_FAILED", "sleep_failed"]:
                            print(f"[event] Request {current_request_id} failed: {event_type}")
                            del self._pending_requests[current_request_id]
                            return False

                        if (
                                self._last_event.get("status") == "success"
                                and all(k in self._last_event for k in ("x", "y", "z"))
                        ):
                            print(f"[event] Request {current_request_id} completed: baritone goal reached")
                            del self._pending_requests[current_request_id]
                            return True

            time.sleep(0.5)

        print(f"[event] Request {current_request_id} timed out after {timeout}s")
        if current_request_id in self._pending_requests:
            del self._pending_requests[current_request_id]
        return False
