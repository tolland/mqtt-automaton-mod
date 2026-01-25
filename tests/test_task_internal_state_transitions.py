import pytest

from mqttbot.core.protocol.task_status import TaskInternalState
from mqttbot.core.protocol.thread_status import IllegalStateTransition


def test_ready_to_enqueued_allowed():
    """READY -> ENQUEUED is a valid transition."""
    assert TaskInternalState.INITIAL.can_transition_to(TaskInternalState.ENQUEUED)
    assert TaskInternalState.INITIAL.transition_to(TaskInternalState.ENQUEUED) is TaskInternalState.ENQUEUED


def test_init_to_ready_disallowed():
    """INIT -> READY should be disallowed and raise IllegalStateTransition."""
    assert not TaskInternalState.READY.can_transition_to(TaskInternalState.INITIAL)
    with pytest.raises(IllegalStateTransition):
        TaskInternalState.READY.transition_to(TaskInternalState.INITIAL)


def test_waiting_to_done_allowed():
    """WAITING -> DONE is a valid terminal transition."""
    assert TaskInternalState.WAITING.can_transition_to(TaskInternalState.DONE)
    assert TaskInternalState.WAITING.transition_to(TaskInternalState.DONE) is TaskInternalState.DONE


def test_sent_to_waiting_allowed_and_sent_to_ready_disallowed():
    """SENT -> WAITING allowed; SENT -> READY disallowed."""
    assert TaskInternalState.SENT.can_transition_to(TaskInternalState.WAITING)
    assert TaskInternalState.SENT.transition_to(TaskInternalState.WAITING) is TaskInternalState.WAITING
    assert not TaskInternalState.SENT.can_transition_to(TaskInternalState.INITIAL)
    with pytest.raises(IllegalStateTransition):
        TaskInternalState.SENT.transition_to(TaskInternalState.INITIAL)
