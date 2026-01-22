from unittest.mock import Mock

from mqttbot import ServiceMessage
from mqttbot.core.services.message_service import RequestResult, RequestStatus
from mqttbot.core.tasks.goto_task import GotoTask
from mqttbot.core.tasks.task_status import TaskInternalState, TaskStatus
from mqttbot.core.threads.scheduler_context import Context


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

        task.enter(ctx)

        # Step 1: INIT -> SENT
        status = task.step(ctx)

        assert status == TaskStatus.RUNNING
        assert task._state == TaskInternalState.SENT

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
        task._state = TaskInternalState.SENT
        task.request_id = "test-req-id"

        # Mock successful response
        mock_bot_service.get_result.return_value = RequestResult(
            request_id="test-req-id",
            status=RequestStatus.SUCCESS
        )

        # Step: SENT -> WAITING -> SUCCESS
        status = task.step(ctx)
        assert status == TaskStatus.RUNNING
        assert task._state == TaskInternalState.WAITING

        status = task.step(ctx)
        assert status == TaskStatus.SUCCESS

    def test_goto_task_suspend_resume(self):
        mock_bot_service = Mock()
        ctx = Context(
            message_sender=Mock(),
            blackboard=Mock(),
            bot_service=mock_bot_service,
            mqtt=None
        )

        task = GotoTask.create(x=10, y=20, z=30)
        task.request_id = "test-req-id"
        task._state = TaskInternalState.SENT
        task.correlation_id = "test-corr-id"

        # Trigger suspension
        task.suspend(ctx)
        assert task._state == TaskInternalState.SUSPEND
        task.step(ctx)

        # Verify cancel message was sent
        mock_bot_service.send_message.assert_called_once()
        msg = mock_bot_service.send_message.call_args[0][0]
        assert isinstance(msg, ServiceMessage)
        assert msg.method == "cancel"
        assert msg.params["request_id"] == "test-req-id"
        assert msg.correlation_id == "test-corr-id"

        # Resume
        task.resume(ctx)
        assert task._state == TaskInternalState.INIT
        assert task.request_id is None

    def test_goto_task_suspend_without_request_id(self):
        mock_bot_service = Mock()
        ctx = Context(
            message_sender=Mock(),
            blackboard=Mock(),
            bot_service=mock_bot_service,
            mqtt=None
        )

        task = GotoTask.create(x=10, y=20, z=30)
        task.request_id = None
        task._state = TaskInternalState.INIT

        # Trigger suspension
        task.suspend(ctx)
        assert task._state == TaskInternalState.SUSPEND

        # Verify NO cancel message was sent
        mock_bot_service.send_message.assert_not_called()
