import logging
from unittest.mock import Mock
import importlib
import pytest
import yaml
from loguru import logger

from mocks.message_service_mock import make_success_service
from mqttbot.config.model.full_config import FullConfig
from mqttbot.core.events.event_manager import EventManager
from mqttbot.core.threads.dynamic_handler import DynamicHandler
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.protocol.thread_status import ThreadStatus
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.thread import TaskThread
from mqttbot.core.threads.thread_factory import ThreadFactory
from mqttbot.utils.collections import first_or_default


inspect = importlib.import_module("rich").inspect
rprint = importlib.import_module("rich").print

"""Tests for correct callback task generation

These tests generated various callback configurations that produce
the expect task sequences when the thread is started, suspended,
resumed, cancelled, or failed.
"""


class TestCallbackThreadConstruction:
    """Test PatternThread initialization and setup"""

    @pytest.mark.asyncio
    async def test_create_pattern_threadxxx(
        self,
        caplog,
    ):
        caplog.set_level(logging.INFO)
        mock_message_sender = Mock()
        mock_bot_service = make_success_service()
        ctx = Context(
            message_sender=Mock(), blackboard=Mock(), bot_service=mock_bot_service, mqtt=None
        )
        logger.debug("test")
        config_path = "configs/config.yml"
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        full_config = FullConfig.model_validate(yaml_data)
        pydantic_patterns = full_config.pattern_config
        thread_configs = full_config.thread_config

        # inspect(pydantic_patterns)
        task_compiler = TaskCompiler(pydantic_patterns)
        thread_factory = ThreadFactory(task_compiler)
        thread = thread_factory.create_thread(first_or_default(thread_configs.threads))
        assert len(thread.task_queue) == 0
        inspect(thread)
        # rprint(thread)
        # pprint(thread)

        thread.start(ctx)
        assert thread.status == ThreadStatus.RUNNING
        counter = 0
        while thread.status == ThreadStatus.RUNNING and counter < 100:
            counter += 1
            thread.step(ctx)
            rprint(thread)
        assert thread.status == ThreadStatus.COMPLETED
        rprint(thread)

    @pytest.mark.asyncio
    async def test_create_pattern_thread_with_scheduler(
        self,
        caplog,
    ):
        from mqttbot.core.threads import scheduler as scheduler_mod

        caplog.set_level(logging.INFO)
        mock_message_sender = Mock()
        mock_bot_service = make_success_service()
        ctx = Context(
            message_sender=Mock(), blackboard=Mock(), bot_service=mock_bot_service, mqtt=None
        )
        mock_scheduler = scheduler_mod.create()
        logger.debug("test")
        config_path = "configs/config.yml"
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        full_config = FullConfig.model_validate(yaml_data)
        pydantic_patterns = full_config.pattern_config
        thread_configs = full_config.thread_config

        # inspect(pydantic_patterns)
        task_compiler = TaskCompiler(pydantic_patterns)
        thread_factory = ThreadFactory(task_compiler)
        thread = thread_factory.create_thread(first_or_default(thread_configs.threads))
        assert len(thread.task_queue) == 0
        mock_scheduler.enqueue_thread(thread)
        rprint(mock_scheduler)
        # rprint(thread)
        # pprint(thread)

        # mock_scheduler.start(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        mock_scheduler.current_thread.cancel(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        rprint(mock_scheduler)

        # assert thread.status == ThreadStatus.RUNNING
        # assert thread._internal_status == ThreadInternalStatus.CANCELING
        # rprint(thread)
        # thread.step(ctx)
        # rprint(thread)
        # rprint(thread)

        # inspect(thread)

    @pytest.mark.asyncio
    async def test_create_event_manager(
        self,
        caplog,
    ):
        from mqttbot.core.threads import scheduler as scheduler_mod

        caplog.set_level(logging.INFO)
        mock_message_sender = Mock()
        mock_bot_service = make_success_service()
        ctx = Context(
            message_sender=Mock(), blackboard=Mock(), bot_service=mock_bot_service, mqtt=None
        )
        mock_scheduler = scheduler_mod.create()
        logger.debug("test")
        config_path = "configs/config.yml"
        with open(config_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        full_config = FullConfig.model_validate(yaml_data)
        pydantic_patterns = full_config.pattern_config
        thread_configs = full_config.thread_config
        event_configs = full_config.event_handlers

        event_manager = EventManager(event_configs)

        rprint(event_manager)

        handler_config = event_manager.get_handler_config(
           "inventory", "inventory_full"
        )
        rprint(handler_config)

        task_compiler = TaskCompiler(pydantic_patterns)
        thread_factory = ThreadFactory(task_compiler)

        thread = thread_factory.create_thread(first_or_default(thread_configs.threads))
        mock_scheduler.enqueue_thread(thread)
        rprint(mock_scheduler)

        event_thread = TaskThread(
            thread_id="event-thread-1",
            main_source_provider=DynamicHandler(handler_config.steps, task_compiler),
            on_suspend_provider=DynamicHandler([], task_compiler),
            on_resume_provider=DynamicHandler([], task_compiler),
            on_cancel_provider=DynamicHandler([], task_compiler),
            on_failed_provider=DynamicHandler([], task_compiler),
            priority=ThreadPriority.HIGH,
        )

        rprint(event_thread)

        mock_scheduler.enqueue_thread(event_thread)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        await mock_scheduler.step(ctx)
        rprint(mock_scheduler)

        counter = 0
        print(f"--- Starting Scheduler Loop ---")
        while (not mock_scheduler.is_complete()) and counter < 100:
            counter += 1
            print(f"--- Scheduler Step {counter} ---")
            await mock_scheduler.step(ctx)
            rprint(mock_scheduler)
