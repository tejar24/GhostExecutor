"""
Storage Data Models

Defines data structures for persisting test results and features.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class StepResult:
    """Result of a single test step execution."""
    step_text: str
    status: TestStatus
    duration_ms: float = 0.0
    action: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_text": self.step_text,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "action": self.action,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepResult":
        """Create from dictionary."""
        return cls(
            step_text=data["step_text"],
            status=TestStatus(data["status"]),
            duration_ms=data.get("duration_ms", 0.0),
            action=data.get("action"),
            error=data.get("error"),
            screenshot_path=data.get("screenshot_path"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data else datetime.now(),
        )


@dataclass
class ScenarioResult:
    """Result of a test scenario execution."""
    scenario_name: str
    status: TestStatus
    steps: List[StepResult] = field(default_factory=list)
    duration_ms: float = 0.0
    tags: List[str] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def passed_steps(self) -> int:
        """Count of passed steps."""
        return sum(1 for s in self.steps if s.status == TestStatus.PASSED)

    @property
    def failed_steps(self) -> int:
        """Count of failed steps."""
        return sum(1 for s in self.steps if s.status == TestStatus.FAILED)

    @property
    def skipped_steps(self) -> int:
        """Count of skipped steps."""
        return sum(1 for s in self.steps if s.status == TestStatus.SKIPPED)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_name": self.scenario_name,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioResult":
        """Create from dictionary."""
        return cls(
            scenario_name=data["scenario_name"],
            status=TestStatus(data["status"]),
            steps=[StepResult.from_dict(s) for s in data.get("steps", [])],
            duration_ms=data.get("duration_ms", 0.0),
            tags=data.get("tags", []),
            error=data.get("error"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data else datetime.now(),
        )


@dataclass
class TestResult:
    """Result of a complete test execution (feature file)."""
    id: str
    feature_name: str
    feature_file: str
    status: TestStatus
    scenarios: List[ScenarioResult] = field(default_factory=list)
    duration_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_scenarios(self) -> int:
        """Total number of scenarios."""
        return len(self.scenarios)

    @property
    def passed_scenarios(self) -> int:
        """Count of passed scenarios."""
        return sum(1 for s in self.scenarios if s.status == TestStatus.PASSED)

    @property
    def failed_scenarios(self) -> int:
        """Count of failed scenarios."""
        return sum(1 for s in self.scenarios if s.status == TestStatus.FAILED)

    @property
    def total_steps(self) -> int:
        """Total number of steps across all scenarios."""
        return sum(len(s.steps) for s in self.scenarios)

    @property
    def passed_steps(self) -> int:
        """Count of passed steps across all scenarios."""
        return sum(s.passed_steps for s in self.scenarios)

    @property
    def pass_rate(self) -> float:
        """Percentage of passed scenarios."""
        if not self.scenarios:
            return 0.0
        return (self.passed_scenarios / self.total_scenarios) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "feature_name": self.feature_name,
            "feature_file": self.feature_file,
            "status": self.status.value,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "duration_ms": self.duration_ms,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "environment": self.environment,
            "metadata": self.metadata,
            "summary": {
                "total_scenarios": self.total_scenarios,
                "passed_scenarios": self.passed_scenarios,
                "failed_scenarios": self.failed_scenarios,
                "total_steps": self.total_steps,
                "passed_steps": self.passed_steps,
                "pass_rate": self.pass_rate,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestResult":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            feature_name=data["feature_name"],
            feature_file=data["feature_file"],
            status=TestStatus(data["status"]),
            scenarios=[ScenarioResult.from_dict(s) for s in data.get("scenarios", [])],
            duration_ms=data.get("duration_ms", 0.0),
            start_time=datetime.fromisoformat(data["start_time"])
            if "start_time" in data else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"])
            if data.get("end_time") else None,
            environment=data.get("environment", {}),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TestResult":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class FeatureRecord:
    """Record of a feature file."""
    id: str
    name: str
    file_path: str
    content: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    scenario_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None  # "generated", "imported", "manual"
    user_story: Optional[str] = None  # Original user story if generated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "content": self.content,
            "description": self.description,
            "tags": self.tags,
            "scenario_count": self.scenario_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source": self.source,
            "user_story": self.user_story,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureRecord":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            file_path=data["file_path"],
            content=data["content"],
            description=data.get("description"),
            tags=data.get("tags", []),
            scenario_count=data.get("scenario_count", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(),
            source=data.get("source"),
            user_story=data.get("user_story"),
        )


@dataclass
class ExecutionSummary:
    """Summary of test executions over time."""
    total_runs: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_scenarios: int = 0
    total_steps: int = 0
    average_duration_ms: float = 0.0
    pass_rate: float = 0.0
    last_run: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_runs": self.total_runs,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_scenarios": self.total_scenarios,
            "total_steps": self.total_steps,
            "average_duration_ms": self.average_duration_ms,
            "pass_rate": self.pass_rate,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }

    @classmethod
    def from_results(cls, results: List[TestResult]) -> "ExecutionSummary":
        """Create summary from a list of test results."""
        if not results:
            return cls()

        total_runs = len(results)
        total_passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        total_failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        total_scenarios = sum(r.total_scenarios for r in results)
        total_steps = sum(r.total_steps for r in results)
        total_duration = sum(r.duration_ms for r in results)

        return cls(
            total_runs=total_runs,
            total_passed=total_passed,
            total_failed=total_failed,
            total_scenarios=total_scenarios,
            total_steps=total_steps,
            average_duration_ms=total_duration / total_runs if total_runs > 0 else 0.0,
            pass_rate=(total_passed / total_runs * 100) if total_runs > 0 else 0.0,
            last_run=max((r.start_time for r in results), default=None),
            period_start=min((r.start_time for r in results), default=None),
            period_end=max((r.end_time for r in results if r.end_time), default=None),
        )
