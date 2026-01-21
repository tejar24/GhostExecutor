"""
SSE Streaming Module

Server-Sent Events endpoint for live log streaming during test execution.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

# Per-run event queues for SSE streaming
_event_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
_run_status: Dict[str, str] = {}  # "running", "completed", "error"


async def emit_log(run_id: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    Emit a log event to all connected SSE clients for a run.

    Args:
        run_id: The test run ID
        event_type: Type of event (step_start, step_result, scenario_start, scenario_end, etc.)
        data: Event data payload
    """
    if run_id not in _event_queues:
        _event_queues[run_id] = asyncio.Queue()

    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    await _event_queues[run_id].put(event)


def emit_log_sync(run_id: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    Synchronous version of emit_log for use in non-async contexts.
    Creates a new event loop if needed.
    """
    if run_id not in _event_queues:
        _event_queues[run_id] = asyncio.Queue()

    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    # Try to use existing event loop, or create new one for sync context
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, use thread-safe method
            asyncio.run_coroutine_threadsafe(
                _event_queues[run_id].put(event),
                loop
            )
        else:
            loop.run_until_complete(_event_queues[run_id].put(event))
    except RuntimeError:
        # No event loop, put directly (will work for simple Queue)
        _event_queues[run_id].put_nowait(event)


def mark_run_completed(run_id: str, status: str = "completed") -> None:
    """Mark a run as completed so SSE stream knows to end."""
    _run_status[run_id] = status
    # Send completion event
    emit_log_sync(run_id, "run_complete", {"status": status})


def mark_run_started(run_id: str) -> None:
    """Mark a run as started."""
    _run_status[run_id] = "running"
    _event_queues[run_id] = asyncio.Queue()


def cleanup_run(run_id: str) -> None:
    """Cleanup resources for a completed run."""
    if run_id in _event_queues:
        del _event_queues[run_id]
    if run_id in _run_status:
        del _run_status[run_id]


async def event_generator(run_id: str):
    """Generate SSE events for a run."""
    queue = _event_queues.get(run_id)
    if not queue:
        queue = asyncio.Queue()
        _event_queues[run_id] = queue

    # Send initial connection event
    yield {
        "event": "connected",
        "data": json.dumps({"run_id": run_id, "message": "Connected to log stream"})
    }

    try:
        while True:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)

                yield {
                    "event": event["type"],
                    "data": json.dumps(event)
                }

                # Check if run is complete
                if event["type"] == "run_complete":
                    break

            except asyncio.TimeoutError:
                # Send keepalive
                yield {
                    "event": "keepalive",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()})
                }

                # Check if run completed while we were waiting
                if _run_status.get(run_id) in ("completed", "error"):
                    break

    except asyncio.CancelledError:
        pass


@router.get(
    "/tests/{run_id}/stream",
    tags=["Tests"],
    summary="Stream test execution logs via SSE",
)
async def stream_test_logs(run_id: str):
    """
    Stream live test execution logs via Server-Sent Events.

    Connect to this endpoint to receive real-time updates about test execution:
    - step_start: When a step begins
    - step_result: When a step completes (pass/fail)
    - scenario_start: When a scenario begins
    - scenario_end: When a scenario completes
    - healing: When auto-healing is attempted
    - run_complete: When the entire run finishes

    The connection will remain open until the run completes or an error occurs.
    """
    return EventSourceResponse(event_generator(run_id))


@router.get(
    "/tests/{run_id}/logs",
    tags=["Tests"],
    summary="Get buffered logs for a run",
)
async def get_buffered_logs(run_id: str):
    """
    Get any buffered logs for a run (for clients that missed SSE events).
    """
    # This is a fallback for non-SSE clients
    from .routes import _running_tests

    if run_id not in _running_tests:
        raise HTTPException(status_code=404, detail="Test run not found")

    run_data = _running_tests[run_id]

    return {
        "run_id": run_id,
        "status": run_data.get("status"),
        "logs": run_data.get("logs", []),
    }
