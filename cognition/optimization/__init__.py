"""
Cognition Optimization Package

Performance and efficiency optimization.
"""

from cognition.optimization.performance import (
    BreakSuggestion,
    BreakType,
    EfficiencyMetrics,
    LoadLevel,
    OptimizationResult,
    PerformanceOptimizer,
    get_performance_optimizer,
)

__all__ = [
    "PerformanceOptimizer",
    "LoadLevel",
    "BreakType",
    "BreakSuggestion",
    "OptimizationResult",
    "EfficiencyMetrics",
    "get_performance_optimizer",
]
