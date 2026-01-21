"""
Test Execution Reporter

Generates detailed test execution reports in multiple formats.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.executor.soft_assertions import SoftAssertionCollector
    from app.executor.step_logger import StepLogger


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_text: str
    keyword: str
    status: str  # passed, failed, skipped
    duration_ms: float = 0
    action: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


@dataclass
class ScenarioResult:
    """Result of a scenario execution."""
    name: str
    status: str  # passed, failed, skipped
    steps: List[StepResult] = field(default_factory=list)
    duration_ms: float = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class FeatureResult:
    """Result of a feature execution."""
    name: str
    file_path: str
    status: str  # passed, failed, skipped
    scenarios: List[ScenarioResult] = field(default_factory=list)
    duration_ms: float = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class TestRunResult:
    """Complete test run result."""
    start_time: str
    end_time: str
    duration_ms: float
    total_features: int = 0
    total_scenarios: int = 0
    total_steps: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    skipped_scenarios: int = 0
    features: List[FeatureResult] = field(default_factory=list)


class TestReporter:
    """
    Generates test execution reports in various formats.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir = self.output_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

    def generate_report(
        self,
        result: TestRunResult,
        report_name: str = "test_report",
        soft_assertions: Optional["SoftAssertionCollector"] = None,
        step_logger: Optional["StepLogger"] = None
    ) -> Dict[str, str]:
        """
        Generate reports in multiple formats.

        Args:
            result: Test run result data
            report_name: Base name for report files
            soft_assertions: Optional soft assertion collector for failure details
            step_logger: Optional step logger for detailed logs

        Returns:
            Dict of format -> file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{report_name}_{timestamp}"

        reports = {}

        # JSON report (with soft assertions and healing stats)
        json_path = self.output_dir / f"{base_name}.json"
        self._write_json_report(result, json_path, soft_assertions, step_logger)
        reports["json"] = str(json_path)

        # HTML report (with soft assertions and healing stats)
        html_path = self.output_dir / f"{base_name}.html"
        self._write_html_report(result, html_path, soft_assertions, step_logger)
        reports["html"] = str(html_path)

        # Console summary (with soft assertion info)
        self._print_console_summary(result, soft_assertions, step_logger)

        return reports

    def save_screenshot(self, screenshot_base64: str, name: str) -> str:
        """Save a base64 screenshot and return the file path."""
        import base64
        import re
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        # Sanitize filename - remove special characters
        safe_name = re.sub(r'[<>:"/\\|?*@]', '_', name)[:30]
        filename = f"{safe_name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename

        image_data = base64.b64decode(screenshot_base64)
        filepath.write_bytes(image_data)

        return str(filepath)

    def _write_json_report(
        self,
        result: TestRunResult,
        path: Path,
        soft_assertions: Optional["SoftAssertionCollector"] = None,
        step_logger: Optional["StepLogger"] = None
    ) -> None:
        """Write JSON report with soft assertions and healing stats."""
        # Convert to dict, handling nested dataclasses
        def to_dict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: to_dict(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [to_dict(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            return obj

        report_dict = to_dict(result)

        # Add soft assertion summary if available
        if soft_assertions:
            report_dict["soft_assertions"] = soft_assertions.get_summary()

        # Add healing statistics if available
        if step_logger:
            report_dict["healing_statistics"] = step_logger.get_healing_statistics()

        path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")

    def _write_html_report(
        self,
        result: TestRunResult,
        path: Path,
        soft_assertions: Optional["SoftAssertionCollector"] = None,
        step_logger: Optional["StepLogger"] = None
    ) -> None:
        """Write HTML report with soft assertions and healing stats."""
        html = self._generate_html(result, soft_assertions, step_logger)
        path.write_text(html, encoding="utf-8")

    def _generate_html(
        self,
        result: TestRunResult,
        soft_assertions: Optional["SoftAssertionCollector"] = None,
        step_logger: Optional["StepLogger"] = None
    ) -> str:
        """Generate HTML report content."""
        pass_rate = (result.passed_scenarios / result.total_scenarios * 100) if result.total_scenarios > 0 else 0

        scenarios_html = ""
        for feature in result.features:
            scenarios_html += f'<div class="feature"><h2>{self._escape_html(feature.name)}</h2>'

            for scenario in feature.scenarios:
                status_class = scenario.status
                scenarios_html += f'''
                <div class="scenario {status_class}">
                    <h3>{self._escape_html(scenario.name)} - <span class="status">{scenario.status.upper()}</span></h3>
                    <div class="steps">
                '''

                for step in scenario.steps:
                    step_class = step.status
                    error_html = ""
                    if step.error:
                        error_html = f'<div class="error">{self._escape_html(step.error)}</div>'

                    screenshot_html = ""
                    if step.screenshot_path:
                        screenshot_html = f'<div class="screenshot"><a href="{step.screenshot_path}" target="_blank">View Screenshot</a></div>'

                    scenarios_html += f'''
                    <div class="step {step_class}">
                        <span class="keyword">{step.keyword}</span> {self._escape_html(step.step_text)}
                        <span class="duration">({step.duration_ms:.0f}ms)</span>
                        {error_html}
                        {screenshot_html}
                    </div>
                    '''

                scenarios_html += '</div></div>'
            scenarios_html += '</div>'

        # Generate soft assertion failures section
        soft_assertions_html = ""
        if soft_assertions and soft_assertions.has_failures():
            failures_html = ""
            for failure in soft_assertions.failures:
                failures_html += f'''
                <div class="assertion-failure">
                    <div class="assertion-type">{self._escape_html(failure.assertion_type.upper())}</div>
                    <div class="assertion-step">Step: {self._escape_html(failure.step_text)}</div>
                    <div class="assertion-message">{self._escape_html(failure.message)}</div>
                    <div class="assertion-details">
                        Expected: {self._escape_html(str(failure.expected))} |
                        Actual: {self._escape_html(str(failure.actual))}
                    </div>
                </div>
                '''

            soft_assertions_html = f'''
            <div class="soft-assertions">
                <h2>Soft Assertion Failures ({soft_assertions.get_failure_count()})</h2>
                {failures_html}
            </div>
            '''

        # Generate healing statistics section
        healing_html = ""
        if step_logger:
            healing_stats = step_logger.get_healing_statistics()
            if healing_stats["total_steps_healed"] > 0:
                methods_html = ""
                for method, count in healing_stats.get("methods_used", {}).items():
                    methods_html += f'<span class="heal-method">{method}: {count}</span> '

                healing_html = f'''
                <div class="healing-stats">
                    <h2>Auto-Healing Statistics</h2>
                    <div class="healing-grid">
                        <div class="heal-item">
                            <div class="heal-number">{healing_stats["total_steps_healed"]}</div>
                            <div class="heal-label">Steps Healed</div>
                        </div>
                        <div class="heal-item">
                            <div class="heal-number">{healing_stats["heal_success_rate"]:.1f}%</div>
                            <div class="heal-label">Success Rate</div>
                        </div>
                    </div>
                    <div class="heal-methods">
                        <strong>Methods used:</strong> {methods_html}
                    </div>
                </div>
                '''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ghost QC Test Report</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .summary-item {{ text-align: center; padding: 15px; border-radius: 6px; }}
        .summary-item.passed {{ background: #d4edda; }}
        .summary-item.failed {{ background: #f8d7da; }}
        .summary-item.total {{ background: #e2e3e5; }}
        .summary-item .number {{ font-size: 2em; font-weight: bold; }}
        .summary-item .label {{ font-size: 0.9em; color: #666; }}
        .feature {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .feature h2 {{ color: #333; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .scenario {{ padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid #ccc; }}
        .scenario.passed {{ border-left-color: #28a745; background: #f8fff9; }}
        .scenario.failed {{ border-left-color: #dc3545; background: #fff8f8; }}
        .scenario.skipped {{ border-left-color: #ffc107; background: #fffef8; }}
        .scenario h3 {{ font-size: 1.1em; margin-bottom: 10px; }}
        .status {{ font-size: 0.8em; padding: 2px 8px; border-radius: 4px; }}
        .passed .status {{ background: #28a745; color: white; }}
        .failed .status {{ background: #dc3545; color: white; }}
        .skipped .status {{ background: #ffc107; color: #333; }}
        .steps {{ margin-left: 20px; }}
        .step {{ padding: 8px 12px; margin: 5px 0; border-radius: 4px; font-family: monospace; }}
        .step.passed {{ background: #e8f5e9; }}
        .step.failed {{ background: #ffebee; }}
        .step.skipped {{ background: #fff8e1; }}
        .keyword {{ font-weight: bold; color: #5c6bc0; }}
        .duration {{ color: #999; font-size: 0.85em; }}
        .error {{ color: #dc3545; margin-top: 5px; padding: 8px; background: #fff; border-radius: 4px; font-size: 0.9em; }}
        .screenshot {{ margin-top: 5px; }}
        .screenshot a {{ color: #007bff; }}
        .progress-bar {{ height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 10px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s; }}

        /* Soft Assertions Styles */
        .soft-assertions {{ background: #fff3cd; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ffc107; }}
        .soft-assertions h2 {{ color: #856404; margin-bottom: 15px; }}
        .assertion-failure {{ background: white; padding: 12px; margin: 10px 0; border-radius: 6px; border-left: 3px solid #dc3545; }}
        .assertion-type {{ font-weight: bold; color: #dc3545; font-size: 0.9em; }}
        .assertion-step {{ margin-top: 5px; color: #333; }}
        .assertion-message {{ margin-top: 5px; color: #666; }}
        .assertion-details {{ margin-top: 5px; font-size: 0.85em; color: #888; }}

        /* Healing Stats Styles */
        .healing-stats {{ background: #d4edda; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745; }}
        .healing-stats h2 {{ color: #155724; margin-bottom: 15px; }}
        .healing-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 15px; }}
        .heal-item {{ text-align: center; background: white; padding: 15px; border-radius: 6px; }}
        .heal-number {{ font-size: 1.5em; font-weight: bold; color: #155724; }}
        .heal-label {{ font-size: 0.85em; color: #666; }}
        .heal-methods {{ margin-top: 10px; }}
        .heal-method {{ display: inline-block; background: white; padding: 4px 10px; border-radius: 15px; margin: 2px; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Ghost QC - Test Execution Report</h1>

        <div class="summary">
            <div class="summary-grid">
                <div class="summary-item total">
                    <div class="number">{result.total_scenarios}</div>
                    <div class="label">Total Scenarios</div>
                </div>
                <div class="summary-item passed">
                    <div class="number">{result.passed_scenarios}</div>
                    <div class="label">Passed</div>
                </div>
                <div class="summary-item failed">
                    <div class="number">{result.failed_scenarios}</div>
                    <div class="label">Failed</div>
                </div>
                <div class="summary-item total">
                    <div class="number">{pass_rate:.1f}%</div>
                    <div class="label">Pass Rate</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {pass_rate}%"></div>
            </div>
            <p style="margin-top: 15px; color: #666;">
                Duration: {result.duration_ms/1000:.2f}s |
                Started: {result.start_time} |
                Ended: {result.end_time}
            </p>
        </div>

        {healing_html}

        {soft_assertions_html}

        {scenarios_html}
    </div>
</body>
</html>'''

        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def _print_console_summary(
        self,
        result: TestRunResult,
        soft_assertions: Optional["SoftAssertionCollector"] = None,
        step_logger: Optional["StepLogger"] = None
    ) -> None:
        """Print summary to console with soft assertion and healing info."""
        print("\n" + "=" * 60)
        print("GHOST QC - TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Duration: {result.duration_ms/1000:.2f} seconds")
        print(f"Features: {result.total_features}")
        print(f"Scenarios: {result.total_scenarios}")
        print(f"  Passed: {result.passed_scenarios}")
        print(f"  Failed: {result.failed_scenarios}")
        print(f"  Skipped: {result.skipped_scenarios}")

        if result.total_scenarios > 0:
            pass_rate = result.passed_scenarios / result.total_scenarios * 100
            print(f"Pass Rate: {pass_rate:.1f}%")

        # Print healing statistics if available
        if step_logger:
            healing_stats = step_logger.get_healing_statistics()
            if healing_stats["total_steps_healed"] > 0:
                print("\n" + "-" * 40)
                print("AUTO-HEALING STATISTICS:")
                print(f"  Steps healed: {healing_stats['total_steps_healed']}")
                print(f"  Success rate: {healing_stats['heal_success_rate']:.1f}%")
                if healing_stats.get("methods_used"):
                    methods = ", ".join(f"{k}: {v}" for k, v in healing_stats["methods_used"].items())
                    print(f"  Methods: {methods}")

        # Print soft assertion summary if available
        if soft_assertions and soft_assertions.has_failures():
            print("\n" + "-" * 40)
            print(f"SOFT ASSERTION FAILURES: {soft_assertions.get_failure_count()}")
            for failure in soft_assertions.failures[:5]:  # Show first 5
                print(f"  - [{failure.assertion_type}] {failure.message}")
            if soft_assertions.get_failure_count() > 5:
                print(f"  ... and {soft_assertions.get_failure_count() - 5} more")

        print("=" * 60)

        # Print failed scenarios
        if result.failed_scenarios > 0:
            print("\nFAILED SCENARIOS:")
            print("-" * 40)
            for feature in result.features:
                for scenario in feature.scenarios:
                    if scenario.status == "failed":
                        print(f"  - {scenario.name}")
                        for step in scenario.steps:
                            if step.status == "failed":
                                print(f"    Step: {step.keyword} {step.step_text}")
                                print(f"    Error: {step.error}")
            print()
