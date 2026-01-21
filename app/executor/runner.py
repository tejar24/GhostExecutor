"""
Autonomous Test Runner

Main orchestrator for AI-driven test execution.
Coordinates parsing, interpretation, execution, and reporting.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

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
        stop_on_failure: bool = False
    ):
        """
        Initialize the test runner.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down actions by this many milliseconds
            output_dir: Directory for reports and screenshots
            stop_on_failure: Stop execution on first failure
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.output_dir = output_dir
        self.stop_on_failure = stop_on_failure
        self.parser = GherkinParser()
        self.reporter = TestReporter(output_dir)
        self._browser: Optional[BrowserAutomation] = None
        self._interpreter: Optional[StepInterpreter] = None

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

        # Generate reports
        self.reporter.generate_report(result)

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
        self._interpreter = StepInterpreter(self._browser)

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

            scenario_result = self._run_scenario(scenario)
            result.scenarios.append(scenario_result)

            if scenario_result.status == "failed":
                result.status = "failed"
                if self.stop_on_failure:
                    abort = True

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _run_scenario(self, scenario: Scenario) -> ScenarioResult:
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

        start_time = time.time()
        skip_remaining = False

        for step in scenario.steps:
            if skip_remaining:
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
                result.status = "failed"
                skip_remaining = True

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _run_step(self, step: Step, max_retries: int = 2) -> StepResult:
        """Execute a single step with retry logic."""
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

                execution_result = self._interpreter.execute_step(full_step)
                duration_ms = (time.time() - start_time) * 1000
                total_duration_ms += duration_ms

                if execution_result["success"]:
                    print(f"... PASSED ({duration_ms:.0f}ms)")
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

        # Save screenshot if available
        screenshot_path = None
        if last_result and last_result.get("screenshot"):
            screenshot_path = self.reporter.save_screenshot(
                last_result["screenshot"],
                f"failed_{step.keyword}_{step.text[:20]}"
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
    stop_on_failure: bool = False
) -> TestRunResult:
    """
    Convenience function to run tests.

    Args:
        feature_files: List of .feature file paths
        headless: Run browser in headless mode
        slow_mo: Slow down browser actions (ms)
        output_dir: Directory for reports
        stop_on_failure: Stop on first failure

    Returns:
        TestRunResult with execution details
    """
    runner = AutonomousTestRunner(
        headless=headless,
        slow_mo=slow_mo,
        output_dir=output_dir,
        stop_on_failure=stop_on_failure
    )
    return runner.run_feature_files(feature_files)
