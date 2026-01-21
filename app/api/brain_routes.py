"""
UI Brain API Routes

FastAPI router for UI Brain operations including:
- DOM snapshot capture
- Page brain management
- Element resolution
- Scenario execution with brain integration
- Self-healing operations
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from .brain_schemas import (
    # Element models
    ElementResolutionRequest,
    ElementResolutionResponse,
    ElementDescriptorSchema,
    # Brain models
    PageBrainSchema,
    CaptureBrainRequest,
    CaptureBrainResponse,
    GetBrainRequest,
    GetBrainResponse,
    ListBrainsResponse,
    DeleteBrainRequest,
    DeleteBrainResponse,
    ValidateBrainRequest,
    ValidateBrainResponse,
    ExportBrainRequest,
    ImportBrainRequest,
    # DOM models
    DOMSnapshotRequest,
    DOMSnapshotResponse,
    # Scenario models
    ScenarioDefinition,
    ScenarioStep,
    ScenarioAssertion,
    ExecuteScenarioRequest,
    ExecuteScenarioResponse,
    StepExecutionResult,
    AssertionResult,
    StepStatus,
    ScenarioStatus,
    ActionType,
    AssertionType,
    # Feature models
    ExecuteFeatureRequest,
    ExecuteFeatureResponse,
    BatchExecuteRequest,
    BatchExecuteResponse,
    # Healing models
    HealingReportResponse,
    HealingLogEntry,
)

router = APIRouter(prefix="/brain", tags=["UI Brain"])

# In-memory storage for running executions
_running_executions: Dict[str, Dict[str, Any]] = {}


# ============================================================
# DOM Snapshot Endpoints
# ============================================================

@router.post(
    "/dom/snapshot",
    response_model=DOMSnapshotResponse,
    summary="Capture DOM snapshot",
    description="Capture current DOM state from browser"
)
async def capture_dom_snapshot(request: DOMSnapshotRequest):
    """
    Capture a snapshot of the current DOM state.

    If URL is provided, navigates to that URL first.
    Returns element information and DOM hash for comparison.
    """
    try:
        from app.executor.browser import BrowserAutomation

        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            # Navigate if URL provided
            if request.url:
                result = browser.navigate(request.url)
                if not result.success:
                    return DOMSnapshotResponse(
                        success=False,
                        error=f"Navigation failed: {result.error}"
                    )

            # Wait for stability
            browser.wait_for_dom_stable()

            # Get snapshot
            snapshot = browser.get_dom_snapshot()
            dom_hash = browser.get_dom_hash()

            return DOMSnapshotResponse(
                success=True,
                ready_state=snapshot.get("readyState", "unknown"),
                url=snapshot.get("url", browser.get_current_url()),
                title=snapshot.get("title", browser.get_title()),
                dom_hash=dom_hash,
                timestamp=snapshot.get("timestamp", datetime.now().isoformat()),
                element_count=snapshot.get("elementCount", 0),
                elements=snapshot.get("elements", []) if request.include_elements else []
            )

        finally:
            browser.stop()

    except Exception as e:
        return DOMSnapshotResponse(success=False, error=str(e))


@router.get(
    "/dom/hash",
    summary="Get current DOM hash",
    description="Get DOM hash without full snapshot"
)
async def get_dom_hash(url: str = Query(..., description="URL to check")):
    """Get DOM hash for a URL without capturing full snapshot."""
    try:
        from app.executor.browser import BrowserAutomation

        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            browser.navigate(url)
            browser.wait_for_dom_stable()
            dom_hash = browser.get_dom_hash()

            return {
                "url": url,
                "dom_hash": dom_hash,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            browser.stop()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Page Brain Endpoints
# ============================================================

@router.post(
    "/capture",
    response_model=CaptureBrainResponse,
    summary="Capture page brain",
    description="Navigate to URL and capture complete UI Brain"
)
async def capture_page_brain(request: CaptureBrainRequest):
    """
    Navigate to a URL and capture the complete UI Brain.

    Discovers all interactive elements, generates selectors,
    and optionally stores the brain for future use.
    """
    try:
        from app.executor.browser import BrowserAutomation
        from app.brain import UIBrain, PageBrainStore

        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            # Navigate
            result = browser.navigate(request.url)
            if not result.success:
                return CaptureBrainResponse(
                    success=False,
                    error=f"Navigation failed: {result.error}"
                )

            # Wait for stability if requested
            if request.wait_for_stable:
                browser.wait_for_dom_stable()

            # Build brain
            ui_brain = UIBrain()
            brain = ui_brain.build_page_brain(browser)

            # Convert to schema
            brain_schema = PageBrainSchema(
                url=brain.url,
                title=brain.title,
                dom_hash=brain.dom_hash,
                capture_timestamp=brain.capture_timestamp,
                ready_state=brain.ready_state,
                page_signature=brain.page_signature,
                element_count=len(brain.elements),
                elements=[
                    ElementDescriptorSchema(
                        element_id=e.element_id,
                        element_type=e.element_type,
                        element_subtype=e.element_subtype,
                        resolved_label=e.resolved_label,
                        logical_selector=e.logical_selector,
                        structural_selector=e.structural_selector,
                        visibility_state=e.visibility_state,
                        enabled_state=e.enabled_state,
                        required=e.required,
                        current_value=e.current_value,
                        parent_context=e.parent_context,
                        supported_actions=e.supported_actions,
                        selector_confidence=e.selector_confidence,
                        attributes=e.attributes
                    )
                    for e in brain.elements
                ]
            )

            # Store if requested
            page_key = None
            if request.store_brain:
                store = PageBrainStore()
                page_key = store.save_brain(brain.to_dict())

            return CaptureBrainResponse(
                success=True,
                brain=brain_schema,
                page_key=page_key
            )

        finally:
            browser.stop()

    except Exception as e:
        return CaptureBrainResponse(success=False, error=str(e))


@router.post(
    "/get",
    response_model=GetBrainResponse,
    summary="Get stored brain",
    description="Retrieve a previously stored page brain"
)
async def get_stored_brain(request: GetBrainRequest):
    """Get a previously stored page brain by URL."""
    try:
        from app.brain import PageBrainStore

        store = PageBrainStore()
        brain_data = store.load_brain(request.url, request.title or "")

        if not brain_data:
            return GetBrainResponse(found=False)

        # Convert to schema
        elements = []
        for e in brain_data.get("elements", []):
            elements.append(ElementDescriptorSchema(
                element_id=e.get("element_id", ""),
                element_type=e.get("element_type", "unknown"),
                element_subtype=e.get("element_subtype"),
                resolved_label=e.get("resolved_label"),
                logical_selector=e.get("logical_selector", ""),
                structural_selector=e.get("structural_selector"),
                visibility_state=e.get("visibility_state", True),
                enabled_state=e.get("enabled_state", True),
                required=e.get("required", False),
                current_value=e.get("current_value"),
                parent_context=e.get("parent_context"),
                supported_actions=e.get("supported_actions", []),
                selector_confidence=e.get("selector_confidence", 1.0),
                attributes=e.get("attributes", {})
            ))

        brain_schema = PageBrainSchema(
            url=brain_data.get("url", ""),
            title=brain_data.get("title", ""),
            dom_hash=brain_data.get("dom_hash", ""),
            capture_timestamp=brain_data.get("capture_timestamp", ""),
            ready_state=brain_data.get("ready_state", "complete"),
            page_signature=brain_data.get("page_signature"),
            element_count=len(elements),
            elements=elements
        )

        page_key = brain_data.get("_storage", {}).get("page_key")

        return GetBrainResponse(
            found=True,
            brain=brain_schema,
            page_key=page_key
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/list",
    response_model=ListBrainsResponse,
    summary="List stored brains",
    description="List all stored page brains"
)
async def list_stored_brains():
    """List all stored page brains."""
    try:
        from app.brain import PageBrainStore

        store = PageBrainStore()
        pages = store.list_stored_pages()

        return ListBrainsResponse(
            total=len(pages),
            brains=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/validate",
    response_model=ValidateBrainResponse,
    summary="Validate brain",
    description="Check if stored brain matches current DOM"
)
async def validate_brain(request: ValidateBrainRequest):
    """Validate a stored brain against the current DOM state."""
    try:
        from app.executor.browser import BrowserAutomation
        from app.brain import PageBrainStore, UIBrain

        store = PageBrainStore()
        brain_data = store.load_brain(request.url, request.title or "")

        if not brain_data:
            return ValidateBrainResponse(
                valid=False,
                needs_refresh=True
            )

        stored_hash = brain_data.get("dom_hash")

        # Get current DOM hash
        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            browser.navigate(request.url)
            browser.wait_for_dom_stable()

            current_hash = browser.get_dom_hash()

            valid = stored_hash == current_hash

            return ValidateBrainResponse(
                valid=valid,
                stored_hash=stored_hash,
                current_hash=current_hash,
                elements_matched=len(brain_data.get("elements", [])) if valid else 0,
                needs_refresh=not valid
            )

        finally:
            browser.stop()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/delete",
    response_model=DeleteBrainResponse,
    summary="Delete brain",
    description="Delete a stored page brain"
)
async def delete_brain(request: DeleteBrainRequest):
    """Delete a stored page brain."""
    try:
        from app.brain import PageBrainStore

        store = PageBrainStore()
        deleted = store.delete_brain(request.url, request.title or "")

        return DeleteBrainResponse(deleted=deleted)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/clear",
    summary="Clear all brains",
    description="Delete all stored page brains"
)
async def clear_all_brains():
    """Clear all stored page brains."""
    try:
        from app.brain import PageBrainStore

        store = PageBrainStore()
        count = store.clear_all()

        return {"deleted": count, "message": f"Cleared {count} stored brains"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Element Resolution Endpoints
# ============================================================

@router.post(
    "/resolve",
    response_model=ElementResolutionResponse,
    summary="Resolve element",
    description="Resolve element from natural language description"
)
async def resolve_element(request: ElementResolutionRequest):
    """
    Resolve an element from a natural language description.

    Uses the UI Brain to find the best matching element
    and returns its selector with confidence score.
    """
    try:
        from app.executor.browser import BrowserAutomation
        from app.brain import BrainInterpreter

        if not request.page_url:
            raise HTTPException(
                status_code=400,
                detail="page_url is required for element resolution"
            )

        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            browser.navigate(request.page_url)
            browser.wait_for_dom_stable()

            interpreter = BrainInterpreter(browser)
            resolution = interpreter.resolve_element(
                request.description,
                request.element_type
            )

            return ElementResolutionResponse(
                found=resolution.found,
                selector=resolution.selector,
                confidence=resolution.confidence,
                strategy=resolution.strategy,
                element_id=resolution.element_id,
                healed=resolution.healed,
                original_selector=resolution.original_selector
            )

        finally:
            browser.stop()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/elements",
    summary="Get page elements",
    description="Get all elements for a page from brain or live DOM"
)
async def get_page_elements(
    url: str = Query(..., description="Page URL"),
    from_brain: bool = Query(True, description="Get from stored brain"),
    element_type: Optional[str] = Query(None, description="Filter by type")
):
    """Get all elements for a page."""
    try:
        if from_brain:
            from app.brain import PageBrainStore
            store = PageBrainStore()
            brain_data = store.load_brain(url)

            if brain_data:
                elements = brain_data.get("elements", [])
                if element_type:
                    elements = [
                        e for e in elements
                        if e.get("element_type") == element_type or
                           e.get("element_subtype") == element_type
                    ]
                return {"source": "brain", "elements": elements}

        # Get from live DOM
        from app.executor.browser import BrowserAutomation
        from app.brain import UIBrain

        browser = BrowserAutomation(headless=True)
        browser.start()

        try:
            browser.navigate(url)
            browser.wait_for_dom_stable()

            ui_brain = UIBrain()
            brain = ui_brain.build_page_brain(browser)

            elements = [e.to_dict() for e in brain.elements]
            if element_type:
                elements = [
                    e for e in elements
                    if e.get("element_type") == element_type or
                       e.get("element_subtype") == element_type
                ]

            return {"source": "live", "elements": elements}

        finally:
            browser.stop()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Scenario Execution Endpoints
# ============================================================

@router.post(
    "/execute/scenario",
    response_model=ExecuteScenarioResponse,
    summary="Execute scenario",
    description="Execute a test scenario with UI Brain integration"
)
async def execute_scenario(request: ExecuteScenarioRequest):
    """
    Execute a test scenario using the UI Brain.

    Steps are executed sequentially with element resolution
    through the brain. Self-healing is applied when selectors fail.
    """
    try:
        from app.executor.browser import BrowserAutomation
        from app.brain import BrainInterpreter

        start_time = datetime.now()

        browser = BrowserAutomation(
            headless=request.headless,
            slow_mo=request.slow_mo
        )
        browser.start()

        try:
            interpreter = BrainInterpreter(
                browser,
                auto_heal=request.auto_heal
            ) if request.use_brain else None

            step_results: List[StepExecutionResult] = []
            assertion_results: List[AssertionResult] = []
            screenshots: List[str] = []
            scenario_status = ScenarioStatus.PASSED
            failure_reason = None

            # Execute preconditions
            all_steps = (
                request.scenario.preconditions +
                request.scenario.steps +
                request.scenario.postconditions
            )

            for idx, step in enumerate(all_steps):
                step_start = datetime.now()
                dom_hash_before = browser.get_dom_hash()

                step_result = await _execute_step(
                    browser, interpreter, step, idx,
                    request.base_url, request.capture_screenshots
                )

                step_result.dom_hash_before = dom_hash_before
                step_result.dom_hash_after = browser.get_dom_hash()

                step_results.append(step_result)

                if step_result.screenshot_path:
                    screenshots.append(step_result.screenshot_path)

                if step_result.status == StepStatus.FAILED:
                    scenario_status = ScenarioStatus.FAILED
                    failure_reason = step_result.error
                    break

            # Execute assertions
            for idx, assertion in enumerate(request.scenario.assertions):
                assertion_result = await _execute_assertion(
                    browser, interpreter, assertion, idx
                )
                assertion_results.append(assertion_result)

                if not assertion_result.passed:
                    scenario_status = ScenarioStatus.FAILED
                    if not failure_reason:
                        failure_reason = assertion_result.error

            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            healing_log = []
            if interpreter:
                healing_log = interpreter.get_healing_log()

            return ExecuteScenarioResponse(
                scenario_name=request.scenario.name,
                status=scenario_status,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration_ms=duration_ms,
                steps_total=len(step_results),
                steps_passed=len([s for s in step_results if s.status == StepStatus.PASSED]),
                steps_failed=len([s for s in step_results if s.status == StepStatus.FAILED]),
                assertions_total=len(assertion_results),
                assertions_passed=len([a for a in assertion_results if a.passed]),
                assertions_failed=len([a for a in assertion_results if not a.passed]),
                step_results=step_results,
                assertion_results=assertion_results,
                failure_reason=failure_reason,
                healing_log=healing_log,
                final_dom_hash=browser.get_dom_hash(),
                screenshots=screenshots
            )

        finally:
            browser.stop()

    except Exception as e:
        return ExecuteScenarioResponse(
            scenario_name=request.scenario.name,
            status=ScenarioStatus.ERROR,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_ms=0,
            steps_total=0,
            steps_passed=0,
            steps_failed=0,
            assertions_total=0,
            assertions_passed=0,
            assertions_failed=0,
            failure_reason=str(e)
        )


async def _execute_step(
    browser,
    interpreter,
    step: ScenarioStep,
    index: int,
    base_url: Optional[str],
    capture_screenshots: bool
) -> StepExecutionResult:
    """Execute a single scenario step."""
    from app.executor.browser import BrowserAction

    step_start = datetime.now()
    selector = None
    confidence = 1.0
    healed = False
    error = None
    screenshot_path = None

    try:
        # Resolve element if needed
        if step.target and step.action not in [ActionType.NAVIGATE, ActionType.WAIT]:
            if interpreter:
                resolution = interpreter.resolve_element(step.target)
                selector = resolution.selector
                confidence = resolution.confidence
                healed = resolution.healed

                if not resolution.found:
                    raise Exception(f"Element not found: {step.target}")
            else:
                selector = step.target

        # Execute action
        result: BrowserAction

        if step.action == ActionType.NAVIGATE:
            url = step.value or step.target
            if base_url and not url.startswith("http"):
                url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            result = browser.navigate(url)

        elif step.action == ActionType.CLICK:
            result = browser.click(selector)

        elif step.action in [ActionType.TYPE, ActionType.FILL]:
            result = browser.fill(selector, step.value or "")

        elif step.action == ActionType.SELECT:
            result = browser.select_option(selector, step.value or "")

        elif step.action == ActionType.CHECK:
            result = browser.check(selector)

        elif step.action == ActionType.UNCHECK:
            result = browser.uncheck(selector)

        elif step.action == ActionType.HOVER:
            result = browser.hover(selector)

        elif step.action == ActionType.WAIT:
            if selector:
                result = browser.wait_for_selector(selector, step.timeout_ms)
            else:
                # Wait for time (value in seconds)
                import time
                time.sleep(float(step.value or 1))
                result = BrowserAction(success=True, action="wait")

        elif step.action == ActionType.VERIFY:
            is_visible = browser.is_visible(selector)
            result = BrowserAction(
                success=is_visible,
                action="verify",
                selector=selector,
                error=None if is_visible else f"Element not visible: {selector}"
            )

        elif step.action == ActionType.SCREENSHOT:
            screenshot_data = browser.take_screenshot()
            # Save screenshot (simplified)
            result = BrowserAction(success=True, action="screenshot")

        else:
            result = BrowserAction(
                success=False,
                action=step.action.value,
                error=f"Unknown action: {step.action}"
            )

        if not result.success:
            error = result.error
            if capture_screenshots:
                try:
                    import base64
                    from pathlib import Path
                    screenshot_data = browser.take_screenshot()
                    screenshot_path = f"reports/screenshots/step_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    Path("reports/screenshots").mkdir(parents=True, exist_ok=True)
                    with open(screenshot_path, "wb") as f:
                        f.write(base64.b64decode(screenshot_data))
                except Exception:
                    pass

        duration_ms = (datetime.now() - step_start).total_seconds() * 1000

        return StepExecutionResult(
            step_index=index,
            action=step.action,
            target=step.target,
            status=StepStatus.PASSED if result.success else StepStatus.FAILED,
            duration_ms=duration_ms,
            selector_used=selector,
            selector_confidence=confidence,
            healed=healed,
            error=error,
            screenshot_path=screenshot_path
        )

    except Exception as e:
        duration_ms = (datetime.now() - step_start).total_seconds() * 1000
        return StepExecutionResult(
            step_index=index,
            action=step.action,
            target=step.target,
            status=StepStatus.FAILED,
            duration_ms=duration_ms,
            selector_used=selector,
            selector_confidence=confidence,
            healed=healed,
            error=str(e),
            screenshot_path=screenshot_path
        )


async def _execute_assertion(
    browser,
    interpreter,
    assertion: ScenarioAssertion,
    index: int
) -> AssertionResult:
    """Execute a single assertion."""
    try:
        passed = False
        actual = None
        error = None

        if assertion.type == AssertionType.ELEMENT_VISIBLE:
            selector = assertion.target
            if interpreter:
                resolution = interpreter.resolve_element(assertion.target)
                selector = resolution.selector
            actual = browser.is_visible(selector)
            passed = actual

        elif assertion.type == AssertionType.ELEMENT_NOT_VISIBLE:
            selector = assertion.target
            if interpreter:
                resolution = interpreter.resolve_element(assertion.target)
                selector = resolution.selector
            actual = not browser.is_visible(selector)
            passed = actual

        elif assertion.type == AssertionType.ELEMENT_VALUE:
            selector = assertion.target
            if interpreter:
                resolution = interpreter.resolve_element(assertion.target)
                selector = resolution.selector
            actual = browser.get_attribute(selector, "value")
            passed = actual == assertion.expected

        elif assertion.type == AssertionType.ELEMENT_TEXT:
            selector = assertion.target
            if interpreter:
                resolution = interpreter.resolve_element(assertion.target)
                selector = resolution.selector
            actual = browser.get_text(selector)
            passed = assertion.expected in (actual or "")

        elif assertion.type == AssertionType.TEXT_PRESENT:
            page_text = browser.get_visible_text()
            actual = assertion.expected in page_text
            passed = actual

        elif assertion.type == AssertionType.URL_CONTAINS:
            actual = browser.get_current_url()
            passed = assertion.expected in actual

        elif assertion.type == AssertionType.URL_EQUALS:
            actual = browser.get_current_url()
            passed = actual == assertion.expected

        elif assertion.type == AssertionType.TITLE_CONTAINS:
            actual = browser.get_title()
            passed = assertion.expected in actual

        elif assertion.type == AssertionType.TITLE_EQUALS:
            actual = browser.get_title()
            passed = actual == assertion.expected

        else:
            error = f"Unknown assertion type: {assertion.type}"

        if not passed and not error:
            error = f"Assertion failed: expected {assertion.expected}, got {actual}"

        return AssertionResult(
            assertion_index=index,
            type=assertion.type,
            target=assertion.target,
            expected=assertion.expected,
            actual=actual,
            passed=passed,
            error=error
        )

    except Exception as e:
        return AssertionResult(
            assertion_index=index,
            type=assertion.type,
            target=assertion.target,
            expected=assertion.expected,
            actual=None,
            passed=False,
            error=str(e)
        )


# ============================================================
# Feature File Execution Endpoints
# ============================================================

@router.post(
    "/execute/feature",
    response_model=ExecuteFeatureResponse,
    summary="Execute feature file",
    description="Execute a Gherkin feature file with UI Brain"
)
async def execute_feature_file(
    request: ExecuteFeatureRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a Gherkin feature file using the UI Brain.

    Parses the feature file, executes all scenarios,
    and generates a comprehensive report.
    """
    run_id = str(uuid.uuid4())

    # Store initial state
    _running_executions[run_id] = {
        "status": "running",
        "started_at": datetime.now(),
        "request": request.model_dump(),
        "results": None
    }

    # Execute in background
    background_tasks.add_task(
        _execute_feature_background,
        run_id,
        request
    )

    return ExecuteFeatureResponse(
        run_id=run_id,
        feature_name="",
        feature_file=request.feature_file,
        status=ScenarioStatus.RUNNING,
        start_time=datetime.now().isoformat(),
        end_time="",
        duration_ms=0,
        scenarios_total=0,
        scenarios_passed=0,
        scenarios_failed=0,
        scenarios_skipped=0
    )


async def _execute_feature_background(run_id: str, request: ExecuteFeatureRequest):
    """Execute feature file in background."""
    try:
        from app.executor.runner import AutonomousTestRunner

        runner = AutonomousTestRunner(
            headless=request.headless,
            slow_mo=request.slow_mo,
            output_dir=request.output_dir,
            stop_on_failure=request.stop_on_failure
        )

        result = await asyncio.to_thread(
            runner.run_feature_file,
            request.feature_file
        )

        _running_executions[run_id]["status"] = "completed"
        _running_executions[run_id]["results"] = result
        _running_executions[run_id]["completed_at"] = datetime.now()

    except Exception as e:
        _running_executions[run_id]["status"] = "error"
        _running_executions[run_id]["error"] = str(e)


@router.get(
    "/execute/status/{run_id}",
    summary="Get execution status",
    description="Get status of a running execution"
)
async def get_execution_status(run_id: str):
    """Get the status of a running execution."""
    if run_id not in _running_executions:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = _running_executions[run_id]

    return {
        "run_id": run_id,
        "status": execution["status"],
        "started_at": execution["started_at"].isoformat(),
        "completed_at": execution.get("completed_at", "").isoformat() if execution.get("completed_at") else None,
        "error": execution.get("error"),
        "results": execution.get("results")
    }


@router.post(
    "/execute/batch",
    response_model=BatchExecuteResponse,
    summary="Execute multiple features",
    description="Execute multiple feature files"
)
async def execute_batch(
    request: BatchExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Execute multiple feature files."""
    batch_id = str(uuid.uuid4())

    _running_executions[batch_id] = {
        "status": "running",
        "started_at": datetime.now(),
        "request": request.model_dump(),
        "feature_results": [],
        "completed": 0
    }

    background_tasks.add_task(
        _execute_batch_background,
        batch_id,
        request
    )

    return BatchExecuteResponse(
        batch_id=batch_id,
        status="running",
        total_features=len(request.feature_files),
        completed_features=0,
        passed_features=0,
        failed_features=0,
        start_time=datetime.now().isoformat()
    )


async def _execute_batch_background(batch_id: str, request: BatchExecuteRequest):
    """Execute batch in background."""
    try:
        from app.executor.runner import AutonomousTestRunner
        from glob import glob

        # Expand glob patterns
        feature_files = []
        for pattern in request.feature_files:
            matches = glob(pattern)
            feature_files.extend(matches if matches else [pattern])

        runner = AutonomousTestRunner(
            headless=request.headless,
            slow_mo=request.slow_mo,
            output_dir=request.output_dir,
            stop_on_failure=request.stop_on_failure
        )

        result = await asyncio.to_thread(
            runner.run_feature_files,
            feature_files
        )

        _running_executions[batch_id]["status"] = "completed"
        _running_executions[batch_id]["results"] = result
        _running_executions[batch_id]["completed_at"] = datetime.now()

    except Exception as e:
        _running_executions[batch_id]["status"] = "error"
        _running_executions[batch_id]["error"] = str(e)


# ============================================================
# Healing Report Endpoints
# ============================================================

@router.get(
    "/healing/report",
    response_model=HealingReportResponse,
    summary="Get healing report",
    description="Get report of all self-healing actions"
)
async def get_healing_report(
    run_id: Optional[str] = Query(None, description="Filter by run ID")
):
    """Get a report of self-healing actions."""
    entries = []

    if run_id and run_id in _running_executions:
        execution = _running_executions[run_id]
        if "healing_log" in execution:
            for log in execution["healing_log"]:
                entries.append(HealingLogEntry(
                    timestamp=log.get("timestamp", ""),
                    original_element_id=log.get("original_id", ""),
                    original_selector=log.get("original_selector", ""),
                    healed_element_id=log.get("healed_id", ""),
                    healed_selector=log.get("healed_selector", ""),
                    confidence=log.get("confidence", 0.0),
                    description=log.get("description", "")
                ))

    return HealingReportResponse(
        total_heals=len(entries),
        successful_heals=len(entries),
        failed_heals=0,
        entries=entries
    )
