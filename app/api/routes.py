"""
API Routes

FastAPI router with all API endpoints.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from .schemas import (
    TestRunRequest,
    TestRunResponse,
    TestRunStatusResponse,
    TestResultResponse,
    TestResultsQuery,
    FeatureGenerateRequest,
    FeatureGenerateResponse,
    FeatureEnhanceRequest,
    FeatureEnhanceResponse,
    FeatureListResponse,
    FeatureDetailResponse,
    ExecutionSummaryResponse,
    HealthResponse,
    ErrorResponse,
    TestStatus,
)
from app.config import get_config
from .streaming import emit_log_sync, mark_run_started, mark_run_completed

router = APIRouter()


def get_api_base_url() -> str:
    """Get the full API base URL from config."""
    config = get_config()
    return f"{config.api.base_url}{config.api.api_prefix}"

# In-memory storage for running tests
_running_tests: Dict[str, Dict[str, Any]] = {}

# Store runner instances for cancellation
_active_runners: Dict[str, Any] = {}


# Health & Info

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthResponse()


@router.get("/info", tags=["System"])
async def api_info():
    """Get API information."""
    base_url = get_api_base_url()
    return {
        "name": "Ghost-QC API",
        "version": "1.0.0",
        "description": "Autonomous test execution framework API",
        "base_url": base_url,
        "endpoints": {
            "health": f"{base_url}/health",
            "tests": f"{base_url}/tests",
            "features": f"{base_url}/features",
            "generate": f"{base_url}/generate",
            "results": f"{base_url}/results",
            "brain": f"{base_url}/brain",
        },
    }


# Test Execution

@router.post(
    "/tests/run",
    response_model=TestRunResponse,
    tags=["Tests"],
    summary="Start a test run",
)
async def run_tests(
    request: TestRunRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new test run with the specified feature files.

    The test runs asynchronously. Use the returned run_id to check status.
    """
    run_id = str(uuid.uuid4())

    # Store initial state
    _running_tests[run_id] = {
        "status": TestStatus.PENDING,
        "started_at": datetime.now(),
        "request": request.model_dump(),
        "results": [],
        "current_scenario": None,
        "progress": {"total": 0, "completed": 0, "passed": 0, "failed": 0},
    }

    # Start test execution in background
    background_tasks.add_task(_execute_tests, run_id, request)

    base_url = get_api_base_url()
    return TestRunResponse(
        run_id=run_id,
        status="started",
        message="Test run initiated",
        results_url=f"{base_url}/tests/{run_id}",
    )


async def _execute_tests(run_id: str, request: TestRunRequest):
    """Execute tests in background."""
    try:
        _running_tests[run_id]["status"] = TestStatus.RUNNING
        mark_run_started(run_id)

        # Import here to avoid circular imports
        from app.executor.runner import AutonomousTestRunner
        from app.utils.file_utils import find_files

        # Get project root directory
        project_root = Path(__file__).parent.parent.parent

        # Find feature files
        feature_files = []
        for pattern in request.feature_files:
            if "*" in pattern:
                feature_files.extend(find_files(pattern))
            else:
                # Try relative to project root first
                path = project_root / pattern
                if path.exists():
                    feature_files.append(path)
                else:
                    # Try as absolute path
                    path = Path(pattern)
                    if path.exists():
                        feature_files.append(path)

        _running_tests[run_id]["progress"]["total"] = len(feature_files)

        # Create emit callback for step logger
        def emit_callback(event_type: str, data: dict):
            emit_log_sync(run_id, event_type, data)

        # Run tests
        runner = AutonomousTestRunner(
            headless=request.headless,
            slow_mo=request.slow_mo,
            emit_callback=emit_callback,
        )

        # Store runner for cancellation
        _active_runners[run_id] = runner

        all_results = []
        for feature_file in feature_files:
            # Check if cancelled before running next feature
            if runner.is_cancelled():
                break

            _running_tests[run_id]["current_scenario"] = str(feature_file)

            # Run the feature file
            test_result = await asyncio.to_thread(
                runner.run_feature_file,
                str(feature_file),
            )

            # Check if cancelled during execution
            if runner.is_cancelled():
                break

            # Convert result to dict for JSON serialization
            result_dict = {
                "status": "passed" if test_result.failed_scenarios == 0 else "failed",
                "total_scenarios": test_result.total_scenarios,
                "passed_scenarios": test_result.passed_scenarios,
                "failed_scenarios": test_result.failed_scenarios,
                "scenarios": []
            }

            # Add scenario details
            for feature in test_result.features:
                for scenario in feature.scenarios:
                    scenario_dict = {
                        "name": scenario.name,
                        "status": scenario.status,
                        "steps": []
                    }
                    for step in scenario.steps:
                        scenario_dict["steps"].append({
                            "keyword": step.keyword,
                            "step_text": step.step_text,
                            "status": step.status,
                            "error": step.error
                        })
                    result_dict["scenarios"].append(scenario_dict)

            all_results.append(result_dict)
            _running_tests[run_id]["results"].append(result_dict)
            _running_tests[run_id]["progress"]["completed"] += 1

            if result_dict["status"] == "passed":
                _running_tests[run_id]["progress"]["passed"] += 1
            else:
                _running_tests[run_id]["progress"]["failed"] += 1

        # Determine final status
        all_passed = all(r["status"] == "passed" for r in all_results)
        final_status = TestStatus.PASSED if all_passed else TestStatus.FAILED
        _running_tests[run_id]["status"] = final_status
        _running_tests[run_id]["completed_at"] = datetime.now()

        # Mark run as completed for SSE streaming
        mark_run_completed(run_id, "passed" if all_passed else "failed")

        # Cleanup runner reference
        _active_runners.pop(run_id, None)

    except Exception as e:
        _running_tests[run_id]["status"] = TestStatus.ERROR
        _running_tests[run_id]["error"] = str(e)
        mark_run_completed(run_id, "error")
        # Cleanup runner reference
        _active_runners.pop(run_id, None)


@router.get(
    "/tests/{run_id}",
    tags=["Tests"],
    summary="Get test run status",
)
async def get_test_status(run_id: str):
    """Get the status of a test run."""
    if run_id not in _running_tests:
        raise HTTPException(status_code=404, detail="Test run not found")

    run_data = _running_tests[run_id]

    return {
        "run_id": run_id,
        "status": run_data["status"],
        "progress": run_data["progress"],
        "current_scenario": run_data.get("current_scenario"),
        "results": run_data.get("results"),
        "error": run_data.get("error"),
    }


@router.delete(
    "/tests/{run_id}",
    tags=["Tests"],
    summary="Cancel a test run",
)
async def cancel_test_run(run_id: str):
    """Cancel a running test."""
    if run_id not in _running_tests:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Actually cancel the running test
    runner = _active_runners.get(run_id)
    if runner:
        try:
            runner.cancel()
        except Exception as e:
            print(f"Error cancelling runner: {e}")
        finally:
            _active_runners.pop(run_id, None)

    # Mark as cancelled
    _running_tests[run_id]["status"] = TestStatus.SKIPPED
    _running_tests[run_id]["error"] = "Cancelled by user"
    _running_tests[run_id]["completed_at"] = datetime.now()

    # Mark run as completed for SSE streaming
    mark_run_completed(run_id, "cancelled")

    return {"message": "Test run cancelled successfully"}


# Feature Generation

@router.post(
    "/generate/feature",
    response_model=FeatureGenerateResponse,
    tags=["Generation"],
    summary="Generate a feature from user story",
)
async def generate_feature(request: FeatureGenerateRequest):
    """
    Generate a Gherkin feature file from a user story using AI.
    """
    try:
        from app.generator import FeatureGenerator, GenerationConfig

        config = GenerationConfig(
            include_negative_cases=request.include_negative_cases,
            include_edge_cases=request.include_edge_cases,
            max_scenarios=request.max_scenarios,
            tags=request.tags or [],
        )

        generator = FeatureGenerator(config=config)
        result = await asyncio.to_thread(generator.generate, request.user_story)

        # Save to file if requested
        file_path = None
        if request.output_file and result.success:
            output_dir = Path(request.output_file).parent
            filename = Path(request.output_file).name
            file_path = generator.save_feature(result, str(output_dir), filename)

        return FeatureGenerateResponse(
            success=result.success,
            feature_content=result.feature_content,
            feature_name=result.feature_name,
            scenario_count=result.scenario_count,
            file_path=file_path,
            error=result.error,
        )

    except Exception as e:
        return FeatureGenerateResponse(
            success=False,
            error=str(e),
        )


@router.post(
    "/generate/enhance",
    response_model=FeatureEnhanceResponse,
    tags=["Generation"],
    summary="Enhance an existing feature",
)
async def enhance_feature(request: FeatureEnhanceRequest):
    """
    Enhance an existing Gherkin feature with additional scenarios.
    """
    try:
        from app.generator import FeatureEnhancer

        enhancer = FeatureEnhancer()
        enhanced = await asyncio.to_thread(
            enhancer.enhance_feature,
            request.feature_content,
            add_negative=request.add_negative_cases,
            add_edge_cases=request.add_edge_cases,
            optimize_outlines=request.optimize_outlines,
        )

        # Count additions
        original_scenarios = request.feature_content.lower().count("scenario")
        new_scenarios = enhanced.lower().count("scenario")

        return FeatureEnhanceResponse(
            enhanced_content=enhanced,
            additions={"scenarios": new_scenarios - original_scenarios},
            suggestions=[],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate/analyze",
    tags=["Generation"],
    summary="Analyze a feature for improvements",
)
async def analyze_feature(feature_content: str):
    """
    Analyze a feature and get improvement suggestions.
    """
    try:
        from app.generator import FeatureEnhancer

        enhancer = FeatureEnhancer()
        analysis = await asyncio.to_thread(enhancer.analyze, feature_content)

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Results & History

@router.get(
    "/results",
    tags=["Results"],
    summary="Get test results",
)
async def get_results(
    status: Optional[str] = Query(None, description="Filter by status"),
    feature_file: Optional[str] = Query(None, description="Filter by feature file"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get historical test results with optional filtering.
    """
    try:
        from app.storage import TestResultRepository, TestStatus as StorageTestStatus

        repo = TestResultRepository()

        status_filter = None
        if status:
            status_filter = StorageTestStatus(status)

        results = repo.find(
            status=status_filter,
            feature_file=feature_file,
            limit=limit,
            offset=offset,
        )

        return {
            "results": [r.to_dict() for r in results],
            "total": len(results),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/results/{result_id}",
    tags=["Results"],
    summary="Get a specific test result",
)
async def get_result(result_id: str):
    """
    Get detailed test result by ID.
    """
    try:
        from app.storage import TestResultRepository

        repo = TestResultRepository()
        result = repo.get(result_id)

        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        return result.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/results/summary",
    response_model=ExecutionSummaryResponse,
    tags=["Results"],
    summary="Get execution summary",
)
async def get_summary(
    days: Optional[int] = Query(None, description="Number of days to include"),
    feature_file: Optional[str] = Query(None, description="Filter by feature file"),
):
    """
    Get aggregated execution statistics.
    """
    try:
        from app.storage import TestResultRepository

        repo = TestResultRepository()
        summary = repo.get_summary(days=days, feature_file=feature_file)

        return ExecutionSummaryResponse(
            total_runs=summary.total_runs,
            total_passed=summary.total_passed,
            total_failed=summary.total_failed,
            total_scenarios=summary.total_scenarios,
            average_duration_ms=summary.average_duration_ms,
            pass_rate=summary.pass_rate,
            last_run=summary.last_run,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Features Management

@router.get(
    "/features",
    response_model=FeatureListResponse,
    tags=["Features"],
    summary="List all features",
)
async def list_features(
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all registered features.
    """
    try:
        from app.storage import FeatureRepository

        repo = FeatureRepository()
        features = repo.find(source=source, limit=limit, offset=offset)

        return FeatureListResponse(
            features=[f.to_dict() for f in features],
            total=len(features),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/features/{feature_id}",
    response_model=FeatureDetailResponse,
    tags=["Features"],
    summary="Get feature details",
)
async def get_feature(feature_id: str):
    """
    Get detailed information about a feature.
    """
    try:
        from app.storage import FeatureRepository

        repo = FeatureRepository()
        feature = repo.get(feature_id)

        if not feature:
            raise HTTPException(status_code=404, detail="Feature not found")

        return FeatureDetailResponse(
            id=feature.id,
            name=feature.name,
            file_path=feature.file_path,
            content=feature.content,
            description=feature.description,
            tags=feature.tags,
            scenario_count=feature.scenario_count,
            source=feature.source,
            created_at=feature.created_at,
            updated_at=feature.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/features/import",
    tags=["Features"],
    summary="Import a feature file",
)
async def import_feature(file_path: str):
    """
    Import a feature file into the system.
    """
    try:
        from app.storage import FeatureRepository

        repo = FeatureRepository()
        feature = repo.import_from_file(file_path)

        return {
            "message": "Feature imported successfully",
            "feature_id": feature.id,
            "name": feature.name,
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Feature file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/features/sync",
    tags=["Features"],
    summary="Sync features from directory",
)
async def sync_features(
    directory: str,
    pattern: str = "**/*.feature",
):
    """
    Sync all features from a directory.
    """
    try:
        from app.storage import FeatureRepository

        repo = FeatureRepository()
        features = repo.sync_from_directory(directory, pattern)

        return {
            "message": f"Synced {len(features)} features",
            "features": [{"id": f.id, "name": f.name} for f in features],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/features/{feature_id}",
    tags=["Features"],
    summary="Delete a feature",
)
async def delete_feature(feature_id: str):
    """
    Delete a feature from the system.
    """
    try:
        from app.storage import FeatureRepository

        repo = FeatureRepository()
        deleted = repo.delete(feature_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Feature not found")

        return {"message": "Feature deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple Feature Save Endpoints

@router.post(
    "/features/save",
    tags=["Features"],
    summary="Save feature content to file",
)
async def save_feature_content(request: dict):
    """Save feature content directly to a file."""
    try:
        filename = request.get("filename", "test.feature")
        content = request.get("content", "")

        # Ensure filename ends with .feature
        if not filename.endswith(".feature"):
            filename += ".feature"

        # Save to features directory
        features_dir = Path("features")
        features_dir.mkdir(exist_ok=True)

        file_path = features_dir / filename
        file_path.write_text(content, encoding="utf-8")

        return {
            "message": "Feature saved successfully",
            "file_path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/features/save-temp",
    tags=["Features"],
    summary="Save feature content to temp file for execution",
)
async def save_temp_feature(request: dict):
    """Save feature content to the default execution file."""
    try:
        content = request.get("content", "")

        # Save to default feature file
        project_root = Path(__file__).parent.parent.parent
        file_path = project_root / "features/edit_compliance_single.feature"
        file_path.parent.mkdir(exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return {
            "message": "Feature saved for execution",
            "file_path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/features/read/{filename}",
    tags=["Features"],
    summary="Read feature file content",
)
async def read_feature_file(filename: str):
    """Read feature file content from disk."""
    try:
        project_root = Path(__file__).parent.parent.parent
        file_path = project_root / "features" / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Feature file not found")

        content = file_path.read_text(encoding="utf-8")

        return {
            "filename": filename,
            "content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
