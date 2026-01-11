import asyncio
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from mqttbot import MessageData
from mqttbot.core.context import Context


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
    - Sending a MessageData request
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

    def send_message(self, message_data: MessageData) -> str:
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

    def get_result(self, request_id: str) -> Optional[RequestResult]:
        """
        Check if response arrived (non-blocking).
        
        Args:
            request_id: The request ID to check
            
        Returns:
            RequestResult if available, None if still pending
        """
        with self._lock:
            if request_id not in self.pending_requests:
                return None
            return self.pending_requests[request_id]

    def handle_response(self, message_data: MessageData) -> None:
        """
        Called when MQTT response arrives. Handles status == "success" or status == "failure".
        
        Args:
            message_data: The response message data
        """
        request_id = message_data.request_id
        # Use service name from message for better logging (supports multiple services)
        service_name = message_data.service or self.service_name

        if not request_id:
            print(f"[{service_name}] No request_id in response: {message_data}")
            return

        with self._lock:
            if request_id not in self.pending_requests:
                print(f"[{service_name}] Unknown request_id: {request_id}")
                return

            response = message_data.response or {}
            status = response.get("status", "unknown")

            if status == "success":
                self.pending_requests[request_id] = RequestResult(
                    request_id=request_id,
                    status=RequestStatus.SUCCESS,
                    response=response
                )
                print(f"[{service_name}] Request {request_id} succeeded")

            elif status == "failure":
                error = response.get("reason", status)
                self.pending_requests[request_id] = RequestResult(
                    request_id=request_id,
                    status=RequestStatus.FAILED,
                    error=error
                )
                print(f"[{service_name}] Request {request_id} failed: {error}")
            else:
                print(f"[{service_name}] Request {request_id} unknown status: {status}")

    async def send_and_wait(
        self, 
        message_data: MessageData, 
        timeout: float = 60.0
    ) -> RequestResult:
        """
        Send a message and wait asynchronously for success or failure.
        
        Args:
            message_data: The message to send
            timeout: Maximum time to wait in seconds
            
        Returns:
            RequestResult with status SUCCESS, FAILED, or TIMEOUT
        """
        request_id = self.send_message(message_data)
        start_time = time.time()

        while True:
            result = self.get_result(request_id)
            if result is not None:
                return result

            if time.time() - start_time > timeout:
                with self._lock:
                    if request_id in self.pending_requests:
                        self.pending_requests[request_id] = RequestResult(
                            request_id=request_id,
                            status=RequestStatus.TIMEOUT,
                            error=f"No response within {timeout}s"
                        )
                return self.pending_requests.get(request_id) or RequestResult(
                    request_id=request_id,
                    status=RequestStatus.TIMEOUT,
                    error=f"No response within {timeout}s"
                )

            await asyncio.sleep(0.1)  # Poll every 100ms
