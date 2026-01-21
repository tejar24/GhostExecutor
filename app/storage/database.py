"""
Database Module

Provides SQLite-based persistence for Ghost-QC data.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from .models import TestResult, FeatureRecord, TestStatus


# Singleton database instance
_database_instance: Optional["Database"] = None


def get_database(db_path: Optional[str] = None) -> "Database":
    """
    Get the database singleton instance.

    Args:
        db_path: Optional database file path

    Returns:
        Database instance
    """
    global _database_instance

    if _database_instance is None:
        _database_instance = Database(db_path)

    return _database_instance


class Database:
    """
    SQLite database for storing test results and features.
    """

    DEFAULT_DB_PATH = "ghost_qc.db"

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        with self._connection() as conn:
            cursor = conn.cursor()

            # Test results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id TEXT PRIMARY KEY,
                    feature_name TEXT NOT NULL,
                    feature_file TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL DEFAULT 0,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    environment TEXT,
                    metadata TEXT,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Scenarios table (for querying)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_result_id TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL DEFAULT 0,
                    step_count INTEGER DEFAULT 0,
                    passed_steps INTEGER DEFAULT 0,
                    failed_steps INTEGER DEFAULT 0,
                    timestamp TEXT,
                    FOREIGN KEY (test_result_id) REFERENCES test_results(id)
                )
            """)

            # Features table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    file_path TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    scenario_count INTEGER DEFAULT 0,
                    source TEXT,
                    user_story TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Execution history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_result_id TEXT NOT NULL,
                    feature_file TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_ms REAL DEFAULT 0,
                    scenarios_total INTEGER DEFAULT 0,
                    scenarios_passed INTEGER DEFAULT 0,
                    scenarios_failed INTEGER DEFAULT 0,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_result_id) REFERENCES test_results(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_results_status
                ON test_results(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_results_start_time
                ON test_results(start_time)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_features_name
                ON features(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_history_date
                ON execution_history(executed_at)
            """)

    # Test Results Methods

    def save_test_result(self, result: TestResult) -> None:
        """
        Save a test result to the database.

        Args:
            result: TestResult to save
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            # Insert main result
            cursor.execute("""
                INSERT OR REPLACE INTO test_results
                (id, feature_name, feature_file, status, duration_ms,
                 start_time, end_time, environment, metadata, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id,
                result.feature_name,
                result.feature_file,
                result.status.value,
                result.duration_ms,
                result.start_time.isoformat(),
                result.end_time.isoformat() if result.end_time else None,
                json.dumps(result.environment),
                json.dumps(result.metadata),
                result.to_json(),
            ))

            # Delete old scenarios for this result
            cursor.execute(
                "DELETE FROM scenarios WHERE test_result_id = ?",
                (result.id,)
            )

            # Insert scenarios
            for scenario in result.scenarios:
                cursor.execute("""
                    INSERT INTO scenarios
                    (test_result_id, scenario_name, status, duration_ms,
                     step_count, passed_steps, failed_steps, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    scenario.scenario_name,
                    scenario.status.value,
                    scenario.duration_ms,
                    len(scenario.steps),
                    scenario.passed_steps,
                    scenario.failed_steps,
                    scenario.timestamp.isoformat(),
                ))

            # Add to execution history
            cursor.execute("""
                INSERT INTO execution_history
                (test_result_id, feature_file, status, duration_ms,
                 scenarios_total, scenarios_passed, scenarios_failed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id,
                result.feature_file,
                result.status.value,
                result.duration_ms,
                result.total_scenarios,
                result.passed_scenarios,
                result.failed_scenarios,
            ))

    def get_test_result(self, result_id: str) -> Optional[TestResult]:
        """
        Get a test result by ID.

        Args:
            result_id: Test result ID

        Returns:
            TestResult or None
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM test_results WHERE id = ?",
                (result_id,)
            )
            row = cursor.fetchone()

            if row:
                return TestResult.from_json(row["data"])
            return None

    def get_test_results(
        self,
        status: Optional[TestStatus] = None,
        feature_file: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "start_time DESC",
    ) -> List[TestResult]:
        """
        Get test results with optional filtering.

        Args:
            status: Filter by status
            feature_file: Filter by feature file
            limit: Maximum results to return
            offset: Results offset
            order_by: Sort order

        Returns:
            List of TestResult
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            query = "SELECT data FROM test_results WHERE 1=1"
            params: List[Any] = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if feature_file:
                query += " AND feature_file = ?"
                params.append(feature_file)

            query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [TestResult.from_json(row["data"]) for row in rows]

    def get_recent_results(self, days: int = 7, limit: int = 50) -> List[TestResult]:
        """
        Get recent test results.

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of TestResult
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM test_results
                WHERE datetime(start_time) >= datetime('now', ?)
                ORDER BY start_time DESC
                LIMIT ?
            """, (f"-{days} days", limit))

            rows = cursor.fetchall()
            return [TestResult.from_json(row["data"]) for row in rows]

    def delete_test_result(self, result_id: str) -> bool:
        """
        Delete a test result.

        Args:
            result_id: Test result ID

        Returns:
            True if deleted
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scenarios WHERE test_result_id = ?", (result_id,))
            cursor.execute("DELETE FROM test_results WHERE id = ?", (result_id,))
            return cursor.rowcount > 0

    # Feature Methods

    def save_feature(self, feature: FeatureRecord) -> None:
        """
        Save a feature record.

        Args:
            feature: FeatureRecord to save
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO features
                (id, name, file_path, content, description, tags,
                 scenario_count, source, user_story, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature.id,
                feature.name,
                feature.file_path,
                feature.content,
                feature.description,
                json.dumps(feature.tags),
                feature.scenario_count,
                feature.source,
                feature.user_story,
                feature.created_at.isoformat(),
                datetime.now().isoformat(),
            ))

    def get_feature(self, feature_id: str) -> Optional[FeatureRecord]:
        """
        Get a feature by ID.

        Args:
            feature_id: Feature ID

        Returns:
            FeatureRecord or None
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM features WHERE id = ?", (feature_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_feature(row)
            return None

    def get_feature_by_path(self, file_path: str) -> Optional[FeatureRecord]:
        """
        Get a feature by file path.

        Args:
            file_path: Feature file path

        Returns:
            FeatureRecord or None
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM features WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()

            if row:
                return self._row_to_feature(row)
            return None

    def get_features(
        self,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[FeatureRecord]:
        """
        Get features with optional filtering.

        Args:
            source: Filter by source
            limit: Maximum results
            offset: Results offset

        Returns:
            List of FeatureRecord
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM features WHERE 1=1"
            params: List[Any] = []

            if source:
                query += " AND source = ?"
                params.append(source)

            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_feature(row) for row in rows]

    def delete_feature(self, feature_id: str) -> bool:
        """
        Delete a feature.

        Args:
            feature_id: Feature ID

        Returns:
            True if deleted
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM features WHERE id = ?", (feature_id,))
            return cursor.rowcount > 0

    def _row_to_feature(self, row: sqlite3.Row) -> FeatureRecord:
        """Convert database row to FeatureRecord."""
        return FeatureRecord(
            id=row["id"],
            name=row["name"],
            file_path=row["file_path"],
            content=row["content"],
            description=row["description"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            scenario_count=row["scenario_count"],
            source=row["source"],
            user_story=row["user_story"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # Statistics Methods

    def get_execution_stats(
        self,
        days: Optional[int] = None,
        feature_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get execution statistics.

        Args:
            days: Number of days to include
            feature_file: Filter by feature file

        Returns:
            Statistics dictionary
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            where_clauses = ["1=1"]
            params: List[Any] = []

            if days:
                where_clauses.append("datetime(executed_at) >= datetime('now', ?)")
                params.append(f"-{days} days")

            if feature_file:
                where_clauses.append("feature_file = ?")
                params.append(feature_file)

            where_sql = " AND ".join(where_clauses)

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(scenarios_total) as total_scenarios,
                    SUM(scenarios_passed) as passed_scenarios,
                    AVG(duration_ms) as avg_duration,
                    MIN(executed_at) as first_run,
                    MAX(executed_at) as last_run
                FROM execution_history
                WHERE {where_sql}
            """, params)

            row = cursor.fetchone()

            total_runs = row["total_runs"] or 0
            passed = row["passed"] or 0

            return {
                "total_runs": total_runs,
                "passed": passed,
                "failed": row["failed"] or 0,
                "pass_rate": (passed / total_runs * 100) if total_runs > 0 else 0.0,
                "total_scenarios": row["total_scenarios"] or 0,
                "passed_scenarios": row["passed_scenarios"] or 0,
                "average_duration_ms": row["avg_duration"] or 0.0,
                "first_run": row["first_run"],
                "last_run": row["last_run"],
            }

    def cleanup_old_results(self, days: int = 30) -> int:
        """
        Delete test results older than specified days.

        Args:
            days: Delete results older than this

        Returns:
            Number of deleted records
        """
        with self._connection() as conn:
            cursor = conn.cursor()

            # Get IDs to delete
            cursor.execute("""
                SELECT id FROM test_results
                WHERE datetime(start_time) < datetime('now', ?)
            """, (f"-{days} days",))

            ids = [row["id"] for row in cursor.fetchall()]

            if not ids:
                return 0

            # Delete scenarios
            placeholders = ",".join("?" * len(ids))
            cursor.execute(
                f"DELETE FROM scenarios WHERE test_result_id IN ({placeholders})",
                ids
            )

            # Delete results
            cursor.execute(
                f"DELETE FROM test_results WHERE id IN ({placeholders})",
                ids
            )

            # Delete history
            cursor.execute(
                f"DELETE FROM execution_history WHERE test_result_id IN ({placeholders})",
                ids
            )

            return len(ids)
