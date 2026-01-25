import importlib
import inspect as pyinspect
import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from rich.repr import rich_repr

from mqttbot.core.tasks.stack.task_state import TaskStatus, TaskState
from mqttbot.core.threads.scheduler_context import Context


class TaskBase(ABC):
    def __init__(self):
        self._state_stack: list[TaskState] = []
        self.request_id: Optional[str] = None
        self.correlation_id: Optional[str] = None

    def push_state(self, state: TaskState, ctx: "Context"):
        self._state_stack.append(state)
        state.on_enter(self, ctx)

    def pop_state(self):
        if len(self._state_stack) > 1:
            self._state_stack.pop()

    def step(self, ctx: "Context") -> TaskStatus:
        if not self._state_stack:
            return TaskStatus.SUCCESS

        current_state = self._state_stack[-1]
        next_state = current_state.step(self, ctx)

        if next_state:
            self.push_state(next_state, ctx)

        return current_state.external_status
