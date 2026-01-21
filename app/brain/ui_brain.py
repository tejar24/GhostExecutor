"""
UI Brain - Core DOM Analysis Engine

Tool-independent AI interpreter that builds and maintains a persistent
representation of the application's interactive structure from DOM state.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class ElementDescriptor:
    """Complete descriptor for an interactive DOM element."""
    element_id: str
    element_type: str
    element_subtype: Optional[str] = None
    resolved_label: Optional[str] = None
    logical_selector: str = ""
    structural_selector: str = ""
    visibility_state: bool = True
    enabled_state: bool = True
    required: bool = False
    current_value: Optional[str] = None
    parent_context: Optional[str] = None
    supported_actions: List[str] = field(default_factory=list)
    selector_confidence: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PageBrain:
    """Complete UI Brain representation for a single page."""
    url: str
    title: str
    dom_hash: str
    capture_timestamp: str
    ready_state: str
    elements: List[ElementDescriptor] = field(default_factory=list)
    page_signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "dom_hash": self.dom_hash,
            "capture_timestamp": self.capture_timestamp,
            "ready_state": self.ready_state,
            "page_signature": self.page_signature,
            "element_count": len(self.elements),
            "elements": [e.to_dict() for e in self.elements]
        }


class UIBrain:
    """
    AI-driven DOM analysis engine that operates on DOM snapshots.

    Discovers, classifies, and indexes all interactive elements,
    generating stable selectors for reliable runtime interaction.
    """

    # Element type mappings
    ELEMENT_TYPES = {
        "input": "input",
        "textarea": "input",
        "select": "select",
        "button": "button",
        "a": "link",
        "label": "label",
        "form": "form",
        "table": "table",
        "dialog": "modal",
        "div": "container",
        "span": "text",
        "img": "image"
    }

    INPUT_SUBTYPES = {
        "text": "text",
        "password": "password",
        "email": "email",
        "number": "number",
        "date": "date",
        "datetime-local": "datetime",
        "time": "time",
        "tel": "phone",
        "url": "url",
        "search": "search",
        "checkbox": "checkbox",
        "radio": "radio",
        "file": "file",
        "hidden": "hidden",
        "submit": "submit_button",
        "reset": "reset_button",
        "button": "button"
    }

    # Actions supported by element type
    ELEMENT_ACTIONS = {
        "input": ["fill", "clear", "type"],
        "password": ["fill", "clear", "type"],
        "email": ["fill", "clear", "type"],
        "text": ["fill", "clear", "type"],
        "number": ["fill", "clear", "type"],
        "search": ["fill", "clear", "type"],
        "checkbox": ["check", "uncheck", "toggle"],
        "radio": ["select", "click"],
        "select": ["select", "click"],
        "button": ["click"],
        "submit_button": ["click"],
        "link": ["click"],
        "modal": ["close", "interact"],
        "file": ["upload"]
    }

    # JavaScript for comprehensive DOM element extraction
    DOM_EXTRACTION_SCRIPT = '''
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
            // Skip if already processed or hidden
            const rect = el.getBoundingClientRect();
            const isVisible = rect.width > 0 && rect.height > 0;
            const style = window.getComputedStyle(el);
            const isDisplayed = style.display !== 'none' && style.visibility !== 'hidden';

            // Generate unique key to avoid duplicates
            const uniqueKey = el.tagName + el.id + el.name + el.textContent?.substring(0, 20);
            if (processedElements.has(uniqueKey)) return;
            processedElements.add(uniqueKey);

            // Get associated label
            let labelText = null;
            if (el.id) {
                const label = document.querySelector(`label[for="${el.id}"]`);
                if (label) labelText = label.textContent?.trim();
            }
            if (!labelText && el.closest('label')) {
                labelText = el.closest('label').textContent?.trim();
            }

            // Build element info
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
                ariaDescribedBy: el.getAttribute('aria-describedby') || null,
                role: el.getAttribute('role') || null,
                title: el.title || null,
                href: el.href || null,
                dataTestId: el.getAttribute('data-testid') || null,
                dataCy: el.getAttribute('data-cy') || null,
                dataId: el.getAttribute('data-id') || null,
                disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                required: el.required || el.getAttribute('aria-required') === 'true',
                readonly: el.readOnly || el.getAttribute('aria-readonly') === 'true',
                checked: el.checked || null,
                selected: el.selected || null,
                labelText: labelText,
                isVisible: isVisible && isDisplayed,
                isEnabled: !el.disabled,
                boundingRect: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                },
                parentTag: el.parentElement?.tagName?.toLowerCase() || null,
                parentId: el.parentElement?.id || null,
                parentClass: el.parentElement?.className || null,
                siblingIndex: Array.from(el.parentElement?.children || []).indexOf(el),
                path: getElementPath(el)
            };

            // Filter null values
            Object.keys(info).forEach(k => {
                if (info[k] === null || info[k] === '' || info[k] === undefined) {
                    delete info[k];
                }
            });

            elements.push(info);
        });

        function getElementPath(el) {
            const path = [];
            let current = el;
            while (current && current !== document.body) {
                let selector = current.tagName.toLowerCase();
                if (current.id) {
                    selector += '#' + current.id;
                } else if (current.className && typeof current.className === 'string') {
                    const classes = current.className.trim().split(/\\s+/).slice(0, 2).join('.');
                    if (classes) selector += '.' + classes;
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
            elementCount: elements.length,
            elements: elements
        };
    }
    '''

    DOM_HASH_SCRIPT = '''
    () => {
        const structuralElements = document.querySelectorAll('input, button, a, select, textarea, [role]');
        let signature = '';
        structuralElements.forEach(el => {
            signature += el.tagName + (el.id || '') + (el.name || '') + (el.type || '');
        });
        return signature;
    }
    '''

    def __init__(self):
        self._current_brain: Optional[PageBrain] = None
        self._brain_cache: Dict[str, PageBrain] = {}

    def extract_dom_state(self, browser) -> Dict[str, Any]:
        """
        Extract complete DOM state from browser.

        Args:
            browser: BrowserAutomation instance

        Returns:
            Dict containing DOM snapshot with all elements
        """
        try:
            dom_state = browser.execute_script(self.DOM_EXTRACTION_SCRIPT)
            return dom_state if dom_state else {}
        except Exception as e:
            return {"error": str(e), "elements": []}

    def compute_dom_hash(self, browser) -> str:
        """
        Generate deterministic hash from DOM structure.

        Args:
            browser: BrowserAutomation instance

        Returns:
            SHA256 hash of structural DOM signature
        """
        try:
            signature = browser.execute_script(self.DOM_HASH_SCRIPT)
            if signature:
                return hashlib.sha256(signature.encode()).hexdigest()[:16]
        except Exception:
            pass
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]

    def is_dom_stable(self, browser, check_count: int = 2) -> bool:
        """
        Check if DOM is stable by comparing consecutive snapshots.

        Args:
            browser: BrowserAutomation instance
            check_count: Number of consecutive checks

        Returns:
            True if DOM is stable
        """
        hashes = []
        for _ in range(check_count):
            current_hash = self.compute_dom_hash(browser)
            hashes.append(current_hash)

        return len(set(hashes)) == 1

    def build_page_brain(self, browser) -> PageBrain:
        """
        Build complete UI Brain for current page state.

        Args:
            browser: BrowserAutomation instance

        Returns:
            PageBrain with all discovered elements
        """
        # Extract DOM state
        dom_state = self.extract_dom_state(browser)

        # Build page brain
        brain = PageBrain(
            url=dom_state.get("url", browser.get_current_url()),
            title=dom_state.get("title", browser.get_title()),
            dom_hash=self.compute_dom_hash(browser),
            capture_timestamp=datetime.now().isoformat(),
            ready_state=dom_state.get("readyState", "unknown")
        )

        # Process each element
        raw_elements = dom_state.get("elements", [])
        for idx, raw_el in enumerate(raw_elements):
            element = self._classify_element(raw_el, idx)
            if element:
                brain.elements.append(element)

        # Generate page signature
        brain.page_signature = self._generate_page_signature(brain)

        # Cache the brain
        self._current_brain = brain
        self._brain_cache[brain.dom_hash] = brain

        return brain

    def _classify_element(self, raw: Dict[str, Any], index: int) -> Optional[ElementDescriptor]:
        """
        Classify a raw DOM element and build descriptor.

        Args:
            raw: Raw element data from DOM extraction
            index: Element index

        Returns:
            ElementDescriptor or None if element should be skipped
        """
        tag = raw.get("tag", "")

        # Skip hidden elements unless they're inputs
        if not raw.get("isVisible", True) and tag != "input":
            return None

        # Determine element type
        element_type = self.ELEMENT_TYPES.get(tag, "unknown")

        # Determine subtype for inputs
        subtype = None
        if tag == "input":
            input_type = raw.get("type", "text")
            subtype = self.INPUT_SUBTYPES.get(input_type, "text")
            element_type = "input"
        elif tag == "select":
            subtype = "dropdown"
        elif tag == "textarea":
            subtype = "multiline"
        elif tag == "button" or raw.get("role") == "button":
            subtype = "button"
        elif tag == "a":
            subtype = "hyperlink"
        elif raw.get("role") == "checkbox":
            subtype = "checkbox"
        elif raw.get("role") == "radio":
            subtype = "radio"
        elif raw.get("role") == "switch":
            subtype = "toggle"

        # Resolve human-readable label
        resolved_label = self._resolve_label(raw)

        # Generate selectors
        logical_selector = self._generate_logical_selector(raw)
        structural_selector = self._generate_structural_selector(raw)

        # Determine supported actions
        action_key = subtype or element_type
        supported_actions = self.ELEMENT_ACTIONS.get(action_key, ["click"])

        # Calculate selector confidence
        confidence = self._calculate_selector_confidence(raw, logical_selector)

        # Build element ID
        element_id = self._generate_element_id(raw, index)

        return ElementDescriptor(
            element_id=element_id,
            element_type=element_type,
            element_subtype=subtype,
            resolved_label=resolved_label,
            logical_selector=logical_selector,
            structural_selector=structural_selector,
            visibility_state=raw.get("isVisible", True),
            enabled_state=raw.get("isEnabled", True),
            required=raw.get("required", False),
            current_value=raw.get("value"),
            parent_context=raw.get("parentId") or raw.get("parentClass"),
            supported_actions=supported_actions,
            selector_confidence=confidence,
            attributes={
                "tag": tag,
                "id": raw.get("id"),
                "name": raw.get("name"),
                "type": raw.get("type"),
                "role": raw.get("role"),
                "data_testid": raw.get("dataTestId"),
                "data_cy": raw.get("dataCy")
            }
        )

    def _resolve_label(self, raw: Dict[str, Any]) -> Optional[str]:
        """
        Resolve human-readable label for an element.

        Priority order:
        1. Associated label text
        2. Aria-label
        3. Placeholder
        4. Title
        5. Visible text content
        6. Name attribute
        """
        candidates = [
            raw.get("labelText"),
            raw.get("ariaLabel"),
            raw.get("placeholder"),
            raw.get("title"),
            raw.get("innerText", "").strip()[:50],
            raw.get("text", "").strip()[:50],
            raw.get("name")
        ]

        for candidate in candidates:
            if candidate and len(str(candidate).strip()) > 0:
                return str(candidate).strip()

        return None

    def _generate_logical_selector(self, raw: Dict[str, Any]) -> str:
        """
        Generate primary selector using semantic attributes.

        Priority order:
        1. data-testid
        2. data-cy
        3. ID
        4. role + name/label
        5. placeholder
        6. text content
        """
        # Test IDs (highest priority)
        if raw.get("dataTestId"):
            return f'[data-testid="{raw["dataTestId"]}"]'

        if raw.get("dataCy"):
            return f'[data-cy="{raw["dataCy"]}"]'

        # ID selector
        if raw.get("id"):
            return f'#{raw["id"]}'

        # Role-based selector
        role = raw.get("role")
        if role:
            name = raw.get("ariaLabel") or raw.get("innerText", "").strip()[:30]
            if name:
                return f'[role="{role}"][name="{name}"]'
            return f'[role="{role}"]'

        tag = raw.get("tag", "")

        # Input with name
        if tag == "input" and raw.get("name"):
            return f'input[name="{raw["name"]}"]'

        # Placeholder-based
        if raw.get("placeholder"):
            return f'[placeholder="{raw["placeholder"]}"]'

        # Text-based selectors
        text = (raw.get("innerText") or raw.get("text") or "").strip()
        if text and len(text) < 50:
            if tag == "button":
                return f'button:has-text("{text}")'
            elif tag == "a":
                return f'a:has-text("{text}")'
            else:
                return f'text="{text}"'

        # Label-based for inputs
        if raw.get("labelText") and tag == "input":
            return f'label:has-text("{raw["labelText"]}") >> input'

        # Fallback to structural
        return self._generate_structural_selector(raw)

    def _generate_structural_selector(self, raw: Dict[str, Any]) -> str:
        """
        Generate fallback selector using DOM structure.
        """
        tag = raw.get("tag", "div")
        parts = [tag]

        # Add type if input
        if raw.get("type"):
            parts.append(f'[type="{raw["type"]}"]')

        # Add class (first significant class only)
        class_name = raw.get("className", "")
        if class_name and isinstance(class_name, str):
            classes = class_name.strip().split()
            # Filter out utility classes
            significant_classes = [c for c in classes if not c.startswith(('ng-', 'v-', 'css-', 'sc-'))]
            if significant_classes:
                parts.append(f'.{significant_classes[0]}')

        # Add nth-child if we have sibling info
        sibling_index = raw.get("siblingIndex")
        if sibling_index is not None and sibling_index >= 0:
            parts.append(f':nth-child({sibling_index + 1})')

        return "".join(parts)

    def _calculate_selector_confidence(self, raw: Dict[str, Any], selector: str) -> float:
        """
        Calculate confidence score for selector uniqueness.
        """
        score = 0.5  # Base score

        # High confidence indicators
        if raw.get("dataTestId"):
            score += 0.4
        elif raw.get("dataCy"):
            score += 0.4
        elif raw.get("id"):
            score += 0.35

        # Medium confidence indicators
        if raw.get("name"):
            score += 0.15
        if raw.get("ariaLabel"):
            score += 0.1
        if raw.get("placeholder"):
            score += 0.1

        # Role adds confidence
        if raw.get("role"):
            score += 0.1

        return min(score, 1.0)

    def _generate_element_id(self, raw: Dict[str, Any], index: int) -> str:
        """
        Generate deterministic unique ID for element.
        """
        # Use existing IDs if available
        if raw.get("dataTestId"):
            return f"test_{raw['dataTestId']}"
        if raw.get("id"):
            return f"id_{raw['id']}"
        if raw.get("name"):
            return f"name_{raw['name']}"

        # Generate from label and type
        label = self._resolve_label(raw)
        tag = raw.get("tag", "element")

        if label:
            # Sanitize label for ID
            sanitized = "".join(c if c.isalnum() else "_" for c in label[:20])
            return f"{tag}_{sanitized}_{index}"

        return f"{tag}_{index}"

    def _generate_page_signature(self, brain: PageBrain) -> str:
        """
        Generate unique page signature from element structure.
        """
        sig_parts = [brain.url, brain.title]
        for el in brain.elements[:20]:  # Use first 20 elements
            sig_parts.append(f"{el.element_type}:{el.resolved_label or el.element_id}")

        signature = "|".join(sig_parts)
        return hashlib.sha256(signature.encode()).hexdigest()[:12]

    def resolve_element(self, description: str) -> Optional[ElementDescriptor]:
        """
        Resolve an element from natural language description.

        Args:
            description: Natural language description (e.g., "login button", "email field")

        Returns:
            Best matching ElementDescriptor or None
        """
        if not self._current_brain:
            return None

        description_lower = description.lower()
        best_match = None
        best_score = 0

        for element in self._current_brain.elements:
            score = self._match_score(element, description_lower)
            if score > best_score:
                best_score = score
                best_match = element

        return best_match if best_score > 0.3 else None

    def _match_score(self, element: ElementDescriptor, description: str) -> float:
        """
        Calculate match score between element and description.
        """
        score = 0.0

        # Check label match
        if element.resolved_label:
            label_lower = element.resolved_label.lower()
            if description in label_lower:
                score += 0.5
            elif any(word in label_lower for word in description.split()):
                score += 0.3

        # Check element ID match
        if element.element_id:
            id_lower = element.element_id.lower()
            if description in id_lower:
                score += 0.3

        # Check type match
        type_keywords = {
            "button": ["button", "btn", "submit", "click"],
            "input": ["field", "input", "textbox", "enter"],
            "checkbox": ["checkbox", "check", "tick"],
            "radio": ["radio", "option"],
            "select": ["dropdown", "select", "choose"],
            "link": ["link", "click", "navigate"]
        }

        for el_type, keywords in type_keywords.items():
            if element.element_type == el_type or element.element_subtype == el_type:
                if any(kw in description for kw in keywords):
                    score += 0.2

        return min(score, 1.0)

    def get_current_brain(self) -> Optional[PageBrain]:
        """Get the current page brain."""
        return self._current_brain

    def get_elements_by_type(self, element_type: str) -> List[ElementDescriptor]:
        """Get all elements of a specific type."""
        if not self._current_brain:
            return []

        return [e for e in self._current_brain.elements
                if e.element_type == element_type or e.element_subtype == element_type]

    def get_actionable_elements(self) -> List[ElementDescriptor]:
        """Get all visible and enabled elements that can be interacted with."""
        if not self._current_brain:
            return []

        return [e for e in self._current_brain.elements
                if e.visibility_state and e.enabled_state]

    def verify_element_exists(self, selector: str, browser) -> bool:
        """
        Verify element exists in current DOM.

        Args:
            selector: CSS/text selector
            browser: BrowserAutomation instance

        Returns:
            True if element exists
        """
        try:
            elements = browser.find_elements(selector)
            return len(elements) > 0
        except Exception:
            return False

    def refresh_brain(self, browser) -> PageBrain:
        """
        Refresh the UI Brain with current DOM state.

        Args:
            browser: BrowserAutomation instance

        Returns:
            Updated PageBrain
        """
        return self.build_page_brain(browser)
