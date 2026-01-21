"""
Brain-Enhanced Step Interpreter

Integrates UI Brain with step interpretation for intelligent,
self-healing element resolution during test execution.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from app.brain.ui_brain import UIBrain, PageBrain, ElementDescriptor
from app.brain.element_classifier import ElementClassifier, SelectorCandidate
from app.brain.page_store import PageBrainStore
from app.executor.browser import BrowserAutomation, BrowserAction


@dataclass
class ElementResolution:
    """Result of element resolution."""
    found: bool
    selector: str
    confidence: float
    strategy: str
    element_id: Optional[str] = None
    healed: bool = False
    original_selector: Optional[str] = None


class BrainInterpreter:
    """
    AI-powered step interpreter with UI Brain integration.

    Uses DOM-based element intelligence for reliable element resolution
    and self-healing capabilities.
    """

    def __init__(
        self,
        browser: BrowserAutomation,
        storage_dir: str = "brain_data",
        auto_heal: bool = True
    ):
        """
        Initialize the brain interpreter.

        Args:
            browser: BrowserAutomation instance
            storage_dir: Directory for brain storage
            auto_heal: Enable self-healing selectors
        """
        self.browser = browser
        self.ui_brain = UIBrain()
        self.classifier = ElementClassifier()
        self.store = PageBrainStore(storage_dir)
        self.auto_heal = auto_heal

        self._current_brain: Optional[PageBrain] = None
        self._step_history: List[str] = []
        self._healing_log: List[Dict[str, Any]] = []

    def capture_page_brain(self) -> PageBrain:
        """
        Capture and store the current page's UI Brain.

        Returns:
            PageBrain for current page
        """
        # Check DOM stability
        if not self.ui_brain.is_dom_stable(self.browser):
            # Wait briefly and retry
            self.browser.page.wait_for_load_state("networkidle")

        # Build the brain
        brain = self.ui_brain.build_page_brain(self.browser)
        self._current_brain = brain

        # Store for persistence
        self.store.save_brain(brain.to_dict())

        return brain

    def get_or_build_brain(self) -> PageBrain:
        """
        Get existing brain or build new one.

        Returns:
            Current PageBrain
        """
        url = self.browser.get_current_url()
        dom_hash = self.ui_brain.compute_dom_hash(self.browser)

        # Check if we have a valid cached brain
        if self._current_brain and self._current_brain.dom_hash == dom_hash:
            return self._current_brain

        # Check stored brain
        if self.store.check_brain_valid(url, dom_hash):
            brain_data = self.store.load_brain(url)
            if brain_data:
                # Reconstruct PageBrain from stored data
                self._current_brain = self._reconstruct_brain(brain_data)
                return self._current_brain

        # Build new brain
        return self.capture_page_brain()

    def _reconstruct_brain(self, data: Dict[str, Any]) -> PageBrain:
        """Reconstruct PageBrain from stored dictionary."""
        elements = []
        for el_data in data.get("elements", []):
            element = ElementDescriptor(
                element_id=el_data.get("element_id", ""),
                element_type=el_data.get("element_type", "unknown"),
                element_subtype=el_data.get("element_subtype"),
                resolved_label=el_data.get("resolved_label"),
                logical_selector=el_data.get("logical_selector", ""),
                structural_selector=el_data.get("structural_selector", ""),
                visibility_state=el_data.get("visibility_state", True),
                enabled_state=el_data.get("enabled_state", True),
                required=el_data.get("required", False),
                current_value=el_data.get("current_value"),
                parent_context=el_data.get("parent_context"),
                supported_actions=el_data.get("supported_actions", []),
                selector_confidence=el_data.get("selector_confidence", 1.0),
                attributes=el_data.get("attributes", {})
            )
            elements.append(element)

        brain = PageBrain(
            url=data.get("url", ""),
            title=data.get("title", ""),
            dom_hash=data.get("dom_hash", ""),
            capture_timestamp=data.get("capture_timestamp", ""),
            ready_state=data.get("ready_state", "complete"),
            elements=elements,
            page_signature=data.get("page_signature", "")
        )

        self.ui_brain._current_brain = brain
        return brain

    def resolve_element(
        self,
        description: str,
        element_type: Optional[str] = None
    ) -> ElementResolution:
        """
        Resolve an element from natural language description.

        Args:
            description: Natural language description (e.g., "login button")
            element_type: Optional type hint (e.g., "button", "input")

        Returns:
            ElementResolution with selector and metadata
        """
        # Ensure we have a brain
        brain = self.get_or_build_brain()

        # Try to resolve from brain
        element = self._find_element_in_brain(description, element_type)

        if element:
            # Verify element exists in current DOM
            if self._verify_selector(element.logical_selector):
                return ElementResolution(
                    found=True,
                    selector=element.logical_selector,
                    confidence=element.selector_confidence,
                    strategy="brain_match",
                    element_id=element.element_id
                )

            # Try structural selector as fallback
            if self._verify_selector(element.structural_selector):
                return ElementResolution(
                    found=True,
                    selector=element.structural_selector,
                    confidence=element.selector_confidence * 0.8,
                    strategy="brain_structural",
                    element_id=element.element_id
                )

            # Attempt self-healing
            if self.auto_heal:
                healed = self._attempt_healing(element, description)
                if healed:
                    return healed

        # Fall back to DOM search
        return self._search_current_dom(description, element_type)

    def _find_element_in_brain(
        self,
        description: str,
        element_type: Optional[str]
    ) -> Optional[ElementDescriptor]:
        """Find element in current brain using fuzzy matching."""
        if not self._current_brain:
            return None

        description_lower = description.lower()
        candidates: List[Tuple[ElementDescriptor, float]] = []

        for element in self._current_brain.elements:
            # Skip if type doesn't match
            if element_type:
                if element.element_type != element_type and element.element_subtype != element_type:
                    continue

            score = self._calculate_match_score(element, description_lower)
            if score > 0.3:
                candidates.append((element, score))

        if not candidates:
            return None

        # Sort by score and return best match
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _calculate_match_score(self, element: ElementDescriptor, description: str) -> float:
        """Calculate match score between element and description."""
        score = 0.0
        words = description.split()

        # Label matching (highest weight)
        if element.resolved_label:
            label_lower = element.resolved_label.lower()
            if description in label_lower:
                score += 0.5
            elif label_lower in description:
                score += 0.4
            else:
                # Word matching
                for word in words:
                    if len(word) > 2 and word in label_lower:
                        score += 0.15

        # ID matching
        if element.element_id:
            id_lower = element.element_id.lower()
            for word in words:
                if len(word) > 2 and word in id_lower:
                    score += 0.1

        # Type keywords
        type_keywords = {
            "button": ["button", "btn", "submit", "click", "press"],
            "input": ["field", "input", "textbox", "enter", "type"],
            "text": ["field", "input", "textbox", "text"],
            "password": ["password", "passwd", "secret"],
            "email": ["email", "mail"],
            "checkbox": ["checkbox", "check", "tick", "toggle"],
            "radio": ["radio", "option", "choice"],
            "select": ["dropdown", "select", "choose", "pick"],
            "link": ["link", "navigate", "go", "click"]
        }

        for el_type, keywords in type_keywords.items():
            if element.element_type == el_type or element.element_subtype == el_type:
                for kw in keywords:
                    if kw in description:
                        score += 0.15
                        break

        return min(score, 1.0)

    def _verify_selector(self, selector: str) -> bool:
        """Verify a selector exists in current DOM."""
        try:
            elements = self.browser.find_elements(selector)
            return len(elements) > 0
        except Exception:
            return False

    def _attempt_healing(
        self,
        original: ElementDescriptor,
        description: str
    ) -> Optional[ElementResolution]:
        """Attempt to heal a broken selector."""
        # Rebuild brain with fresh DOM
        fresh_brain = self.capture_page_brain()

        # Find similar element in fresh brain
        healed_element = self._find_element_in_brain(description, original.element_type)

        if healed_element and self._verify_selector(healed_element.logical_selector):
            # Log the healing
            self._healing_log.append({
                "original_id": original.element_id,
                "original_selector": original.logical_selector,
                "healed_id": healed_element.element_id,
                "healed_selector": healed_element.logical_selector,
                "description": description
            })

            return ElementResolution(
                found=True,
                selector=healed_element.logical_selector,
                confidence=healed_element.selector_confidence * 0.9,
                strategy="self_healed",
                element_id=healed_element.element_id,
                healed=True,
                original_selector=original.logical_selector
            )

        return None

    def _search_current_dom(
        self,
        description: str,
        element_type: Optional[str]
    ) -> ElementResolution:
        """Search current DOM for element matching description."""
        # Rebuild brain
        brain = self.capture_page_brain()

        # Search with fresh brain
        element = self._find_element_in_brain(description, element_type)

        if element and self._verify_selector(element.logical_selector):
            return ElementResolution(
                found=True,
                selector=element.logical_selector,
                confidence=element.selector_confidence,
                strategy="dom_search",
                element_id=element.element_id
            )

        # Last resort: generate selector from description
        return ElementResolution(
            found=False,
            selector=self._generate_fallback_selector(description, element_type),
            confidence=0.3,
            strategy="fallback"
        )

    def _generate_fallback_selector(
        self,
        description: str,
        element_type: Optional[str]
    ) -> str:
        """Generate a fallback selector from description."""
        desc_clean = description.strip()

        # Try text-based selector
        if element_type == "button":
            return f'button:has-text("{desc_clean}")'
        elif element_type == "link":
            return f'a:has-text("{desc_clean}")'
        elif element_type in ("input", "text"):
            return f'[placeholder*="{desc_clean}" i]'
        else:
            return f'text="{desc_clean}"'

    def execute_action(
        self,
        action_type: str,
        selector: str,
        value: Optional[str] = None
    ) -> BrowserAction:
        """
        Execute a browser action with brain-enhanced verification.

        Args:
            action_type: Type of action (click, fill, etc.)
            selector: Element selector
            value: Optional value for fill/select actions

        Returns:
            BrowserAction result
        """
        # Verify element exists before action
        if not self._verify_selector(selector):
            return BrowserAction(
                success=False,
                action=action_type,
                selector=selector,
                error=f"Element not found: {selector}"
            )

        # Execute action
        if action_type == "click":
            result = self.browser.click(selector)
        elif action_type == "fill":
            result = self.browser.fill(selector, value or "")
        elif action_type == "select":
            result = self.browser.select_option(selector, value or "")
        elif action_type == "check":
            result = self.browser.check(selector)
        elif action_type == "uncheck":
            result = self.browser.uncheck(selector)
        elif action_type == "hover":
            result = self.browser.hover(selector)
        elif action_type == "type":
            result = self.browser.type_text(selector, value or "")
        else:
            result = BrowserAction(
                success=False,
                action=action_type,
                error=f"Unknown action type: {action_type}"
            )

        # Refresh brain after action if DOM might have changed
        if result.success and action_type in ("click", "fill", "select", "check", "uncheck"):
            # Invalidate current brain to force refresh on next access
            self._current_brain = None

        return result

    def get_page_elements_summary(self) -> Dict[str, Any]:
        """
        Get a summary of elements on current page.

        Returns:
            Summary dictionary with element counts and types
        """
        brain = self.get_or_build_brain()

        type_counts: Dict[str, int] = {}
        for element in brain.elements:
            el_type = element.element_type
            type_counts[el_type] = type_counts.get(el_type, 0) + 1

        return {
            "url": brain.url,
            "title": brain.title,
            "total_elements": len(brain.elements),
            "element_types": type_counts,
            "dom_hash": brain.dom_hash,
            "actionable_count": len([e for e in brain.elements if e.visibility_state and e.enabled_state])
        }

    def get_elements_for_ai(self) -> str:
        """
        Get element summary formatted for AI prompt.

        Returns:
            JSON string of element summaries
        """
        brain = self.get_or_build_brain()

        elements_summary = []
        for element in brain.elements[:50]:  # Limit for prompt size
            if not element.visibility_state:
                continue

            summary = {
                "id": element.element_id,
                "type": element.element_type,
                "label": element.resolved_label,
                "selector": element.logical_selector,
                "actions": element.supported_actions
            }
            # Filter None values
            summary = {k: v for k, v in summary.items() if v}
            elements_summary.append(summary)

        return json.dumps(elements_summary, indent=2)

    def get_healing_log(self) -> List[Dict[str, Any]]:
        """Get the self-healing log."""
        return self._healing_log.copy()

    def clear_healing_log(self) -> None:
        """Clear the self-healing log."""
        self._healing_log.clear()

    def reset_for_scenario(self) -> None:
        """Reset state for new scenario."""
        self._step_history.clear()
        self._current_brain = None

    def get_brain_json(self) -> Optional[str]:
        """
        Get current brain as JSON string.

        Returns:
            JSON string or None if no brain
        """
        if not self._current_brain:
            self.get_or_build_brain()

        if self._current_brain:
            return json.dumps(self._current_brain.to_dict(), indent=2)

        return None
