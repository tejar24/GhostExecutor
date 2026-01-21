"""
Ghost-QC Storage Module

Provides persistence layer for test results, features, and execution history.
"""

from .models import (
    TestResult,
    ScenarioResult,
    StepResult,
    FeatureRecord,
    ExecutionSummary,
)
from .database import Database, get_database
from .repository import (
    TestResultRepository,
    FeatureRepository,
)

__all__ = [
    # Models
    "TestResult",
    "ScenarioResult",
    "StepResult",
    "FeatureRecord",
    "ExecutionSummary",
    # Database
    "Database",
    "get_database",
    # Repositories
    "TestResultRepository",
    "FeatureRepository",
]
