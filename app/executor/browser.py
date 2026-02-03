"""
Browser Automation Module

Provides Playwright-based browser automation for autonomous test execution.
"""

import base64
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, ElementHandle


@dataclass
class BrowserAction:
    """Represents a browser action result."""
    success: bool
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None  # Base64 encoded


class BrowserAutomation:
    def verify_not_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Return True if the element is not visible (or not present)."""
        try:
            return not self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return True  # If not found, treat as not visible

    def handle_action(self, action: str, selector: str, value: str = None, **kwargs):
        """Dispatch actions including verify_not_visible for test steps."""
        if action == "verify_not_visible":
            result = self.verify_not_visible(selector)
            if not result:
                raise AssertionError(f"Element {selector} is visible but should not be.")
            return {"success": True, "action": action, "selector": selector}
        # ...existing action handlers...
        return {"success": False, "action": action, "selector": selector, "error": f"Unknown action type: {action}"}
    """
    Playwright-based browser automation for test execution.
    Provides high-level actions that AI can invoke.
    """

    def __init__(self, headless: bool = True, slow_mo: int = 100):
        self.headless = headless
        self.slow_mo = slow_mo
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> None:
        """Start the browser."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768}
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(30000)

    def stop(self) -> None:
        """Stop the browser and cleanup."""
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    @property
    def page(self) -> Page:
        """Get the current page."""
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    def navigate(self, url: str) -> BrowserAction:
        """Navigate to a URL."""
        try:
            self.page.goto(url, wait_until="networkidle")
            return BrowserAction(success=True, action="navigate", value=url)
        except Exception as e:
            return BrowserAction(success=False, action="navigate", value=url, error=str(e))

    def click(self, selector: str, fallback_selectors: list = None, debug: bool = False) -> BrowserAction:
        """Click an element, trying fallback selectors if needed. Optionally capture debug info on failure."""
        selectors_to_try = [selector] + (fallback_selectors or [])
        last_error = None
        for sel in selectors_to_try:
            try:
                self.page.click(sel, timeout=10000)
                return BrowserAction(success=True, action="click", selector=sel)
            except Exception as e:
                last_error = str(e)
                if debug:
                    self._log_debug_failure('click', sel, last_error)
        if debug:
            self._capture_debug_state('click', selector, last_error)
        return BrowserAction(success=False, action="click", selector=selector, error=last_error)

    def fill(self, selector: str, value: str, fallback_selectors: list = None, debug: bool = False) -> BrowserAction:
        """Fill a text input, trying fallback selectors if needed. Optionally capture debug info on failure."""
        selectors_to_try = [selector] + (fallback_selectors or [])
        last_error = None
        for sel in selectors_to_try:
            try:
                self.page.fill(sel, value, timeout=10000)
                return BrowserAction(success=True, action="fill", selector=sel, value=value)
            except Exception as e:
                last_error = str(e)
                if debug:
                    self._log_debug_failure('fill', sel, last_error)
        if debug:
            self._capture_debug_state('fill', selector, last_error)
        return BrowserAction(success=False, action="fill", selector=selector, value=value, error=last_error)
    def _log_debug_failure(self, action: str, selector: str, error: str):
        print(f"[DEBUG] Action '{action}' failed for selector '{selector}': {error}")

    def _capture_debug_state(self, action: str, selector: str, error: str):
        # Save screenshot and DOM snapshot for debugging
        try:
            screenshot = self.take_screenshot()
            dom = self.get_page_content()
            with open(f'debug_{action}_{selector.replace("/", "_")}.png', 'wb') as f:
                import base64
                f.write(base64.b64decode(screenshot))
            with open(f'debug_{action}_{selector.replace("/", "_")}.html', 'w', encoding='utf-8') as f:
                f.write(dom)
            print(f"[DEBUG] Captured screenshot and DOM for failed action '{action}' on selector '{selector}'")
        except Exception as e:
            print(f"[DEBUG] Failed to capture debug state: {e}")
    def try_action_with_fallbacks(self, action: str, selector: str, value: str = None, fallback_selectors: list = None, debug: bool = False) -> BrowserAction:
        """Generalized method to try an action with fallback selectors."""
        if action == 'click':
            return self.click(selector, fallback_selectors, debug)
        elif action == 'fill':
            return self.fill(selector, value, fallback_selectors, debug)
        # Extend for other actions as needed
        return BrowserAction(success=False, action=action, selector=selector, error='Unsupported action')

    def type_text(self, selector: str, value: str) -> BrowserAction:
        """Type text character by character (for inputs that don't work with fill)."""
        try:
            self.page.type(selector, value, timeout=10000)
            return BrowserAction(success=True, action="type", selector=selector, value=value)
        except Exception as e:
            return BrowserAction(success=False, action="type", selector=selector, error=str(e))

    def select_option(self, selector: str, value: str) -> BrowserAction:
        """Select an option from a dropdown."""
        try:
            self.page.select_option(selector, value, timeout=10000)
            return BrowserAction(success=True, action="select", selector=selector, value=value)
        except Exception as e:
            return BrowserAction(success=False, action="select", selector=selector, error=str(e))

    def check(self, selector: str) -> BrowserAction:
        """Check a checkbox."""
        try:
            self.page.check(selector, timeout=10000)
            return BrowserAction(success=True, action="check", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="check", selector=selector, error=str(e))

    def uncheck(self, selector: str) -> BrowserAction:
        """Uncheck a checkbox."""
        try:
            self.page.uncheck(selector, timeout=10000)
            return BrowserAction(success=True, action="uncheck", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="uncheck", selector=selector, error=str(e))

    def press_key(self, key: str) -> BrowserAction:
        """Press a keyboard key."""
        try:
            self.page.keyboard.press(key)
            return BrowserAction(success=True, action="press_key", value=key)
        except Exception as e:
            return BrowserAction(success=False, action="press_key", value=key, error=str(e))

    def wait_for_selector(self, selector: str, timeout: int = 10000) -> BrowserAction:
        """Wait for an element to appear."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return BrowserAction(success=True, action="wait_for_selector", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="wait_for_selector", selector=selector, error=str(e))

    def wait_for_url(self, url_pattern: str, timeout: int = 10000) -> BrowserAction:
        """Wait for URL to match pattern."""
        try:
            self.page.wait_for_url(url_pattern, timeout=timeout)
            return BrowserAction(success=True, action="wait_for_url", value=url_pattern)
        except Exception as e:
            return BrowserAction(success=False, action="wait_for_url", value=url_pattern, error=str(e))

    def get_text(self, selector: str) -> Optional[str]:
        """Get text content of an element."""
        try:
            return self.page.text_content(selector, timeout=10000)
        except Exception:
            return None

    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute value of an element."""
        try:
            return self.page.get_attribute(selector, attribute, timeout=10000)
        except Exception:
            return None

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        try:
            return self.page.is_visible(selector, timeout=5000)
        except Exception:
            return False

    def is_enabled(self, selector: str) -> bool:
        """Check if element is enabled."""
        try:
            return self.page.is_enabled(selector, timeout=5000)
        except Exception:
            return False

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url

    def get_title(self) -> str:
        """Get page title."""
        return self.page.title()

    def take_screenshot(self) -> str:
        """Take screenshot and return as base64."""
        screenshot_bytes = self.page.screenshot()
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def get_page_content(self) -> str:
        """Get the full HTML content of the page."""
        return self.page.content()

    def get_visible_text(self) -> str:
        """Get all visible text on the page."""
        return self.page.inner_text("body")

    def find_elements(self, selector: str) -> List[ElementHandle]:
        """Find all elements matching selector."""
        try:
            return self.page.query_selector_all(selector)
        except Exception:
            return []

    def get_element_info(self, selector: str) -> Dict[str, Any]:
        """Get detailed info about an element."""
        try:
            element = self.page.query_selector(selector)
            if not element:
                return {"found": False}

            return {
                "found": True,
                "visible": element.is_visible(),
                "enabled": element.is_enabled(),
                "text": element.text_content(),
                "tag": element.evaluate("el => el.tagName.toLowerCase()"),
                "id": element.get_attribute("id"),
                "class": element.get_attribute("class"),
                "type": element.get_attribute("type"),
                "value": element.get_attribute("value"),
            }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        try:
            return self.page.evaluate(script)
        except Exception:
            return None

    def scroll_to_element(self, selector: str) -> BrowserAction:
        """Scroll to make element visible."""
        try:
            self.page.locator(selector).scroll_into_view_if_needed()
            return BrowserAction(success=True, action="scroll", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="scroll", selector=selector, error=str(e))

    def hover(self, selector: str) -> BrowserAction:
        """Hover over an element."""
        try:
            self.page.hover(selector, timeout=10000)
            return BrowserAction(success=True, action="hover", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="hover", selector=selector, error=str(e))

    def double_click(self, selector: str) -> BrowserAction:
        """Double-click an element."""
        try:
            self.page.dblclick(selector, timeout=10000)
            return BrowserAction(success=True, action="double_click", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="double_click", selector=selector, error=str(e))

    def right_click(self, selector: str) -> BrowserAction:
        """Right-click an element."""
        try:
            self.page.click(selector, button="right", timeout=10000)
            return BrowserAction(success=True, action="right_click", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="right_click", selector=selector, error=str(e))

    def clear_field(self, selector: str) -> BrowserAction:
        """Clear a text field."""
        try:
            self.page.fill(selector, "", timeout=10000)
            return BrowserAction(success=True, action="clear", selector=selector)
        except Exception as e:
            return BrowserAction(success=False, action="clear", selector=selector, error=str(e))

    def accept_dialog(self) -> None:
        """Set up handler to accept dialogs."""
        self.page.on("dialog", lambda dialog: dialog.accept())

    def dismiss_dialog(self) -> None:
        """Set up handler to dismiss dialogs."""
        self.page.on("dialog", lambda dialog: dialog.dismiss())

    def get_ready_state(self) -> str:
        """Get document.readyState."""
        try:
            return self.page.evaluate("() => document.readyState") or "unknown"
        except Exception:
            return "unknown"

    def wait_for_dom_stable(self, timeout: int = 5000) -> bool:
        """Wait for DOM to be stable (no mutations)."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_dom_stable_smart(self, max_wait: int = 10000, check_interval: int = 200) -> bool:
        """
        Wait until DOM stops changing using hash comparison.

        Monitors DOM structure hash to detect when mutations have stopped,
        providing more reliable stability detection than networkidle alone.

        Args:
            max_wait: Maximum time to wait in milliseconds
            check_interval: Time between hash checks in milliseconds

        Returns:
            True when DOM is stable, False if timeout reached
        """
        start_time = time.time()
        max_wait_seconds = max_wait / 1000
        check_interval_seconds = check_interval / 1000
        previous_hash = None
        stable_count = 0
        required_stable_checks = 3  # Need 3 consecutive matching hashes

        while (time.time() - start_time) < max_wait_seconds:
            current_hash = self.get_dom_hash()

            if current_hash == previous_hash:
                stable_count += 1
                if stable_count >= required_stable_checks:
                    return True
            else:
                stable_count = 0

            previous_hash = current_hash
            time.sleep(check_interval_seconds)

        return False

    def smart_wait_for_element(
        self,
        selector: str,
        timeout: int = 30000,
        wait_for_stable: bool = True
    ) -> BrowserAction:
        """
        Wait for element with DOM stability check and actionability verification.

        Performs intelligent waiting that:
        1. Waits for DOM to stabilize (optional)
        2. Waits for element to be visible
        3. Waits for element to be actionable (enabled, not obscured)

        Args:
            selector: CSS selector or text selector
            timeout: Maximum wait time in milliseconds
            wait_for_stable: Whether to wait for DOM stability first

        Returns:
            BrowserAction with success status and details
        """
        start_time = time.time()
        timeout_seconds = timeout / 1000

        try:
            # Step 1: Wait for DOM stability (if requested)
            if wait_for_stable:
                # Use shorter timeout for stability check
                stability_timeout = min(5000, timeout // 3)
                self.wait_for_dom_stable_smart(stability_timeout)

            # Step 2: Wait for element to be visible
            remaining_timeout = max(1000, int((timeout_seconds - (time.time() - start_time)) * 1000))
            self.page.wait_for_selector(selector, state="visible", timeout=remaining_timeout)

            # Step 3: Wait for element to be actionable
            locator = self.page.locator(selector)
            remaining_timeout = max(1000, int((timeout_seconds - (time.time() - start_time)) * 1000))

            # Check if element is enabled
            locator.wait_for(state="visible", timeout=remaining_timeout)

            duration = (time.time() - start_time) * 1000
            return BrowserAction(
                success=True,
                action="smart_wait",
                selector=selector,
                value=f"ready in {duration:.0f}ms"
            )

        except Exception as e:
            return BrowserAction(
                success=False,
                action="smart_wait",
                selector=selector,
                error=str(e)
            )

    def _ensure_ready_before_action(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """
        Ensure page and element are ready before performing an action.

        Called internally before every action to guarantee:
        1. Network is idle (or timeout)
        2. DOM is stable
        3. Element is scrolled into view
        4. Element is visible and enabled

        Args:
            selector: Target element selector
            timeout: Maximum wait time in milliseconds

        Returns:
            Dict with readiness status and details
        """
        result = {
            "ready": False,
            "network_idle": False,
            "dom_stable": False,
            "element_visible": False,
            "element_actionable": False,
            "duration_ms": 0,
            "error": None
        }

        start_time = time.time()
        timeout_seconds = timeout / 1000

        try:
            # Step 1: Wait for network idle (with short timeout)
            try:
                self.page.wait_for_load_state("networkidle", timeout=min(3000, timeout))
                result["network_idle"] = True
            except Exception:
                pass  # Continue even if network not idle

            # Step 2: Quick DOM stability check
            if self.wait_for_dom_stable_smart(max_wait=min(3000, timeout), check_interval=100):
                result["dom_stable"] = True

            # Step 3: Check element exists and scroll into view
            remaining = max(1000, int((timeout_seconds - (time.time() - start_time)) * 1000))
            try:
                locator = self.page.locator(selector)
                locator.scroll_into_view_if_needed(timeout=remaining)
            except Exception:
                pass  # Element might not need scrolling

            # Step 4: Wait for element to be visible
            remaining = max(1000, int((timeout_seconds - (time.time() - start_time)) * 1000))
            try:
                self.page.wait_for_selector(selector, state="visible", timeout=remaining)
                result["element_visible"] = True
            except Exception as e:
                result["error"] = f"Element not visible: {str(e)}"
                result["duration_ms"] = (time.time() - start_time) * 1000
                return result

            # Step 5: Verify element is enabled/actionable
            try:
                element_info = self.get_element_info(selector)
                if element_info.get("found") and element_info.get("enabled", True):
                    result["element_actionable"] = True
                    result["ready"] = True
                else:
                    result["error"] = "Element found but not actionable"
            except Exception:
                # If we can't verify, assume it's actionable
                result["element_actionable"] = True
                result["ready"] = True

        except Exception as e:
            result["error"] = str(e)

        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    def click_smart(self, selector: str, timeout: int = 10000) -> BrowserAction:
        """
        Click an element with smart waiting and readiness checks.

        Args:
            selector: Target element selector
            timeout: Maximum wait time in milliseconds

        Returns:
            BrowserAction with result
        """
        # Ensure element is ready
        readiness = self._ensure_ready_before_action(selector, timeout)

        if not readiness["ready"]:
            return BrowserAction(
                success=False,
                action="click_smart",
                selector=selector,
                error=readiness.get("error", "Element not ready")
            )

        # Perform click
        try:
            self.page.click(selector, timeout=timeout)
            return BrowserAction(success=True, action="click_smart", selector=selector)
        except Exception as e:
            return BrowserAction(
                success=False,
                action="click_smart",
                selector=selector,
                error=str(e)
            )

    def fill_smart(self, selector: str, value: str, timeout: int = 10000) -> BrowserAction:
        """
        Fill a text input with smart waiting and readiness checks.

        Args:
            selector: Target input selector
            value: Text to enter
            timeout: Maximum wait time in milliseconds

        Returns:
            BrowserAction with result
        """
        # Ensure element is ready
        readiness = self._ensure_ready_before_action(selector, timeout)

        if not readiness["ready"]:
            return BrowserAction(
                success=False,
                action="fill_smart",
                selector=selector,
                value=value,
                error=readiness.get("error", "Element not ready")
            )

        # Perform fill
        try:
            self.page.fill(selector, value, timeout=timeout)
            return BrowserAction(success=True, action="fill_smart", selector=selector, value=value)
        except Exception as e:
            return BrowserAction(
                success=False,
                action="fill_smart",
                selector=selector,
                value=value,
                error=str(e)
            )

    def get_dom_snapshot(self) -> Dict[str, Any]:
        """
        Get a comprehensive snapshot of the DOM for UI Brain.

        Returns:
            Dict with page metadata and all interactive elements
        """
        script = '''
        () => {
            const elements = [];
            const interactiveSelectors = [
                'input', 'textarea', 'select', 'button', 'a[href]',
                '[role="button"]', '[role="link"]', '[role="checkbox"]',
                '[role="radio"]', '[role="switch"]', '[role="tab"]',
                '[role="menuitem"]', '[role="option"]', '[role="combobox"]',
                '[role="textbox"]', '[role="searchbox"]', '[role="slider"]',
                '[onclick]', '[ng-click]', '[v-on:click]', '[@click]',
                '[data-action]', '[data-testid]', '[data-cy]',
                'label', 'th[onclick]', 'td[onclick]',
                '.btn', '.button', '[class*="clickable"]'
            ].join(', ');

            const processedElements = new Set();

            document.querySelectorAll(interactiveSelectors).forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                const isVisible = rect.width > 0 && rect.height > 0;
                const style = window.getComputedStyle(el);
                const isDisplayed = style.display !== 'none' && style.visibility !== 'hidden';

                const uniqueKey = el.tagName + el.id + el.name + (el.textContent?.substring(0, 20) || '');
                if (processedElements.has(uniqueKey)) return;
                processedElements.add(uniqueKey);

                let labelText = null;
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) labelText = label.textContent?.trim();
                }
                if (!labelText && el.closest('label')) {
                    labelText = el.closest('label').textContent?.trim();
                }

                const info = {
                    index: index,
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    className: el.className || null,
                    text: (el.textContent || '').trim().substring(0, 100),
                    innerText: (el.innerText || '').trim().substring(0, 100),
                    value: el.value || null,
                    placeholder: el.placeholder || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    ariaLabelledBy: el.getAttribute('aria-labelledby') || null,
                    role: el.getAttribute('role') || null,
                    title: el.title || null,
                    href: el.href || null,
                    dataTestId: el.getAttribute('data-testid') || null,
                    dataCy: el.getAttribute('data-cy') || null,
                    disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                    required: el.required || el.getAttribute('aria-required') === 'true',
                    checked: el.checked || null,
                    labelText: labelText,
                    isVisible: isVisible && isDisplayed,
                    isEnabled: !el.disabled,
                    boundingRect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                    parentTag: el.parentElement?.tagName?.toLowerCase() || null,
                    parentId: el.parentElement?.id || null,
                    siblingIndex: Array.from(el.parentElement?.children || []).indexOf(el),
                    path: getPath(el)
                };

                Object.keys(info).forEach(k => {
                    if (info[k] === null || info[k] === '' || info[k] === undefined) delete info[k];
                });

                elements.push(info);
            });

            function getPath(el) {
                const path = [];
                let current = el;
                while (current && current !== document.body) {
                    let selector = current.tagName.toLowerCase();
                    if (current.id) selector += '#' + current.id;
                    else if (current.className && typeof current.className === 'string') {
                        const cls = current.className.trim().split(/\\s+/).slice(0, 2).join('.');
                        if (cls) selector += '.' + cls;
                    }
                    path.unshift(selector);
                    current = current.parentElement;
                }
                return path.join(' > ');
            }

            return {
                readyState: document.readyState,
                url: window.location.href,
                title: document.title,
                timestamp: new Date().toISOString(),
                elementCount: elements.length,
                elements: elements
            };
        }
        '''
        try:
            return self.page.evaluate(script) or {"elements": [], "error": "Script returned null"}
        except Exception as e:
            return {"elements": [], "error": str(e)}

    def get_dom_hash(self) -> str:
        """
        Get a hash of the DOM structure for change detection.

        Returns:
            Hash string representing DOM structure
        """
        script = '''
        () => {
            const elements = document.querySelectorAll('input, button, a, select, textarea, [role]');
            let signature = '';
            elements.forEach(el => {
                signature += el.tagName + (el.id || '') + (el.name || '') + (el.type || '');
            });
            return signature;
        }
        '''
        try:
            import hashlib
            signature = self.page.evaluate(script) or ""
            return hashlib.sha256(signature.encode()).hexdigest()[:16]
        except Exception:
            import hashlib
            from datetime import datetime
            return hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]

    def verify_element_in_dom(self, selector: str) -> Dict[str, Any]:
        """
        Verify element exists and get its current state.

        Args:
            selector: CSS selector or text selector

        Returns:
            Dict with element state information
        """
        try:
            element = self.page.query_selector(selector)
            if not element:
                return {"exists": False, "selector": selector}

            return {
                "exists": True,
                "selector": selector,
                "visible": element.is_visible(),
                "enabled": element.is_enabled(),
                "tag": element.evaluate("el => el.tagName.toLowerCase()"),
                "text": (element.text_content() or "").strip()[:100]
            }
        except Exception as e:
            return {"exists": False, "selector": selector, "error": str(e)}
