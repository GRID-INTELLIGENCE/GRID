"""
Guardrail System - Module Personality Profiler & Boundary Enforcer

A comprehensive system that characterizes module "personalities" and enforces
boundaries to prevent compile-but-fail-at-runtime patterns.
"""

from .profiler.module_profiler import (
    ModuleProfiler,
    ModulePersonality,
    PersonalityTone,
    PersonalityStyle,
    PersonalityNuance,
    analyze_module,
    analyze_package,
)

from .middleware.personality_guardrails import (
    GuardrailMiddleware,
    GuardrailViolation,
    PersonalityGuardrail,
    get_middleware,
    initialize_guardrails,
    guardrail_check,
    GuardrailContext,
)

from .events.guardrail_events import (
    GuardrailEventTypes,
    GuardrailEvent,
    GuardrailEventPublisher,
    GuardrailEventAnalyzer,
    connect_guardrail_events,
    get_guardrail_analytics,
    setup_realtime_monitoring,
)

from .learning.adaptive_engine import (
    AdaptiveEngine,
    ViolationPattern,
    ModuleCluster,
    PatternExtractor,
    RuleGenerator,
    QCurveProfile,
    QCurveBand,
    get_adaptive_engine,
    learn_from_violation,
    get_module_recommendations,
    get_q_curve_profile,
)

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__all__ = [
    # Profiler
    "ModuleProfiler",
    "ModulePersonality",
    "PersonalityTone",
    "PersonalityStyle",
    "PersonalityNuance",
    "analyze_module",
    "analyze_package",
    
    # Middleware
    "GuardrailMiddleware",
    "GuardrailViolation",
    "PersonalityGuardrail",
    "get_middleware",
    "initialize_guardrails",
    "guardrail_check",
    "GuardrailContext",
    
    # Events
    "GuardrailEventTypes",
    "GuardrailEvent",
    "GuardrailEventPublisher",
    "GuardrailEventAnalyzer",
    "connect_guardrail_events",
    "get_guardrail_analytics",
    "setup_realtime_monitoring",
    
    # Learning
    "AdaptiveEngine",
    "ViolationPattern",
    "ModuleCluster",
    "PatternExtractor",
    "RuleGenerator",
    "QCurveProfile",
    "QCurveBand",
    "get_adaptive_engine",
    "learn_from_violation",
    "get_module_recommendations",
    "get_q_curve_profile",
]


class GuardrailSystem:
    """Main orchestrator for the guardrail system."""
    
    def __init__(self, root_path: str, mode: str = "observer"):
        """
        Initialize the guardrail system.
        
        Args:
            root_path: Root path of the codebase to analyze
            mode: "observer", "warning", "enforcement", or "adaptive"
        """
        self.root_path = root_path
        self.mode = mode
        
        # Initialize components
        self.profiler = ModuleProfiler(root_path)
        self.middleware = GuardrailMiddleware(mode)
        self.adaptive_engine = AdaptiveEngine()
        
        # Event integration
        self.event_publisher = None
        self.event_analyzer = None
        
        # System state
        self.initialized = False
        self.stats = {
            "modules_analyzed": 0,
            "violations_detected": 0,
            "rules_generated": 0,
            "recommendations_made": 0,
        }
        
    def initialize(self) -> None:
        """Initialize the guardrail system."""
        logger.info(f"Initializing guardrail system for {self.root_path}")
        
        # Analyze the codebase
        personalities = self.profiler.analyze_package(self.root_path)
        self.stats["modules_analyzed"] = len(personalities)
        
        # Register guardrails
        for name, personality in personalities.items():
            guardrail = PersonalityGuardrail(personality)
            self.middleware.guardrails[name] = guardrail
            
        # Connect events
        self.event_publisher = connect_guardrail_events()
        self.event_analyzer = GuardrailEventAnalyzer()
        
        # Publish personality events
        for personality in personalities.values():
            self.event_publisher.publish_personality_analysis(personality)
            
        # Install import hook if not in observer mode
        if self.mode != "observer":
            self.middleware.install_import_hook()
            
        self.initialized = True
        logger.info(f"Guardrail system initialized with {len(personalities)} modules")
        
    def check_module(self, module_name: str) -> Dict[str, Any]:
        """Check a module for violations and return results."""
        if not self.initialized:
            raise RuntimeError("Guardrail system not initialized")

        resolved_name = module_name
        personality = self.profiler.get_personality(resolved_name)
        if personality is None and "." in module_name:
            candidate = module_name.split(".", 1)[1]
            personality = self.profiler.get_personality(candidate)
            if personality is not None:
                resolved_name = candidate
        if personality:
            module_data = {
                "is_path_dependent": personality.is_path_dependent,
                "is_runtime_fragile": personality.is_runtime_fragile,
                "is_circular_prone": personality.is_circular_prone,
                "is_import_heavy": personality.is_import_heavy,
                "has_side_effects": personality.has_side_effects,
                "is_stateful": personality.is_stateful,
                "hardcoded_paths": len(personality.hardcoded_paths),
                "conditional_imports": len(personality.conditional_imports),
                "import_count": personality.import_count,
                "line_count": personality.line_count,
            }
            q_curve_profile = get_q_curve_profile(module_name, module_data)
        else:
            module_data = {}
            q_curve_profile = None

        effective_mode = self.mode
        if self.mode == "adaptive" and q_curve_profile is not None:
            effective_mode = self._map_q_curve_band_to_mode(q_curve_profile.band)

        # Check for violations
        original_mode = self.middleware.mode
        self.middleware.mode = effective_mode
        violations = self.middleware.check_module(resolved_name)
        self.middleware.mode = original_mode
        self.stats["violations_detected"] += len(violations)
        
        # Publish violations
        for violation in violations:
            self.event_publisher.publish_violation(violation)
            
            # Learn from violation
            learn_from_violation({
                "type": violation.violation_type,
                "module": violation.module,
                "severity": violation.severity,
                "message": str(violation),
            })
            
        # Get recommendations
        if personality:
            recommendations = get_module_recommendations(
                module_name,
                {
                    "has_hardcoded_paths": personality.is_path_dependent,
                    "is_circular_prone": personality.is_circular_prone,
                    "has_conditional_imports": len(personality.conditional_imports) > 0,
                }
            )
            self.stats["recommendations_made"] += len(recommendations)
        else:
            recommendations = []
            
        return {
            "module": module_name,
            "violations": violations,
            "recommendations": recommendations,
            "personality": personality,
            "q_curve_profile": self._serialize_q_curve_profile(q_curve_profile),
        }
        
    def get_system_report(self) -> Dict[str, Any]:
        """Generate a comprehensive system report."""
        if not self.initialized:
            return {"error": "System not initialized"}
            
        # Get profiler report
        profiler_report = self.profiler.generate_report()
        
        # Get middleware summary
        middleware_summary = self.middleware.get_violations_summary()
        
        # Get learning summary
        learning_summary = self.adaptive_engine.get_learning_summary()
        
        # Get event analytics
        event_analytics = get_guardrail_analytics()
        
        return {
            "stats": self.stats,
            "profiler": profiler_report,
            "middleware": middleware_summary,
            "learning": learning_summary,
            "events": event_analytics,
            "mode": self.mode,
            "initialized_at": datetime.now(timezone.utc).isoformat(),
        }
        
    def get_risky_modules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get modules with highest risk scores."""
        if not self.initialized:
            return []
            
        risky = self.profiler._get_riskiest_modules(limit)
        
        # Add violation counts
        for module in risky:
            guardrail = self.middleware.get_guardrail(module["module"])
            if guardrail:
                module["violations_count"] = len(guardrail.violations)
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                recent = 0
                for violation in guardrail.violations:
                    data = getattr(violation, "data", None)
                    if not isinstance(data, dict):
                        continue
                    timestamp = data.get("timestamp")
                    if not timestamp:
                        continue
                    try:
                        occurred_at = datetime.fromisoformat(timestamp)
                        if occurred_at.tzinfo is None:
                            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                    if occurred_at > cutoff:
                        recent += 1
                module["recent_violations"] = recent
                
        return risky
        
    def update_mode(self, new_mode: str) -> None:
        """Update the operating mode."""
        self.mode = new_mode
        self.middleware.mode = new_mode
        
        if new_mode != "observer" and not self.middleware._has_import_hook():
            self.middleware.install_import_hook()
        elif new_mode == "observer" and self.middleware._has_import_hook():
            self.middleware.uninstall_import_hook()
            
        logger.info(f"Updated guardrail mode to: {new_mode}")

    def _map_q_curve_band_to_mode(self, band: QCurveBand) -> str:
        """Map Q-curve bands to guardrail operating modes."""
        if band == QCurveBand.H3:
            return "enforcement"
        if band == QCurveBand.H2:
            return "warning"
        return "observer"

    def _serialize_q_curve_profile(self, profile: Optional[QCurveProfile]) -> Optional[Dict[str, Any]]:
        """Serialize Q-curve profile for reporting."""
        if profile is None:
            return None
        return {
            "module": profile.module,
            "score": profile.score,
            "band": profile.band.value,
            "leading_signals": profile.leading_signals,
            "lagging_signals": profile.lagging_signals,
            "updated_at": profile.updated_at.isoformat(),
        }
        
    def shutdown(self) -> None:
        """Shutdown the guardrail system."""
        if self.middleware._has_import_hook():
            self.middleware.uninstall_import_hook()
            
        # Save learning data
        self.adaptive_engine._save_learning_data()
        
        logger.info("Guardrail system shutdown")


# Convenience function for quick setup
def setup_guardrails(root_path: str, mode: str = "observer") -> GuardrailSystem:
    """Quick setup of the guardrail system."""
    system = GuardrailSystem(root_path, mode)
    system.initialize()
    return system


# Import datetime for timestamp calculations
from datetime import datetime, timedelta, timezone
