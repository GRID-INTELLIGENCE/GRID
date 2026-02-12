"""
Workspace Utilities Package

Unified package for workspace utility scripts including:
- Repository analysis
- Project comparison
- Entity classification
- EUFLE verification
"""

from .repo_analyzer import RepositoryAnalyzer
from .project_comparator import ProjectComparator
from .entity_classifier import Entity, Category, Attribute, SignalClassification
from .eufle_verifier import EUFLEVerifier

__version__ = "1.0.0"
__all__ = [
    "RepositoryAnalyzer",
    "ProjectComparator",
    "Entity",
    "Category",
    "Attribute",
    "SignalClassification",
    "EUFLEVerifier",
]