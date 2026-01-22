"""
Remote Execution Schemas

WebSocket message types and data classes for client-server communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WebSocket message types."""
    # Client -> Server
    CLIENT_REGISTER = "client_register"
    PAGE_STATE = "page_state"
    ACTION_RESULT = "action_result"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

    # Server -> Client
    SERVER_ACK = "server_ack"
    START_BROWSER = "start_browser"
    STOP_BROWSER = "stop_browser"
    REQUEST_PAGE_STATE = "request_page_state"
    EXECUTE_ACTION = "execute_action"
    HEARTBEAT_ACK = "heartbeat_ack"


class ActionType(str, Enum):
    """Browser action types."""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    PRESS_KEY = "press_key"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_URL = "wait_for_url"
    SCROLL = "scroll"
    HOVER = "hover"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    CLEAR = "clear"
    TAKE_SCREENSHOT = "take_screenshot"
    EXECUTE_SCRIPT = "execute_script"


class ClientStatus(str, Enum):
    """Client connection status."""
    CONNECTED = "connected"
    BUSY = "busy"
    DISCONNECTED = "disconnected"


# Base message
class WebSocketMessage(BaseModel):
    """Base WebSocket message."""
    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


# Client -> Server Messages

class ClientRegisterMessage(WebSocketMessage):
    """Client registration message."""
    type: MessageType = MessageType.CLIENT_REGISTER
    client_name: str
    client_info: Dict[str, Any] = Field(default_factory=dict)


class PageStateMessage(WebSocketMessage):
    """Page state response from client."""
    type: MessageType = MessageType.PAGE_STATE
    url: str
    title: str
    ready_state: str
    dom_snapshot: Dict[str, Any]
    screenshot: Optional[str] = None  # Base64 encoded


class ActionResultMessage(WebSocketMessage):
    """Action result from client."""
    type: MessageType = MessageType.ACTION_RESULT
    success: bool
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None
    duration_ms: float = 0.0


class HeartbeatMessage(WebSocketMessage):
    """Heartbeat from client."""
    type: MessageType = MessageType.HEARTBEAT


class ErrorMessage(WebSocketMessage):
    """Error message from client."""
    type: MessageType = MessageType.ERROR
    error: str
    details: Optional[str] = None


# Server -> Client Messages

class ServerAckMessage(WebSocketMessage):
    """Server acknowledgment of client registration."""
    type: MessageType = MessageType.SERVER_ACK
    session_id: str
    message: str = "Registration successful"


class StartBrowserMessage(WebSocketMessage):
    """Command to start browser."""
    type: MessageType = MessageType.START_BROWSER
    headless: bool = False
    slow_mo: int = 100


class StopBrowserMessage(WebSocketMessage):
    """Command to stop browser."""
    type: MessageType = MessageType.STOP_BROWSER


class RequestPageStateMessage(WebSocketMessage):
    """Request page state from client."""
    type: MessageType = MessageType.REQUEST_PAGE_STATE
    include_screenshot: bool = False


class ExecuteActionMessage(WebSocketMessage):
    """Command to execute browser action."""
    type: MessageType = MessageType.EXECUTE_ACTION
    action: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: int = 10000


class HeartbeatAckMessage(WebSocketMessage):
    """Heartbeat acknowledgment."""
    type: MessageType = MessageType.HEARTBEAT_ACK


# Session Management

class ClientSession(BaseModel):
    """Represents a connected client session."""
    session_id: str
    client_name: str
    client_info: Dict[str, Any] = Field(default_factory=dict)
    status: ClientStatus = ClientStatus.CONNECTED
    connected_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    browser_running: bool = False


# API Schemas

class ClientInfo(BaseModel):
    """Client information for API response."""
    session_id: str
    client_name: str
    status: ClientStatus
    connected_at: datetime
    last_heartbeat: datetime
    browser_running: bool


class ClientListResponse(BaseModel):
    """List of connected clients."""
    clients: List[ClientInfo]
    total: int


class RemoteRunRequest(BaseModel):
    """Request to run test on remote client."""
    session_id: str
    feature_content: str
    headless: bool = False
    slow_mo: int = 100


class RemoteRunResponse(BaseModel):
    """Response for remote test run."""
    run_id: str
    session_id: str
    status: str = "started"
    message: str = "Test run initiated on remote client"
