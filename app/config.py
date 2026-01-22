"""
Ghost-QC Configuration Module

Centralized configuration management with support for environment variables,
config files, and programmatic settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Look for .env file in project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use OS environment only


def _get_env(key: str, default: Any = None, cast: type = str) -> Any:
    """Get environment variable with type casting."""
    value = os.environ.get(key, default)
    if value is None:
        return default
    if cast == bool:
        return str(value).lower() in ("true", "1", "yes", "on")
    return cast(value)


@dataclass
class BrowserConfig:
    """Browser automation configuration."""
    headless: bool = True
    slow_mo: int = 100  # milliseconds
    viewport_width: int = 1366
    viewport_height: int = 768
    default_timeout: int = 30000  # milliseconds
    browser_type: str = "chromium"  # chromium, firefox, webkit
    screenshot_on_failure: bool = True
    video_recording: bool = False

    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """Create config from environment variables."""
        return cls(
            headless=_get_env("GHOST_QC_HEADLESS", True, bool),
            slow_mo=_get_env("GHOST_QC_SLOW_MO", 100, int),
            viewport_width=_get_env("GHOST_QC_VIEWPORT_WIDTH", 1366, int),
            viewport_height=_get_env("GHOST_QC_VIEWPORT_HEIGHT", 768, int),
            default_timeout=_get_env("GHOST_QC_TIMEOUT", 30000, int),
            browser_type=_get_env("GHOST_QC_BROWSER", "chromium"),
            screenshot_on_failure=_get_env("GHOST_QC_SCREENSHOT_ON_FAILURE", True, bool),
            video_recording=_get_env("GHOST_QC_VIDEO_RECORDING", False, bool),
        )


@dataclass
class AIConfig:
    """AI/Claude configuration."""
    timeout: int = 120  # seconds
    max_retries: int = 3
    model: str = "claude-3-sonnet"
    temperature: float = 0.7
    api_key: Optional[str] = None
    use_cli: bool = False  # Use Claude API by default (CLI not available on remote servers)

    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create config from environment variables."""
        return cls(
            timeout=_get_env("GHOST_QC_AI_TIMEOUT", 120, int),
            max_retries=_get_env("GHOST_QC_AI_RETRIES", 3, int),
            model=_get_env("GHOST_QC_AI_MODEL", "claude-3-sonnet"),
            temperature=_get_env("GHOST_QC_AI_TEMPERATURE", 0.7, float),
            api_key=_get_env("ANTHROPIC_API_KEY"),
            use_cli=_get_env("GHOST_QC_USE_CLI", False, bool),
        )


@dataclass
class StorageConfig:
    """Storage and database configuration."""
    database_path: str = "ghost_qc.db"
    reports_dir: str = "reports"
    screenshots_dir: str = "reports/screenshots"
    features_dir: str = "features"
    cleanup_days: int = 30

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Create config from environment variables."""
        return cls(
            database_path=_get_env("GHOST_QC_DATABASE", "ghost_qc.db"),
            reports_dir=_get_env("GHOST_QC_REPORTS_DIR", "reports"),
            screenshots_dir=_get_env("GHOST_QC_SCREENSHOTS_DIR", "reports/screenshots"),
            features_dir=_get_env("GHOST_QC_FEATURES_DIR", "features"),
            cleanup_days=_get_env("GHOST_QC_CLEANUP_DAYS", 30, int),
        )


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    base_url: str = "http://192.168.0.31:8000"  # Base URL for API
    api_prefix: str = "/api/v1"  # API route prefix
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://192.168.0.31:8000",
        "http://192.168.0.31:3000",
        "*",  # Allow all origins for development
    ])

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create config from environment variables."""
        origins_str = _get_env("GHOST_QC_CORS_ORIGINS", "")
        origins = origins_str.split(",") if origins_str else []

        return cls(
            host=_get_env("GHOST_QC_API_HOST", "0.0.0.0"),
            port=_get_env("GHOST_QC_API_PORT", 8000, int),
            workers=_get_env("GHOST_QC_API_WORKERS", 1, int),
            reload=_get_env("GHOST_QC_API_RELOAD", False, bool),
            base_url=_get_env("GHOST_QC_API_BASE_URL", "http://192.168.0.31:8000"),
            api_prefix=_get_env("GHOST_QC_API_PREFIX", "/api/v1"),
            cors_origins=origins or [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://192.168.0.31:8000",
                "http://192.168.0.31:3000",
                "*",
            ],
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create config from environment variables."""
        return cls(
            level=_get_env("GHOST_QC_LOG_LEVEL", "INFO"),
            file=_get_env("GHOST_QC_LOG_FILE"),
            format=_get_env(
                "GHOST_QC_LOG_FORMAT",
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            ),
        )


@dataclass
class Config:
    """Main configuration container."""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Project settings
    project_root: str = "."
    environment: str = "development"

    @classmethod
    def from_env(cls) -> "Config":
        """Create full config from environment variables."""
        return cls(
            browser=BrowserConfig.from_env(),
            ai=AIConfig.from_env(),
            storage=StorageConfig.from_env(),
            api=APIConfig.from_env(),
            logging=LoggingConfig.from_env(),
            project_root=_get_env("GHOST_QC_PROJECT_ROOT", "."),
            environment=_get_env("GHOST_QC_ENV", "development"),
        )

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Config":
        """Load config from a JSON file."""
        file_path = Path(path)

        if not file_path.exists():
            return cls()

        with open(file_path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from a dictionary."""
        config = cls()

        if "browser" in data:
            config.browser = BrowserConfig(**data["browser"])
        if "ai" in data:
            config.ai = AIConfig(**data["ai"])
        if "storage" in data:
            config.storage = StorageConfig(**data["storage"])
        if "api" in data:
            config.api = APIConfig(**data["api"])
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])
        if "project_root" in data:
            config.project_root = data["project_root"]
        if "environment" in data:
            config.environment = data["environment"]

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "browser": {
                "headless": self.browser.headless,
                "slow_mo": self.browser.slow_mo,
                "viewport_width": self.browser.viewport_width,
                "viewport_height": self.browser.viewport_height,
                "default_timeout": self.browser.default_timeout,
                "browser_type": self.browser.browser_type,
                "screenshot_on_failure": self.browser.screenshot_on_failure,
                "video_recording": self.browser.video_recording,
            },
            "ai": {
                "timeout": self.ai.timeout,
                "max_retries": self.ai.max_retries,
                "model": self.ai.model,
                "temperature": self.ai.temperature,
                "use_cli": self.ai.use_cli,
            },
            "storage": {
                "database_path": self.storage.database_path,
                "reports_dir": self.storage.reports_dir,
                "screenshots_dir": self.storage.screenshots_dir,
                "features_dir": self.storage.features_dir,
                "cleanup_days": self.storage.cleanup_days,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "workers": self.api.workers,
                "reload": self.api.reload,
                "base_url": self.api.base_url,
                "api_prefix": self.api.api_prefix,
                "cors_origins": self.api.cors_origins,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "format": self.logging.format,
            },
            "project_root": self.project_root,
            "environment": self.environment,
        }

    def save(self, path: Union[str, Path]) -> None:
        """Save config to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def merge(self, other: "Config") -> "Config":
        """Merge another config into this one (other takes precedence)."""
        merged_dict = self.to_dict()
        other_dict = other.to_dict()

        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif value is not None:
                    result[key] = value
            return result

        return Config.from_dict(deep_merge(merged_dict, other_dict))


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = load_config()

    return _config_instance


def load_config(
    config_file: Optional[str] = None,
    use_env: bool = True,
) -> Config:
    """
    Load configuration from file and/or environment.

    Args:
        config_file: Path to config file (JSON)
        use_env: Also load from environment variables

    Returns:
        Loaded Config instance
    """
    global _config_instance

    # Start with defaults
    config = Config()

    # Load from file if exists
    config_paths = [
        config_file,
        "ghost-qc.json",
        "ghost_qc.json",
        ".ghost-qc.json",
        "config/ghost-qc.json",
    ]

    for path in config_paths:
        if path and Path(path).exists():
            file_config = Config.from_file(path)
            config = config.merge(file_config)
            break

    # Override with environment variables
    if use_env:
        env_config = Config.from_env()
        config = config.merge(env_config)

    _config_instance = config
    return config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config_instance
    _config_instance = None


# Environment variable template for reference
ENV_TEMPLATE = """
# Ghost-QC Configuration Environment Variables

# Browser Settings
GHOST_QC_HEADLESS=true
GHOST_QC_SLOW_MO=100
GHOST_QC_VIEWPORT_WIDTH=1366
GHOST_QC_VIEWPORT_HEIGHT=768
GHOST_QC_TIMEOUT=30000
GHOST_QC_BROWSER=chromium
GHOST_QC_SCREENSHOT_ON_FAILURE=true
GHOST_QC_VIDEO_RECORDING=false

# AI Settings
GHOST_QC_AI_TIMEOUT=120
GHOST_QC_AI_RETRIES=3
GHOST_QC_AI_MODEL=claude-3-sonnet
GHOST_QC_AI_TEMPERATURE=0.7
GHOST_QC_USE_CLI=false
ANTHROPIC_API_KEY=your-api-key-here

# Storage Settings
GHOST_QC_DATABASE=ghost_qc.db
GHOST_QC_REPORTS_DIR=reports
GHOST_QC_SCREENSHOTS_DIR=reports/screenshots
GHOST_QC_FEATURES_DIR=features
GHOST_QC_CLEANUP_DAYS=30

# API Settings
GHOST_QC_API_HOST=0.0.0.0
GHOST_QC_API_PORT=8000
GHOST_QC_API_WORKERS=1
GHOST_QC_API_RELOAD=false
GHOST_QC_API_BASE_URL=http://192.168.0.31:8000
GHOST_QC_API_PREFIX=/api/v1
GHOST_QC_CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://192.168.0.31:8000

# Logging Settings
GHOST_QC_LOG_LEVEL=INFO
GHOST_QC_LOG_FILE=

# Project Settings
GHOST_QC_PROJECT_ROOT=.
GHOST_QC_ENV=development
"""


def generate_env_file(path: str = ".env.example") -> str:
    """
    Generate an example environment file.

    Args:
        path: Output file path

    Returns:
        Path to generated file
    """
    file_path = Path(path)
    file_path.write_text(ENV_TEMPLATE.strip())
    return str(file_path)


def generate_config_file(path: str = "ghost-qc.json") -> str:
    """
    Generate an example config file.

    Args:
        path: Output file path

    Returns:
        Path to generated file
    """
    config = Config()
    config.save(path)
    return path
