"""
UI Brain Module

AI-driven DOM analysis and element intelligence for autonomous test execution.
Provides tool-independent element discovery, classification, and self-healing
capabilities for reliable test automation.
"""

from app.brain.ui_brain import UIBrain, PageBrain, ElementDescriptor
from app.brain.element_classifier import ElementClassifier, SelectorCandidate
from app.brain.page_store import PageBrainStore
from app.brain.brain_interpreter import BrainInterpreter, ElementResolution

__all__ = [
    "UIBrain",
    "PageBrain",
    "ElementDescriptor",
    "ElementClassifier",
    "SelectorCandidate",
    "PageBrainStore",
    "BrainInterpreter",
    "ElementResolution"
]
