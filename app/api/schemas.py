"""
API Schemas

Pydantic models for API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# Health Check

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)


# Test Execution

class TestRunRequest(BaseModel):
    """Request to run tests."""
    feature_files: List[str] = Field(
        ...,
        description="List of feature file paths or glob patterns"
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    slow_mo: int = Field(
        default=100,
        description="Slow down execution by this many milliseconds"
    )
    stop_on_failure: bool = Field(
        default=False,
        description="Stop execution on first failure"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter scenarios by tags"
    )
    environment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Environment variables for test execution"
    )


class StepResultResponse(BaseModel):
    """Result of a single step."""
    step_text: str
    status: TestStatus
    duration_ms: float = 0.0
    error: Optional[str] = None
    screenshot_url: Optional[str] = None


class ScenarioResultResponse(BaseModel):
    """Result of a scenario."""
    scenario_name: str
    status: TestStatus
    steps: List[StepResultResponse] = []
    duration_ms: float = 0.0
    tags: List[str] = []
    error: Optional[str] = None


class TestResultResponse(BaseModel):
    """Result of a test run."""
    id: str
    feature_name: str
    feature_file: str
    status: TestStatus
    scenarios: List[ScenarioResultResponse] = []
    duration_ms: float = 0.0
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Dict[str, Any] = Field(default_factory=dict)


class TestRunResponse(BaseModel):
    """Response for test run request."""
    run_id: str
    status: str = "started"
    message: str = "Test run initiated"
    results_url: Optional[str] = None


class TestRunStatusResponse(BaseModel):
    """Status of a running test."""
    run_id: str
    status: TestStatus
    progress: Dict[str, int] = Field(default_factory=dict)
    current_scenario: Optional[str] = None
    results: Optional[List[TestResultResponse]] = None


# Feature Generation

class FeatureGenerateRequest(BaseModel):
    """Request to generate a feature."""
    user_story: str = Field(
        ...,
        description="User story or requirement description"
    )
    include_negative_cases: bool = Field(
        default=True,
        description="Include negative test cases"
    )
    include_edge_cases: bool = Field(
        default=True,
        description="Include edge cases"
    )
    max_scenarios: int = Field(
        default=10,
        description="Maximum number of scenarios to generate"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags to add to the feature"
    )
    output_file: Optional[str] = Field(
        default=None,
        description="Save generated feature to this file"
    )


class FeatureGenerateResponse(BaseModel):
    """Response for feature generation."""
    success: bool
    feature_content: Optional[str] = None
    feature_name: Optional[str] = None
    scenario_count: int = 0
    file_path: Optional[str] = None
    error: Optional[str] = None


# Feature Enhancement

class FeatureEnhanceRequest(BaseModel):
    """Request to enhance a feature."""
    feature_content: str = Field(
        ...,
        description="Existing feature content to enhance"
    )
    add_negative_cases: bool = True
    add_edge_cases: bool = True
    optimize_outlines: bool = True


class FeatureEnhanceResponse(BaseModel):
    """Response for feature enhancement."""
    enhanced_content: str
    additions: Dict[str, int] = Field(default_factory=dict)
    suggestions: List[str] = []


# Results and History

class TestResultsQuery(BaseModel):
    """Query parameters for test results."""
    status: Optional[TestStatus] = None
    feature_file: Optional[str] = None
    days: Optional[int] = Field(default=7, description="Number of days to look back")
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


class ExecutionSummaryResponse(BaseModel):
    """Execution summary statistics."""
    total_runs: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_scenarios: int = 0
    total_steps: int = 0
    average_duration_ms: float = 0.0
    pass_rate: float = 0.0
    last_run: Optional[datetime] = None


# Features Management

class FeatureListResponse(BaseModel):
    """List of features."""
    features: List[Dict[str, Any]]
    total: int


class FeatureDetailResponse(BaseModel):
    """Feature details."""
    id: str
    name: str
    file_path: str
    content: str
    description: Optional[str] = None
    tags: List[str] = []
    scenario_count: int = 0
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Errors

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
