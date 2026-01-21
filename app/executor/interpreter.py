"""
AI-Driven Step Interpreter

Uses Claude AI to interpret Gherkin steps and determine browser actions.
This is the intelligence layer that enables autonomous test execution.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.ai.engine import run_ai
from app.executor.browser import BrowserAutomation, BrowserAction


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

    def __init__(self, browser: BrowserAutomation):
        self.browser = browser
        self.step_history: List[str] = []

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
                # Try to find element, with fallback
                browser_result = self._execute_click(selector)
                result["success"] = browser_result.success
                result["error"] = browser_result.error

            elif action_type == "fill":
                selector = action.get("selector", "")
                value = action.get("value", "")
                browser_result = self.browser.fill(selector, value)
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

    def _execute_click(self, selector: str) -> BrowserAction:
        """Execute click with smart retries and selector alternatives."""
        # Try direct selector first
        result = self.browser.click(selector)
        if result.success:
            return result

        # Try text-based alternatives
        alternatives = self._generate_selector_alternatives(selector)
        for alt_selector in alternatives:
            result = self.browser.click(alt_selector)
            if result.success:
                return result

        return result

    def _generate_selector_alternatives(self, selector: str) -> List[str]:
        """Generate alternative selectors to try."""
        alternatives = []

        # If it looks like a text selector, try variations
        if 'text=' in selector or ':has-text' in selector:
            # Extract text content
            text_match = re.search(r'text="([^"]+)"', selector)
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

    def reset_history(self) -> None:
        """Clear step history for new scenario."""
        self.step_history = []
