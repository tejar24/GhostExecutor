"""
UI Brain API Schemas

Pydantic models for UI Brain API request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# Enums

class ActionType(str, Enum):
    """Supported action types."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    TOGGLE = "toggle"
    HOVER = "hover"
    WAIT = "wait"
    VERIFY = "verify"
    SCREENSHOT = "screenshot"


class AssertionType(str, Enum):
    """Supported assertion types."""
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_NOT_VISIBLE = "element_not_visible"
    ELEMENT_ENABLED = "element_enabled"
    ELEMENT_DISABLED = "element_disabled"
    ELEMENT_VALUE = "element_value"
    ELEMENT_TEXT = "element_text"
    TEXT_PRESENT = "text_present"
    TEXT_NOT_PRESENT = "text_not_present"
    URL_CONTAINS = "url_contains"
    URL_EQUALS = "url_equals"
    TITLE_CONTAINS = "title_contains"
    TITLE_EQUALS = "title_equals"
    DOM_HASH_CHANGED = "dom_hash_changed"
    DOM_HASH_UNCHANGED = "dom_hash_unchanged"


class StepStatus(str, Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScenarioStatus(str, Enum):
    """Scenario execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# Element Models

class ElementDescriptorSchema(BaseModel):
    """Schema for element descriptor."""
    element_id: str
    element_type: str
    element_subtype: Optional[str] = None
    resolved_label: Optional[str] = None
    logical_selector: str
    structural_selector: Optional[str] = None
    visibility_state: bool = True
    enabled_state: bool = True
    required: bool = False
    current_value: Optional[str] = None
    parent_context: Optional[str] = None
    supported_actions: List[str] = []
    selector_confidence: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ElementResolutionRequest(BaseModel):
    """Request to resolve an element."""
    description: str = Field(..., description="Natural language element description")
    element_type: Optional[str] = Field(None, description="Optional type hint (button, input, etc.)")
    page_url: Optional[str] = Field(None, description="Page URL for context")


class ElementResolutionResponse(BaseModel):
    """Response for element resolution."""
    found: bool
    selector: str
    confidence: float
    strategy: str
    element_id: Optional[str] = None
    healed: bool = False
    original_selector: Optional[str] = None
    element: Optional[ElementDescriptorSchema] = None


# Page Brain Models

class PageBrainSchema(BaseModel):
    """Schema for page brain."""
    url: str
    title: str
    dom_hash: str
    capture_timestamp: str
    ready_state: str = "complete"
    page_signature: Optional[str] = None
    element_count: int = 0
    elements: List[ElementDescriptorSchema] = []


class CaptureBrainRequest(BaseModel):
    """Request to capture page brain."""
    url: str = Field(..., description="URL to navigate to and capture")
    wait_for_stable: bool = Field(True, description="Wait for DOM stability")
    store_brain: bool = Field(True, description="Store brain for future use")


class CaptureBrainResponse(BaseModel):
    """Response for brain capture."""
    success: bool
    brain: Optional[PageBrainSchema] = None
    page_key: Optional[str] = None
    error: Optional[str] = None


class GetBrainRequest(BaseModel):
    """Request to get stored brain."""
    url: str = Field(..., description="Page URL")
    title: Optional[str] = Field(None, description="Page title for disambiguation")


class GetBrainResponse(BaseModel):
    """Response for getting brain."""
    found: bool
    brain: Optional[PageBrainSchema] = None
    page_key: Optional[str] = None


# DOM Snapshot Models

class DOMSnapshotRequest(BaseModel):
    """Request for DOM snapshot."""
    url: Optional[str] = Field(None, description="URL (if navigation needed)")
    include_elements: bool = Field(True, description="Include element details")


class DOMSnapshotResponse(BaseModel):
    """Response with DOM snapshot."""
    success: bool
    ready_state: str = "unknown"
    url: str = ""
    title: str = ""
    dom_hash: str = ""
    timestamp: str = ""
    element_count: int = 0
    elements: List[Dict[str, Any]] = []
    error: Optional[str] = None


# Scenario Execution Models

class ScenarioStep(BaseModel):
    """A single step in a scenario."""
    action: ActionType
    target: Optional[str] = Field(None, description="Element ID, selector, or description")
    value: Optional[str] = Field(None, description="Value for type/fill/select actions")
    description: Optional[str] = Field(None, description="Human-readable step description")
    timeout_ms: int = Field(10000, description="Step timeout in milliseconds")


class ScenarioAssertion(BaseModel):
    """An assertion to validate."""
    type: AssertionType
    target: Optional[str] = Field(None, description="Element or text to check")
    expected: Optional[Any] = Field(None, description="Expected value")
    description: Optional[str] = Field(None, description="Human-readable assertion description")


class ScenarioDefinition(BaseModel):
    """Complete scenario definition."""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    tags: List[str] = Field(default_factory=list, description="Scenario tags")
    preconditions: List[ScenarioStep] = Field(default_factory=list, description="Setup steps")
    steps: List[ScenarioStep] = Field(..., description="Main scenario steps")
    assertions: List[ScenarioAssertion] = Field(default_factory=list, description="Assertions to validate")
    postconditions: List[ScenarioStep] = Field(default_factory=list, description="Cleanup steps")


class ExecuteScenarioRequest(BaseModel):
    """Request to execute a scenario."""
    scenario: ScenarioDefinition
    base_url: Optional[str] = Field(None, description="Base URL for relative navigation")
    headless: bool = Field(True, description="Run browser in headless mode")
    slow_mo: int = Field(100, description="Slow down actions by milliseconds")
    capture_screenshots: bool = Field(True, description="Capture screenshots on failure")
    use_brain: bool = Field(True, description="Use UI Brain for element resolution")
    auto_heal: bool = Field(True, description="Enable self-healing selectors")


class StepExecutionResult(BaseModel):
    """Result of a single step execution."""
    step_index: int
    action: ActionType
    target: Optional[str] = None
    status: StepStatus
    duration_ms: float = 0.0
    selector_used: Optional[str] = None
    selector_confidence: float = 1.0
    healed: bool = False
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    dom_hash_before: Optional[str] = None
    dom_hash_after: Optional[str] = None


class AssertionResult(BaseModel):
    """Result of an assertion."""
    assertion_index: int
    type: AssertionType
    target: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    passed: bool
    error: Optional[str] = None


class ExecuteScenarioResponse(BaseModel):
    """Response for scenario execution."""
    scenario_name: str
    status: ScenarioStatus
    start_time: str
    end_time: str
    duration_ms: float
    steps_total: int
    steps_passed: int
    steps_failed: int
    assertions_total: int
    assertions_passed: int
    assertions_failed: int
    step_results: List[StepExecutionResult] = []
    assertion_results: List[AssertionResult] = []
    failure_reason: Optional[str] = None
    healing_log: List[Dict[str, Any]] = []
    final_dom_hash: Optional[str] = None
    screenshots: List[str] = []


# Feature File Execution Models

class ExecuteFeatureRequest(BaseModel):
    """Request to execute a feature file."""
    feature_file: str = Field(..., description="Path to feature file")
    scenario_filter: Optional[str] = Field(None, description="Filter scenarios by name pattern")
    tag_filter: Optional[List[str]] = Field(None, description="Filter scenarios by tags")
    headless: bool = Field(True, description="Run browser in headless mode")
    slow_mo: int = Field(100, description="Slow down actions by milliseconds")
    stop_on_failure: bool = Field(False, description="Stop on first failure")
    use_brain: bool = Field(True, description="Use UI Brain for element resolution")
    auto_heal: bool = Field(True, description="Enable self-healing selectors")
    output_dir: str = Field("reports", description="Directory for reports")


class ExecuteFeatureResponse(BaseModel):
    """Response for feature file execution."""
    run_id: str
    feature_name: str
    feature_file: str
    status: ScenarioStatus
    start_time: str
    end_time: str
    duration_ms: float
    scenarios_total: int
    scenarios_passed: int
    scenarios_failed: int
    scenarios_skipped: int
    scenario_results: List[ExecuteScenarioResponse] = []
    report_path: Optional[str] = None
    brain_data_path: Optional[str] = None


# Batch Execution Models

class BatchExecuteRequest(BaseModel):
    """Request to execute multiple features."""
    feature_files: List[str] = Field(..., description="List of feature file paths or patterns")
    parallel: bool = Field(False, description="Execute features in parallel")
    max_workers: int = Field(4, description="Max parallel workers")
    headless: bool = Field(True, description="Run browser in headless mode")
    slow_mo: int = Field(100, description="Slow down actions by milliseconds")
    stop_on_failure: bool = Field(False, description="Stop on first failure")
    use_brain: bool = Field(True, description="Use UI Brain")
    auto_heal: bool = Field(True, description="Enable self-healing")
    output_dir: str = Field("reports", description="Directory for reports")


class BatchExecuteResponse(BaseModel):
    """Response for batch execution."""
    batch_id: str
    status: str
    total_features: int
    completed_features: int
    passed_features: int
    failed_features: int
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    feature_results: List[ExecuteFeatureResponse] = []
    report_path: Optional[str] = None


# Self-Healing Models

class HealingLogEntry(BaseModel):
    """Entry in the self-healing log."""
    timestamp: str
    original_element_id: str
    original_selector: str
    healed_element_id: str
    healed_selector: str
    confidence: float
    description: str


class HealingReportResponse(BaseModel):
    """Report of all healing actions."""
    total_heals: int
    successful_heals: int
    failed_heals: int
    entries: List[HealingLogEntry] = []


# Brain Management Models

class ListBrainsResponse(BaseModel):
    """Response listing all stored brains."""
    total: int
    brains: List[Dict[str, Any]] = []


class DeleteBrainRequest(BaseModel):
    """Request to delete a brain."""
    url: str
    title: Optional[str] = None


class DeleteBrainResponse(BaseModel):
    """Response for brain deletion."""
    deleted: bool
    page_key: Optional[str] = None


class ExportBrainRequest(BaseModel):
    """Request to export a brain."""
    url: str
    output_path: str


class ImportBrainRequest(BaseModel):
    """Request to import a brain."""
    input_path: str


# Validation Models

class ValidateBrainRequest(BaseModel):
    """Request to validate a brain against current DOM."""
    url: str
    title: Optional[str] = None


class ValidateBrainResponse(BaseModel):
    """Response for brain validation."""
    valid: bool
    stored_hash: Optional[str] = None
    current_hash: Optional[str] = None
    elements_matched: int = 0
    elements_missing: int = 0
    elements_new: int = 0
    needs_refresh: bool = False
