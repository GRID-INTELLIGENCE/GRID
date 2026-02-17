"""
Inference Abrasiveness Configuration Module.

Provides fine-tuned control over inference behavior with controlled automation,
similar to Storage Sense Group Policy/Intune settings. Allows subtle adjustment
of abrasiveness parameters that work with relevant references and extensions.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum
from typing import Any

# Import quality gates configuration
try:
    from config.qualityGates import (
        QualityGates,
        get_inference_threshold,
    )
except ImportError:
    # Fallback if qualityGates not available
    QualityGates = None

    def get_inference_threshold(threshold_type: str) -> float:
        # Default fallback values
        defaults = {
            "confidence": 0.7,
            "resourceUtilization": 0.8,
            "failureCount": 5,
            "temporalDecay": 0.5,
            "patternDeviation": 0.3,
        }
        return defaults.get(threshold_type, 0.7)


logger = logging.getLogger(__name__)


class AbrasivenessCadence(IntEnum):
    """Execution frequency for abrasiveness control (similar to Storage Sense cadence)."""

    LOW_SPACE = 0  # Trigger only when resources are low
    DAILY = 1  # Daily execution
    WEEKLY = 7  # Weekly execution
    MONTHLY = 30  # Monthly execution
    CONTINUOUS = -1  # Continuous monitoring (highest abrasiveness)


class InferenceAbrasivenessLevel(StrEnum):
    """Levels of inference abrasiveness (how aggressive inference operations are)."""

    PASSIVE = "passive"  # Minimal interference, high confidence required
    BALANCED = "balanced"  # Default balanced approach
    AGGRESSIVE = "aggressive"  # More proactive inference
    MAXIMUM = "maximum"  # Maximum abrasiveness (use with caution)


@dataclass
class AbrasivenessThresholds:
    """Thresholds for triggering abrasiveness adjustments."""

    confidence_threshold: float = field(default_factory=lambda: get_inference_threshold("confidence"))
    resource_utilization_threshold: float = field(
        default_factory=lambda: get_inference_threshold("resourceUtilization")
    )
    inference_failure_threshold: int = field(default_factory=lambda: int(get_inference_threshold("failureCount")))
    temporal_decay_threshold: float = field(default_factory=lambda: get_inference_threshold("temporalDecay"))
    pattern_deviation_threshold: float = field(default_factory=lambda: get_inference_threshold("patternDeviation"))

    def to_dict(self) -> dict[str, Any]:
        """Convert thresholds to dictionary."""
        return {
            "confidence_threshold": self.confidence_threshold,
            "resource_utilization_threshold": self.resource_utilization_threshold,
            "inference_failure_threshold": self.inference_failure_threshold,
            "temporal_decay_threshold": self.temporal_decay_threshold,
            "pattern_deviation_threshold": self.pattern_deviation_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AbrasivenessThresholds:
        """Create thresholds from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InferenceCleanupSettings:
    """Settings for cleanup operations (similar to Storage Sense cleanup)."""

    enable_temporary_cleanup: bool = True  # Cleanup temporary inference artifacts
    enable_stale_cleanup: bool = True  # Cleanup stale inference results
    enable_cache_cleanup: bool = True  # Cleanup inference cache

    temporary_files_cleanup_threshold: int = 7  # Days before temp file cleanup (similar to Storage Sense)
    stale_results_cleanup_threshold: int = 30  # Days before stale result cleanup
    cache_cleanup_threshold: int = 90  # Days before cache cleanup

    cloud_content_dehydration_threshold: float = 0.5  # Threshold for cloud content (0.0-1.0)
    downloads_cleanup_threshold: int = 30  # Days before download cleanup (similar to Storage Sense)
    recycle_bin_cleanup_threshold: int = 14  # Days before recycle bin cleanup (similar to Storage Sense)

    def to_dict(self) -> dict[str, Any]:
        """Convert cleanup settings to dictionary."""
        return {
            "enable_temporary_cleanup": self.enable_temporary_cleanup,
            "enable_stale_cleanup": self.enable_stale_cleanup,
            "enable_cache_cleanup": self.enable_cache_cleanup,
            "temporary_files_cleanup_threshold": self.temporary_files_cleanup_threshold,
            "stale_results_cleanup_threshold": self.stale_results_cleanup_threshold,
            "cache_cleanup_threshold": self.cache_cleanup_threshold,
            "cloud_content_dehydration_threshold": self.cloud_content_dehydration_threshold,
            "downloads_cleanup_threshold": self.downloads_cleanup_threshold,
            "recycle_bin_cleanup_threshold": self.recycle_bin_cleanup_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InferenceCleanupSettings:
        """Create cleanup settings from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InferenceAbrasivenessConfig:
    """
    Fine-tuned inference abrasiveness configuration.

    Provides controlled automation configs that work with relevant references
    and extensions, allowing subtle adjustment of abrasiveness parameters.
    Similar to Storage Sense Group Policy/Intune settings pattern.
    """

    # Global Control (similar to AllowStorageSenseGlobal)
    enabled: bool = True  # Enable/disable inference abrasiveness control system-wide
    global_cadence: AbrasivenessCadence = AbrasivenessCadence.DAILY  # Execution frequency
    abrasiveness_level: InferenceAbrasivenessLevel = InferenceAbrasivenessLevel.BALANCED

    # Thresholds for triggering adjustments
    thresholds: AbrasivenessThresholds = field(default_factory=AbrasivenessThresholds)

    # Cleanup settings (similar to Storage Sense cleanup controls)
    cleanup: InferenceCleanupSettings = field(default_factory=InferenceCleanupSettings)

    # Automation Configuration
    enable_automated_adjustment: bool = True  # Enable automatic abrasiveness adjustment
    enable_reference_integration: bool = True  # Enable integration with reference patterns
    enable_extension_support: bool = True  # Enable support for extensions

    # Reference Integration (works with reference architecture patterns)
    reference_pattern_matching: bool = True  # Use reference patterns for alignment
    reference_threshold_adjustment: float = 0.1  # Adjustment factor based on references (0.0-1.0)
    reference_confidence_boost: float = 0.05  # Confidence boost from reference patterns (0.0-1.0)

    # Extension Support (works with extensions/modules)
    extension_enabled: list[str] = field(default_factory=list)  # List of enabled extensions
    extension_abrasiveness_override: dict[str, InferenceAbrasivenessLevel] = field(
        default_factory=dict
    )  # Per-extension overrides
    extension_threshold_multiplier: dict[str, float] = field(
        default_factory=dict
    )  # Per-extension threshold multipliers

    # Fine-Tuning Parameters (subtle adjustment controls)
    confidence_adjustment_factor: float = 1.1  # Multiplier (Optimized: Risk Mobility Boost)
    temporal_decay_rate: float = 0.95  # Rate of temporal decay per time unit (0.0-1.0)
    pattern_adherence_weight: float = 0.85  # Weight (Optimized: Structural Integrity)
    deviation_tolerance: float = 0.10  # Tolerance (Optimized: Strict Boundaries)

    # Cadence Configuration (similar to ConfigStorageSenseGlobalCadence)
    cadence_override: AbrasivenessCadence | None = None  # Override global cadence
    cadence_scheduling: bool = True  # Enable scheduled execution
    cadence_adaptive: bool = True  # Adaptive cadence based on system state

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "global_cadence": (
                self.global_cadence.value if isinstance(self.global_cadence, Enum) else self.global_cadence
            ),
            "abrasiveness_level": (
                self.abrasiveness_level.value if isinstance(self.abrasiveness_level, Enum) else self.abrasiveness_level
            ),
            "thresholds": self.thresholds.to_dict(),
            "cleanup": self.cleanup.to_dict(),
            "enable_automated_adjustment": self.enable_automated_adjustment,
            "enable_reference_integration": self.enable_reference_integration,
            "enable_extension_support": self.enable_extension_support,
            "reference_pattern_matching": self.reference_pattern_matching,
            "reference_threshold_adjustment": self.reference_threshold_adjustment,
            "reference_confidence_boost": self.reference_confidence_boost,
            "extension_enabled": self.extension_enabled,
            "extension_abrasiveness_override": {
                k: v.value if isinstance(v, Enum) else v for k, v in self.extension_abrasiveness_override.items()
            },
            "extension_threshold_multiplier": self.extension_threshold_multiplier,
            "confidence_adjustment_factor": self.confidence_adjustment_factor,
            "temporal_decay_rate": self.temporal_decay_rate,
            "pattern_adherence_weight": self.pattern_adherence_weight,
            "deviation_tolerance": self.deviation_tolerance,
            "cadence_override": (
                self.cadence_override.value if isinstance(self.cadence_override, Enum) else self.cadence_override
            ),
            "cadence_scheduling": self.cadence_scheduling,
            "cadence_adaptive": self.cadence_adaptive,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InferenceAbrasivenessConfig:
        """Create configuration from dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            InferenceAbrasivenessConfig instance
        """
        from enum import Enum

        # Extract thresholds
        thresholds_data = data.get("thresholds", {})
        thresholds = AbrasivenessThresholds.from_dict(thresholds_data)

        # Extract cleanup
        cleanup_data = data.get("cleanup", {})
        cleanup = InferenceCleanupSettings.from_dict(cleanup_data)

        # Extract enums
        global_cadence_str = data.get("global_cadence")
        if isinstance(global_cadence_str, str):
            global_cadence = AbrasivenessCadence(int(global_cadence_str))
        elif isinstance(global_cadence_str, int):
            global_cadence = AbrasivenessCadence(global_cadence_str)
        elif isinstance(global_cadence_str, Enum):
            global_cadence = global_cadence_str
        else:
            global_cadence = AbrasivenessCadence.DAILY

        abrasiveness_level_str = data.get("abrasiveness_level")
        if isinstance(abrasiveness_level_str, str):
            abrasiveness_level = InferenceAbrasivenessLevel(abrasiveness_level_str)
        elif isinstance(abrasiveness_level_str, Enum):
            abrasiveness_level = abrasiveness_level_str
        else:
            abrasiveness_level = InferenceAbrasivenessLevel.BALANCED

        cadence_override_str = data.get("cadence_override")
        cadence_override = None
        if cadence_override_str is not None:
            if isinstance(cadence_override_str, str):
                cadence_override = AbrasivenessCadence(int(cadence_override_str))
            elif isinstance(cadence_override_str, int):
                cadence_override = AbrasivenessCadence(cadence_override_str)
            elif isinstance(cadence_override_str, Enum):
                cadence_override = cadence_override_str

        # Extract extension overrides
        extension_abrasiveness_override = {}
        ext_overrides = data.get("extension_abrasiveness_override", {})
        for ext, level in ext_overrides.items():
            if isinstance(level, str):
                extension_abrasiveness_override[ext] = InferenceAbrasivenessLevel(level)
            elif isinstance(level, Enum):
                extension_abrasiveness_override[ext] = level

        return cls(
            enabled=data.get("enabled", True),
            global_cadence=global_cadence,
            abrasiveness_level=abrasiveness_level,
            thresholds=thresholds,
            cleanup=cleanup,
            enable_automated_adjustment=data.get("enable_automated_adjustment", True),
            enable_reference_integration=data.get("enable_reference_integration", True),
            enable_extension_support=data.get("enable_extension_support", True),
            reference_pattern_matching=data.get("reference_pattern_matching", True),
            reference_threshold_adjustment=data.get("reference_threshold_adjustment", 0.1),
            reference_confidence_boost=data.get("reference_confidence_boost", 0.05),
            extension_enabled=data.get("extension_enabled", []),
            extension_abrasiveness_override=extension_abrasiveness_override,
            extension_threshold_multiplier=data.get("extension_threshold_multiplier", {}),
            confidence_adjustment_factor=data.get("confidence_adjustment_factor", 1.0),
            temporal_decay_rate=data.get("temporal_decay_rate", 0.95),
            pattern_adherence_weight=data.get("pattern_adherence_weight", 0.7),
            deviation_tolerance=data.get("deviation_tolerance", 0.15),
            cadence_override=cadence_override,
            cadence_scheduling=data.get("cadence_scheduling", True),
            cadence_adaptive=data.get("cadence_adaptive", True),
        )

    @classmethod
    def from_env(cls) -> InferenceAbrasivenessConfig:
        """Load configuration from environment variables (similar to Storage Sense Intune pattern)."""
        env = os.environ

        # Global Control
        enabled = env.get("INFERENCE_ABRASIVENESS_ENABLED", "true").lower() in {"true", "1", "yes"}
        global_cadence = AbrasivenessCadence(int(env.get("INFERENCE_ABRASIVENESS_GLOBAL_CADENCE", "1")))
        abrasiveness_level = InferenceAbrasivenessLevel(env.get("INFERENCE_ABRASIVENESS_LEVEL", "balanced").lower())

        # Thresholds
        thresholds = AbrasivenessThresholds(
            confidence_threshold=float(env.get("INFERENCE_CONFIDENCE_THRESHOLD", "0.7")),
            resource_utilization_threshold=float(env.get("INFERENCE_RESOURCE_THRESHOLD", "0.8")),
            inference_failure_threshold=int(env.get("INFERENCE_FAILURE_THRESHOLD", "5")),
            temporal_decay_threshold=float(env.get("INFERENCE_TEMPORAL_DECAY_THRESHOLD", "0.5")),
            pattern_deviation_threshold=float(env.get("INFERENCE_PATTERN_DEVIATION_THRESHOLD", "0.3")),
        )

        # Cleanup Settings (similar to Storage Sense)
        cleanup = InferenceCleanupSettings(
            enable_temporary_cleanup=env.get("INFERENCE_CLEANUP_TEMPORARY", "true").lower() in {"true", "1", "yes"},
            enable_stale_cleanup=env.get("INFERENCE_CLEANUP_STALE", "true").lower() in {"true", "1", "yes"},
            enable_cache_cleanup=env.get("INFERENCE_CLEANUP_CACHE", "true").lower() in {"true", "1", "yes"},
            temporary_files_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_TEMP_THRESHOLD", "7")),
            stale_results_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_STALE_THRESHOLD", "30")),
            cache_cleanup_threshold=int(env.get("INFERENCE_CLEANUP_CACHE_THRESHOLD", "90")),
            cloud_content_dehydration_threshold=float(env.get("INFERENCE_CLOUD_DEHYDRATION_THRESHOLD", "0.5")),
            downloads_cleanup_threshold=int(env.get("INFERENCE_DOWNLOADS_CLEANUP_THRESHOLD", "30")),
            recycle_bin_cleanup_threshold=int(env.get("INFERENCE_RECYCLE_BIN_CLEANUP_THRESHOLD", "14")),
        )

        # Automation
        enable_automated_adjustment = env.get("INFERENCE_AUTOMATED_ADJUSTMENT", "true").lower() in {"true", "1", "yes"}
        enable_reference_integration = env.get("INFERENCE_REFERENCE_INTEGRATION", "true").lower() in {
            "true",
            "1",
            "yes",
        }
        enable_extension_support = env.get("INFERENCE_EXTENSION_SUPPORT", "true").lower() in {"true", "1", "yes"}

        # Reference Integration
        reference_pattern_matching = env.get("INFERENCE_REFERENCE_PATTERN_MATCHING", "true").lower() in {
            "true",
            "1",
            "yes",
        }
        reference_threshold_adjustment = float(env.get("INFERENCE_REFERENCE_THRESHOLD_ADJUSTMENT", "0.1"))
        reference_confidence_boost = float(env.get("INFERENCE_REFERENCE_CONFIDENCE_BOOST", "0.05"))

        # Extensions (comma-separated list)
        extension_enabled_str = env.get("INFERENCE_EXTENSION_ENABLED", "")
        extension_enabled = [ext.strip() for ext in extension_enabled_str.split(",") if ext.strip()]

        # Fine-Tuning
        confidence_adjustment_factor = float(env.get("INFERENCE_CONFIDENCE_ADJUSTMENT_FACTOR", "1.0"))
        temporal_decay_rate = float(env.get("INFERENCE_TEMPORAL_DECAY_RATE", "0.95"))
        pattern_adherence_weight = float(env.get("INFERENCE_PATTERN_ADHERENCE_WEIGHT", "0.7"))
        deviation_tolerance = float(env.get("INFERENCE_DEVIATION_TOLERANCE", "0.15"))

        # Cadence
        cadence_override_str = env.get("INFERENCE_CADENCE_OVERRIDE", "")
        cadence_override = AbrasivenessCadence(int(cadence_override_str)) if cadence_override_str.isdigit() else None
        cadence_scheduling = env.get("INFERENCE_CADENCE_SCHEDULING", "true").lower() in {"true", "1", "yes"}
        cadence_adaptive = env.get("INFERENCE_CADENCE_ADAPTIVE", "true").lower() in {"true", "1", "yes"}

        return cls(
            enabled=enabled,
            global_cadence=global_cadence,
            abrasiveness_level=abrasiveness_level,
            thresholds=thresholds,
            cleanup=cleanup,
            enable_automated_adjustment=enable_automated_adjustment,
            enable_reference_integration=enable_reference_integration,
            enable_extension_support=enable_extension_support,
            reference_pattern_matching=reference_pattern_matching,
            reference_threshold_adjustment=reference_threshold_adjustment,
            reference_confidence_boost=reference_confidence_boost,
            extension_enabled=extension_enabled,
            extension_abrasiveness_override={},
            extension_threshold_multiplier={},
            confidence_adjustment_factor=confidence_adjustment_factor,
            temporal_decay_rate=temporal_decay_rate,
            pattern_adherence_weight=pattern_adherence_weight,
            deviation_tolerance=deviation_tolerance,
            cadence_override=cadence_override,
            cadence_scheduling=cadence_scheduling,
            cadence_adaptive=cadence_adaptive,
        )

    def get_effective_cadence(self) -> AbrasivenessCadence:
        """Get effective cadence (override if set, otherwise global)."""
        return self.cadence_override if self.cadence_override is not None else self.global_cadence

    def get_extension_abrasiveness(self, extension_name: str) -> InferenceAbrasivenessLevel:
        """Get abrasiveness level for a specific extension (with override support)."""
        if extension_name in self.extension_abrasiveness_override:
            return self.extension_abrasiveness_override[extension_name]
        return self.abrasiveness_level

    def get_extension_threshold_multiplier(self, extension_name: str) -> float:
        """Get threshold multiplier for a specific extension."""
        return self.extension_threshold_multiplier.get(extension_name, 1.0)

    def adjust_confidence(self, base_confidence: float, use_reference_boost: bool = True) -> float:
        """
        Adjust confidence based on configuration.

        Args:
            base_confidence: Base confidence value (0.0-1.0)
            use_reference_boost: Whether to apply reference confidence boost

        Returns:
            Adjusted confidence value
        """
        adjusted = base_confidence * self.confidence_adjustment_factor

        if use_reference_boost and self.enable_reference_integration and self.reference_pattern_matching:
            adjusted += self.reference_confidence_boost

        # Clamp to valid range
        return max(0.0, min(1.0, adjusted))

    def should_trigger_adjustment(
        self,
        current_confidence: float,
        resource_utilization: float,
        failure_count: int,
        pattern_deviation: float,
    ) -> bool:
        """
        Determine if abrasiveness adjustment should be triggered.

        Args:
            current_confidence: Current confidence value
            resource_utilization: Current resource utilization (0.0-1.0)
            failure_count: Number of recent failures
            pattern_deviation: Current pattern deviation (0.0-1.0)

        Returns:
            True if adjustment should be triggered
        """
        if not self.enable_automated_adjustment:
            return False

        # Check thresholds
        if current_confidence < self.thresholds.confidence_threshold:
            return True

        if resource_utilization > self.thresholds.resource_utilization_threshold:
            return True

        if failure_count >= self.thresholds.inference_failure_threshold:
            return True

        if pattern_deviation > self.thresholds.pattern_deviation_threshold:
            return True

        return False

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.

        Returns:
            List of validation issues (empty if valid)
        """
        issues: list[str] = []

        # Validate thresholds
        if not 0.0 <= self.thresholds.confidence_threshold <= 1.0:
            issues.append("confidence_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.thresholds.resource_utilization_threshold <= 1.0:
            issues.append("resource_utilization_threshold must be between 0.0 and 1.0")

        if self.thresholds.inference_failure_threshold < 0:
            issues.append("inference_failure_threshold must be non-negative")

        if not 0.0 <= self.thresholds.temporal_decay_threshold <= 1.0:
            issues.append("temporal_decay_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.thresholds.pattern_deviation_threshold <= 1.0:
            issues.append("pattern_deviation_threshold must be between 0.0 and 1.0")

        # Validate fine-tuning parameters
        if not 0.5 <= self.confidence_adjustment_factor <= 2.0:
            issues.append("confidence_adjustment_factor should be between 0.5 and 2.0")

        if not 0.0 <= self.temporal_decay_rate <= 1.0:
            issues.append("temporal_decay_rate must be between 0.0 and 1.0")

        if not 0.0 <= self.pattern_adherence_weight <= 1.0:
            issues.append("pattern_adherence_weight must be between 0.0 and 1.0")

        if not 0.0 <= self.deviation_tolerance <= 1.0:
            issues.append("deviation_tolerance must be between 0.0 and 1.0")

        # Validate reference integration
        if not 0.0 <= self.reference_threshold_adjustment <= 1.0:
            issues.append("reference_threshold_adjustment must be between 0.0 and 1.0")

        if not 0.0 <= self.reference_confidence_boost <= 1.0:
            issues.append("reference_confidence_boost must be between 0.0 and 1.0")

        return issues
