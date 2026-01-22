"""
Session Manager

Manages connected client sessions for remote execution.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from .schemas import ClientSession, ClientStatus, ClientInfo


class SessionManager:
    """
    Manages client sessions for remote test execution.

    Thread-safe session management with:
    - Registration and deregistration
    - Heartbeat tracking
    - Automatic cleanup of stale sessions
    """

    def __init__(self, heartbeat_timeout: int = 60):
        """
        Initialize session manager.

        Args:
            heartbeat_timeout: Seconds before session is considered stale
        """
        self._sessions: Dict[str, ClientSession] = {}
        self._heartbeat_timeout = heartbeat_timeout
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the session manager and cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the session manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def register(self, client_name: str, client_info: Dict = None) -> ClientSession:
        """
        Register a new client session.

        Args:
            client_name: Human-readable client name
            client_info: Optional additional client metadata

        Returns:
            Created ClientSession
        """
        async with self._lock:
            session_id = str(uuid.uuid4())
            session = ClientSession(
                session_id=session_id,
                client_name=client_name,
                client_info=client_info or {},
                status=ClientStatus.CONNECTED,
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                browser_running=False,
            )
            self._sessions[session_id] = session
            return session

    async def unregister(self, session_id: str) -> bool:
        """
        Unregister a client session.

        Args:
            session_id: Session ID to remove

        Returns:
            True if session was removed
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    async def get_session(self, session_id: str) -> Optional[ClientSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID to lookup

        Returns:
            ClientSession if found, None otherwise
        """
        return self._sessions.get(session_id)

    async def update_heartbeat(self, session_id: str) -> bool:
        """
        Update session heartbeat timestamp.

        Args:
            session_id: Session to update

        Returns:
            True if session was updated
        """
        async with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].last_heartbeat = datetime.now()
                return True
            return False

    async def set_status(self, session_id: str, status: ClientStatus) -> bool:
        """
        Update session status.

        Args:
            session_id: Session to update
            status: New status

        Returns:
            True if session was updated
        """
        async with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = status
                return True
            return False

    async def set_browser_running(self, session_id: str, running: bool) -> bool:
        """
        Update browser running state.

        Args:
            session_id: Session to update
            running: Whether browser is running

        Returns:
            True if session was updated
        """
        async with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].browser_running = running
                return True
            return False

    async def get_all_sessions(self) -> Dict[str, ClientSession]:
        """Get all active sessions."""
        return dict(self._sessions)

    async def get_available_clients(self) -> list[ClientInfo]:
        """
        Get list of available (connected, not busy) clients.

        Returns:
            List of ClientInfo for available clients
        """
        clients = []
        for session in self._sessions.values():
            if session.status == ClientStatus.CONNECTED:
                clients.append(ClientInfo(
                    session_id=session.session_id,
                    client_name=session.client_name,
                    status=session.status,
                    connected_at=session.connected_at,
                    last_heartbeat=session.last_heartbeat,
                    browser_running=session.browser_running,
                ))
        return clients

    async def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._sessions)

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup stale sessions."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Log error but continue

    async def _cleanup_stale_sessions(self) -> None:
        """Remove sessions that haven't sent heartbeat recently."""
        async with self._lock:
            cutoff = datetime.now() - timedelta(seconds=self._heartbeat_timeout)
            stale = [
                sid for sid, session in self._sessions.items()
                if session.last_heartbeat < cutoff
            ]
            for sid in stale:
                del self._sessions[sid]


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
