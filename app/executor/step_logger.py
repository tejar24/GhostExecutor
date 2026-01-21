"""
Step Logger Module

Provides detailed logging for each test step execution,
capturing actions, timing, DOM state, and healing attempts.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


@dataclass
class StepLogEntry:
    """Detailed log entry for a single step execution."""
    timestamp: str
    step_text: str
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    duration_ms: float = 0
    success: bool = False
    error: Optional[str] = None
    healing_attempts: List[Dict[str, Any]] = field(default_factory=list)
    dom_state: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioLog:
    """Complete log for a scenario execution."""
    scenario_name: str
    feature_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    healed_steps: int = 0
    steps: List[StepLogEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "feature_name": self.feature_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "total_steps": self.total_steps,
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "healed_steps": self.healed_steps,
            "steps": [s.to_dict() for s in self.steps]
        }


class StepLogger:
    """
    Detailed logging for each test step.

    Captures comprehensive information about step execution including
    timing, DOM state, healing attempts, and error details.
    """

    def __init__(
        self,
        log_dir: str = "reports/logs",
        emit_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_scenario_log: Optional[ScenarioLog] = None
        self._current_step: Optional[Dict[str, Any]] = None
        self._all_scenario_logs: List[ScenarioLog] = []
        self._verbose = True
        self._emit_callback = emit_callback

    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable verbose console output."""
        self._verbose = verbose

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event via the callback if set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception:
                pass  # Don't let emit failures break test execution

    def start_scenario(self, scenario_name: str, feature_name: str) -> None:
        """
        Start logging for a new scenario.

        Args:
            scenario_name: Name of the scenario
            feature_name: Name of the feature
        """
        self._current_scenario_log = ScenarioLog(
            scenario_name=scenario_name,
            feature_name=feature_name,
            start_time=datetime.now().isoformat()
        )

        if self._verbose:
            print(f"\n[LOG] Starting scenario: {scenario_name}")

        # Emit scenario start event
        self._emit("scenario_start", {
            "scenario_name": scenario_name,
            "feature_name": feature_name,
            "timestamp": self._current_scenario_log.start_time
        })

    def end_scenario(self) -> ScenarioLog:
        """
        End logging for current scenario.

        Returns:
            The completed ScenarioLog
        """
        if self._current_scenario_log:
            self._current_scenario_log.end_time = datetime.now().isoformat()
            self._current_scenario_log.total_steps = len(self._current_scenario_log.steps)
            self._current_scenario_log.passed_steps = sum(
                1 for s in self._current_scenario_log.steps if s.success
            )
            self._current_scenario_log.failed_steps = sum(
                1 for s in self._current_scenario_log.steps if not s.success
            )
            self._current_scenario_log.healed_steps = sum(
                1 for s in self._current_scenario_log.steps if s.healing_attempts
            )

            # Calculate duration
            start = datetime.fromisoformat(self._current_scenario_log.start_time)
            end = datetime.fromisoformat(self._current_scenario_log.end_time)
            self._current_scenario_log.duration_ms = (end - start).total_seconds() * 1000

            self._all_scenario_logs.append(self._current_scenario_log)

            if self._verbose:
                self._print_scenario_summary()

            # Emit scenario end event
            self._emit("scenario_end", {
                "scenario_name": self._current_scenario_log.scenario_name,
                "feature_name": self._current_scenario_log.feature_name,
                "duration_ms": self._current_scenario_log.duration_ms,
                "total_steps": self._current_scenario_log.total_steps,
                "passed_steps": self._current_scenario_log.passed_steps,
                "failed_steps": self._current_scenario_log.failed_steps,
                "healed_steps": self._current_scenario_log.healed_steps,
                "timestamp": self._current_scenario_log.end_time
            })

            return self._current_scenario_log

        return ScenarioLog(
            scenario_name="Unknown",
            feature_name="Unknown",
            start_time=datetime.now().isoformat()
        )

    def log_step_start(self, step_text: str, action: Dict[str, Any]) -> None:
        """
        Log when a step begins execution.

        Args:
            step_text: The Gherkin step text
            action: The interpreted action dictionary
        """
        self._current_step = {
            "start_time": datetime.now(),
            "step_text": step_text,
            "action": action,
            "healing_attempts": []
        }

        if self._verbose:
            action_type = action.get("action", "unknown") if action else "unknown"
            selector = action.get("selector", "") if action else ""
            print(f"  [STEP] {step_text}")
            print(f"         Action: {action_type}", end="")
            if selector:
                print(f" | Selector: {selector[:50]}...", end="")
            print()

        # Emit step start event
        self._emit("step_start", {
            "step_text": step_text,
            "action_type": action.get("action", "unknown") if action else "unknown",
            "selector": action.get("selector") if action else None,
            "timestamp": self._current_step["start_time"].isoformat()
        })

    def log_step_action(
        self,
        action_type: str,
        selector: str = None,
        value: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log the actual browser action being performed.

        Args:
            action_type: Type of action (click, fill, navigate, etc.)
            selector: Target selector
            value: Value being entered (if applicable)
            details: Additional action details
        """
        if self._current_step:
            self._current_step["action_details"] = {
                "action_type": action_type,
                "selector": selector,
                "value": value,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }

        if self._verbose and value:
            # Mask sensitive values
            display_value = value
            if any(kw in (selector or "").lower() for kw in ["password", "secret", "token"]):
                display_value = "***"
            print(f"         Value: {display_value[:30]}...")

    def log_step_result(
        self,
        success: bool,
        duration_ms: float,
        error: str = None,
        screenshot_path: str = None
    ) -> None:
        """
        Log step completion.

        Args:
            success: Whether step passed
            duration_ms: Step execution time
            error: Error message if failed
            screenshot_path: Path to failure screenshot
        """
        if self._current_step and self._current_scenario_log:
            action = self._current_step.get("action", {}) or {}

            entry = StepLogEntry(
                timestamp=self._current_step["start_time"].isoformat(),
                step_text=self._current_step["step_text"],
                action_type=action.get("action", "unknown"),
                selector=action.get("selector"),
                value=action.get("value"),
                duration_ms=duration_ms,
                success=success,
                error=error,
                healing_attempts=self._current_step.get("healing_attempts", []),
                screenshot_path=screenshot_path
            )

            self._current_scenario_log.steps.append(entry)

            if self._verbose:
                status = "PASS" if success else "FAIL"
                print(f"         Result: {status} ({duration_ms:.0f}ms)")
                if error:
                    print(f"         Error: {error[:100]}...")

            # Emit step result event
            self._emit("step_result", {
                "step_text": entry.step_text,
                "success": success,
                "duration_ms": duration_ms,
                "error": error,
                "action_type": entry.action_type,
                "timestamp": datetime.now().isoformat()
            })

        self._current_step = None

    def log_healing_attempt(
        self,
        original_selector: str,
        tried_selector: str,
        success: bool,
        method: str = "alternative"
    ) -> None:
        """
        Log an auto-healing attempt.

        Args:
            original_selector: The original failing selector
            tried_selector: The alternative selector tried
            success: Whether the alternative worked
            method: Healing method used (alternative, ui_brain, generated)
        """
        attempt = {
            "original": original_selector,
            "tried": tried_selector,
            "success": success,
            "method": method,
            "timestamp": datetime.now().isoformat()
        }

        if self._current_step:
            self._current_step["healing_attempts"].append(attempt)

        if self._verbose:
            status = "SUCCESS" if success else "failed"
            print(f"         [HEAL] {method}: {tried_selector[:40]}... -> {status}")

        # Emit healing event
        self._emit("healing", {
            "original_selector": original_selector,
            "tried_selector": tried_selector,
            "success": success,
            "method": method,
            "timestamp": datetime.now().isoformat()
        })

    def log_dom_state(self, browser, event: str) -> None:
        """
        Capture DOM state at key moments.

        Args:
            browser: BrowserAutomation instance
            event: Event name (before_action, after_action, on_failure)
        """
        if not self._current_step:
            return

        try:
            dom_state = {
                "event": event,
                "timestamp": datetime.now().isoformat(),
                "url": browser.get_current_url(),
                "title": browser.get_title(),
                "ready_state": browser.get_ready_state()
            }

            # Get element count
            script = "() => document.querySelectorAll('input, button, a, select, textarea').length"
            dom_state["interactive_elements"] = browser.execute_script(script) or 0

            self._current_step["dom_state"] = dom_state

            if self._verbose and event == "on_failure":
                print(f"         [DOM] URL: {dom_state['url']}")
                print(f"         [DOM] Elements: {dom_state['interactive_elements']}")

        except Exception:
            pass

    def log_smart_wait(
        self,
        wait_type: str,
        selector: str = None,
        duration_ms: float = 0,
        success: bool = True
    ) -> None:
        """
        Log smart wait operations.

        Args:
            wait_type: Type of wait (dom_stable, element_visible, actionable)
            selector: Target selector if waiting for element
            duration_ms: How long the wait took
            success: Whether wait completed successfully
        """
        if self._verbose:
            status = "done" if success else "timeout"
            target = f" for {selector[:30]}..." if selector else ""
            print(f"         [WAIT] {wait_type}{target} -> {status} ({duration_ms:.0f}ms)")

    def export_scenario_log(self, scenario_name: str = None) -> str:
        """
        Export detailed log for a scenario.

        Args:
            scenario_name: Name of scenario to export (or current if None)

        Returns:
            Path to the exported log file
        """
        log_to_export = None

        if scenario_name:
            for log in self._all_scenario_logs:
                if log.scenario_name == scenario_name:
                    log_to_export = log
                    break
        else:
            log_to_export = self._current_scenario_log

        if not log_to_export:
            return ""

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in log_to_export.scenario_name[:30])
        filename = f"step_log_{safe_name}_{timestamp}.json"
        filepath = self.log_dir / filename

        # Write log
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_to_export.to_dict(), f, indent=2)

        return str(filepath)

    def export_all_logs(self, run_name: str = "test_run") -> str:
        """
        Export all scenario logs to a single file.

        Args:
            run_name: Name for the test run

        Returns:
            Path to the exported log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_log_{run_name}_{timestamp}.json"
        filepath = self.log_dir / filename

        logs_data = {
            "run_name": run_name,
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(self._all_scenario_logs),
            "scenarios": [log.to_dict() for log in self._all_scenario_logs]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(logs_data, f, indent=2)

        return str(filepath)

    def get_current_scenario_log(self) -> Optional[ScenarioLog]:
        """Get the current scenario log."""
        return self._current_scenario_log

    def get_all_scenario_logs(self) -> List[ScenarioLog]:
        """Get all collected scenario logs."""
        return self._all_scenario_logs

    def get_healing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about auto-healing across all scenarios.

        Returns:
            Dict with healing statistics
        """
        total_healed = 0
        total_healing_attempts = 0
        successful_heals = 0
        heal_methods: Dict[str, int] = {}

        for scenario_log in self._all_scenario_logs:
            for step in scenario_log.steps:
                if step.healing_attempts:
                    total_healed += 1
                    for attempt in step.healing_attempts:
                        total_healing_attempts += 1
                        if attempt.get("success"):
                            successful_heals += 1
                        method = attempt.get("method", "unknown")
                        heal_methods[method] = heal_methods.get(method, 0) + 1

        return {
            "total_steps_healed": total_healed,
            "total_healing_attempts": total_healing_attempts,
            "successful_heals": successful_heals,
            "heal_success_rate": (successful_heals / total_healing_attempts * 100)
                if total_healing_attempts > 0 else 0,
            "methods_used": heal_methods
        }

    def clear(self) -> None:
        """Clear all logs."""
        self._all_scenario_logs.clear()
        self._current_scenario_log = None
        self._current_step = None

    def _print_scenario_summary(self) -> None:
        """Print scenario summary to console."""
        if not self._current_scenario_log:
            return

        log = self._current_scenario_log
        print(f"\n[LOG] Scenario complete: {log.scenario_name}")
        print(f"      Duration: {log.duration_ms:.0f}ms")
        print(f"      Steps: {log.passed_steps}/{log.total_steps} passed")
        if log.healed_steps > 0:
            print(f"      Auto-healed: {log.healed_steps} steps")
        if log.failed_steps > 0:
            print(f"      Failed: {log.failed_steps} steps")
