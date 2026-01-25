from __future__ import annotations

from typing import Any

from pydantic import RootModel, model_validator

from mqttbot.config.model.events.event_handler_config import EventHandlerConfig


class EventsConfig(RootModel):
    root: dict[tuple[str, str], EventHandlerConfig]

    @model_validator(mode="before")
    @classmethod
    def validate_events(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # If it's already in the target format (tuple keys), return as is
        if any(isinstance(k, tuple) for k in data.keys()):
            return data

        # Otherwise, parse from nested structure: {service: {method: config}}
        normalized = {}
        for service_name, methods in data.items():
            if not isinstance(methods, dict):
                continue
            for method_name, handler_config in methods.items():
                if not isinstance(handler_config, dict):
                    continue

                # Filter out disabled handlers early to match legacy behavior if needed,
                # but legacy code kept them if enabled was True.
                # Actually legacy code did: if not handler_config.get("enabled", False): continue
                if not handler_config.get("enabled", False):
                    continue

                normalized[(service_name, method_name)] = handler_config

        return normalized
