"""
Framework and Component Library Registry
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Component:
    """Defines a UI component and how to identify/interact with it."""
    name: str  # e.g., "Button", "TextField", "Select"
    selectors: List[str]  # CSS selectors to find this component
    attributes: List[str]  # Data attributes to look for
    actions: Dict[str, str]  # action_name -> playwright method
    child_selectors: Dict[str, str] = field(default_factory=dict)  # For nested elements


@dataclass
class ComponentLibrary:
    """Defines a component library (MUI, Ant Design, etc.)."""
    name: str
    base_framework: str  # react, angular, vue
    prefix: str  # CSS class prefix (e.g., "Mui", "ant")
    components: Dict[str, Component] = field(default_factory=dict)

    def get_component(self, name: str) -> Optional[Component]:
        return self.components.get(name.lower())


class FrameworkRegistry:
    """Central registry for all frameworks and component libraries."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._libraries = {}
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        """Load all component library definitions."""
        if self._initialized:
            return

        from .components import mui, antd, bootstrap, primereact, chakra

        self.register_library(mui.get_library())
        self.register_library(antd.get_library())
        self.register_library(bootstrap.get_library())
        self.register_library(primereact.get_library())
        self.register_library(chakra.get_library())

        self._initialized = True

    def register_library(self, library: ComponentLibrary):
        """Register a component library."""
        self._libraries[library.name.lower()] = library

    def get_library(self, name: str) -> Optional[ComponentLibrary]:
        """Get a component library by name."""
        return self._libraries.get(name.lower())

    def list_libraries(self) -> List[str]:
        """List all registered libraries."""
        return list(self._libraries.keys())

    def get_libraries_for_framework(self, framework: str) -> List[ComponentLibrary]:
        """Get all libraries for a base framework (react, angular, vue)."""
        return [lib for lib in self._libraries.values()
                if lib.base_framework.lower() == framework.lower()]
