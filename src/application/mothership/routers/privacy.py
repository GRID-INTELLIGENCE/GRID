"""
Privacy API Router (Mothership Integration).

Wraps Grid API privacy functionality for unified Mothership deployment.
Provides PII detection and masking endpoints with Mothership authentication.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from application.mothership.dependencies import Auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/privacy", tags=["privacy"])


# Stats for usage reporting
_stats = {"total_requests": 0, "entities_detected": 0, "texts_processed": 0, "_start_time": time.time()}


class PrivacyRequest(BaseModel):
    """Privacy processing request."""

    text: str = Field(..., description="Text to process for PII", min_length=1)
    level: str | None = Field(default=None, description="Privacy level: strict, balanced, minimal")
    context: str | None = Field(default=None, description="Optional context for processing")


class PrivacyBatchRequest(BaseModel):
    """Batch privacy processing request."""

    texts: list[str] = Field(..., description="List of texts to process", min_length=1)
    level: str | None = Field(default=None, description="Privacy level: strict, balanced, minimal")
    context: str | None = Field(default=None, description="Optional context for processing")


class DetectionRequest(BaseModel):
    """PII detection request."""

    text: str = Field(..., description="Text to analyze for PII", min_length=1)


class DetectedEntity(BaseModel):
    """Detected PII entity."""

    type: str = Field(..., description="Entity type (e.g., email, phone, ssn)")
    value: str = Field(..., description="Detected value")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")


class DetectionResponse(BaseModel):
    """PII detection response."""

    detected_entities: list[DetectedEntity] = Field(default_factory=list, description="List of detected entities")
    entity_count: int = Field(..., description="Total number of entities detected")


class PrivacyMaskResponse(BaseModel):
    """Privacy masking response."""

    original_text: str = Field(..., description="Original input text")
    masked_text: str = Field(..., description="Text with PII masked")
    detected_entities: list[DetectedEntity] = Field(default_factory=list, description="Entities that were masked")
    applied_rules: list[str] = Field(default_factory=list, description="Rules that were applied")


class BatchResult(BaseModel):
    """Single item result in batch processing."""

    original_text: str = Field(..., description="Original input text")
    masked_text: str = Field(..., description="Text with PII masked")
    detected_entities: list[DetectedEntity] = Field(default_factory=list, description="Entities that were masked")


class BatchPrivacyResponse(BaseModel):
    """Batch privacy processing response."""

    results: list[BatchResult] = Field(default_factory=list, description="Results for each text")
    total_processed: int = Field(..., description="Total number of texts processed")
    level: str = Field(..., description="Privacy level used")


def _get_privacy_level(level_str: str | None) -> str:
    """Map level string to valid privacy level."""
    valid_levels = ["strict", "balanced", "minimal"]
    if level_str and level_str.lower() in valid_levels:
        return level_str.lower()
    return "balanced"  # Default


@router.post("/detect", response_model=DetectionResponse)
async def detect_pii(request: DetectionRequest, auth: Auth = Depends()):
    """Detect PII entities in text."""
    try:
        from safety.privacy.engine import PrivacyEngine

        engine = PrivacyEngine(level=_get_privacy_level(None))
        detected = engine.detect(request.text)

        entities = [
            DetectedEntity(
                type=e.type,
                value=e.value,
                start=e.start,
                end=e.end,
            )
            for e in detected
        ]

        _stats["total_requests"] += 1
        _stats["entities_detected"] += len(entities)

        return DetectionResponse(detected_entities=entities, entity_count=len(entities))
    except ImportError as e:
        logger.error(f"Privacy engine not available: {e}")
        raise HTTPException(status_code=503, detail="Privacy service not available")
    except Exception as e:
        logger.exception("PII detection failed: %s", e)
        raise HTTPException(status_code=500, detail=f"PII detection failed: {str(e)}")


@router.post("/mask", response_model=PrivacyMaskResponse)
async def mask_pii(request: PrivacyRequest, auth: Auth = Depends()):
    """Mask PII entities in text."""
    try:
        from safety.privacy.engine import PrivacyEngine

        level = _get_privacy_level(request.level)
        engine = PrivacyEngine(level=level)
        result = engine.mask_text(request.text)

        entities = [
            DetectedEntity(
                type=e.type,
                value=e.value,
                start=e.start,
                end=e.end,
            )
            for e in result.detected_entities
        ]

        _stats["total_requests"] += 1
        _stats["entities_detected"] += len(entities)
        _stats["texts_processed"] += 1

        return PrivacyMaskResponse(
            original_text=request.text,
            masked_text=result.masked_text,
            detected_entities=entities,
            applied_rules=result.applied_rules,
        )
    except ImportError as e:
        logger.error(f"Privacy engine not available: {e}")
        raise HTTPException(status_code=503, detail="Privacy service not available")
    except Exception as e:
        logger.exception("PII masking failed: %s", e)
        raise HTTPException(status_code=500, detail=f"PII masking failed: {str(e)}")


@router.post("/batch", response_model=BatchPrivacyResponse)
async def batch_privacy_processing(request: PrivacyBatchRequest, auth: Auth = Depends()):
    """Process multiple texts for PII detection and masking."""
    try:
        from safety.privacy.engine import PrivacyEngine

        level = _get_privacy_level(request.level)
        engine = PrivacyEngine(level=level)
        privacy_results = engine.batch_process(request.texts)

        results = []
        total_entities = 0

        for text, pr in zip(request.texts, privacy_results, strict=False):
            entities = [
                DetectedEntity(
                    type=e.type,
                    value=e.value,
                    start=e.start,
                    end=e.end,
                )
                for e in pr.detected_entities
            ]

            results.append(
                BatchResult(
                    original_text=text,
                    masked_text=pr.masked_text,
                    detected_entities=entities,
                )
            )
            total_entities += len(entities)

        _stats["total_requests"] += 1
        _stats["entities_detected"] += total_entities
        _stats["texts_processed"] += len(request.texts)

        return BatchPrivacyResponse(
            results=results,
            total_processed=len(results),
            level=level,
        )
    except ImportError as e:
        logger.error(f"Privacy engine not available: {e}")
        raise HTTPException(status_code=503, detail="Privacy service not available")
    except Exception as e:
        logger.exception("Batch processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/levels")
async def get_privacy_levels(auth: Auth = Depends()):
    """Get available privacy processing levels."""
    return {
        "levels": {
            "strict": "Maximum privacy protection, masks all potential PII",
            "balanced": "Balanced approach between privacy and utility",
            "minimal": "Minimal masking, only obvious PII",
        },
        "default": "balanced",
    }


@router.get("/stats")
async def get_privacy_stats(auth: Auth = Depends()):
    """Get privacy processing statistics."""
    uptime_sec = time.time() - _stats["_start_time"]
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    return {
        "total_requests": _stats["total_requests"],
        "entities_detected": _stats["entities_detected"],
        "texts_processed": _stats["texts_processed"],
        "uptime": f"{days}d {hours}h {minutes}m",
    }
