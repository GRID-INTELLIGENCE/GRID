"""
Core Privacy Engine - Main orchestrator for privacy operations.

Supports both singular (personal) and collaborative (shared) modes.
"""

from __future__ import annotations

import threading
from typing import Any

from safety.observability.logging_setup import get_logger
from safety.privacy.cache.result_cache import DetectionCache, get_detection_cache
from safety.privacy.core.masking import (
    CompliancePreset,
    MaskResult,
    create_compliance_engine,
)
from safety.privacy.core.presets import PrivacyPreset, get_preset_config

logger = get_logger("privacy.core")


from safety.privacy.core.types import PrivacyAction, PrivacyConfig, PrivacyResult


class PrivacyEngine:
    """
    Core privacy engine orchestrating detection and masking.

    Supports both singular and collaborative modes:
    - Singular: Personal AI assistant, individual queries
    - Collaborative: Team workspaces, shared AI platforms

    Default behavior: Interactive (ASK) - user preference per detection
    """

    def __init__(self, config: PrivacyConfig | None = None):
        self._config = config or PrivacyConfig()

        # Initialize detection (imported from detector module)
        self._detector = None

        # Initialize masking engine
        if self._config.masking_engine:
            self._masking_engine = self._config.masking_engine
        elif self._config.compliance_preset:
            self._masking_engine = create_compliance_engine(self._config.compliance_preset)
        else:
            from safety.privacy.core.masking import MaskingEngine

            self._masking_engine = MaskingEngine()

        # Initialize cache
        self._cache: DetectionCache | None = None
        if self._config.enable_cache:
            self._cache = get_detection_cache(
                collaborative=self._config.collaborative,
                default_ttl=self._config.cache_ttl,
            )

    def _get_detector(self):
        """Lazy import of detector to avoid circular imports."""
        if self._detector is None:
            from safety.privacy.detector import AsyncPIIDetector

            self._detector = AsyncPIIDetector(
                enable_cache=False,  # We handle caching ourselves
                max_workers=4,
            )
            if self._config.enabled_patterns:
                self._detector.enable_patterns(self._config.enabled_patterns)
        return self._detector

    def _get_action(self, pii_type: str) -> PrivacyAction:
        """Get the action for a specific PII type."""
        return self._config.per_type_actions.get(
            pii_type,
            self._config.default_action,
        )

    async def detect(
        self,
        text: str,
        context_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Detect PII in text without taking action.

        Args:
            text: Text to scan
            context_id: Optional context for collaborative mode

        Returns:
            List of detection results
        """
        detector = self._get_detector()
        ctx = context_id or self._config.context_id

        # Check cache first
        if self._cache and ctx:
            cached = await self._cache.get(
                text,
                frozenset(detector._enabled_patterns),
                ctx,
            )
            if cached is not None:
                logger.debug("detection_cache_hit", context_id=ctx)
                return cached

        # Run detection
        detections = await detector.detect_async(text)
        results = [d.to_dict() for d in detections]

        # Cache results
        if self._cache and ctx:
            await self._cache.set(
                text,
                results,
                frozenset(detector._enabled_patterns),
                context_id=ctx,
            )

        return results

    async def process(
        self,
        text: str,
        user_choice: str | None = None,
        context_id: str | None = None,
    ) -> PrivacyResult:
        """
        Process text through the privacy pipeline.

        Args:
            text: Text to process
            user_choice: If requires_user_input was True, user's decision
            context_id: Optional context for collaborative mode

        Returns:
            PrivacyResult with processing outcome
        """
        try:
            # Step 1: Detect PII
            detections = await self.detect(text, context_id)

            if not detections:
                return PrivacyResult(
                    success=True,
                    original_text=text,
                    processed_text=text,
                    detections=[],
                    action_taken=None,
                )

            # Step 2: Determine action per detection
            # For interactive mode, check if we need user input
            needs_user_input = False
            actions_to_take = {}

            for detection in detections:
                pii_type = detection.get("pii_type", "UNKNOWN")
                action = self._get_action(pii_type)

                if action == PrivacyAction.ASK:
                    needs_user_input = True

                actions_to_take[pii_type] = action

            # Step 3: If interactive and no user choice, return for user input
            if needs_user_input and user_choice is None:
                return PrivacyResult(
                    success=True,
                    original_text=text,
                    processed_text=None,
                    detections=detections,
                    requires_user_input=True,
                )

            # Step 4: Apply actions
            processed_text = text
            masked = False
            blocked = False

            for detection in detections:
                pii_type = detection.get("pii_type", "UNKNOWN")

                # Get action for this type
                if user_choice and user_choice in [a.value for a in PrivacyAction]:
                    action = PrivacyAction(user_choice)
                else:
                    action = actions_to_take.get(pii_type, self._config.default_action)

                if action == PrivacyAction.BLOCK:
                    blocked = True
                    break

                elif action == PrivacyAction.MASK:
                    mask_result = self._masking_engine.mask_text(
                        processed_text,
                        [detection],
                    )
                    processed_text = mask_result.masked
                    masked = True

                elif action == PrivacyAction.ASK and user_choice == "mask":
                    mask_result = self._masking_engine.mask_text(
                        processed_text,
                        [detection],
                    )
                    processed_text = mask_result.masked
                    masked = True

                elif action == PrivacyAction.FLAG or action == PrivacyAction.LOG:
                    # Just log, no modification
                    pass

            return PrivacyResult(
                success=True,
                original_text=text,
                processed_text=processed_text if not blocked else None,
                detections=detections,
                action_taken=PrivacyAction.BLOCK if blocked else (PrivacyAction.MASK if masked else PrivacyAction.LOG),
                masked=masked,
                blocked=blocked,
                user_choice=user_choice,
            )

        except Exception as e:
            logger.error("privacy_processing_error", error=str(e))
            return PrivacyResult(
                success=False,
                original_text=text,
                error=str(e),
            )

    async def mask(
        self,
        text: str,
        detections: list[dict[str, Any]] | None = None,
    ) -> MaskResult:
        """
        Mask detected PII in text.

        Args:
            text: Text with potential PII
            detections: Pre-detected PII (optional, will detect if not provided)

        Returns:
            MaskResult with masked text
        """
        if detections is None:
            detections = await self.detect(text)

        return self._masking_engine.mask_text(text, detections)

    async def get_stats(self) -> dict[str, Any]:
        """Get privacy engine statistics."""
        stats = {
            "config": {
                "default_action": self._config.default_action.value,
                "collaborative": self._config.collaborative,
                "compliance_preset": self._config.compliance_preset.value if self._config.compliance_preset else None,
            },
        }

        if self._cache:
            stats["cache"] = await self._cache.get_stats()

        return stats


# Preset engine factories
def create_privacy_engine(
    preset: PrivacyPreset,
    collaborative: bool = False,
    context_id: str | None = None,
) -> PrivacyEngine:
    """
    Create a privacy engine with preset configuration.

    Args:
        preset: Privacy preset to use
        collaborative: Enable collaborative mode
        context_id: Workspace/team ID for collaborative

    Returns:
        Configured PrivacyEngine
    """
    config_dict = get_preset_config(preset)

    # Map preset to compliance
    compliance = None
    if preset == PrivacyPreset.GDPR_COMPLIANT:
        compliance = CompliancePreset.GDPR
    elif preset == PrivacyPreset.HIPAA_COMPLIANT:
        compliance = CompliancePreset.HIPAA
    elif preset == PrivacyPreset.PCI_COMPLIANT:
        compliance = CompliancePreset.PCI_DSS

    config = PrivacyConfig(
        enable_detection=config_dict.get("enable_detection", True),
        enabled_patterns=config_dict.get("enabled_patterns"),
        default_action=PrivacyAction(config_dict.get("default_action", "ask")),
        per_type_actions=config_dict.get("per_type_actions", {}),
        compliance_preset=compliance,
        enable_cache=config_dict.get("enable_cache", True),
        cache_ttl=config_dict.get("cache_ttl", 3600),
        collaborative=collaborative,
        context_id=context_id,
    )

    return PrivacyEngine(config)


# Global instances for different modes
_singular_engine: PrivacyEngine | None = None
_collaborative_engines: dict[str, PrivacyEngine] = {}
_privacy_engine_lock = threading.RLock()


def get_privacy_engine(
    collaborative: bool = False,
    context_id: str | None = None,
    preset: PrivacyPreset = PrivacyPreset.BALANCED,
) -> PrivacyEngine:
    """
    Get or create a privacy engine (thread-safe).

    For singular mode, returns a shared instance.
    For collaborative mode, returns instance per context_id.
    """
    global _singular_engine, _collaborative_engines

    if not collaborative:
        if _singular_engine is None:
            with _privacy_engine_lock:
                if _singular_engine is None:
                    _singular_engine = create_privacy_engine(preset, False)
        return _singular_engine

    # Collaborative mode - per-context instance
    if context_id is None:
        raise ValueError("context_id must be provided for collaborative mode.")

    if context_id not in _collaborative_engines:
        with _privacy_engine_lock:
            if context_id not in _collaborative_engines:
                _collaborative_engines[context_id] = create_privacy_engine(preset, True, context_id)

    return _collaborative_engines[context_id]


async def invalidate_context(context_id: str) -> int:
    """Invalidate cache for a collaborative context."""
    cache = get_detection_cache(collaborative=True)
    return await cache.invalidate(context_id)
