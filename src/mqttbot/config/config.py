"""Configuration loading and management."""

from pathlib import Path
from typing import Any, Optional

import yaml

from mqttbot.core.models.settings import Settings


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_settings(
        config_path: str | Path,
        broker: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[str] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        log_level: Optional[str] = None,
) -> Settings:
    """
    Build Settings object from configuration file and CLI arguments.

    Returns:
        tuple: (settings, waypoints, patterns)
    """
    cfg = load_yaml(config_path)

    # Get client_id from args or config
    final_client_id = client_id or cfg.get("client_id")
    if not final_client_id:
        raise ValueError("client_id must be provided via --client-id or in config YAML")

    # Expected player name for replies (defaults to client_id if not specified)
    expected_player_name = cfg.get("expected_player_name") or final_client_id

    settings = Settings(
        broker=broker or "127.0.0.1",
        port=port or 1883,
        client_id=final_client_id,
        expected_player_name=expected_player_name,
        topic_cmd=f"mqttbot/{final_client_id}/command",
        topic_reply=f"mqttbot/{expected_player_name}/reply",
        topic_pos=f"mqttbot/{expected_player_name}/pos",
        timeout_seconds=timeout or cfg.get("timeout_seconds", 300),
        max_retries=retries or cfg.get("max_retries", 2),
        retry_delay_seconds=retry_delay or cfg.get("retry_delay_seconds", 3),
        cmd_tpl_name=cfg.get("command_template_name", "#wp goto {name}"),
        cmd_tpl_xyz=cfg.get("command_template_xyz", "#goto {x} {y} {z}"),
        log_level=log_level or cfg.get("log_level", "INFO"),
        services=cfg.get("services", {}),
        events=cfg.get("events", {}),
    )

    return settings
