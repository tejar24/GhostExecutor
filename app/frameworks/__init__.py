"""
UI Framework and Component Library Registry

Provides framework-aware element identification for autonomous test execution.
"""

from .registry import FrameworkRegistry, ComponentLibrary, Component
from .config import FrameworkConfig, load_config

__all__ = [
    'FrameworkRegistry',
    'ComponentLibrary',
    'Component',
    'FrameworkConfig',
    'load_config'
]
