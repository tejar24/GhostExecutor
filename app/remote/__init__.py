"""
Remote Execution Module

Provides client-server architecture for distributed test execution.
"""

from .schemas import (
    MessageType,
    ActionType,
    ClientStatus,
    WebSocketMessage,
    ClientRegisterMessage,
    PageStateMessage,
    ActionResultMessage,
    HeartbeatMessage,
    ErrorMessage,
    ServerAckMessage,
    StartBrowserMessage,
    StopBrowserMessage,
    RequestPageStateMessage,
    ExecuteActionMessage,
    HeartbeatAckMessage,
    ClientSession,
    ClientInfo,
    ClientListResponse,
    RemoteRunRequest,
    RemoteRunResponse,
)
from .session_manager import SessionManager
from .websocket_hub import WebSocketHub
from .orchestrator import RemoteBrowserProxy, RemoteTestOrchestrator

__all__ = [
    # Message types
    "MessageType",
    "ActionType",
    "ClientStatus",
    # Messages
    "WebSocketMessage",
    "ClientRegisterMessage",
    "PageStateMessage",
    "ActionResultMessage",
    "HeartbeatMessage",
    "ErrorMessage",
    "ServerAckMessage",
    "StartBrowserMessage",
    "StopBrowserMessage",
    "RequestPageStateMessage",
    "ExecuteActionMessage",
    "HeartbeatAckMessage",
    # Session
    "ClientSession",
    "ClientInfo",
    "ClientListResponse",
    # API
    "RemoteRunRequest",
    "RemoteRunResponse",
    # Managers
    "SessionManager",
    "WebSocketHub",
    "RemoteBrowserProxy",
    "RemoteTestOrchestrator",
]
