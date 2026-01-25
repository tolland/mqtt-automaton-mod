from typing import Optional

from mqttbot.core.protocol.task_status import TaskStatus


class GotoWaitingForAckState:
    external_status = TaskStatus.RUNNING

    def step(self, task: "GotoTask", ctx: "Context") -> Optional[TaskState]:
        # Check if the response has arrived in the context/blackboard
        response = ctx.get_response(task.request_id)

        if response and response.is_success:
            # Success! Pop this state and move to the 'Moving' phase
            task.pop_state()
            return GotoMovingState()

        if time.time() - task.last_sent_time > 30:
            return GlobalFailedState(reason="Timeout waiting for Baritone ACK")

        return None  # Keep waiting

    def handle_suspend(self, task: "GotoTask", ctx: "Context") -> Optional[TaskState]:
        # Push a SUSPENDING state that waits for the ACK before finally yielding
        return GotoSuspendingWaitState()
