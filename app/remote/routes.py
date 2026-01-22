"""
Remote Execution API Routes

FastAPI routes for remote test execution.
"""

import asyncio
import uuid
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks

from .schemas import (
    MessageType,
    ClientStatus,
    ClientInfo,
    ClientListResponse,
    RemoteRunRequest,
    RemoteRunResponse,
    ServerAckMessage,
)
from .session_manager import get_session_manager
from .websocket_hub import get_websocket_hub
from .orchestrator import RemoteTestOrchestrator


router = APIRouter(tags=["Remote Execution"])

# Track running tests
_running_tests: Dict[str, Dict[str, Any]] = {}


@router.websocket("/remote/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for remote client connections.

    Protocol:
    1. Client connects and sends client_register message
    2. Server acknowledges with session_id
    3. Client receives commands and sends results
    4. Heartbeats maintain connection
    """
    await websocket.accept()

    session_manager = get_session_manager()
    websocket_hub = get_websocket_hub()

    # Ensure session manager is started
    await session_manager.start()

    session_id = None

    try:
        # Wait for registration message
        registration_data = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=30.0
        )

        if registration_data.get("type") != MessageType.CLIENT_REGISTER.value:
            await websocket.close(code=4001, reason="Expected client_register message")
            return

        # Register client session
        client_name = registration_data.get("client_name", "Unknown")
        client_info = registration_data.get("client_info", {})

        session = await session_manager.register(client_name, client_info)
        session_id = session.session_id

        # Register WebSocket connection
        await websocket_hub.connect(session_id, websocket)

        # Send acknowledgment
        ack = ServerAckMessage(
            session_id=session_id,
            message=f"Welcome {client_name}! Session ID: {session_id}",
        )
        await websocket.send_json(ack.model_dump(mode="json"))

        print(f"[Remote] Client connected: {client_name} ({session_id})")

        # Main message loop
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                # Handle heartbeat
                if message_type == MessageType.HEARTBEAT.value:
                    await session_manager.update_heartbeat(session_id)
                    await websocket_hub.send_heartbeat_ack(session_id, data.get("request_id"))
                    continue

                # Route message through hub (handles request/response correlation)
                await websocket_hub.handle_message(session_id, data)

            except asyncio.TimeoutError:
                # No message received, check if connection is still alive
                continue

    except WebSocketDisconnect:
        print(f"[Remote] Client disconnected: {session_id}")
    except asyncio.TimeoutError:
        print(f"[Remote] Client registration timeout")
        await websocket.close(code=4002, reason="Registration timeout")
    except Exception as e:
        print(f"[Remote] WebSocket error: {e}")
    finally:
        # Cleanup
        if session_id:
            await websocket_hub.disconnect(session_id)
            await session_manager.unregister(session_id)
            print(f"[Remote] Session cleaned up: {session_id}")


@router.get("/remote/clients", response_model=ClientListResponse)
async def list_clients():
    """
    List all connected remote clients.

    Returns list of clients with their connection status and details.
    """
    session_manager = get_session_manager()
    sessions = await session_manager.get_all_sessions()

    clients = []
    for session in sessions.values():
        clients.append(ClientInfo(
            session_id=session.session_id,
            client_name=session.client_name,
            status=session.status,
            connected_at=session.connected_at,
            last_heartbeat=session.last_heartbeat,
            browser_running=session.browser_running,
        ))

    return ClientListResponse(clients=clients, total=len(clients))


@router.get("/remote/clients/{session_id}")
async def get_client(session_id: str):
    """
    Get details for a specific connected client.

    Args:
        session_id: Client session ID

    Returns:
        Client information
    """
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientInfo(
        session_id=session.session_id,
        client_name=session.client_name,
        status=session.status,
        connected_at=session.connected_at,
        last_heartbeat=session.last_heartbeat,
        browser_running=session.browser_running,
    )


@router.post("/remote/run", response_model=RemoteRunResponse)
async def run_remote_test(
    request: RemoteRunRequest,
    background_tasks: BackgroundTasks
):
    """
    Start test execution on a remote client.

    The test runs asynchronously. Use the streaming endpoint to monitor progress.

    Args:
        request: Remote run request with session_id and feature content

    Returns:
        Run response with run_id
    """
    session_manager = get_session_manager()
    websocket_hub = get_websocket_hub()

    # Verify client is connected
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Client not found")

    if session.status == ClientStatus.BUSY:
        raise HTTPException(status_code=409, detail="Client is busy with another test")

    if not websocket_hub.is_connected(request.session_id):
        raise HTTPException(status_code=503, detail="Client is not connected")

    # Generate run ID
    run_id = str(uuid.uuid4())

    # Mark client as busy
    await session_manager.set_status(request.session_id, ClientStatus.BUSY)

    # Track running test
    _running_tests[run_id] = {
        "session_id": request.session_id,
        "status": "starting",
        "result": None,
    }

    # Start test execution in background
    background_tasks.add_task(
        _execute_remote_test,
        run_id,
        request.session_id,
        request.feature_content,
        request.headless,
        request.slow_mo,
    )

    return RemoteRunResponse(
        run_id=run_id,
        session_id=request.session_id,
        status="started",
        message="Test execution started on remote client",
    )


async def _execute_remote_test(
    run_id: str,
    session_id: str,
    feature_content: str,
    headless: bool,
    slow_mo: int,
):
    """Background task to execute test on remote client."""
    session_manager = get_session_manager()

    print(f"[Remote Routes] Starting remote test execution")
    print(f"[Remote Routes] Run ID: {run_id}")
    print(f"[Remote Routes] Session ID: {session_id}")
    print(f"[Remote Routes] Feature content:\n{feature_content[:500]}...")

    try:
        # Create orchestrator
        orchestrator = RemoteTestOrchestrator(
            session_id=session_id,
            emit_callback=lambda event, data: _emit_test_event(run_id, event, data),
        )

        # Update test status
        _running_tests[run_id]["status"] = "running"

        # Run the test
        result = await orchestrator.run_feature_content(
            feature_content=feature_content,
            headless=headless,
            slow_mo=slow_mo,
        )

        print(f"[Remote Routes] Test completed with status: {result.get('status')}")

        # Store result
        _running_tests[run_id]["status"] = result.get("status", "completed")
        _running_tests[run_id]["result"] = result

    except Exception as e:
        print(f"[Remote Routes] Test execution error: {e}")
        import traceback
        traceback.print_exc()
        _running_tests[run_id]["status"] = "error"
        _running_tests[run_id]["result"] = {"error": str(e)}

    finally:
        # Mark client as available again
        await session_manager.set_status(session_id, ClientStatus.CONNECTED)


def _emit_test_event(run_id: str, event: str, data: Dict[str, Any]):
    """Emit test event (can be extended to use SSE)."""
    # For now, just update the status
    if run_id in _running_tests:
        _running_tests[run_id]["last_event"] = {"event": event, "data": data}


@router.get("/remote/run/{run_id}")
async def get_run_status(run_id: str):
    """
    Get status of a remote test run.

    Args:
        run_id: Test run ID

    Returns:
        Run status and result if completed
    """
    if run_id not in _running_tests:
        raise HTTPException(status_code=404, detail="Run not found")

    return _running_tests[run_id]


@router.delete("/remote/run/{run_id}")
async def cancel_run(run_id: str):
    """
    Cancel a running remote test.

    Args:
        run_id: Test run ID

    Returns:
        Cancellation status
    """
    if run_id not in _running_tests:
        raise HTTPException(status_code=404, detail="Run not found")

    # Mark as cancelled
    _running_tests[run_id]["status"] = "cancelled"

    return {"status": "cancelled", "run_id": run_id}


@router.get("/remote/health")
async def remote_health():
    """
    Health check for remote execution subsystem.

    Returns:
        Health status with connected client count
    """
    session_manager = get_session_manager()
    websocket_hub = get_websocket_hub()

    return {
        "status": "healthy",
        "connected_clients": websocket_hub.get_connected_count(),
        "active_sessions": await session_manager.get_client_count(),
        "running_tests": len([t for t in _running_tests.values() if t["status"] == "running"]),
    }
