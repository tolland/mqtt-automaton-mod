import pytest
import logging
from unittest.mock import Mock

from mqttbot.core.tasks.concrete import GotoTask
from mqttbot.core.threads.scheduler_context import Context
from mqttbot.core.threads.thread_factory import ThreadFactory
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.config.model.full_config import FullConfig
from mqttbot.core.protocol.task_priority import ThreadPriority
from mqttbot.core.threads.thread import TaskThread
from mqttbot.core.threads.dynamic_handler import DynamicHandler
from mqttbot.core.events.event_manager import EventManager
from mqttbot.utils.collections import first_or_default
from rich import print as rprint, inspect


@pytest.mark.asyncio
async def test_preemption_with_metadata(
    caplog,
    sample_config,
    mock_success_message_service,
    mock_scheduler,
    step_until_helper
):
    """
    Test preemption of a thread by an event handler using metadata for synchronization.
    1. Start a main thread.
    2. Step until a specific task (marked with metadata) is reached.
    3. Enqueue a high-priority event thread.
    4. Verify preemption occurs.
    """
    caplog.set_level(logging.DEBUG)
    ctx = Context(
        message_sender=Mock(),
        blackboard=Mock(),
        bot_service=mock_success_message_service,
        mqtt=None
    )

    # 1. Setup the main thread from config
    # We'll use the first thread from config, but we'll inject metadata into one of its steps
    # to make it identifiable.

    pydantic_patterns = sample_config.pattern_config
    thread_configs = sample_config.thread_config
    task_compiler = TaskCompiler(pydantic_patterns)
    thread_factory = ThreadFactory(task_compiler)

    thread_def = first_or_default(thread_configs.threads)
    # Inject a marked waypoint/pattern if needed, or just rely on existing ones.
    # Let's look at config.yml: cane_row_02 has a pattern step with metadata: {} at the end.
    # Let's add a custom note to it for identification.
    if thread_def.waypoints:
        # Waypoints are processed into tasks.
        # Actually, let's just create a simple thread manually to have full control.
        pass

    # Better: Use the existing config but ensure we can find a task with specific metadata.
    # In config.yml:
    # cane_row_02:
    #   - type: pattern
    #     metadata: {}

    # Let's modify the sample_config in memory to add a specific tag.
    found_step = False
    for pattern in pydantic_patterns.patterns:
        rprint(f"[DEBUG_LOG] Pattern: {pattern.pattern_id}")
        if pattern.pattern_id == "cane_row_02":
            for i, step in enumerate(pattern.steps):
                rprint(f"[DEBUG_LOG] Step {i}: {step.type}")
                if step.type == "pattern":
                    rprint(f"[DEBUG_LOG] Metadata before: {step.metadata}")
                    if step.metadata:
                        step.metadata.note = f"target_task_{i}"
                        found_step = True
                        rprint(f"[DEBUG_LOG] Metadata after: {step.metadata}")
    assert found_step, "Could not find the target step in cane_row_02"

    # 1.5 Manually create a thread and inject a task with metadata
    from mqttbot.core.tasks.concrete.dwell_task import DwellTask

    main_thread = thread_factory.create_thread(thread_def)

    # Create a marked task
    marked_task = GotoTask(params={"target": {"x": 199, "y": 100, "z":1000}}, metadata={"note": "target_task"})
    main_thread.enqueue_task(marked_task)

    mock_scheduler.enqueue_thread(main_thread)

    # 2. Step until the marked task is CURRENT
    # The predicate checks if the current thread's current task has the note.
    def is_at_target_task(s):
        if s.current_thread and s.current_thread.current_task:
            note = s.current_thread.current_task.metadata.get("note")
            if note:
                rprint(f"[DEBUG_LOG] Current task note: {note}")
            return note == "target_task"
        return False

    reached = await step_until_helper(mock_scheduler, ctx, is_at_target_task, timeout=200)
    assert reached, "Failed to reach the target task"
    rprint(f"[DEBUG_LOG] Reached target task: {mock_scheduler.current_thread.current_task}")

    # 3. Create and enqueue a high-priority event thread
    event_configs = sample_config.event_handlers
    event_manager = EventManager(event_configs)
    handler_config = event_manager.get_handler_config("inventory", "inventory_full")

    event_thread = TaskThread(
        thread_id="inventory_full_event",
        main_source_provider=DynamicHandler(handler_config.steps, task_compiler),
        on_suspend_provider=DynamicHandler([], task_compiler),
        on_resume_provider=DynamicHandler([], task_compiler),
        on_cancel_provider=DynamicHandler([], task_compiler),
        on_failed_provider=DynamicHandler([], task_compiler),
        priority=ThreadPriority.HIGH, # Preempts NORMAL
    )

    rprint("[DEBUG_LOG] Enqueuing high-priority event thread")
    mock_scheduler.enqueue_thread(event_thread)

    # 4. Verify preemption
    # Next step should trigger preemption
    rprint(f"[DEBUG_LOG] Current thread BEFORE preemption step: {mock_scheduler.current_thread.thread_id}")
    rprint(f"[DEBUG_LOG] Ready threads: {[t.thread_id for t in mock_scheduler.ready_threads]}")
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    await mock_scheduler.step(ctx)
    rprint(mock_scheduler)

    # After preemption, the current thread should be the event thread
    rprint(f"[DEBUG_LOG] Current thread AFTER preemption step: {mock_scheduler.current_thread.thread_id if mock_scheduler.current_thread else 'None'}")
    inspect(mock_scheduler.current_thread)
    assert mock_scheduler.current_thread.thread_id == "inventory_full_event"
    rprint(f"[DEBUG_LOG] Preempted! Current thread: {mock_scheduler.current_thread.thread_id}")

    # 5. Step until completion
    counter = 0
    while not mock_scheduler.is_complete() and counter < 100:
        await mock_scheduler.step(ctx)
        counter += 1

    assert mock_scheduler.is_complete()
    rprint("[DEBUG_LOG] Scheduler completed successfully")
