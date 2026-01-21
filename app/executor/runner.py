"""
Autonomous Test Runner

Main orchestrator for AI-driven test execution.
Coordinates parsing, interpretation, execution, and reporting.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

from app.executor.parser import GherkinParser, Feature, Scenario, Step
from app.executor.browser import BrowserAutomation
from app.executor.interpreter import StepInterpreter
from app.executor.reporter import (
    TestReporter,
    TestRunResult,
    FeatureResult,
    ScenarioResult,
    StepResult
)
from app.executor.soft_assertions import SoftAssertionCollector
from app.executor.step_logger import StepLogger


class AutonomousTestRunner:
    """
    AI-driven autonomous test runner.

    Executes Gherkin feature files without manual step definitions.
    Uses AI to interpret steps and determine browser actions.
    """

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 100,
        output_dir: str = "reports",
        stop_on_failure: bool = False,
        use_soft_assertions: bool = True,
        enable_auto_healing: bool = True,
        enable_detailed_logging: bool = True,
        emit_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Initialize the test runner.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down actions by this many milliseconds
            output_dir: Directory for reports and screenshots
            stop_on_failure: Stop execution on first failure
            use_soft_assertions: Continue execution on failures (collect all failures)
            enable_auto_healing: Enable UI Brain auto-healing for selectors
            enable_detailed_logging: Enable detailed step-by-step logging
            emit_callback: Optional callback for emitting SSE events
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.output_dir = output_dir
        self.stop_on_failure = stop_on_failure
        self.use_soft_assertions = use_soft_assertions
        self.enable_auto_healing = enable_auto_healing
        self.enable_detailed_logging = enable_detailed_logging
        self.parser = GherkinParser()
        self.reporter = TestReporter(output_dir)
        self._browser: Optional[BrowserAutomation] = None
        self._interpreter: Optional[StepInterpreter] = None

        # Soft assertions collector (shared across scenarios)
        self._soft_assertions = SoftAssertionCollector()

        # Step logger for detailed logging (with optional SSE emit callback)
        self._step_logger = StepLogger(
            log_dir=f"{output_dir}/logs",
            emit_callback=emit_callback
        )
        self._step_logger.set_verbose(enable_detailed_logging)

    def run_feature_file(self, file_path: str) -> TestRunResult:
        """
        Run all scenarios in a feature file.

        Args:
            file_path: Path to the .feature file

        Returns:
            TestRunResult with execution details
        """
        return self.run_feature_files([file_path])

    def run_feature_files(self, file_paths: List[str]) -> TestRunResult:
        """
        Run multiple feature files.

        Args:
            file_paths: List of paths to .feature files

        Returns:
            TestRunResult with execution details
        """
        start_time = datetime.now()

        result = TestRunResult(
            start_time=start_time.isoformat(),
            end_time="",
            duration_ms=0
        )

        try:
            # Start browser
            self._start_browser()

            # Run each feature file
            for file_path in file_paths:
                feature_result = self._run_feature(file_path)
                result.features.append(feature_result)

        finally:
            # Stop browser
            self._stop_browser()

        # Calculate totals
        end_time = datetime.now()
        result.end_time = end_time.isoformat()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        result.total_features = len(result.features)
        for feature in result.features:
            result.total_scenarios += len(feature.scenarios)
            for scenario in feature.scenarios:
                result.total_steps += len(scenario.steps)
                if scenario.status == "passed":
                    result.passed_scenarios += 1
                elif scenario.status == "failed":
                    result.failed_scenarios += 1
                else:
                    result.skipped_scenarios += 1

        # Export detailed logs if enabled
        if self.enable_detailed_logging:
            log_path = self._step_logger.export_all_logs("test_run")
            print(f"\nDetailed logs exported to: {log_path}")

            # Get and print healing statistics
            healing_stats = self._step_logger.get_healing_statistics()
            if healing_stats["total_steps_healed"] > 0:
                print(f"\nAuto-healing statistics:")
                print(f"  Steps healed: {healing_stats['total_steps_healed']}")
                print(f"  Success rate: {healing_stats['heal_success_rate']:.1f}%")

        # Generate reports (passing soft assertion data and step logger)
        self.reporter.generate_report(
            result,
            soft_assertions=self._soft_assertions if self.use_soft_assertions else None,
            step_logger=self._step_logger if self.enable_detailed_logging else None
        )

        return result

    def run_scenario(self, feature_path: str, scenario_name: str) -> ScenarioResult:
        """
        Run a specific scenario from a feature file.

        Args:
            feature_path: Path to the .feature file
            scenario_name: Name of the scenario to run

        Returns:
            ScenarioResult with execution details
        """
        feature = self.parser.parse_file(feature_path)

        # Find the scenario
        target_scenario = None
        for scenario in feature.scenarios:
            if scenario.name.lower() == scenario_name.lower():
                target_scenario = scenario
                break

        if not target_scenario:
            raise ValueError(f"Scenario '{scenario_name}' not found in {feature_path}")

        try:
            self._start_browser()
            result = self._run_scenario(target_scenario)
        finally:
            self._stop_browser()

        return result

    def _start_browser(self) -> None:
        """Start browser and interpreter."""
        self._browser = BrowserAutomation(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self._browser.start()
        self._interpreter = StepInterpreter(
            self._browser,
            enable_auto_healing=self.enable_auto_healing,
            step_logger=self._step_logger if self.enable_detailed_logging else None
        )

    def _stop_browser(self) -> None:
        """Stop browser and cleanup."""
        if self._browser:
            self._browser.stop()
            self._browser = None
            self._interpreter = None

    def _run_feature(self, file_path: str) -> FeatureResult:
        """Run all scenarios in a feature."""
        print(f"\nRunning feature: {file_path}")
        print("-" * 50)

        feature = self.parser.parse_file(file_path)

        result = FeatureResult(
            name=feature.name,
            file_path=file_path,
            status="passed",
            tags=feature.tags
        )

        start_time = time.time()
        abort = False

        for scenario in feature.scenarios:
            if abort:
                # Skip remaining scenarios
                scenario_result = ScenarioResult(
                    name=scenario.name,
                    status="skipped",
                    tags=scenario.tags
                )
                result.scenarios.append(scenario_result)
                continue

            scenario_result = self._run_scenario(scenario, feature_name=feature.name)
            result.scenarios.append(scenario_result)

            if scenario_result.status == "failed":
                result.status = "failed"
                if self.stop_on_failure:
                    abort = True

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _run_scenario(self, scenario: Scenario, feature_name: str = "") -> ScenarioResult:
        """Run a single scenario."""
        print(f"\n  Scenario: {scenario.name}")

        result = ScenarioResult(
            name=scenario.name,
            status="passed",
            tags=scenario.tags
        )

        # Reset browser context for clean state (new session, no cookies)
        if self._browser and self._browser._context:
            try:
                self._browser._page.close()
                self._browser._context.close()
                self._browser._context = self._browser._browser.new_context(
                    viewport={"width": 1366, "height": 768}
                )
                self._browser._page = self._browser._context.new_page()
                self._browser._page.set_default_timeout(30000)
            except Exception:
                pass

        # Reset interpreter history for new scenario
        if self._interpreter:
            self._interpreter.reset_history()

        # Initialize soft assertions for this scenario
        self._soft_assertions.clear_for_scenario()
        self._soft_assertions.set_context(feature_name=feature_name, scenario_name=scenario.name)

        # Start step logging for this scenario
        if self.enable_detailed_logging:
            self._step_logger.start_scenario(scenario.name, feature_name)

        start_time = time.time()
        skip_remaining = False
        has_failures = False

        for step in scenario.steps:
            # Determine if we should skip
            should_skip = skip_remaining and not self.use_soft_assertions

            if should_skip:
                step_result = StepResult(
                    step_text=step.text,
                    keyword=step.keyword,
                    status="skipped"
                )
                result.steps.append(step_result)
                continue

            step_result = self._run_step(step)
            result.steps.append(step_result)

            if step_result.status == "failed":
                has_failures = True
                if not self.use_soft_assertions:
                    # Hard assertion mode: stop on first failure
                    result.status = "failed"
                    skip_remaining = True
                else:
                    # Soft assertion mode: record failure but continue
                    self._soft_assertions.assert_soft(
                        condition=False,
                        message=step_result.error or "Step failed",
                        step_info={
                            "step_text": f"{step.keyword} {step.text}",
                            "selector": step_result.action.get("selector") if step_result.action else None,
                            "screenshot": None
                        },
                        assertion_type="step_execution"
                    )

        # Determine final scenario status
        if has_failures:
            result.status = "failed"

        result.duration_ms = (time.time() - start_time) * 1000

        # End step logging
        if self.enable_detailed_logging:
            scenario_log = self._step_logger.end_scenario()
            # Export individual scenario log
            self._step_logger.export_scenario_log(scenario.name)

        # Print soft assertion summary if there were failures
        if self.use_soft_assertions and self._soft_assertions.has_failures():
            print(self._soft_assertions.format_report())

        return result

    def _run_step(self, step: Step, max_retries: int = 2) -> StepResult:
        """Execute a single step with retry logic and detailed logging."""
        full_step = f"{step.keyword} {step.text}"

        last_error = None
        last_result = None
        total_duration_ms = 0

        for attempt in range(max_retries + 1):
            if attempt == 0:
                print(f"    {full_step}", end=" ")
            else:
                print(f"    [Retry {attempt}/{max_retries}] {full_step}", end=" ")

            start_time = time.time()

            try:
                if not self._interpreter:
                    raise RuntimeError("Interpreter not initialized")

                # Log step start
                if self.enable_detailed_logging:
                    self._step_logger.log_step_start(full_step, {})

                execution_result = self._interpreter.execute_step(full_step)
                duration_ms = (time.time() - start_time) * 1000
                total_duration_ms += duration_ms

                # Log step action details
                if self.enable_detailed_logging and execution_result.get("action"):
                    action = execution_result["action"]
                    self._step_logger.log_step_action(
                        action_type=action.get("action", "unknown"),
                        selector=action.get("selector"),
                        value=action.get("value")
                    )

                if execution_result["success"]:
                    print(f"... PASSED ({duration_ms:.0f}ms)")

                    # Log successful result
                    if self.enable_detailed_logging:
                        self._step_logger.log_step_result(
                            success=True,
                            duration_ms=duration_ms
                        )

                    return StepResult(
                        step_text=step.text,
                        keyword=step.keyword,
                        status="passed",
                        duration_ms=total_duration_ms,
                        action=execution_result.get("action")
                    )
                else:
                    last_error = execution_result.get('error')
                    last_result = execution_result
                    print(f"... FAILED")
                    print(f"      Error: {last_error}")

                    # Log DOM state on failure
                    if self.enable_detailed_logging and self._browser:
                        self._step_logger.log_dom_state(self._browser, "on_failure")

                    if attempt < max_retries:
                        print(f"      Retrying...")
                        time.sleep(1)  # Wait 1 second before retry
                        continue

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                total_duration_ms += duration_ms
                last_error = str(e)
                print(f"... ERROR: {last_error}")

                if attempt < max_retries:
                    print(f"      Retrying...")
                    time.sleep(1)
                    continue

        # All retries exhausted - return failure
        print(f"      All {max_retries} retries exhausted")

        # Log final failure
        if self.enable_detailed_logging:
            self._step_logger.log_step_result(
                success=False,
                duration_ms=total_duration_ms,
                error=last_error
            )

        # Save screenshot if available
        screenshot_path = None
        if last_result and last_result.get("screenshot"):
            screenshot_path = self.reporter.save_screenshot(
                last_result["screenshot"],
                f"failed_{step.keyword}_{step.text[:20]}"
            )
            # Update step logger with screenshot path
            if self.enable_detailed_logging:
                self._step_logger.log_step_result(
                    success=False,
                    duration_ms=total_duration_ms,
                    error=last_error,
                    screenshot_path=screenshot_path
                )

        return StepResult(
            step_text=step.text,
            keyword=step.keyword,
            status="failed",
            duration_ms=total_duration_ms,
            action=last_result.get("action") if last_result else None,
            error=last_error,
            screenshot_path=screenshot_path
        )


def run_tests(
    feature_files: List[str],
    headless: bool = True,
    slow_mo: int = 100,
    output_dir: str = "reports",
    stop_on_failure: bool = False,
    use_soft_assertions: bool = True,
    enable_auto_healing: bool = True,
    enable_detailed_logging: bool = True
) -> TestRunResult:
    """
    Convenience function to run tests.

    Args:
        feature_files: List of .feature file paths
        headless: Run browser in headless mode
        slow_mo: Slow down browser actions (ms)
        output_dir: Directory for reports
        stop_on_failure: Stop on first failure
        use_soft_assertions: Continue execution on failures (collect all failures)
        enable_auto_healing: Enable UI Brain auto-healing for selectors
        enable_detailed_logging: Enable detailed step-by-step logging

    Returns:
        TestRunResult with execution details
    """
    runner = AutonomousTestRunner(
        headless=headless,
        slow_mo=slow_mo,
        output_dir=output_dir,
        stop_on_failure=stop_on_failure,
        use_soft_assertions=use_soft_assertions,
        enable_auto_healing=enable_auto_healing,
        enable_detailed_logging=enable_detailed_logging
    )
    return runner.run_feature_files(feature_files)
