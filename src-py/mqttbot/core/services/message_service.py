import threading
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from mqttbot import ServiceMessage
from mqttbot.core.threads.scheduler_context import Context


class RequestStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class RequestResult:
    """Result of a specific request"""

    request_id: str
    status: RequestStatus
    response: dict | None = None
    error: str | None = None


class MessageService:
    """
    Base service for handling MQTT message requests with response tracking.

    This service provides a common pattern for:
    - Sending a ServiceMessage request
    - Waiting for either status == "success" or status == "failure"
    - Tracking pending requests and their results
    """

    def __init__(self, ctx: Context, service_name: str):
        """
        Initialize the message service.

        Args:
            ctx: Context containing message_sender and other dependencies
            service_name: Name of the service (e.g., "baritone", "sleep")
        """
        self.ctx = ctx
        self.service_name = service_name
        self.pending_requests: dict[str, RequestResult | None] = {}
        self._lock = threading.Lock()

    def send_message(self, message_data: ServiceMessage) -> str:
        """
        Send a message and return the request_id immediately (non-blocking).

        Args:
            message_data: The message to send (must have request_id set)

        Returns:
            The request_id of the sent message
        """
        request_id = message_data.request_id

        with self._lock:
            self.pending_requests[request_id] = None  # Mark as pending

        # Send MQTT message (non-blocking)
        self.ctx.message_sender(message_data)

        return request_id

    def get_result(self, request_id: str) -> RequestResult | None:
        """
        Check if response arrived (non-blocking).

        Args:
            request_id: The request ID to check

        Returns:
            RequestResult if available, None if still pending
        """
        with self._lock:
            result = self.pending_requests.get(request_id)
            if not result:
                return None
            if result.status in (
                RequestStatus.SUCCESS,
                RequestStatus.FAILED,
                RequestStatus.TIMEOUT,
            ):
                self.pending_requests.pop(request_id)
            return result

    def handle_response(self, message_data: ServiceMessage) -> None:
        """
        Called when MQTT response arrives. Handles status == "success" or status == "failure".

        Args:
            message_data: The response message data
        """
        request_id = message_data.request_id

        service_name = message_data.service

        if not request_id:
            logger.warning(f"No request_id in response: {message_data}")
            raise ValueError("Response message missing request_id")

        logger.debug(f"pending_requests: {list(self.pending_requests.keys())}")

        with self._lock:
            if request_id not in self.pending_requests:
                logger.debug(f"Unknown request_id: {request_id}")
                return

            response = message_data.response or {}
            status = response.get("status", "unknown")

            if status == "success":
                self.pending_requests[request_id] = RequestResult(
                    request_id=request_id, status=RequestStatus.SUCCESS, response=response
                )
                logger.debug(f"Request {request_id} succeeded")

            elif status == "failure":
                error = response.get("reason", status)
                self.pending_requests[request_id] = RequestResult(
                    request_id=request_id, status=RequestStatus.FAILED, error=error
                )
                logger.error(f"Request {request_id} failed: {error}")
                logger.error(f"Full response: {message_data}")
            else:
                logger.warning(f"Request {request_id} unknown status: {status}")
                logger.warning(f"Full response: {message_data}")
