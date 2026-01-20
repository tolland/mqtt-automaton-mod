from typing import Any

from mqttbot.config.service_config import ServiceConfig
from mqttbot.config.threads.thread_config import ThreadConfig
from mqttbot.core.tasks.task_priority import TaskPriority
from mqttbot.model.waypoint import Waypoint
from mqttbot.utils.common import parse_dwell


class ThreadConfigParser:
    """Parse YAML config and build thread configs"""

    @staticmethod
    def from_yaml(yaml_data: dict[str, Any]) -> list[ThreadConfig]:
        """
        Parse YAML config and return list of ThreadConfig objects.
        ```
        """

        threads = []
        threads_data = yaml_data.get("threads", {})
        patterns = yaml_data.get("patterns", {})

        for thread_id, thread_data in threads_data.items():
            # Parse priority
            priority_str = thread_data.get("priority", "NORMAL").upper()
            priority = TaskPriority[priority_str]

            # Parse waypoints
            waypoints = []
            for wp_data in thread_data.get("waypoints", []):
                if isinstance(wp_data, dict):
                    if "type" in wp_data and wp_data["type"] == "dwell":
                        # Skip dwell entries (handle separately)
                        continue

                    waypoint = Waypoint(
                        x=wp_data["x"],
                        y=wp_data["y"],
                        z=wp_data["z"],
                        patterns=wp_data.get("patterns", []),
                        dwell_seconds=parse_dwell(wp_data.get("dwell", 0)),
                    )
                    waypoints.append(waypoint)

            # Parse services
            services = {}
            for service_name, service_data in thread_data.get("services", {}).items():
                service_config = ServiceConfig(
                    name=service_name,
                    timeout=service_data.get("timeout", 60),
                    metadata=service_data.get("metadata", {}),
                )
                services[service_name] = service_config

            # Build thread config
            thread_config = ThreadConfig(
                thread_id=thread_id,
                priority=priority,
                waypoints=waypoints,
                services=services,
                on_suspend_tasks=thread_data.get("on_suspend", []),
                on_resume_tasks=thread_data.get("on_resume", []),
                on_cancel_tasks=thread_data.get("on_cancel", []),
                on_waypoint_end_tasks=thread_data.get("on_waypoint_end", []),
                on_waypoint_start_tasks=thread_data.get("on_waypoint_start", []),
                metadata=thread_data.get("metadata", {}),
            )
            threads.append(thread_config)

        return threads
