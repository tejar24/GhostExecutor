"""
WebSocket Hub

Central WebSocket communication hub for client-server messaging.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from fastapi import WebSocket

from .schemas import (
    MessageType,
    WebSocketMessage,
    ServerAckMessage,
    HeartbeatAckMessage,
)


class WebSocketHub:
    """
    Central hub for WebSocket communication with clients.

    Provides:
    - Connection management
    - Message sending/receiving
    - Request/response pattern with correlation IDs
    - Broadcast capabilities
    """

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """
        Register a WebSocket connection.

        Args:
            session_id: Client session ID
            websocket: WebSocket connection
        """
        async with self._lock:
            self._connections[session_id] = websocket

    async def disconnect(self, session_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            session_id: Client session ID
        """
        async with self._lock:
            if session_id in self._connections:
                del self._connections[session_id]

    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        """
        Get WebSocket connection for a session.

        Args:
            session_id: Client session ID

        Returns:
            WebSocket if connected, None otherwise
        """
        return self._connections.get(session_id)

    def is_connected(self, session_id: str) -> bool:
        """Check if session has active connection."""
        return session_id in self._connections

    async def send_message(self, session_id: str, message: WebSocketMessage) -> bool:
        """
        Send a message to a specific client.

        Args:
            session_id: Target client session ID
            message: Message to send

        Returns:
            True if message was sent
        """
        websocket = self._connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message.model_dump(mode="json"))
                return True
            except Exception:
                return False
        return False

    async def send_raw(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Send raw JSON data to a client.

        Args:
            session_id: Target client session ID
            data: Data to send

        Returns:
            True if message was sent
        """
        websocket = self._connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(data)
                return True
            except Exception:
                return False
        return False

    async def broadcast(self, message: WebSocketMessage) -> int:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast

        Returns:
            Number of clients that received the message
        """
        sent = 0
        data = message.model_dump(mode="json")
        for websocket in self._connections.values():
            try:
                await websocket.send_json(data)
                sent += 1
            except Exception:
                pass
        return sent

    async def request(
        self,
        session_id: str,
        message: WebSocketMessage,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for response with matching request_id.

        Args:
            session_id: Target client session ID
            message: Request message
            timeout: Timeout in seconds

        Returns:
            Response data or None if timeout/error
        """
        # Generate request ID if not set
        if not message.request_id:
            message.request_id = str(uuid.uuid4())

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[message.request_id] = future

        try:
            # Send request
            sent = await self.send_message(session_id, message)
            if not sent:
                return None

            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            return None
        finally:
            # Cleanup
            self._pending_requests.pop(message.request_id, None)

    def resolve_request(self, request_id: str, response: Dict[str, Any]) -> bool:
        """
        Resolve a pending request with response data.

        Args:
            request_id: Request ID to resolve
            response: Response data

        Returns:
            True if request was resolved
        """
        future = self._pending_requests.get(request_id)
        if future and not future.done():
            future.set_result(response)
            return True
        return False

    def register_handler(self, message_type: MessageType, handler: Callable) -> None:
        """
        Register a handler for a message type.

        Args:
            message_type: Message type to handle
            handler: Handler function (async or sync)
        """
        self._message_handlers[message_type] = handler

    async def handle_message(self, session_id: str, data: Dict[str, Any]) -> Optional[WebSocketMessage]:
        """
        Process an incoming message and route to appropriate handler.

        Args:
            session_id: Source client session ID
            data: Message data

        Returns:
            Response message if any
        """
        message_type_str = data.get("type")
        request_id = data.get("request_id")

        # Check if this is a response to a pending request
        if request_id and request_id in self._pending_requests:
            self.resolve_request(request_id, data)
            return None

        # Route to registered handler
        try:
            message_type = MessageType(message_type_str)
            handler = self._message_handlers.get(message_type)
            if handler:
                result = handler(session_id, data)
                if asyncio.iscoroutine(result):
                    return await result
                return result
        except (ValueError, KeyError):
            pass  # Unknown message type

        return None

    async def send_ack(self, session_id: str, original_request_id: str = None) -> bool:
        """
        Send acknowledgment message.

        Args:
            session_id: Target client session ID
            original_request_id: Request ID being acknowledged

        Returns:
            True if sent
        """
        ack = ServerAckMessage(
            session_id=session_id,
            request_id=original_request_id,
        )
        return await self.send_message(session_id, ack)

    async def send_heartbeat_ack(self, session_id: str, request_id: str = None) -> bool:
        """
        Send heartbeat acknowledgment.

        Args:
            session_id: Target client session ID
            request_id: Request ID from heartbeat

        Returns:
            True if sent
        """
        ack = HeartbeatAckMessage(request_id=request_id)
        return await self.send_message(session_id, ack)

    def get_connected_count(self) -> int:
        """Get number of connected clients."""
        return len(self._connections)

    def get_connected_sessions(self) -> list[str]:
        """Get list of connected session IDs."""
        return list(self._connections.keys())


# Global hub instance
_websocket_hub: Optional[WebSocketHub] = None


def get_websocket_hub() -> WebSocketHub:
    """Get or create the global WebSocket hub."""
    global _websocket_hub
    if _websocket_hub is None:
        _websocket_hub = WebSocketHub()
    return _websocket_hub
