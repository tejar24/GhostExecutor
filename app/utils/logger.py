"""
Logging Configuration Module

Provides consistent logging setup across the Ghost-QC application.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Custom log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Color codes for console output
COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",      # Reset
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""

    def format(self, record: logging.LogRecord) -> str:
        # Add color if outputting to terminal
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            color = COLORS.get(record.levelname, COLORS["RESET"])
            record.levelname = f"{color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> None:
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level (default: INFO)
        log_file: Specific log file path (optional)
        log_dir: Directory to store log files (optional)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File handler if log file is specified
    if log_file or log_dir:
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = str(log_path / f"ghost_qc_{timestamp}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Ensure at least basic console handler exists
    if not logging.getLogger().handlers:
        setup_logging()

    return logger


class LogContext:
    """Context manager for temporary log level changes."""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.new_level = level
        self.original_level = logger.level

    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)
        return False


class StepLogger:
    """Helper class for logging test step execution."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.step_count = 0

    def log_step_start(self, step_text: str) -> None:
        """Log the start of a test step."""
        self.step_count += 1
        self.logger.info(f"Step {self.step_count}: {step_text}")

    def log_step_success(self, step_text: str, duration_ms: float) -> None:
        """Log successful step completion."""
        self.logger.info(f"  ✓ Passed ({duration_ms:.0f}ms)")

    def log_step_failure(self, step_text: str, error: str) -> None:
        """Log step failure."""
        self.logger.error(f"  ✗ Failed: {error}")

    def log_step_skip(self, step_text: str, reason: str) -> None:
        """Log skipped step."""
        self.logger.warning(f"  ○ Skipped: {reason}")

    def reset(self) -> None:
        """Reset step counter for new scenario."""
        self.step_count = 0
