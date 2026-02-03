"""
AI Prompts for Ghost-QC
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
