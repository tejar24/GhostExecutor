"""
Repository Classes

High-level data access patterns for Ghost-QC storage.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .database import Database, get_database
from .models import (
    TestResult,
    ScenarioResult,
    StepResult,
    FeatureRecord,
    ExecutionSummary,
    TestStatus,
)


class TestResultRepository:
    """
    Repository for managing test results.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize repository.

        Args:
            database: Database instance (uses singleton if not provided)
        """
        self.db = database or get_database()

    def create(
        self,
        feature_name: str,
        feature_file: str,
        environment: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TestResult:
        """
        Create a new test result.

        Args:
            feature_name: Name of the feature
            feature_file: Path to feature file
            environment: Environment information
            metadata: Additional metadata

        Returns:
            New TestResult instance
        """
        return TestResult(
            id=str(uuid.uuid4()),
            feature_name=feature_name,
            feature_file=feature_file,
            status=TestStatus.PENDING,
            start_time=datetime.now(),
            environment=environment or {},
            metadata=metadata or {},
        )

    def save(self, result: TestResult) -> None:
        """
        Save a test result.

        Args:
            result: TestResult to save
        """
        self.db.save_test_result(result)

    def get(self, result_id: str) -> Optional[TestResult]:
        """
        Get a test result by ID.

        Args:
            result_id: Test result ID

        Returns:
            TestResult or None
        """
        return self.db.get_test_result(result_id)

    def find(
        self,
        status: Optional[TestStatus] = None,
        feature_file: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TestResult]:
        """
        Find test results with optional filters.

        Args:
            status: Filter by status
            feature_file: Filter by feature file
            limit: Maximum results
            offset: Results offset

        Returns:
            List of TestResult
        """
        return self.db.get_test_results(
            status=status,
            feature_file=feature_file,
            limit=limit,
            offset=offset,
        )

    def get_recent(self, days: int = 7, limit: int = 50) -> List[TestResult]:
        """
        Get recent test results.

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of TestResult
        """
        return self.db.get_recent_results(days=days, limit=limit)

    def delete(self, result_id: str) -> bool:
        """
        Delete a test result.

        Args:
            result_id: Test result ID

        Returns:
            True if deleted
        """
        return self.db.delete_test_result(result_id)

    def get_by_feature(
        self,
        feature_file: str,
        limit: int = 10,
    ) -> List[TestResult]:
        """
        Get results for a specific feature file.

        Args:
            feature_file: Feature file path
            limit: Maximum results

        Returns:
            List of TestResult
        """
        return self.db.get_test_results(
            feature_file=feature_file,
            limit=limit,
        )

    def get_failed(self, limit: int = 50) -> List[TestResult]:
        """
        Get failed test results.

        Args:
            limit: Maximum results

        Returns:
            List of failed TestResult
        """
        return self.db.get_test_results(
            status=TestStatus.FAILED,
            limit=limit,
        )

    def get_summary(
        self,
        days: Optional[int] = None,
        feature_file: Optional[str] = None,
    ) -> ExecutionSummary:
        """
        Get execution summary statistics.

        Args:
            days: Number of days to include
            feature_file: Filter by feature file

        Returns:
            ExecutionSummary
        """
        stats = self.db.get_execution_stats(
            days=days,
            feature_file=feature_file,
        )

        return ExecutionSummary(
            total_runs=stats["total_runs"],
            total_passed=stats["passed"],
            total_failed=stats["failed"],
            total_scenarios=stats["total_scenarios"],
            average_duration_ms=stats["average_duration_ms"],
            pass_rate=stats["pass_rate"],
            last_run=datetime.fromisoformat(stats["last_run"])
            if stats["last_run"] else None,
        )

    def cleanup(self, days: int = 30) -> int:
        """
        Clean up old test results.

        Args:
            days: Delete results older than this

        Returns:
            Number of deleted records
        """
        return self.db.cleanup_old_results(days=days)

    def finalize(
        self,
        result: TestResult,
        status: Optional[TestStatus] = None,
    ) -> TestResult:
        """
        Finalize a test result (set end time, calculate status).

        Args:
            result: TestResult to finalize
            status: Override status (auto-calculated if not provided)

        Returns:
            Updated TestResult
        """
        result.end_time = datetime.now()
        result.duration_ms = (
            result.end_time - result.start_time
        ).total_seconds() * 1000

        if status:
            result.status = status
        else:
            # Auto-calculate status based on scenarios
            if not result.scenarios:
                result.status = TestStatus.PENDING
            elif all(s.status == TestStatus.PASSED for s in result.scenarios):
                result.status = TestStatus.PASSED
            elif any(s.status == TestStatus.ERROR for s in result.scenarios):
                result.status = TestStatus.ERROR
            elif any(s.status == TestStatus.FAILED for s in result.scenarios):
                result.status = TestStatus.FAILED
            else:
                result.status = TestStatus.PASSED

        self.save(result)
        return result


class FeatureRepository:
    """
    Repository for managing feature records.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize repository.

        Args:
            database: Database instance (uses singleton if not provided)
        """
        self.db = database or get_database()

    def create(
        self,
        name: str,
        file_path: str,
        content: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: str = "manual",
        user_story: Optional[str] = None,
    ) -> FeatureRecord:
        """
        Create a new feature record.

        Args:
            name: Feature name
            file_path: Path to feature file
            content: Feature content (Gherkin)
            description: Feature description
            tags: Feature tags
            source: Source of feature (manual, generated, imported)
            user_story: Original user story if generated

        Returns:
            New FeatureRecord instance
        """
        # Count scenarios in content
        scenario_count = content.lower().count("scenario:")
        scenario_count += content.lower().count("scenario outline:")

        return FeatureRecord(
            id=str(uuid.uuid4()),
            name=name,
            file_path=file_path,
            content=content,
            description=description,
            tags=tags or [],
            scenario_count=scenario_count,
            source=source,
            user_story=user_story,
        )

    def save(self, feature: FeatureRecord) -> None:
        """
        Save a feature record.

        Args:
            feature: FeatureRecord to save
        """
        self.db.save_feature(feature)

    def get(self, feature_id: str) -> Optional[FeatureRecord]:
        """
        Get a feature by ID.

        Args:
            feature_id: Feature ID

        Returns:
            FeatureRecord or None
        """
        return self.db.get_feature(feature_id)

    def get_by_path(self, file_path: str) -> Optional[FeatureRecord]:
        """
        Get a feature by file path.

        Args:
            file_path: Feature file path

        Returns:
            FeatureRecord or None
        """
        return self.db.get_feature_by_path(file_path)

    def find(
        self,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[FeatureRecord]:
        """
        Find features with optional filters.

        Args:
            source: Filter by source
            limit: Maximum results
            offset: Results offset

        Returns:
            List of FeatureRecord
        """
        return self.db.get_features(
            source=source,
            limit=limit,
            offset=offset,
        )

    def delete(self, feature_id: str) -> bool:
        """
        Delete a feature.

        Args:
            feature_id: Feature ID

        Returns:
            True if deleted
        """
        return self.db.delete_feature(feature_id)

    def get_generated(self, limit: int = 50) -> List[FeatureRecord]:
        """
        Get AI-generated features.

        Args:
            limit: Maximum results

        Returns:
            List of generated FeatureRecord
        """
        return self.db.get_features(source="generated", limit=limit)

    def import_from_file(self, file_path: str) -> FeatureRecord:
        """
        Import a feature from a file.

        Args:
            file_path: Path to feature file

        Returns:
            Imported FeatureRecord
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Feature file not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        # Extract feature name from content
        name = path.stem
        for line in content.splitlines():
            if line.strip().startswith("Feature:"):
                name = line.strip()[8:].strip()
                break

        # Extract tags
        tags = []
        for line in content.splitlines():
            if line.strip().startswith("@"):
                tags.extend(
                    tag.strip()
                    for tag in line.strip().split()
                    if tag.startswith("@")
                )
            elif line.strip().startswith("Feature:"):
                break

        feature = self.create(
            name=name,
            file_path=str(path.absolute()),
            content=content,
            tags=tags,
            source="imported",
        )

        self.save(feature)
        return feature

    def export_to_file(
        self,
        feature: FeatureRecord,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export a feature to a file.

        Args:
            feature: FeatureRecord to export
            output_path: Output file path (uses original if not provided)

        Returns:
            Path to exported file
        """
        path = Path(output_path or feature.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(feature.content, encoding="utf-8")
        return str(path)

    def sync_from_directory(
        self,
        directory: str,
        pattern: str = "**/*.feature",
    ) -> List[FeatureRecord]:
        """
        Sync features from a directory.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for feature files

        Returns:
            List of synced FeatureRecord
        """
        dir_path = Path(directory)
        features = []

        for file_path in dir_path.glob(pattern):
            existing = self.get_by_path(str(file_path.absolute()))

            if existing:
                # Update if content changed
                current_content = file_path.read_text(encoding="utf-8")
                if current_content != existing.content:
                    existing.content = current_content
                    existing.updated_at = datetime.now()
                    self.save(existing)
                features.append(existing)
            else:
                # Import new feature
                feature = self.import_from_file(str(file_path))
                features.append(feature)

        return features
