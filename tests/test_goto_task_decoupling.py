import pytest
from unittest.mock import Mock, patch
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_priority import TaskStatus
from mqttbot.core.tasks.task_status import TaskState
from mqttbot.core.context import Context
from mqttbot.core.services.message_service import RequestResult, RequestStatus
from mqttbot import ServiceMessage

class TestGotoTaskDecoupling:
    def test_goto_task_sends_message_directly(self):
        # Setup mock context
        mock_message_sender = Mock()
        mock_bot_service = Mock()
        ctx = Context(
            message_sender=mock_message_sender,
            blackboard=Mock(),
            bot_service=mock_bot_service,
            mqtt=None
        )
        
        # Create task
        task = GotoTask.create(x=10, y=20, z=30)
        task.correlation_id = "test-corr-id"
        
        # Step 1: INIT -> SENT
        status = task.step(ctx)
        
        assert status == TaskStatus.RUNNING
        assert task._state == TaskState.SENT
        
        # Verify message was sent via bot_service.send_message
        # and it contains the correct data
        mock_bot_service.send_message.assert_called_once()
        message_data = mock_bot_service.send_message.call_args[0][0]
        assert isinstance(message_data, ServiceMessage)
        assert message_data.service == "baritone"
        assert message_data.method == "goto"
        assert message_data.params == {"x": 10, "y": 20, "z": 30}
        assert message_data.correlation_id == "test-corr-id"
        assert message_data.request_id == task.request_id

    def test_goto_task_handles_response(self):
        mock_bot_service = Mock()
        ctx = Context(
            message_sender=Mock(),
            blackboard=Mock(),
            bot_service=mock_bot_service,
            mqtt=None
        )
        
        task = GotoTask.create(x=10, y=20, z=30)
        task._state = TaskState.SENT
        task.request_id = "test-req-id"
        
        # Mock successful response
        mock_bot_service.get_result.return_value = RequestResult(
            request_id="test-req-id",
            status=RequestStatus.SUCCESS
        )
        
        # Step: SENT -> WAITING -> SUCCESS
        status = task.step(ctx)
        assert status == TaskStatus.RUNNING
        assert task._state == TaskState.WAITING
        
        status = task.step(ctx)
        assert status == TaskStatus.SUCCESS

    def test_goto_task_suspend_resume(self):
        ctx = Context(
            message_sender=Mock(),
            blackboard=Mock(),
            bot_service=Mock(),
            mqtt=None
        )
        
        task = GotoTask.create(x=10, y=20, z=30)
        task.request_id = "test-req-id"
        task._state = TaskState.SENT
        
        task.suspend()
        assert task._state == TaskState.SUSPENDED
        
        task.resume(ctx)
        assert task._state == TaskState.SENT
        assert task.request_id == "test-req-id"
