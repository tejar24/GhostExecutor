"""
Ghost-QC API Module

REST API for remote test execution and management.
"""

from .server import create_app, run_server
from .routes import router
from .schemas import (
    TestRunRequest,
    TestRunResponse,
    FeatureGenerateRequest,
    FeatureGenerateResponse,
    TestResultResponse,
    HealthResponse,
)

__all__ = [
    # Server
    "create_app",
    "run_server",
    "router",
    # Schemas
    "TestRunRequest",
    "TestRunResponse",
    "FeatureGenerateRequest",
    "FeatureGenerateResponse",
    "TestResultResponse",
    "HealthResponse",
]
