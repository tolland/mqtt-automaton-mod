from typing import Callable, Any

from mqttbot.state.state_module import StateModule
import copy

# Extensible blackboard
class TypedBlackboard:
    _instance: "TypedBlackboard" = None
    _modules: dict[str, StateModule] = {}
    _subscribers: dict[str, list[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            print('Creating new instance')
            cls._instance = super().__new__(cls)
            # Put any initialization here.
        return cls._instance


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

    def unsubscribe(
            self,
            module: str,
            callback: Callable[[Any], None]
    ) -> None:
        """Unsubscribe from module state changes"""
        if module in self._subscribers:
            self._subscribers[module].remove(callback)

    def get_module(self, name: str) -> StateModule:
        """Get a module by name"""
        return self._modules.get(name)

    def reset_state(self, module_name: str):
        if module_name not in self._modules:
            raise ValueError(f"Unknown module: {module_name}")

        module = self._modules[module_name]
        module.reset_state()

    def emit_event(self, module_name: str, event: dict[str, Any]) -> None:
        """Route event to module, notify subscribers"""
        if module_name not in self._modules:
            raise ValueError(f"Unknown module: {module_name}")

        module = self._modules[module_name]
        old_facts = copy.deepcopy(module.get_state())
        print(old_facts)
        module.handle_event(event)
        new_facts = module.get_state()
        print(new_facts)

        for key in new_facts.__dataclass_fields__:
            value = getattr(new_facts, key)
            if getattr(old_facts, key) != value:
                # self._emit_fact_change(key, value)
                if module_name in self._subscribers:
                    for callback in self._subscribers[module_name]:
                        callback(module.get_state())

    def _emit_fact_change(self, key, value):
        pass
