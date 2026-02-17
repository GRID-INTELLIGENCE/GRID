"""
Cognition Explainability Package

XAI (Explainable AI) for cognitive decisions.
"""

from cognition.explainability.explainer import (
    CognitiveExplainer,
    Explanation,
    ExplanationCategory,
    ExplanationFactor,
    ExplanationLevel,
    get_cognitive_explainer,
)

__all__ = [
    "CognitiveExplainer",
    "Explanation",
    "ExplanationFactor",
    "ExplanationLevel",
    "ExplanationCategory",
    "get_cognitive_explainer",
]
