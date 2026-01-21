"""
UI Component Library Definitions

This package contains selector and interaction definitions for popular
component libraries to improve AI-driven test automation accuracy.
"""

from .mui import get_library as get_mui_library
from .antd import get_library as get_antd_library
from .bootstrap import get_library as get_bootstrap_library
from .primereact import get_library as get_primereact_library
from .chakra import get_library as get_chakra_library

__all__ = [
    "get_mui_library",
    "get_antd_library",
    "get_bootstrap_library",
    "get_primereact_library",
    "get_chakra_library",
]
