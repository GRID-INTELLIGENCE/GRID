import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from safety.privacy.engine import PrivacyEngine, PrivacyLevel

from ...core.config import settings
from ...core.security import get_current_active_user
from ...models.user import User

router = APIRouter()

# Stats for usage reporting (incremented by detect, mask, batch endpoints)
_stats = {"total_requests": 0, "entities_detected": 0, "texts_processed": 0, "_start_time": time.time()}


def _get_privacy_level(level_str: str | None) -> PrivacyLevel:
    """Map level string to PrivacyLevel enum."""
    level_str = level_str or settings.PRIVACY_LEVEL
    try:
        return PrivacyLevel(level_str.lower())
    except ValueError:
        return PrivacyLevel.BALANCED


def _entity_to_dict(entity: Any) -> dict[str, Any]:
    """Convert DetectedEntity to API response dict."""
    return {
        "type": entity.type,
        "value": entity.value,
        "start": entity.start,
        "end": entity.end,
    }


class PrivacyRequest(BaseModel):
    text: str
    level: str | None = None
    context: str | None = None


class PrivacyBatchRequest(BaseModel):
    texts: list[str]
    level: str | None = None
    context: str | None = None


class DetectionRequest(BaseModel):
    text: str


class DetectionResponse(BaseModel):
    detected_entities: list[dict[str, Any]]
    entity_count: int


@router.post("/detect", response_model=DetectionResponse)
async def detect_pii(request: DetectionRequest, current_user: User = Depends(get_current_active_user)):
    """Detect PII entities in text"""
    try:
        engine = PrivacyEngine(level=_get_privacy_level(None))
        detected = engine.detect(request.text)
        detected_entities = [_entity_to_dict(e) for e in detected]
        _stats["total_requests"] += 1
        _stats["entities_detected"] += len(detected_entities)
        return DetectionResponse(detected_entities=detected_entities, entity_count=len(detected_entities))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII detection failed: {str(e)}")


@router.post("/mask")
async def mask_pii(request: PrivacyRequest, current_user: User = Depends(get_current_active_user)):
    """Mask PII entities in text"""
    try:
        engine = PrivacyEngine(level=_get_privacy_level(request.level))
        result = engine.mask_text(request.text)
        _stats["total_requests"] += 1
        _stats["entities_detected"] += len(result.detected_entities)
        _stats["texts_processed"] += 1
        return {
            "original_text": request.text,
            "masked_text": result.masked_text,
            "detected_entities": [_entity_to_dict(e) for e in result.detected_entities],
            "applied_rules": result.applied_rules,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII masking failed: {str(e)}")


@router.post("/batch")
async def batch_privacy_processing(request: PrivacyBatchRequest, current_user: User = Depends(get_current_active_user)):
    """Process multiple texts for PII detection and masking"""
    try:
        engine = PrivacyEngine(level=_get_privacy_level(request.level))
        privacy_results = engine.batch_process(request.texts)
        results = []
        total_entities = 0
        for text, pr in zip(request.texts, privacy_results, strict=False):
            results.append(
                {
                    "original_text": text,
                    "masked_text": pr.masked_text,
                    "detected_entities": [_entity_to_dict(e) for e in pr.detected_entities],
                }
            )
            total_entities += len(pr.detected_entities)
        _stats["total_requests"] += 1
        _stats["entities_detected"] += total_entities
        _stats["texts_processed"] += len(request.texts)
        return {"results": results, "total_processed": len(results), "level": request.level or settings.PRIVACY_LEVEL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/levels")
async def get_privacy_levels(current_user: User = Depends(get_current_active_user)):
    """Get available privacy processing levels"""
    return {
        "levels": {
            "strict": "Maximum privacy protection, masks all potential PII",
            "balanced": "Balanced approach between privacy and utility",
            "minimal": "Minimal masking, only obvious PII",
        },
        "default": settings.PRIVACY_LEVEL,
    }


@router.get("/stats")
async def get_privacy_stats(current_user: User = Depends(get_current_active_user)):
    """Get privacy processing statistics"""
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
