"""
Ghost-QC Remote Client

Connects to Ghost-QC server and executes browser commands locally.
"""

import asyncio
import json
import platform
import signal
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

try:
    import websockets
except ImportError:
    print("Error: websockets package is required.")
    print("Install it with: pip install websockets")
    sys.exit(1)

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class RemoteClient:
    """
    Ghost-QC remote client that connects to the server and executes browser commands.

    The client:
    1. Connects to the server via WebSocket
    2. Receives browser commands from the server
    3. Executes commands on the local Playwright browser
    4. Sends results back to the server
    """

    def __init__(
        self,
        server_url: str,
        client_name: str = None,
        heartbeat_interval: int = 30,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the remote client.

        Args:
            server_url: WebSocket URL of the Ghost-QC server
            client_name: Human-readable name for this client
            heartbeat_interval: Seconds between heartbeats
            on_status_change: Callback for status updates
        """
        self.server_url = server_url
        self.client_name = client_name or f"{platform.node()}"
        self.heartbeat_interval = heartbeat_interval
        self._on_status_change = on_status_change

        # Connection state
        self._websocket = None
        self._session_id: Optional[str] = None
        self._connected = False
        self._running = False

        # Browser state
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._browser_running = False

        # Tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """
        Connect to the Ghost-QC server.

        Returns:
            True if connection successful
        """
        try:
            self._status("Connecting to server...")

            self._websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=60,
            )

            # Send registration
            registration = {
                "type": "client_register",
                "client_name": self.client_name,
                "client_info": {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node(),
                },
                "timestamp": datetime.now().isoformat(),
            }
            await self._websocket.send(json.dumps(registration))

            # Wait for acknowledgment
            response = await asyncio.wait_for(
                self._websocket.recv(),
                timeout=30.0
            )
            ack = json.loads(response)

            if ack.get("type") == "server_ack":
                self._session_id = ack.get("session_id")
                self._connected = True
                self._status(f"Connected! Session: {self._session_id}")
                return True
            else:
                self._status(f"Unexpected response: {ack.get('type')}")
                return False

        except Exception as e:
            self._status(f"Connection failed: {e}")
            return False

    async def run(self) -> None:
        """
        Main run loop - process messages from server.
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

        self._running = True

        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        self._status("Ready - waiting for commands...")

        try:
            # Message processing loop
            async for message in self._websocket:
                if not self._running:
                    break

                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message[:100]}")
                except Exception as e:
                    print(f"Error handling message: {e}")

        except websockets.ConnectionClosed:
            self._status("Connection closed by server")
        except Exception as e:
            self._status(f"Connection error: {e}")
        finally:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            await self._cleanup()

    async def disconnect(self) -> None:
        """Disconnect from server and cleanup."""
        self._running = False
        self._connected = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self._websocket:
            await self._websocket.close()

        await self._cleanup()
        self._status("Disconnected")

    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming message from server."""
        message_type = data.get("type")
        request_id = data.get("request_id")

        print(f"[Client] Received message: {message_type} (request_id: {request_id})")

        if message_type == "heartbeat_ack":
            # Server acknowledged heartbeat
            return

        elif message_type == "start_browser":
            result = await self._handle_start_browser(data)
            await self._send_result(request_id, result)

        elif message_type == "stop_browser":
            result = await self._handle_stop_browser(data)
            await self._send_result(request_id, result)

        elif message_type == "request_page_state":
            result = await self._handle_request_page_state(data)
            await self._send_page_state(request_id, result)

        elif message_type == "execute_action":
            result = await self._handle_execute_action(data)
            await self._send_result(request_id, result)

        else:
            print(f"[Client] Unknown message type: {message_type}")

    async def _handle_start_browser(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start_browser command."""
        self._status("Starting browser...")

        try:
            headless = data.get("headless", False)
            slow_mo = data.get("slow_mo", 100)

            # Run Playwright in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._start_browser_sync, headless, slow_mo)

            self._browser_running = True
            self._status("Browser started")

            return {"success": True, "action": "start_browser"}

        except Exception as e:
            self._status(f"Failed to start browser: {e}")
            return {"success": False, "action": "start_browser", "error": str(e)}

    def _start_browser_sync(self, headless: bool, slow_mo: int) -> None:
        """Synchronous browser start (runs in thread pool)."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo
        )
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768}
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(30000)

    async def _handle_stop_browser(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop_browser command."""
        self._status("Stopping browser...")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._stop_browser_sync)

            self._browser_running = False
            self._status("Browser stopped")

            return {"success": True, "action": "stop_browser"}

        except Exception as e:
            return {"success": False, "action": "stop_browser", "error": str(e)}

    def _stop_browser_sync(self) -> None:
        """Synchronous browser stop (runs in thread pool)."""
        if self._page:
            self._page.close()
            self._page = None
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    async def _handle_request_page_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request_page_state command."""
        if not self._browser_running or not self._page:
            return {"error": "Browser not running"}

        try:
            include_screenshot = data.get("include_screenshot", False)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._get_page_state_sync, include_screenshot
            )
            return result

        except Exception as e:
            return {"error": str(e)}

    def _get_page_state_sync(self, include_screenshot: bool) -> Dict[str, Any]:
        """Get page state synchronously."""
        result = {
            "url": self._page.url,
            "title": self._page.title(),
            "ready_state": self._get_ready_state(),
            "dom_snapshot": self._get_dom_snapshot(),
        }

        if include_screenshot:
            import base64
            screenshot_bytes = self._page.screenshot()
            result["screenshot"] = base64.b64encode(screenshot_bytes).decode("utf-8")

        return result

    def _get_ready_state(self) -> str:
        """Get document.readyState."""
        try:
            return self._page.evaluate("() => document.readyState") or "unknown"
        except Exception:
            return "unknown"

    def _get_dom_snapshot(self) -> Dict[str, Any]:
        """Get DOM snapshot for AI analysis."""
        script = '''
        () => {
            const elements = [];
            const interactiveSelectors = [
                'input', 'textarea', 'select', 'button', 'a[href]',
                '[role="button"]', '[role="link"]', '[role="checkbox"]',
                '[role="radio"]', '[role="switch"]', '[role="tab"]',
                '[onclick]', '[data-testid]', '[data-cy]',
                'label', '.btn', '.button'
            ].join(', ');

            document.querySelectorAll(interactiveSelectors).forEach((el, index) => {
                if (index > 100) return; // Limit elements

                const rect = el.getBoundingClientRect();
                const isVisible = rect.width > 0 && rect.height > 0;
                const style = window.getComputedStyle(el);
                const isDisplayed = style.display !== 'none' && style.visibility !== 'hidden';

                if (!isVisible || !isDisplayed) return;

                const info = {
                    index: index,
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    text: (el.textContent || '').trim().substring(0, 100),
                    value: el.value || null,
                    placeholder: el.placeholder || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    role: el.getAttribute('role') || null,
                    dataTestId: el.getAttribute('data-testid') || null,
                    disabled: el.disabled || false,
                    isVisible: true
                };

                // Remove null/empty values
                Object.keys(info).forEach(k => {
                    if (info[k] === null || info[k] === '') delete info[k];
                });

                elements.push(info);
            });

            return {
                url: window.location.href,
                title: document.title,
                timestamp: new Date().toISOString(),
                elementCount: elements.length,
                elements: elements
            };
        }
        '''
        try:
            return self._page.evaluate(script) or {"elements": []}
        except Exception as e:
            return {"elements": [], "error": str(e)}

    async def _handle_execute_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_action command."""
        if not self._browser_running or not self._page:
            return {"success": False, "error": "Browser not running"}

        action = data.get("action")
        selector = data.get("selector")
        value = data.get("value")
        timeout = data.get("timeout", 10000)

        self._status(f"Executing: {action} {selector or value or ''}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._execute_action_sync, action, selector, value, timeout
            )
            return result

        except Exception as e:
            return {
                "success": False,
                "action": action,
                "selector": selector,
                "error": str(e)
            }

    def _execute_action_sync(
        self,
        action: str,
        selector: Optional[str],
        value: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute browser action synchronously."""
        start_time = time.time()

        try:
            if action == "navigate":
                self._page.goto(value, wait_until="networkidle")
                return {"success": True, "action": action, "value": value}

            elif action == "click":
                self._page.click(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "fill":
                self._page.fill(selector, value, timeout=timeout)
                return {"success": True, "action": action, "selector": selector, "value": value}

            elif action == "type":
                self._page.type(selector, value, timeout=timeout)
                return {"success": True, "action": action, "selector": selector, "value": value}

            elif action == "select":
                self._page.select_option(selector, value, timeout=timeout)
                return {"success": True, "action": action, "selector": selector, "value": value}

            elif action == "check":
                self._page.check(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "uncheck":
                self._page.uncheck(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "press_key":
                self._page.keyboard.press(value)
                return {"success": True, "action": action, "value": value}

            elif action == "wait_for_selector":
                self._page.wait_for_selector(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "wait_for_url":
                self._page.wait_for_url(value, timeout=timeout)
                return {"success": True, "action": action, "value": value}

            elif action == "hover":
                self._page.hover(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "scroll":
                self._page.locator(selector).scroll_into_view_if_needed()
                return {"success": True, "action": action, "selector": selector}

            elif action == "double_click":
                self._page.dblclick(selector, timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "right_click":
                self._page.click(selector, button="right", timeout=timeout)
                return {"success": True, "action": action, "selector": selector}

            elif action == "take_screenshot":
                import base64
                screenshot_bytes = self._page.screenshot()
                screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
                return {"success": True, "action": action, "screenshot": screenshot}

            elif action == "execute_script":
                result = self._page.evaluate(value)
                return {"success": True, "action": action, "value": str(result)}

            else:
                return {"success": False, "action": action, "error": f"Unknown action: {action}"}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "action": action,
                "selector": selector,
                "error": str(e),
                "duration_ms": duration_ms
            }

    async def _send_result(self, request_id: str, result: Dict[str, Any]) -> None:
        """Send action result to server."""
        message = {
            "type": "action_result",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            **result
        }
        await self._websocket.send(json.dumps(message))

    async def _send_page_state(self, request_id: str, result: Dict[str, Any]) -> None:
        """Send page state to server."""
        message = {
            "type": "page_state",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            **result
        }
        await self._websocket.send(json.dumps(message))

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to server."""
        while self._running and self._connected:
            try:
                heartbeat = {
                    "type": "heartbeat",
                    "request_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                }
                await self._websocket.send(json.dumps(heartbeat))
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                break

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._browser_running:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._stop_browser_sync)
            except Exception:
                pass
            self._browser_running = False

    def _status(self, message: str) -> None:
        """Update status and notify callback."""
        print(f"[Ghost-QC Client] {message}")
        if self._on_status_change:
            try:
                self._on_status_change(message)
            except Exception:
                pass


async def run_client(
    server_url: str,
    client_name: str = None,
    auto_reconnect: bool = True,
    reconnect_delay: int = 5,
) -> None:
    """
    Run the remote client with optional auto-reconnect.

    Args:
        server_url: WebSocket URL of the Ghost-QC server
        client_name: Human-readable name for this client
        auto_reconnect: Whether to reconnect on disconnect
        reconnect_delay: Seconds to wait before reconnecting
    """
    client = RemoteClient(server_url, client_name)

    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        print("\nShutting down...")
        stop_event.set()

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass

    while not stop_event.is_set():
        try:
            connected = await client.connect()
            if connected:
                await client.run()

            if not auto_reconnect:
                break

            if not stop_event.is_set():
                print(f"Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)

        except Exception as e:
            print(f"Error: {e}")
            if not auto_reconnect:
                break
            await asyncio.sleep(reconnect_delay)

    await client.disconnect()
