from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from mqttbot import ServiceMessage
from mqttbot.core.services.message_service import RequestResult, RequestStatus

"""Test helpers: Mock implementations of MessageService for unit tests.

Provides deterministic behaviors for send_message/get_result so tests can
exercise success/failure flows without running a real MQTT broker.

Usage examples:
    svc = make_success_service()
    req = svc.send_message(msg)
    result = svc.get_result(req)  # will be a RequestResult with SUCCESS

    svc = make_delayed_service()
    req = svc.send_message(msg)
    svc.simulate_response(req, RequestStatus.SUCCESS)
    result = svc.get_result(req)
"""

class MockMessageService:
    """A lightweight mock of MessageService suitable for unit tests.

    Parameters
    - auto_response: if "success" or "failure" the mock will immediately
      populate a RequestResult when send_message is called. If None the mock
      will leave the request pending until simulate_response is used.
    - response_payload: optional dict used as the response body for success
      responses or to populate the error reason for failures.
    """

    def __init__(self, auto_response: Optional[str] = None, response_payload: Optional[Dict[str, Any]] = None):
        self.auto_response = auto_response
        self.response_payload = response_payload or {}
        # request_id -> RequestResult | None
        self.pending_requests: Dict[str, Optional[RequestResult]] = {}
        # history of messages sent through this mock
        self.sent_messages: List[ServiceMessage] = []

    def send_message(self, message_data: ServiceMessage) -> str:
        """Mimic MessageService.send_message: register as pending and optionally respond.

        Returns the request_id used.
        """
        request_id = message_data.request_id
        self.pending_requests[request_id] = None
        self.sent_messages.append(message_data)

        if self.auto_response == "success":
            self.pending_requests[request_id] = RequestResult(
                request_id=request_id,
                status=RequestStatus.SUCCESS,
                response=self.response_payload or {},
            )
        elif self.auto_response == "failure":
            self.pending_requests[request_id] = RequestResult(
                request_id=request_id,
                status=RequestStatus.FAILED,
                error=self.response_payload.get("reason", "mock failure"),
            )

        return request_id

    def get_result(self, request_id: str) -> Optional[RequestResult]:
        """Return the RequestResult if available. If the result is final it is
        removed from the pending map to simulate consumption by the caller.
        """
        result = self.pending_requests.get(request_id)
        if not result:
            return None
        if result.status in (RequestStatus.SUCCESS, RequestStatus.FAILED, RequestStatus.TIMEOUT):
            # mimic MessageService behavior of popping final results
            self.pending_requests.pop(request_id, None)
        return result

    def simulate_response(self, request_id: str, status: RequestStatus = RequestStatus.SUCCESS, response: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """Manually inject a response for a pending request."""
        if request_id not in self.pending_requests:
            raise KeyError(f"Unknown request_id: {request_id}")
        self.pending_requests[request_id] = RequestResult(
            request_id=request_id,
            status=status,
            response=response,
            error=error,
        )


# Convenience factories

def make_success_service(response_payload: Optional[Dict[str, Any]] = None) -> MockMessageService:
    return MockMessageService(auto_response="success", response_payload=response_payload)


def make_failure_service(reason: str = "mock failure") -> MockMessageService:
    return MockMessageService(auto_response="failure", response_payload={"reason": reason})


def make_delayed_service() -> MockMessageService:
    """A service that leaves requests pending until simulate_response is called."""
    return MockMessageService(auto_response=None)
