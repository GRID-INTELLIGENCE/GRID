"""
Privacy Shield Module for GRID.

Async PII detection integrated with GRID's safety pipeline.

Modules:
    - detector: Async PII detection engine
    - core: Main privacy engine and masking
    - cache: Detection result caching
    - integration: Middleware and collaborative support
    - workers: Batch processing worker pool

Usage:
    # Direct usage
    from safety.privacy import AsyncPIIDetector
    detector = AsyncPIIDetector()
    results = await detector.detect_async(text)

    # Engine with masking
    from safety.privacy.core.engine import get_privacy_engine
    engine = get_privacy_engine(collaborative=False)
    result = await engine.process(text)

    # Middleware integration
    from safety.privacy.integration.middleware import add_privacy_middleware
    add_privacy_middleware(app, preset=PrivacyPreset.BALANCED)
"""

from safety.privacy.detector import AsyncPIIDetection, AsyncPIIDetector, detector

from safety.privacy.core.engine import (
    PrivacyAction,
    PrivacyConfig,
    PrivacyEngine,
    PrivacyResult,
    create_privacy_engine,
    get_privacy_engine,
    invalidate_context,
)

from safety.privacy.core.masking import (
    CompliancePreset,
    MaskResult,
    MaskStrategyType,
    MaskingEngine,
    create_compliance_engine,
    get_gdpr_engine,
    get_hipaa_engine,
)

from safety.privacy.core.presets import (
    PrivacyPreset,
    get_preset_config,
)

from safety.privacy.integration.middleware import (
    MiddlewareConfig,
    PrivacyMiddleware,
    add_privacy_middleware,
)

from safety.privacy.integration.collaborative import (
    CollaborativeManager,
    WorkspaceConfig,
    get_collaborative_manager,
    create_workspace,
    get_workspace,
    process_for_workspace,
)

from safety.privacy.workers.pool import (
    BatchResult,
    PrivacyWorkerPool,
    get_worker_pool,
    process_batch,
)

from safety.privacy.cache.result_cache import (
    DetectionCache,
    get_detection_cache,
    invalidate_context_cache,
)

__all__ = [
    # Detector
    "AsyncPIIDetection",
    "AsyncPIIDetector",
    "detector",
    # Engine
    "PrivacyAction",
    "PrivacyConfig",
    "PrivacyEngine",
    "PrivacyResult",
    "create_privacy_engine",
    "get_privacy_engine",
    "invalidate_context",
    # Masking
    "CompliancePreset",
    "MaskResult",
    "MaskStrategyType",
    "MaskingEngine",
    "create_compliance_engine",
    "get_gdpr_engine",
    "get_hipaa_engine",
    # Presets
    "PrivacyPreset",
    "get_preset_config",
    # Middleware
    "MiddlewareConfig",
    "PrivacyMiddleware",
    "add_privacy_middleware",
    # Collaborative
    "CollaborativeManager",
    "WorkspaceConfig",
    "get_collaborative_manager",
    "create_workspace",
    "get_workspace",
    "process_for_workspace",
    # Workers
    "BatchResult",
    "PrivacyWorkerPool",
    "get_worker_pool",
    "process_batch",
    # Cache
    "DetectionCache",
    "get_detection_cache",
    "invalidate_context_cache",
]
