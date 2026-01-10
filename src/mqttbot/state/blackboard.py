from dataclasses import dataclass, field
from typing import TypeVar, Generic, Callable, Any, Protocol
from abc import ABC, abstractmethod
import json

from mqttbot.state.state_module import StateModule


# Extensible blackboard
class TypedBlackboard:
    def __init__(self):
        self._modules: dict[str, StateModule] = {}
        self._subscribers: dict[str, list[Callable]] = {}

    def register_module(self, name: str, module: StateModule) -> None:
        """Register a new state module"""
        self._modules[name] = module

    def subscribe(
            self,
            module: str,
            callback: Callable[[Any], None]
    ) -> None:
        """Subscribe to module state changes"""
        if module not in self._subscribers:
            self._subscribers[module] = []
        self._subscribers[module].append(callback)

    def get_module(self, name: str) -> StateModule:
        """Get a module by name"""
        return self._modules.get(name)

    def emit_event(self, module_name: str, event: dict[str, Any]) -> None:
        """Route event to module, notify subscribers"""
        if module_name not in self._modules:
            raise ValueError(f"Unknown module: {module_name}")

        module = self._modules[module_name]
        module.handle_event(event)

        # Notify subscribers
        if module_name in self._subscribers:
            for callback in self._subscribers[module_name]:
                callback(module.get_state())
