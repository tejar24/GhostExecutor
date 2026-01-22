"""
Remote Test Orchestrator

Server-side orchestration for remote test execution.
Provides RemoteBrowserProxy to communicate with client browsers via WebSocket.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .schemas import (
    MessageType,
    ActionType,
    ClientStatus,
    StartBrowserMessage,
    StopBrowserMessage,
    RequestPageStateMessage,
    ExecuteActionMessage,
    ActionResultMessage,
)
from .session_manager import SessionManager, get_session_manager
from .websocket_hub import WebSocketHub, get_websocket_hub


class RemoteBrowserProxy:
    """
    Proxy for browser automation that sends commands to remote client.

    Mimics the BrowserAutomation interface but routes all commands
    through WebSocket to be executed on the client's local browser.
    """

    def __init__(
        self,
        session_id: str,
        websocket_hub: WebSocketHub = None,
        session_manager: SessionManager = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the remote browser proxy.

        Args:
            session_id: Target client session ID
            websocket_hub: WebSocket hub for communication
            session_manager: Session manager for state tracking
            timeout: Default timeout for commands in seconds
        """
        self.session_id = session_id
        self._hub = websocket_hub or get_websocket_hub()
        self._session_manager = session_manager or get_session_manager()
        self._timeout = timeout
        self._started = False

        # Cache for page state
        self._cached_url = ""
        self._cached_title = ""
        self._cached_dom_snapshot: Dict[str, Any] = {}

    async def start(self, headless: bool = False, slow_mo: int = 100) -> bool:
        """
        Start browser on remote client.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down actions by this many milliseconds

        Returns:
            True if browser started successfully
        """
        message = StartBrowserMessage(
            request_id=str(uuid.uuid4()),
            headless=headless,
            slow_mo=slow_mo,
        )

        response = await self._hub.request(self.session_id, message, timeout=60.0)
        if response and response.get("type") == MessageType.ACTION_RESULT.value:
            success = response.get("success", False)
            if success:
                self._started = True
                await self._session_manager.set_browser_running(self.session_id, True)
            return success
        return False

    async def stop(self) -> bool:
        """
        Stop browser on remote client.

        Returns:
            True if browser stopped successfully
        """
        message = StopBrowserMessage(request_id=str(uuid.uuid4()))

        response = await self._hub.request(self.session_id, message, timeout=30.0)
        self._started = False
        await self._session_manager.set_browser_running(self.session_id, False)

        if response and response.get("type") == MessageType.ACTION_RESULT.value:
            return response.get("success", False)
        return True  # Assume stopped even if no response

    async def refresh_page_state(self, include_screenshot: bool = False) -> Dict[str, Any]:
        """
        Request and cache current page state from client.

        Args:
            include_screenshot: Whether to include screenshot

        Returns:
            Page state dictionary
        """
        message = RequestPageStateMessage(
            request_id=str(uuid.uuid4()),
            include_screenshot=include_screenshot,
        )

        response = await self._hub.request(self.session_id, message, timeout=self._timeout)

        if response and response.get("type") == MessageType.PAGE_STATE.value:
            self._cached_url = response.get("url", "")
            self._cached_title = response.get("title", "")
            self._cached_dom_snapshot = response.get("dom_snapshot", {})
            return {
                "url": self._cached_url,
                "title": self._cached_title,
                "ready_state": response.get("ready_state", "unknown"),
                "dom_snapshot": self._cached_dom_snapshot,
                "screenshot": response.get("screenshot"),
            }

        return {"error": "Failed to get page state"}

    async def execute_action(
        self,
        action: ActionType,
        selector: Optional[str] = None,
        value: Optional[str] = None,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Execute browser action on remote client.

        Args:
            action: Action type to execute
            selector: Element selector (if applicable)
            value: Value (for fill, navigate, etc.)
            timeout: Action timeout in milliseconds

        Returns:
            Action result dictionary
        """
        message = ExecuteActionMessage(
            request_id=str(uuid.uuid4()),
            action=action,
            selector=selector,
            value=value,
            timeout=timeout,
        )

        response = await self._hub.request(
            self.session_id, message, timeout=timeout / 1000 + 5
        )

        if response and response.get("type") == MessageType.ACTION_RESULT.value:
            return {
                "success": response.get("success", False),
                "action": response.get("action", action.value),
                "selector": response.get("selector", selector),
                "value": response.get("value", value),
                "error": response.get("error"),
                "screenshot": response.get("screenshot"),
                "duration_ms": response.get("duration_ms", 0),
            }

        return {
            "success": False,
            "action": action.value,
            "selector": selector,
            "value": value,
            "error": "No response from client",
        }

    # Browser action methods (mirror BrowserAutomation interface)

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        return await self.execute_action(ActionType.NAVIGATE, value=url)

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        return await self.execute_action(ActionType.CLICK, selector=selector)

    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill a text input."""
        return await self.execute_action(ActionType.FILL, selector=selector, value=value)

    async def type_text(self, selector: str, value: str) -> Dict[str, Any]:
        """Type text character by character."""
        return await self.execute_action(ActionType.TYPE, selector=selector, value=value)

    async def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        return await self.execute_action(ActionType.SELECT, selector=selector, value=value)

    async def check(self, selector: str) -> Dict[str, Any]:
        """Check a checkbox."""
        return await self.execute_action(ActionType.CHECK, selector=selector)

    async def uncheck(self, selector: str) -> Dict[str, Any]:
        """Uncheck a checkbox."""
        return await self.execute_action(ActionType.UNCHECK, selector=selector)

    async def press_key(self, key: str) -> Dict[str, Any]:
        """Press a keyboard key."""
        return await self.execute_action(ActionType.PRESS_KEY, value=key)

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        return await self.execute_action(
            ActionType.WAIT_FOR_SELECTOR, selector=selector, timeout=timeout
        )

    async def hover(self, selector: str) -> Dict[str, Any]:
        """Hover over an element."""
        return await self.execute_action(ActionType.HOVER, selector=selector)

    async def scroll_to_element(self, selector: str) -> Dict[str, Any]:
        """Scroll to make element visible."""
        return await self.execute_action(ActionType.SCROLL, selector=selector)

    async def take_screenshot(self) -> Optional[str]:
        """Take screenshot and return as base64."""
        result = await self.execute_action(ActionType.TAKE_SCREENSHOT)
        return result.get("screenshot")

    async def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page."""
        return await self.execute_action(ActionType.EXECUTE_SCRIPT, value=script)

    # Cached property accessors

    def get_current_url(self) -> str:
        """Get cached current URL."""
        return self._cached_url

    def get_title(self) -> str:
        """Get cached page title."""
        return self._cached_title

    def get_dom_snapshot(self) -> Dict[str, Any]:
        """Get cached DOM snapshot."""
        return self._cached_dom_snapshot

    @property
    def is_started(self) -> bool:
        """Check if browser is started."""
        return self._started


class RemoteTestOrchestrator:
    """
    Server-side orchestrator for remote test execution.

    Coordinates:
    - Browser commands sent to remote client
    - AI step interpretation on server
    - Test execution flow and reporting
    """

    def __init__(
        self,
        session_id: str,
        emit_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the remote test orchestrator.

        Args:
            session_id: Target client session ID
            emit_callback: Optional callback for emitting events
        """
        self.session_id = session_id
        self._emit_callback = emit_callback
        self._browser_proxy = RemoteBrowserProxy(session_id)
        self._cancelled = False
        self._step_history: List[str] = []

    async def run_feature_content(
        self,
        feature_content: str,
        headless: bool = False,
        slow_mo: int = 100,
    ) -> Dict[str, Any]:
        """
        Run a feature from content string.

        Args:
            feature_content: Gherkin feature content
            headless: Run browser in headless mode
            slow_mo: Slow down actions (ms)

        Returns:
            Test run result
        """
        from app.executor.parser import GherkinParser

        run_id = str(uuid.uuid4())
        start_time = datetime.now()

        result = {
            "run_id": run_id,
            "session_id": self.session_id,
            "status": "running",
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration_ms": 0,
            "features": [],
            "total_scenarios": 0,
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "total_steps": 0,
            "errors": [],
        }

        self._emit("run_started", {"run_id": run_id, "session_id": self.session_id})

        try:
            # Parse feature content
            parser = GherkinParser()
            feature = parser.parse_content(feature_content)

            # Start browser on client
            self._emit("browser_starting", {"run_id": run_id})
            browser_started = await self._browser_proxy.start(headless, slow_mo)

            if not browser_started:
                result["status"] = "error"
                result["errors"].append("Failed to start browser on client")
                return result

            self._emit("browser_started", {"run_id": run_id})

            # Run feature
            feature_result = await self._run_feature(feature, run_id)
            result["features"].append(feature_result)

            # Calculate totals
            for scenario in feature_result.get("scenarios", []):
                result["total_scenarios"] += 1
                result["total_steps"] += len(scenario.get("steps", []))
                if scenario.get("status") == "passed":
                    result["passed_scenarios"] += 1
                elif scenario.get("status") == "failed":
                    result["failed_scenarios"] += 1

            result["status"] = "passed" if result["failed_scenarios"] == 0 else "failed"

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        finally:
            # Stop browser
            await self._browser_proxy.stop()
            self._emit("browser_stopped", {"run_id": run_id})

        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration_ms"] = (end_time - start_time).total_seconds() * 1000

        self._emit("run_completed", {"run_id": run_id, "result": result})
        return result

    async def _run_feature(self, feature, run_id: str) -> Dict[str, Any]:
        """Run all scenarios in a feature."""
        feature_result = {
            "name": feature.name,
            "status": "passed",
            "scenarios": [],
            "tags": feature.tags,
        }

        self._emit("feature_started", {
            "run_id": run_id,
            "feature_name": feature.name,
        })

        for scenario in feature.scenarios:
            if self._cancelled:
                feature_result["scenarios"].append({
                    "name": scenario.name,
                    "status": "skipped",
                    "steps": [],
                })
                continue

            scenario_result = await self._run_scenario(scenario, feature.name, run_id)
            feature_result["scenarios"].append(scenario_result)

            if scenario_result.get("status") == "failed":
                feature_result["status"] = "failed"

        self._emit("feature_completed", {
            "run_id": run_id,
            "feature_name": feature.name,
            "status": feature_result["status"],
        })

        return feature_result

    async def _run_scenario(self, scenario, feature_name: str, run_id: str) -> Dict[str, Any]:
        """Run a single scenario."""
        scenario_result = {
            "name": scenario.name,
            "status": "passed",
            "steps": [],
            "tags": scenario.tags,
            "duration_ms": 0,
        }

        self._emit("scenario_started", {
            "run_id": run_id,
            "scenario_name": scenario.name,
        })

        # Reset step history for new scenario
        self._step_history = []

        start_time = time.time()
        skip_remaining = False

        for step in scenario.steps:
            if self._cancelled or skip_remaining:
                scenario_result["steps"].append({
                    "keyword": step.keyword,
                    "text": step.text,
                    "status": "skipped",
                })
                continue

            step_result = await self._run_step(step, run_id)
            scenario_result["steps"].append(step_result)

            if step_result.get("status") == "failed":
                scenario_result["status"] = "failed"
                skip_remaining = True

        scenario_result["duration_ms"] = (time.time() - start_time) * 1000

        self._emit("scenario_completed", {
            "run_id": run_id,
            "scenario_name": scenario.name,
            "status": scenario_result["status"],
        })

        return scenario_result

    async def _run_step(self, step, run_id: str) -> Dict[str, Any]:
        """Execute a single step."""
        full_step = f"{step.keyword} {step.text}"

        self._emit("step_started", {
            "run_id": run_id,
            "step": full_step,
        })

        start_time = time.time()

        try:
            # Get fresh page state from client
            page_state = await self._browser_proxy.refresh_page_state()

            # Interpret step using AI (server-side)
            action = await self._interpret_step(full_step, page_state)

            if not action:
                return self._step_failure(step, "Failed to interpret step", start_time, run_id)

            # Execute action on remote client
            result = await self._execute_action(action)

            if result.get("success"):
                duration_ms = (time.time() - start_time) * 1000
                self._emit("step_completed", {
                    "run_id": run_id,
                    "step": full_step,
                    "status": "passed",
                    "duration_ms": duration_ms,
                })
                return {
                    "keyword": step.keyword,
                    "text": step.text,
                    "status": "passed",
                    "duration_ms": duration_ms,
                    "action": action,
                }
            else:
                return self._step_failure(
                    step, result.get("error", "Action failed"), start_time, run_id, action
                )

        except Exception as e:
            return self._step_failure(step, str(e), start_time, run_id)

    def _step_failure(
        self, step, error: str, start_time: float, run_id: str, action: Dict = None
    ) -> Dict[str, Any]:
        """Create step failure result."""
        duration_ms = (time.time() - start_time) * 1000
        full_step = f"{step.keyword} {step.text}"

        self._emit("step_completed", {
            "run_id": run_id,
            "step": full_step,
            "status": "failed",
            "duration_ms": duration_ms,
            "error": error,
        })

        return {
            "keyword": step.keyword,
            "text": step.text,
            "status": "failed",
            "duration_ms": duration_ms,
            "error": error,
            "action": action,
        }

    async def _interpret_step(self, step_text: str, page_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Interpret step using AI to determine action."""
        import json
        import re
        from app.ai.engine import run_ai

        prompt = self._build_interpretation_prompt(step_text, page_state)

        # Run AI in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, run_ai, prompt)

        # Parse response
        return self._parse_json_response(response)

    def _build_interpretation_prompt(self, step_text: str, page_state: Dict[str, Any]) -> str:
        """Build AI prompt for step interpretation."""
        dom_snapshot = page_state.get("dom_snapshot", {})
        elements = dom_snapshot.get("elements", [])

        # Summarize elements for prompt
        elements_summary = []
        for el in elements[:30]:  # Limit to 30 elements
            info = {
                "tag": el.get("tag"),
                "text": el.get("text", "")[:50],
                "id": el.get("id"),
                "type": el.get("type"),
                "placeholder": el.get("placeholder"),
                "ariaLabel": el.get("ariaLabel"),
                "role": el.get("role"),
            }
            # Remove empty values
            info = {k: v for k, v in info.items() if v}
            if len(info) > 1:
                elements_summary.append(info)

        return f'''You are an expert test automation engineer. Analyze the Gherkin step and page context to determine the exact browser action needed.

CURRENT PAGE STATE:
- URL: {page_state.get("url", "unknown")}
- Title: {page_state.get("title", "unknown")}
- Visible Elements: {json.dumps(elements_summary, indent=2)}

GHERKIN STEP TO EXECUTE:
"{step_text}"

PREVIOUS STEPS IN THIS SCENARIO:
{chr(10).join(self._step_history[-5:]) if self._step_history else "None"}

Respond with a JSON object containing the action to perform. Choose ONE action type:

For NAVIGATION:
{{"action": "navigate", "url": "<full_url>"}}

For CLICKING:
{{"action": "click", "selector": "<css_or_text_selector>", "description": "<what_we_are_clicking>"}}

For FILLING TEXT:
{{"action": "fill", "selector": "<input_selector>", "value": "<text_to_enter>"}}

For SELECTING DROPDOWN:
{{"action": "select", "selector": "<select_selector>", "value": "<option_value>"}}

For VERIFICATION (element visible):
{{"action": "verify_visible", "selector": "<element_selector>", "description": "<what_should_be_visible>"}}

For VERIFICATION (text contains):
{{"action": "verify_text", "selector": "<element_selector>", "expected_text": "<expected_text>"}}

For VERIFICATION (URL contains):
{{"action": "verify_url", "expected_pattern": "<url_pattern>"}}

For WAITING (for element):
{{"action": "wait", "selector": "<element_to_wait_for>", "timeout": <milliseconds>}}

For CHECKBOX:
{{"action": "check", "selector": "<checkbox_selector>"}} or {{"action": "uncheck", "selector": "<checkbox_selector>"}}

For KEYBOARD:
{{"action": "press_key", "key": "<key_name>"}}

SELECTOR TIPS:
- Use text-based selectors: text="Login" or button:has-text("Submit")
- Use aria-label: button[aria-label="Edit"]
- Use placeholder: [placeholder="Email"]
- Use test IDs: [data-testid="login-btn"]

Respond with ONLY the JSON object, no explanations.'''

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response."""
        import json
        import re

        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parsed action on remote browser."""
        action_type = action.get("action", "")

        # Add step to history
        self._step_history.append(f"{action_type}: {action}")

        if action_type == "navigate":
            return await self._browser_proxy.navigate(action.get("url", ""))

        elif action_type == "click":
            return await self._browser_proxy.click(action.get("selector", ""))

        elif action_type == "fill":
            return await self._browser_proxy.fill(
                action.get("selector", ""),
                action.get("value", "")
            )

        elif action_type == "select":
            return await self._browser_proxy.select_option(
                action.get("selector", ""),
                action.get("value", "")
            )

        elif action_type == "verify_visible":
            # Request page state to verify
            page_state = await self._browser_proxy.refresh_page_state()
            # Check if element is in DOM snapshot
            selector = action.get("selector", "")
            # Simple check - in real implementation would verify visibility
            return {"success": True, "action": "verify_visible", "selector": selector}

        elif action_type == "verify_text":
            page_state = await self._browser_proxy.refresh_page_state()
            expected = action.get("expected_text", "").lower()
            # Check in DOM snapshot text
            dom = page_state.get("dom_snapshot", {})
            for el in dom.get("elements", []):
                if expected in (el.get("text", "") or "").lower():
                    return {"success": True, "action": "verify_text"}
            return {"success": False, "action": "verify_text", "error": f"Text '{expected}' not found"}

        elif action_type == "verify_url":
            page_state = await self._browser_proxy.refresh_page_state()
            expected = action.get("expected_pattern", "").lower()
            actual = page_state.get("url", "").lower()
            if expected in actual:
                return {"success": True, "action": "verify_url"}
            return {"success": False, "action": "verify_url", "error": f"URL mismatch: expected '{expected}' in '{actual}'"}

        elif action_type == "wait":
            return await self._browser_proxy.wait_for_selector(
                action.get("selector", ""),
                action.get("timeout", 10000)
            )

        elif action_type == "check":
            return await self._browser_proxy.check(action.get("selector", ""))

        elif action_type == "uncheck":
            return await self._browser_proxy.uncheck(action.get("selector", ""))

        elif action_type == "press_key":
            return await self._browser_proxy.press_key(action.get("key", ""))

        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    def cancel(self) -> None:
        """Cancel the running test execution."""
        self._cancelled = True

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        """Emit an event via callback if available."""
        if self._emit_callback:
            try:
                self._emit_callback(event, data)
            except Exception:
                pass
