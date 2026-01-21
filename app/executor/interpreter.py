"""
AI-Driven Step Interpreter

Uses Claude AI to interpret Gherkin steps and determine browser actions.
This is the intelligence layer that enables autonomous test execution.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from app.ai.engine import run_ai
from app.executor.browser import BrowserAutomation, BrowserAction
from app.brain.ui_brain import UIBrain, ElementDescriptor

if TYPE_CHECKING:
    from app.executor.step_logger import StepLogger


@dataclass
class StepInterpretation:
    """AI interpretation of a Gherkin step."""
    step_text: str
    action_type: str  # navigate, click, fill, verify, wait, etc.
    selector: Optional[str] = None
    value: Optional[str] = None
    verification_type: Optional[str] = None  # visible, text_contains, url_contains, etc.
    expected_value: Optional[str] = None
    confidence: float = 1.0
    reasoning: str = ""


class StepInterpreter:
    """
    AI-powered interpreter that converts Gherkin steps into executable actions.
    """

    INTERPRETATION_PROMPT = '''You are an expert test automation engineer. Analyze the Gherkin step and page context to determine the exact browser action needed.

CURRENT PAGE STATE:
- URL: {current_url}
- Title: {page_title}
- Visible Elements Summary: {elements_summary}

GHERKIN STEP TO EXECUTE:
"{step_text}"

PREVIOUS STEPS IN THIS SCENARIO:
{previous_steps}

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

For VERIFICATION (element exists):
{{"action": "verify_exists", "selector": "<element_selector>"}}

For WAITING (for element):
{{"action": "wait", "selector": "<element_to_wait_for>", "timeout": <milliseconds>}}

For WAITING (for time/seconds):
{{"action": "wait_time", "seconds": <number_of_seconds>}}

For CHECKBOX:
{{"action": "check", "selector": "<checkbox_selector>"}} or {{"action": "uncheck", "selector": "<checkbox_selector>"}}

For KEYBOARD:
{{"action": "press_key", "key": "<key_name>"}}

SELECTOR TIPS:
- IMPORTANT: For buttons with aria-label, ALWAYS use: button[aria-label="exact label"] (e.g., button[aria-label="Edit"])
- For icon buttons in tables, use aria-label to distinguish: button[aria-label="Edit"] NOT button[aria-label="View Details"]
- Prefer text-based selectors: text="Login" or button:has-text("Submit")
- Use role selectors: role=button[name="Login"]
- Use placeholder: [placeholder="Email"]
- Use label: label:has-text("Email") >> input
- Use test IDs if visible: [data-testid="login-btn"]
- Fallback to CSS: #id, .class, input[type="email"]
- For "first" row in table: .MuiDataGrid-row:first-child button[aria-label="Edit"]

IMPORTANT: When the step mentions "Edit" icon/button, use button[aria-label="Edit"], NOT button[aria-label="View Details"].

Respond with ONLY the JSON object, no explanations.'''

    ELEMENT_FINDER_PROMPT = '''Analyze this page HTML to find the best selector for: "{target_description}"

PAGE HTML (truncated):
{html_snippet}

Return ONLY a JSON object:
{{"selector": "<best_css_or_text_selector>", "confidence": <0.0-1.0>}}'''

    def __init__(
        self,
        browser: BrowserAutomation,
        enable_auto_healing: bool = True,
        step_logger: Optional["StepLogger"] = None
    ):
        self.browser = browser
        self.step_history: List[str] = []
        self.enable_auto_healing = enable_auto_healing
        self.step_logger = step_logger

        # Initialize UI Brain for auto-healing
        self._ui_brain: Optional[UIBrain] = None
        if enable_auto_healing:
            self._ui_brain = UIBrain()

        # Track healing statistics
        self._healing_stats = {
            "attempts": 0,
            "successes": 0,
            "methods_used": {}
        }

    def interpret_step(self, step_text: str) -> Dict[str, Any]:
        """
        Interpret a Gherkin step and return action details.
        """
        # Get current page context
        current_url = self.browser.get_current_url()
        page_title = self.browser.get_title()
        elements_summary = self._get_elements_summary()

        # Build prompt with context
        prompt = self.INTERPRETATION_PROMPT.format(
            current_url=current_url,
            page_title=page_title,
            elements_summary=elements_summary,
            step_text=step_text,
            previous_steps="\n".join(self.step_history[-5:]) if self.step_history else "None"
        )

        # Get AI interpretation
        response = run_ai(prompt)

        # Parse JSON response
        action = self._parse_json_response(response)

        # Add to history
        self.step_history.append(step_text)

        return action

    def execute_step(self, step_text: str) -> Dict[str, Any]:
        """
        Interpret and execute a Gherkin step.
        Returns execution result with status and details.
        """
        result = {
            "step": step_text,
            "success": False,
            "action": None,
            "error": None,
            "screenshot": None
        }

        try:
            # Get AI interpretation
            action = self.interpret_step(step_text)
            result["action"] = action

            if not action:
                result["error"] = "Failed to interpret step"
                return result

            # Execute based on action type
            action_type = action.get("action", "")

            if action_type == "navigate":
                browser_result = self.browser.navigate(action.get("url", ""))
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "click":
                selector = action.get("selector", "")
                description = action.get("description", "")
                # Try to find element, with fallback and auto-healing
                browser_result = self._execute_click(selector, description=description)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "fill":
                selector = action.get("selector", "")
                value = action.get("value", "")
                # Try smart fill first
                browser_result = self.browser.fill_smart(selector, value)
                if not browser_result.success and self.enable_auto_healing:
                    # Try auto-healing
                    browser_result = self._execute_with_healing("fill", selector, value=value)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "select":
                selector = action.get("selector", "")
                value = action.get("value", "")
                browser_result = self.browser.select_option(selector, value)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "verify_visible":
                selector = action.get("selector", "")
                is_visible = self.browser.is_visible(selector)
                result["success"] = is_visible
                if not is_visible:
                    result["error"] = f"Element not visible: {selector}"

            elif action_type == "verify_text":
                selector = action.get("selector", "")
                expected = action.get("expected_text", "")
                actual = self.browser.get_text(selector) or ""
                result["success"] = expected.lower() in actual.lower()
                if not result["success"]:
                    result["error"] = f"Text mismatch. Expected '{expected}' in '{actual}'"

            elif action_type == "verify_url":
                expected = action.get("expected_pattern", "")
                actual = self.browser.get_current_url()
                result["success"] = expected.lower() in actual.lower()
                if not result["success"]:
                    result["error"] = f"URL mismatch. Expected '{expected}' in '{actual}'"

            elif action_type == "verify_exists":
                selector = action.get("selector", "")
                elements = self.browser.find_elements(selector)
                result["success"] = len(elements) > 0
                if not result["success"]:
                    result["error"] = f"Element not found: {selector}"

            elif action_type == "wait":
                selector = action.get("selector", "")
                timeout = action.get("timeout", 10000)
                browser_result = self.browser.wait_for_selector(selector, timeout)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "wait_time":
                import time
                seconds = action.get("seconds", 1)
                time.sleep(float(seconds))
                result["success"] = True

            elif action_type == "check":
                selector = action.get("selector", "")
                browser_result = self.browser.check(selector)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "uncheck":
                selector = action.get("selector", "")
                browser_result = self.browser.uncheck(selector)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "press_key":
                key = action.get("key", "")
                browser_result = self.browser.press_key(key)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            else:
                result["error"] = f"Unknown action type: {action_type}"

        except Exception as e:
            result["error"] = str(e)

        # Take screenshot on failure
        if not result["success"]:
            try:
                result["screenshot"] = self.browser.take_screenshot()
            except Exception:
                pass

        return result

    def _execute_click(self, selector: str, description: str = None) -> BrowserAction:
        """Execute click with smart retries, auto-healing, and selector alternatives."""
        # Try smart click first (includes waiting and readiness checks)
        result = self.browser.click_smart(selector)
        if result.success:
            return result

        # If auto-healing is enabled, try to recover
        if self.enable_auto_healing:
            healed_result = self._execute_with_healing("click", selector, description=description)
            if healed_result.success:
                return healed_result

        # Fallback to basic alternatives
        alternatives = self._generate_selector_alternatives(selector)
        for alt_selector in alternatives:
            result = self.browser.click(alt_selector)
            if result.success:
                self._log_healing_attempt(selector, alt_selector, True, "alternative")
                return result
            else:
                self._log_healing_attempt(selector, alt_selector, False, "alternative")

        return result

    def _execute_with_healing(
        self,
        action: str,
        selector: str,
        value: str = None,
        description: str = None,
        **kwargs
    ) -> BrowserAction:
        """
        Execute action with auto-healing on failure using UI Brain.

        Args:
            action: Action type (click, fill, etc.)
            selector: Original selector that failed
            value: Value for fill actions
            description: Human description of target element
            **kwargs: Additional action parameters

        Returns:
            BrowserAction with result
        """
        if not self._ui_brain:
            return BrowserAction(success=False, action=action, selector=selector, error="UI Brain not available")

        self._healing_stats["attempts"] += 1

        # Build page brain to analyze current DOM
        try:
            self._ui_brain.build_page_brain(self.browser)
        except Exception as e:
            return BrowserAction(success=False, action=action, selector=selector, error=f"Failed to build page brain: {e}")

        # Strategy 1: Try to resolve element by description
        if description:
            element = self._ui_brain.resolve_element(description)
            if element:
                result = self._try_action_on_element(action, element, value)
                if result.success:
                    self._log_healing_attempt(selector, element.logical_selector, True, "ui_brain_description")
                    self._healing_stats["successes"] += 1
                    self._healing_stats["methods_used"]["ui_brain_description"] = \
                        self._healing_stats["methods_used"].get("ui_brain_description", 0) + 1
                    return result

        # Strategy 2: Extract description from selector and try to match
        extracted_description = self._extract_description_from_selector(selector)
        if extracted_description:
            element = self._ui_brain.resolve_element(extracted_description)
            if element:
                result = self._try_action_on_element(action, element, value)
                if result.success:
                    self._log_healing_attempt(selector, element.logical_selector, True, "ui_brain_extracted")
                    self._healing_stats["successes"] += 1
                    self._healing_stats["methods_used"]["ui_brain_extracted"] = \
                        self._healing_stats["methods_used"].get("ui_brain_extracted", 0) + 1
                    return result

        # Strategy 3: Generate smart alternatives based on UI Brain elements
        alternatives = self._generate_smart_alternatives(selector)
        for alt_selector in alternatives:
            result = self._try_action(action, alt_selector, value)
            if result.success:
                self._log_healing_attempt(selector, alt_selector, True, "smart_alternative")
                self._healing_stats["successes"] += 1
                self._healing_stats["methods_used"]["smart_alternative"] = \
                    self._healing_stats["methods_used"].get("smart_alternative", 0) + 1
                return result
            else:
                self._log_healing_attempt(selector, alt_selector, False, "smart_alternative")

        # Strategy 4: Try similar elements by type
        similar_elements = self._find_similar_elements(selector)
        for element in similar_elements[:3]:  # Try top 3 similar elements
            result = self._try_action_on_element(action, element, value)
            if result.success:
                self._log_healing_attempt(selector, element.logical_selector, True, "similar_element")
                self._healing_stats["successes"] += 1
                self._healing_stats["methods_used"]["similar_element"] = \
                    self._healing_stats["methods_used"].get("similar_element", 0) + 1
                return result
            else:
                self._log_healing_attempt(selector, element.logical_selector, False, "similar_element")

        return BrowserAction(success=False, action=action, selector=selector, error="Auto-healing failed - no matching element found")

    def _try_action_on_element(self, action: str, element: ElementDescriptor, value: str = None) -> BrowserAction:
        """Try to execute action on an ElementDescriptor."""
        # Try logical selector first (higher confidence)
        result = self._try_action(action, element.logical_selector, value)
        if result.success:
            return result

        # Fallback to structural selector
        return self._try_action(action, element.structural_selector, value)

    def _try_action(self, action: str, selector: str, value: str = None) -> BrowserAction:
        """Execute a browser action with the given selector."""
        try:
            if action == "click":
                return self.browser.click(selector)
            elif action == "fill":
                return self.browser.fill(selector, value or "")
            elif action == "select":
                return self.browser.select_option(selector, value or "")
            elif action == "check":
                return self.browser.check(selector)
            elif action == "uncheck":
                return self.browser.uncheck(selector)
            else:
                return BrowserAction(success=False, action=action, selector=selector, error=f"Unknown action: {action}")
        except Exception as e:
            return BrowserAction(success=False, action=action, selector=selector, error=str(e))

    def _extract_description_from_selector(self, selector: str) -> Optional[str]:
        """Extract a human-readable description from a selector."""
        # Extract text from :has-text() or text=
        text_match = re.search(r':has-text\("([^"]+)"\)', selector)
        if text_match:
            return text_match.group(1)

        text_match = re.search(r'text="([^"]+)"', selector)
        if text_match:
            return text_match.group(1)

        # Extract from aria-label
        aria_match = re.search(r'\[aria-label="([^"]+)"\]', selector)
        if aria_match:
            return aria_match.group(1)

        # Extract from placeholder
        placeholder_match = re.search(r'\[placeholder="([^"]+)"\]', selector)
        if placeholder_match:
            return placeholder_match.group(1)

        # Extract from data-testid
        testid_match = re.search(r'\[data-testid="([^"]+)"\]', selector)
        if testid_match:
            return testid_match.group(1).replace("-", " ").replace("_", " ")

        # Extract from id
        id_match = re.search(r'#([a-zA-Z0-9_-]+)', selector)
        if id_match:
            return id_match.group(1).replace("-", " ").replace("_", " ")

        return None

    def _generate_selector_alternatives(self, selector: str) -> List[str]:
        """Generate alternative selectors to try."""
        alternatives = []

        # If it looks like a text selector, try variations
        if 'text=' in selector or ':has-text' in selector:
            # Extract text content
            text_match = re.search(r'text="([^"]+)"', selector)
            if not text_match:
                text_match = re.search(r':has-text\("([^"]+)"\)', selector)

            if text_match:
                text = text_match.group(1)
                alternatives.extend([
                    f'button:has-text("{text}")',
                    f'a:has-text("{text}")',
                    f'[role="button"]:has-text("{text}")',
                    f'span:has-text("{text}")',
                    f'div:has-text("{text}")',
                ])

        return alternatives

    def _generate_smart_alternatives(self, selector: str) -> List[str]:
        """Generate smart alternative selectors using UI Brain insights."""
        alternatives = []

        if not self._ui_brain:
            return alternatives

        brain = self._ui_brain.get_current_brain()
        if not brain:
            return alternatives

        # Extract potential identifiers from the original selector
        description = self._extract_description_from_selector(selector)

        if description:
            # Find elements with similar labels
            for element in brain.elements:
                if element.resolved_label and description.lower() in element.resolved_label.lower():
                    alternatives.append(element.logical_selector)
                    if element.structural_selector != element.logical_selector:
                        alternatives.append(element.structural_selector)

        # Remove duplicates while preserving order
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt not in seen and alt != selector:
                seen.add(alt)
                unique_alternatives.append(alt)

        return unique_alternatives[:5]  # Limit to 5 alternatives

    def _find_similar_elements(self, selector: str) -> List[ElementDescriptor]:
        """Find elements similar to what the selector might be targeting."""
        if not self._ui_brain:
            return []

        brain = self._ui_brain.get_current_brain()
        if not brain:
            return []

        similar = []

        # Determine target element type from selector
        is_button = "button" in selector.lower() or "btn" in selector.lower()
        is_input = "input" in selector.lower() or "field" in selector.lower()
        is_link = "link" in selector.lower() or "<a" in selector.lower()

        for element in brain.elements:
            # Filter by type
            if is_button and element.element_type != "button":
                continue
            if is_input and element.element_type != "input":
                continue
            if is_link and element.element_type != "link":
                continue

            # Only include visible and enabled elements
            if element.visibility_state and element.enabled_state:
                similar.append(element)

        return similar

    def _log_healing_attempt(self, original: str, tried: str, success: bool, method: str) -> None:
        """Log a healing attempt to the step logger."""
        if self.step_logger:
            self.step_logger.log_healing_attempt(original, tried, success, method)

    def _get_elements_summary(self) -> str:
        """Get a summary of interactive elements on the page."""
        try:
            script = '''
            () => {
                const elements = [];
                const interactiveSelectors = 'button, a, input, select, textarea, [role="button"], [onclick]';
                document.querySelectorAll(interactiveSelectors).forEach((el, i) => {
                    if (i > 50) return; // Limit to 50 elements
                    const info = {
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || '').trim().substring(0, 50),
                        id: el.id || null,
                        class: el.className || null,
                        type: el.type || null,
                        placeholder: el.placeholder || null,
                        name: el.name || null,
                        role: el.getAttribute('role') || null,
                        ariaLabel: el.getAttribute('aria-label') || null,
                    };
                    // Filter out empty info
                    Object.keys(info).forEach(k => !info[k] && delete info[k]);
                    if (Object.keys(info).length > 1) elements.push(info);
                });
                return elements;
            }
            '''
            elements = self.browser.execute_script(script) or []
            return json.dumps(elements[:30], indent=2)  # Limit output size
        except Exception:
            return "Unable to analyze page elements"

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling various formats."""
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def reset_history(self, reset_healing_stats: bool = False) -> None:
        """Clear step history for new scenario."""
        self.step_history = []
        if reset_healing_stats:
            self._healing_stats = {
                "attempts": 0,
                "successes": 0,
                "methods_used": {}
            }

    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get auto-healing statistics."""
        return {
            **self._healing_stats,
            "success_rate": (
                self._healing_stats["successes"] / self._healing_stats["attempts"] * 100
                if self._healing_stats["attempts"] > 0 else 0
            )
        }
