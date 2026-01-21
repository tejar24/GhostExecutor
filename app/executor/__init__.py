"""
Ghost QC Phase 2 - Autonomous Test Executor

This module provides AI-driven autonomous test execution capabilities.
It parses Gherkin feature files and executes steps without manual step definitions.
"""

from app.executor.runner import AutonomousTestRunner

__all__ = ["AutonomousTestRunner"]
