"""
Element Classifier

Advanced element classification and intelligent selector generation
for self-healing test automation.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SelectorCandidate:
    """A candidate selector with confidence score."""
    selector: str
    strategy: str
    confidence: float
    is_unique: bool = True


class ElementClassifier:
    # Allow extension for custom frameworks/components
    CUSTOM_PATTERNS = {}

    def extend_framework_patterns(self, name: str, patterns: dict):
        self.FRAMEWORK_PATTERNS[name] = patterns
        self.CUSTOM_PATTERNS[name] = patterns
    """
    Intelligent element classifier that generates robust selectors
    and provides self-healing capabilities.
    """

    # Framework-specific patterns
    FRAMEWORK_PATTERNS = {
        "react": {
            "data_attrs": ["data-testid", "data-reactid"],
            "class_patterns": [r"^css-", r"^sc-", r"^styled-"],
            "component_patterns": [r"[A-Z][a-z]+(?:[A-Z][a-z]+)*"]
        },
        "angular": {
            "data_attrs": ["data-cy", "ng-reflect-"],
            "class_patterns": [r"^ng-", r"^mat-", r"^cdk-"],
            "directives": ["ng-click", "ng-model", "ng-if"]
        },
        "vue": {
            "data_attrs": ["data-v-", "v-"],
            "class_patterns": [r"^v-"],
            "directives": ["v-on:", "v-bind:", "@click"]
        },
        "bootstrap": {
            "class_patterns": [r"^btn-", r"^form-", r"^nav-", r"^card-"],
            "component_classes": ["btn", "form-control", "nav-link"]
        },
        "material-ui": {
            "class_patterns": [r"^Mui", r"^MuiButton", r"^MuiInput"],
            "data_attrs": ["data-testid"]
        },
        "ant-design": {
            "class_patterns": [r"^ant-"],
            "data_attrs": ["data-testid"]
        }
    }

    # Semantic element mappings
    SEMANTIC_MAPPINGS = {
        "login": ["login", "sign-in", "signin", "log-in"],
        "logout": ["logout", "sign-out", "signout", "log-out"],
        "submit": ["submit", "send", "save", "confirm", "ok"],
        "cancel": ["cancel", "close", "dismiss", "no"],
        "search": ["search", "find", "lookup", "query"],
        "email": ["email", "e-mail", "mail"],
        "password": ["password", "passwd", "pass", "pwd"],
        "username": ["username", "user", "login", "userid"],
        "next": ["next", "continue", "proceed", "forward"],
        "back": ["back", "previous", "return"],
        "delete": ["delete", "remove", "trash", "destroy"],
        "edit": ["edit", "modify", "update", "change"],
        "add": ["add", "create", "new", "plus"]
    }

    def __init__(self):
        self._selector_cache: Dict[str, List[SelectorCandidate]] = {}

    def classify_element(self, raw_element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep classification of an element.

        Args:
            raw_element: Raw element data from DOM extraction

        Returns:
            Classification result with semantic meaning and context
        """
        classification = {
            "element_type": self._determine_element_type(raw_element),
            "semantic_purpose": self._determine_semantic_purpose(raw_element),
            "framework_hints": self._detect_framework(raw_element),
            "interaction_model": self._determine_interaction_model(raw_element),
            "form_context": self._analyze_form_context(raw_element),
            "accessibility_info": self._extract_accessibility_info(raw_element)
        }

        return classification

    def _determine_element_type(self, raw: Dict[str, Any]) -> str:
        """Determine the functional element type."""
        tag = raw.get("tag", "").lower()
        input_type = raw.get("type", "").lower()
        role = raw.get("role", "").lower()

        # Role-based determination (highest priority)
        if role:
            role_mappings = {
                "button": "button",
                "link": "link",
                "checkbox": "checkbox",
                "radio": "radio",
                "textbox": "text_input",
                "searchbox": "search_input",
                "combobox": "dropdown",
                "listbox": "dropdown",
                "slider": "slider",
                "switch": "toggle",
                "tab": "tab",
                "menuitem": "menu_item",
                "option": "option"
            }
            if role in role_mappings:
                return role_mappings[role]

        # Tag + type based determination
        if tag == "input":
            type_mappings = {
                "text": "text_input",
                "password": "password_input",
                "email": "email_input",
                "number": "number_input",
                "tel": "phone_input",
                "url": "url_input",
                "search": "search_input",
                "date": "date_picker",
                "datetime-local": "datetime_picker",
                "time": "time_picker",
                "checkbox": "checkbox",
                "radio": "radio",
                "file": "file_upload",
                "submit": "submit_button",
                "button": "button",
                "hidden": "hidden_field",
                "range": "slider"
            }
            return type_mappings.get(input_type, "text_input")

        if tag == "textarea":
            return "multiline_input"

        if tag == "select":
            return "dropdown"

        if tag == "button":
            return "button"

        if tag == "a":
            return "link"

        # Detect buttons by class/role
        class_name = raw.get("className", "").lower()
        if any(btn in class_name for btn in ["btn", "button"]):
            return "button"

        return "unknown"

    def _determine_semantic_purpose(self, raw: Dict[str, Any]) -> Optional[str]:
        """Determine the semantic purpose of the element."""
        # Collect all text-like attributes
        text_sources = [
            raw.get("id", ""),
            raw.get("name", ""),
            raw.get("ariaLabel", ""),
            raw.get("placeholder", ""),
            raw.get("innerText", ""),
            raw.get("labelText", ""),
            raw.get("title", ""),
            raw.get("dataTestId", "")
        ]

        combined_text = " ".join(str(s).lower() for s in text_sources if s)

        # Match against semantic mappings
        for purpose, keywords in self.SEMANTIC_MAPPINGS.items():
            if any(kw in combined_text for kw in keywords):
                return purpose

        return None

    def _detect_framework(self, raw: Dict[str, Any]) -> List[str]:
        """Detect UI framework hints from element attributes."""
        detected = []
        class_name = raw.get("className", "")
        attrs = raw.get("attributes", {}) if "attributes" in raw else raw

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            # Check data attributes
            for attr in patterns.get("data_attrs", []):
                if any(key.startswith(attr) for key in attrs.keys() if isinstance(key, str)):
                    detected.append(framework)
                    break

            # Check class patterns
            for pattern in patterns.get("class_patterns", []):
                if re.search(pattern, class_name):
                    if framework not in detected:
                        detected.append(framework)
                    break

        return detected

    def _determine_interaction_model(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Determine how the element should be interacted with."""
        element_type = self._determine_element_type(raw)

        models = {
            "text_input": {
                "primary_action": "fill",
                "secondary_actions": ["clear", "type", "focus"],
                "requires_value": True,
                "clearable": True
            },
            "password_input": {
                "primary_action": "fill",
                "secondary_actions": ["clear", "type"],
                "requires_value": True,
                "clearable": True,
                "sensitive": True
            },
            "checkbox": {
                "primary_action": "toggle",
                "secondary_actions": ["check", "uncheck"],
                "requires_value": False,
                "stateful": True
            },
            "radio": {
                "primary_action": "select",
                "secondary_actions": ["click"],
                "requires_value": False,
                "group_member": True
            },
            "button": {
                "primary_action": "click",
                "secondary_actions": ["hover", "focus"],
                "requires_value": False
            },
            "link": {
                "primary_action": "click",
                "secondary_actions": ["hover"],
                "requires_value": False,
                "navigates": True
            },
            "dropdown": {
                "primary_action": "select",
                "secondary_actions": ["click", "open"],
                "requires_value": True
            },
            "file_upload": {
                "primary_action": "upload",
                "secondary_actions": [],
                "requires_value": True,
                "value_type": "file_path"
            }
        }

        return models.get(element_type, {
            "primary_action": "click",
            "secondary_actions": [],
            "requires_value": False
        })

    def _analyze_form_context(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze form context if element is part of a form."""
        # Check if parent is a form
        parent_tag = raw.get("parentTag", "")
        if parent_tag != "form":
            return None

        return {
            "in_form": True,
            "form_id": raw.get("parentId"),
            "is_required": raw.get("required", False),
            "validation_type": self._infer_validation_type(raw)
        }

    def _infer_validation_type(self, raw: Dict[str, Any]) -> Optional[str]:
        """Infer validation type from element attributes."""
        input_type = raw.get("type", "")
        name = (raw.get("name") or "").lower()
        placeholder = (raw.get("placeholder") or "").lower()

        if input_type == "email" or "email" in name or "email" in placeholder:
            return "email"
        if input_type == "tel" or "phone" in name:
            return "phone"
        if input_type == "url":
            return "url"
        if input_type == "number":
            return "number"
        if "password" in name:
            return "password"

        return None

    def _extract_accessibility_info(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Extract accessibility information."""
        return {
            "has_label": bool(raw.get("labelText") or raw.get("ariaLabel")),
            "aria_label": raw.get("ariaLabel"),
            "aria_labelledby": raw.get("ariaLabelledBy"),
            "aria_describedby": raw.get("ariaDescribedBy"),
            "role": raw.get("role"),
            "is_disabled": raw.get("disabled", False),
            "is_required": raw.get("required", False)
        }

    def generate_selectors(self, raw: Dict[str, Any], include_structural: bool = True) -> List[SelectorCandidate]:
        """
        Generate ranked list of selector candidates.

        Args:
            raw: Raw element data

        Returns:
            List of SelectorCandidate ordered by confidence
        """
        candidates = []

        # Strategy 1: Test ID (highest confidence)
        if raw.get("dataTestId"):
            candidates.append(SelectorCandidate(
                selector=f'[data-testid="{raw["dataTestId"]}"]',
                strategy="test_id",
                confidence=0.99
            ))

        if raw.get("dataCy"):
            candidates.append(SelectorCandidate(
                selector=f'[data-cy="{raw["dataCy"]}"]',
                strategy="cypress_id",
                confidence=0.98
            ))

        # Strategy 2: ID selector
        if raw.get("id"):
            candidates.append(SelectorCandidate(
                selector=f'#{raw["id"]}',
                strategy="id",
                confidence=0.95
            ))

        # Strategy 3: ARIA label
        if raw.get("ariaLabel"):
            tag = raw.get("tag", "*")
            candidates.append(SelectorCandidate(
                selector=f'{tag}[aria-label="{raw["ariaLabel"]}"]',
                strategy="aria_label",
                confidence=0.90
            ))

        # Strategy 4: Name attribute
        if raw.get("name"):
            tag = raw.get("tag", "*")
            candidates.append(SelectorCandidate(
                selector=f'{tag}[name="{raw["name"]}"]',
                strategy="name",
                confidence=0.85
            ))

        # Strategy 5: Role + accessible name
        if raw.get("role"):
            role = raw["role"]
            name = raw.get("ariaLabel") or raw.get("innerText", "").strip()[:30]
            if name:
                candidates.append(SelectorCandidate(
                    selector=f'[role="{role}"][aria-label="{name}"]',
                    strategy="role_name",
                    confidence=0.82
                ))
            candidates.append(SelectorCandidate(
                selector=f'[role="{role}"]',
                strategy="role",
                confidence=0.60,
                is_unique=False
            ))

        # Strategy 6: Placeholder
        if raw.get("placeholder"):
            candidates.append(SelectorCandidate(
                selector=f'[placeholder="{raw["placeholder"]}"]',
                strategy="placeholder",
                confidence=0.80
            ))

        # Strategy 7: Label association
        if raw.get("labelText") and raw.get("tag") == "input":
            candidates.append(SelectorCandidate(
                selector=f'label:has-text("{raw["labelText"]}") >> input',
                strategy="label_text",
                confidence=0.78
            ))

        # Strategy 8: Text content (for buttons/links)
        text = (raw.get("innerText") or "").strip()
        if text and len(text) < 50:
            tag = raw.get("tag", "")
            if tag in ["button", "a"]:
                candidates.append(SelectorCandidate(
                    selector=f'{tag}:has-text("{text}")',
                    strategy="text_content",
                    confidence=0.75
                ))
            else:
                candidates.append(SelectorCandidate(
                    selector=f'text="{text}"',
                    strategy="text_exact",
                    confidence=0.70
                ))

        # Strategy 9: Type + class combination
        tag = raw.get("tag", "")
        input_type = raw.get("type")
        class_name = raw.get("className", "")

        if tag == "input" and input_type:
            # Get first meaningful class
            classes = class_name.split() if class_name else []
            meaningful_class = next(
                (c for c in classes if not c.startswith(('ng-', 'v-', 'css-'))),
                None
            )

            if meaningful_class:
                candidates.append(SelectorCandidate(
                    selector=f'input[type="{input_type}"].{meaningful_class}',
                    strategy="type_class",
                    confidence=0.65
                ))
            else:
                candidates.append(SelectorCandidate(
                    selector=f'input[type="{input_type}"]',
                    strategy="type_only",
                    confidence=0.40,
                    is_unique=False
                ))

        # Strategy 10: XPath-like structural selector
        if include_structural:
            path = raw.get("path", "")
            if path:
                candidates.append(SelectorCandidate(
                    selector=path,
                    strategy="structural_path",
                    confidence=0.50,
                    is_unique=True
                ))

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        return candidates

    def find_healing_selector(
        self,
        original: Dict[str, Any],
        current_elements: List[Dict[str, Any]]
    ) -> Optional[Tuple[str, float]]:
        """
        Attempt to find a healed selector when original fails.

        Args:
            original: Original element data
            current_elements: Current page elements

        Returns:
            Tuple of (new_selector, confidence) or None
        """
        # Extract identifying characteristics
        original_label = (
            original.get("labelText") or
            original.get("ariaLabel") or
            original.get("placeholder") or
            original.get("innerText", "").strip()[:30]
        )
        original_type = original.get("type")
        original_tag = original.get("tag")
        original_name = original.get("name")

        best_match = None
        best_score = 0.0

        for element in current_elements:
            score = 0.0

            # Label matching (highest weight)
            el_label = (
                element.get("labelText") or
                element.get("ariaLabel") or
                element.get("placeholder") or
                element.get("innerText", "").strip()[:30]
            )

            if original_label and el_label:
                if original_label.lower() == el_label.lower():
                    score += 0.5
                elif original_label.lower() in el_label.lower():
                    score += 0.3

            # Type matching
            if original_type and element.get("type") == original_type:
                score += 0.2

            # Tag matching
            if original_tag and element.get("tag") == original_tag:
                score += 0.15

            # Name matching
            if original_name and element.get("name"):
                if original_name == element.get("name"):
                    score += 0.3
                elif original_name.lower() in element.get("name", "").lower():
                    score += 0.15

            if score > best_score:
                best_score = score
                best_match = element

        # Only return if confidence is reasonable
        if best_match and best_score >= 0.5:
            selectors = self.generate_selectors(best_match)
            if selectors:
                return (selectors[0].selector, best_score)

        return None

    def get_selector_strategy_name(self, selector: str) -> str:
        """Get human-readable strategy name for a selector."""
        if selector.startswith('[data-testid='):
            return "Test ID"
        if selector.startswith('[data-cy='):
            return "Cypress ID"
        if selector.startswith('#'):
            return "ID"
        if '[aria-label=' in selector:
            return "ARIA Label"
        if '[name=' in selector:
            return "Name Attribute"
        if '[role=' in selector:
            return "Role"
        if '[placeholder=' in selector:
            return "Placeholder"
        if ':has-text(' in selector:
            return "Text Content"
        if selector.startswith('text='):
            return "Exact Text"
        if 'label:has-text' in selector:
            return "Label Association"

        return "Structural"
