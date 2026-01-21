"""
Soft Assertions Module

Provides soft assertion collection that allows test execution to continue
even when assertions fail, collecting all failures for final reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class SoftAssertionFailure:
    """Represents a single soft assertion failure."""
    step_text: str
    assertion_type: str
    expected: Any
    actual: Any
    message: str
    timestamp: str
    selector: Optional[str] = None
    screenshot: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_text": self.step_text,
            "assertion_type": self.assertion_type,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "timestamp": self.timestamp,
            "selector": self.selector,
            "screenshot": self.screenshot
        }


@dataclass
class SoftWarning:
    """Represents a non-critical warning during test execution."""
    step_text: str
    warning_type: str
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_text": self.step_text,
            "warning_type": self.warning_type,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details
        }


class SoftAssertionCollector:
    """
    Collects assertion failures without stopping test execution.

    Allows tests to continue running even when assertions fail,
    collecting all failures for comprehensive reporting at the end.
    """

    def __init__(self):
        self.failures: List[SoftAssertionFailure] = []
        self.warnings: List[SoftWarning] = []
        self._scenario_name: Optional[str] = None
        self._feature_name: Optional[str] = None

    def set_context(self, feature_name: str = None, scenario_name: str = None) -> None:
        """Set the current test context for better error reporting."""
        if feature_name:
            self._feature_name = feature_name
        if scenario_name:
            self._scenario_name = scenario_name

    def assert_soft(
        self,
        condition: bool,
        message: str,
        step_info: Dict[str, Any],
        expected: Any = None,
        actual: Any = None,
        assertion_type: str = "generic"
    ) -> bool:
        """
        Record assertion result without raising exception on failure.

        Args:
            condition: The assertion condition (True = pass, False = fail)
            message: Description of the assertion
            step_info: Dict containing step details (step_text, selector, screenshot)
            expected: Expected value
            actual: Actual value
            assertion_type: Type of assertion (visible, text, url, exists, etc.)

        Returns:
            The condition value (True if passed, False if failed)
        """
        if not condition:
            failure = SoftAssertionFailure(
                step_text=step_info.get("step_text", "Unknown step"),
                assertion_type=assertion_type,
                expected=expected,
                actual=actual,
                message=message,
                timestamp=datetime.now().isoformat(),
                selector=step_info.get("selector"),
                screenshot=step_info.get("screenshot")
            )
            self.failures.append(failure)

        return condition

    def assert_visible(
        self,
        is_visible: bool,
        selector: str,
        step_text: str,
        screenshot: str = None
    ) -> bool:
        """Soft assertion for element visibility."""
        return self.assert_soft(
            condition=is_visible,
            message=f"Element not visible: {selector}",
            step_info={"step_text": step_text, "selector": selector, "screenshot": screenshot},
            expected="visible",
            actual="not visible" if not is_visible else "visible",
            assertion_type="visible"
        )

    def assert_text_contains(
        self,
        actual_text: str,
        expected_text: str,
        selector: str,
        step_text: str,
        screenshot: str = None
    ) -> bool:
        """Soft assertion for text content."""
        condition = expected_text.lower() in (actual_text or "").lower()
        return self.assert_soft(
            condition=condition,
            message=f"Text mismatch. Expected '{expected_text}' in '{actual_text}'",
            step_info={"step_text": step_text, "selector": selector, "screenshot": screenshot},
            expected=expected_text,
            actual=actual_text,
            assertion_type="text"
        )

    def assert_url_contains(
        self,
        actual_url: str,
        expected_pattern: str,
        step_text: str,
        screenshot: str = None
    ) -> bool:
        """Soft assertion for URL pattern."""
        condition = expected_pattern.lower() in actual_url.lower()
        return self.assert_soft(
            condition=condition,
            message=f"URL mismatch. Expected '{expected_pattern}' in '{actual_url}'",
            step_info={"step_text": step_text, "screenshot": screenshot},
            expected=expected_pattern,
            actual=actual_url,
            assertion_type="url"
        )

    def assert_exists(
        self,
        element_count: int,
        selector: str,
        step_text: str,
        screenshot: str = None
    ) -> bool:
        """Soft assertion for element existence."""
        condition = element_count > 0
        return self.assert_soft(
            condition=condition,
            message=f"Element not found: {selector}",
            step_info={"step_text": step_text, "selector": selector, "screenshot": screenshot},
            expected="exists",
            actual=f"found {element_count} elements",
            assertion_type="exists"
        )

    def add_warning(
        self,
        step_text: str,
        warning_type: str,
        message: str,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Add a non-critical warning.

        Args:
            step_text: The step that generated the warning
            warning_type: Type of warning (timing, selector, recovery, etc.)
            message: Warning message
            details: Additional warning details
        """
        warning = SoftWarning(
            step_text=step_text,
            warning_type=warning_type,
            message=message,
            timestamp=datetime.now().isoformat(),
            details=details
        )
        self.warnings.append(warning)

    def has_failures(self) -> bool:
        """Check if any soft assertions failed."""
        return len(self.failures) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_failure_count(self) -> int:
        """Get the number of failed assertions."""
        return len(self.failures)

    def get_warning_count(self) -> int:
        """Get the number of warnings."""
        return len(self.warnings)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of all failures and warnings.

        Returns:
            Dict with failure and warning details
        """
        return {
            "feature": self._feature_name,
            "scenario": self._scenario_name,
            "total_failures": len(self.failures),
            "total_warnings": len(self.warnings),
            "failures": [f.to_dict() for f in self.failures],
            "warnings": [w.to_dict() for w in self.warnings],
            "has_failures": self.has_failures()
        }

    def get_failures_by_type(self) -> Dict[str, List[SoftAssertionFailure]]:
        """Group failures by assertion type."""
        by_type: Dict[str, List[SoftAssertionFailure]] = {}
        for failure in self.failures:
            if failure.assertion_type not in by_type:
                by_type[failure.assertion_type] = []
            by_type[failure.assertion_type].append(failure)
        return by_type

    def get_failure_messages(self) -> List[str]:
        """Get list of all failure messages."""
        return [f.message for f in self.failures]

    def clear(self) -> None:
        """Clear all collected failures and warnings."""
        self.failures.clear()
        self.warnings.clear()

    def clear_for_scenario(self) -> None:
        """Clear failures and warnings for a new scenario."""
        # Keep feature context but clear scenario-specific data
        self.failures.clear()
        self.warnings.clear()
        self._scenario_name = None

    def merge_from(self, other: "SoftAssertionCollector") -> None:
        """Merge failures and warnings from another collector."""
        self.failures.extend(other.failures)
        self.warnings.extend(other.warnings)

    def __str__(self) -> str:
        """String representation for logging."""
        if not self.has_failures() and not self.has_warnings():
            return "No soft assertion failures or warnings"

        parts = []
        if self.has_failures():
            parts.append(f"{len(self.failures)} assertion failure(s)")
        if self.has_warnings():
            parts.append(f"{len(self.warnings)} warning(s)")

        return ", ".join(parts)

    def format_report(self) -> str:
        """Format failures and warnings for console output."""
        lines = []

        if self.has_failures():
            lines.append("\n=== SOFT ASSERTION FAILURES ===")
            for i, failure in enumerate(self.failures, 1):
                lines.append(f"\n[{i}] {failure.assertion_type.upper()}")
                lines.append(f"    Step: {failure.step_text}")
                lines.append(f"    Message: {failure.message}")
                if failure.expected:
                    lines.append(f"    Expected: {failure.expected}")
                if failure.actual:
                    lines.append(f"    Actual: {failure.actual}")
                if failure.selector:
                    lines.append(f"    Selector: {failure.selector}")

        if self.has_warnings():
            lines.append("\n=== WARNINGS ===")
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"\n[{i}] {warning.warning_type.upper()}")
                lines.append(f"    Step: {warning.step_text}")
                lines.append(f"    Message: {warning.message}")

        return "\n".join(lines) if lines else "No issues found"
