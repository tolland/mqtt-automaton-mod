from typing import Any

import yaml


def _load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
