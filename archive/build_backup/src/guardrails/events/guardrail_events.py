"""
Guardrail Event Integration

Connects the guardrail system with the UnifiedEventBus for real-time monitoring
and analysis of guardrail violations and module behaviors.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import logging

try:
    from grid.events.core import Event, EventPriority
    from grid.events.unified import get_unified_bus
    _HAS_GRID_EVENTS = True
except ImportError:
    _HAS_GRID_EVENTS = False

    class EventPriority:
        """Stub when grid.events is unavailable."""
        NORMAL = "normal"
        HIGH = "high"
        CRITICAL = "critical"
        LOW = "low"

    class Event:
        """Stub Event when grid.events is unavailable."""
        def __init__(self, event_type: str = "", data: Any = None,
                     priority: Any = None, source: str = "", **kwargs):
            self.event_type = event_type
            self.data = data or {}
            self.priority = priority or EventPriority.NORMAL
            self.source = source
            self.timestamp = datetime.now(timezone.utc)
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _StubBus:
        """Stub event bus when grid.events is unavailable."""
        def __init__(self):
            self._history: List[Any] = []
            self._subscribers: Dict[str, List[Any]] = {}

        def emit(self, event: Any) -> None:
            self._history.append(event)
            # Notify matching subscribers
            for pattern, callbacks in self._subscribers.items():
                evt_type = getattr(event, 'event_type', '')
                if pattern == '*' or pattern.rstrip('*') in evt_type:
                    for cb in callbacks:
                        try:
                            cb(event)
                        except Exception:
                            pass

        def publish(self, event: Any) -> None:
            self.emit(event)

        def subscribe(self, pattern: str, callback: Any) -> None:
            self._subscribers.setdefault(pattern, []).append(callback)

        def get_history(self, pattern: str = "*") -> List[Any]:
            if pattern == "*":
                return list(self._history)
            return [e for e in self._history
                    if hasattr(e, 'event_type') and pattern.rstrip('*') in e.event_type]

    _stub_bus = _StubBus()

    def get_unified_bus() -> _StubBus:
        return _stub_bus

from ..profiler.module_profiler import ModulePersonality
from ..middleware.personality_guardrails import GuardrailViolation

logger = logging.getLogger(__name__)


def _dict_to_event(entry: Dict[str, Any]) -> Event:
    """Convert unified bus history dicts into Event objects."""
    priority_value = entry.get("priority", EventPriority.NORMAL)
    try:
        priority = EventPriority(priority_value)
    except (ValueError, TypeError):
        priority = EventPriority.NORMAL

    return Event(
        type=entry.get("event_type", entry.get("type", "unknown")),
        data=entry.get("data", {}),
        source=entry.get("source", "unknown"),
        correlation_id=entry.get("correlation_id"),
        causation_id=entry.get("causation_id"),
        priority=priority,
        metadata=entry.get("metadata", {}),
    )


class _GuardrailBusProxy:
    """Proxy unified bus to normalize history results to Event objects."""

    def __init__(self, bus: Any):
        self._bus = bus

    def get_history(self, *args: Any, **kwargs: Any) -> List[Event]:
        history = self._bus.get_history(*args, **kwargs)
        if not history:
            return []
        if hasattr(history[0], "type"):
            return history
        return [_dict_to_event(entry) for entry in history]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._bus, name)


class GuardrailEventTypes:
    """Constants for guardrail event types."""
    
    # Violations
    HARDCODED_PATH = "guardrail:violation:hardcoded_path"
    CIRCULAR_IMPORT = "guardrail:violation:circular_import"
    MISSING_DEPENDENCY = "guardrail:violation:missing_dependency"
    SIDE_EFFECT = "guardrail:violation:side_effect"
    
    # Warnings
    IMPORT_HEAVY = "guardrail:warning:import_heavy"
    STATEFUL_MODULE = "guardrail:warning:stateful_module"
    RUNTIME_FRAGILE = "guardrail:warning:runtime_fragile"
    
    # Information
    PERSONALITY_CHANGED = "guardrail:info:personality_changed"
    BOUNDARY_CROSS = "guardrail:info:boundary_cross"
    GUARDRAIL_CREATED = "guardrail:info:guardrail_created"
    
    # Metrics
    VIOLATION_RATE = "guardrail:metric:violation_rate"
    PERSONALITY_DISTRIBUTION = "guardrail:metric:personality_distribution"
    TREND_ANALYSIS = "guardrail:metric:trend_analysis"


class GuardrailEvent(Event):
    """Specialized event for guardrail-related occurrences."""
    
    def __init__(
        self,
        event_type: str,
        module: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            type=event_type,
            data={
                "module": module,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details or {},
                **kwargs
            },
            source="guardrails",
            priority=self._get_priority_from_severity(severity)
        )
        
    def _get_priority_from_severity(self, severity: str) -> EventPriority:
        """Convert severity to event priority."""
        mapping = {
            "error": EventPriority.CRITICAL,
            "warning": EventPriority.HIGH,
            "info": EventPriority.NORMAL,
            "debug": EventPriority.LOW,
        }
        return mapping.get(severity, EventPriority.NORMAL)


class GuardrailEventPublisher:
    """Publishes guardrail events to the UnifiedEventBus."""
    
    def __init__(self):
        self.bus = _GuardrailBusProxy(get_unified_bus())
        self.stats = {
            "events_published": 0,
            "violations_published": 0,
            "warnings_published": 0,
        }
        
    def publish_violation(self, violation: GuardrailViolation) -> None:
        """Publish a guardrail violation event."""
        event_type = f"guardrail:violation:{violation.violation_type}"
        
        event = GuardrailEvent(
            event_type=event_type,
            module=violation.module,
            severity=violation.severity,
            details={
                "message": str(violation),
                "violation_type": violation.violation_type,
                "suggestions": self._get_suggestions_for_violation(violation),
            }
        )
        
        self.bus.emit(event)
        self.stats["events_published"] += 1
        self.stats["violations_published"] += 1
        
        logger.debug(f"Published violation event: {event_type} for {violation.module}")
        
    def publish_personality_analysis(self, personality: ModulePersonality) -> None:
        """Publish a module personality analysis event."""
        event = GuardrailEvent(
            event_type=GuardrailEventTypes.GUARDRAIL_CREATED,
            module=personality.name,
            severity="info",
            details={
                "personality": {
                    "tone": personality.tone.value,
                    "style": personality.style.value,
                    "nuance": personality.nuance.value,
                    "traits": {
                        "path_dependent": personality.is_path_dependent,
                        "import_heavy": personality.is_import_heavy,
                        "runtime_fragile": personality.is_runtime_fragile,
                        "circular_prone": personality.is_circular_prone,
                        "has_side_effects": personality.has_side_effects,
                        "stateful": personality.is_stateful,
                    },
                    "hardcoded_paths": personality.hardcoded_paths,
                    "conditional_imports": personality.conditional_imports,
                    "global_state": personality.global_state,
                }
            }
        )
        
        self.bus.emit(event)
        self.stats["events_published"] += 1
        
    def publish_boundary_cross(self, from_module: str, to_layer: str, allowed: bool) -> None:
        """Publish a boundary crossing event."""
        event = GuardrailEvent(
            event_type=GuardrailEventTypes.BOUNDARY_CROSS,
            module=from_module,
            severity="info" if allowed else "warning",
            details={
                "target_layer": to_layer,
                "allowed": allowed,
                "action": "granted" if allowed else "denied",
            }
        )
        
        self.bus.emit(event)
        self.stats["events_published"] += 1
        
    def publish_metrics(self, metrics: Dict[str, Any]) -> None:
        """Publish guardrail metrics."""
        event = GuardrailEvent(
            event_type=GuardrailEventTypes.VIOLATION_RATE,
            module="system",
            severity="info",
            details=metrics
        )
        
        self.bus.emit(event)
        self.stats["events_published"] += 1
        
    def _get_suggestions_for_violation(self, violation: GuardrailViolation) -> List[str]:
        """Get suggestions for fixing a violation."""
        suggestions = {
            "hardcoded_path": [
                "Use environment variables or configuration files",
                "Replace with pathlib.Path for cross-platform compatibility",
                "Consider using a path resolver service",
            ],
            "circular_import": [
                "Refactor to remove circular dependencies",
                "Use dependency injection pattern",
                "Move shared code to a separate module",
            ],
            "missing_dependency": [
                "Add the missing dependency to requirements.txt",
                "Use optional imports with try/except blocks",
                "Provide a fallback implementation",
            ],
            "side_effect": [
                "Move side effects out of module level",
                "Use lazy initialization",
                "Encapsulate in functions or classes",
            ],
        }
        
        return suggestions.get(violation.violation_type, [])


class GuardrailEventAnalyzer:
    """Analyzes guardrail events to detect patterns and trends."""
    
    def __init__(self):
        self.bus = _GuardrailBusProxy(get_unified_bus())
        self.violation_history: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Any] = {}
        
        # Subscribe to relevant events
        self.bus.subscribe("guardrail:*", self._handle_guardrail_event)
        
    def _handle_guardrail_event(self, event: Event) -> None:
        """Handle incoming guardrail events."""
        if "violation" in event.type:
            self.violation_history.append({
                "timestamp": event.data.get("timestamp"),
                "module": event.data.get("module"),
                "type": event.data.get("details", {}).get("violation_type"),
                "severity": event.data.get("severity"),
            })
            
            # Keep only recent history (last 1000 events)
            if len(self.violation_history) > 1000:
                self.violation_history = self.violation_history[-1000:]
                
    def get_violation_trends(self, time_window: int = 3600) -> Dict[str, Any]:
        """Analyze violation trends over a time window (seconds)."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - time_window
        
        recent_violations = []
        for violation in self.violation_history:
            timestamp = violation.get("timestamp")
            if not timestamp:
                continue
            try:
                occurred_at = datetime.fromisoformat(timestamp)
                if occurred_at.tzinfo is None:
                    occurred_at = occurred_at.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if occurred_at.timestamp() > cutoff:
                recent_violations.append(violation)
        
        # Group by type
        by_type = {}
        for violation in recent_violations:
            vtype = violation["type"]
            by_type[vtype] = by_type.get(vtype, 0) + 1
            
        # Group by module
        by_module = {}
        for violation in recent_violations:
            module = violation["module"]
            if module not in by_module:
                by_module[module] = {"total": 0, "types": {}}
            by_module[module]["total"] += 1
            vtype = violation["type"]
            by_module[module]["types"][vtype] = by_module[module]["types"].get(vtype, 0) + 1
            
        return {
            "time_window_seconds": time_window,
            "total_violations": len(recent_violations),
            "violations_per_type": by_type,
            "violations_per_module": by_module,
            "rate_per_hour": len(recent_violations) * 3600 / time_window,
        }
        
    def detect_problematic_modules(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Detect modules with frequent violations."""
        module_counts = {}
        
        for violation in self.violation_history:
            module = violation["module"]
            module_counts[module] = module_counts.get(module, 0) + 1
            
        problematic = [
            {"module": module, "violations": count}
            for module, count in module_counts.items()
            if count >= threshold
        ]
        
        return sorted(problematic, key=lambda x: x["violations"], reverse=True)
        
    def get_personality_distribution(self) -> Dict[str, Any]:
        """Get distribution of module personalities from events."""
        personalities = {}
        
        # Query the event bus for personality events
        personality_events = self.bus.get_history(event_type="guardrail:info:guardrail_created")
        
        for event in personality_events:
            details = event.data.get("details", {})
            personality = details.get("personality", {})
            
            tone = personality.get("tone", "unknown")
            style = personality.get("style", "unknown")
            nuance = personality.get("nuance", "unknown")
            
            key = f"{tone}_{style}_{nuance}"
            personalities[key] = personalities.get(key, 0) + 1
            
        return personalities
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        return {
            "violation_trends": self.get_violation_trends(),
            "problematic_modules": self.detect_problematic_modules(),
            "personality_distribution": self.get_personality_distribution(),
            "total_events_analyzed": len(self.violation_history),
        }


# Integration helper functions
def connect_guardrail_events() -> GuardrailEventPublisher:
    """Connect guardrail system to event bus."""
    publisher = GuardrailEventPublisher()
    analyzer = GuardrailEventAnalyzer()
    
    logger.info("Connected guardrail events to UnifiedEventBus")
    return publisher


def get_guardrail_analytics() -> Dict[str, Any]:
    """Get current guardrail analytics."""
    analyzer = GuardrailEventAnalyzer()
    return analyzer.generate_report()


# Event listener for real-time monitoring
def setup_realtime_monitoring(callback: callable) -> None:
    """Setup real-time monitoring with custom callback."""
    bus = get_unified_bus()
    
    def monitor_handler(event: Event) -> None:
        if "guardrail" in event.type:
            callback({
                "type": event.type,
                "module": event.data.get("module"),
                "severity": event.data.get("severity"),
                "details": event.data.get("details"),
                "timestamp": event.data.get("timestamp"),
            })
            
    bus.subscribe("guardrail:*", monitor_handler)
    logger.info("Setup real-time guardrail monitoring")
