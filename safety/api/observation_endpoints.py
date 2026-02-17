"""
Runtime Observation Endpoints.
Exposes safety/security observation data via REST and WebSockets.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from safety.guardian.engine import get_guardian_engine
from safety.observability.metrics import DETECTOR_HEALTHY
from safety.observability.runtime_observation import observation_service
from safety.workers.worker_utils import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observe", tags=["observation"])


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """Get component health status."""
    return await observation_service.get_system_health()


@router.websocket("/stream")
async def stream_events(
    websocket: WebSocket,
    # token: str = Query(...) # Future: Implement auth
):
    """
    Real-time security observation stream.
    Requires privileged access (validated via auth token or session).
    """
    await websocket.accept()

    # Subscribe to event bus
    queue = await observation_service.event_bus.subscribe()

    try:
        while True:
            # Get event from queue
            event = await queue.get()

            # Serialize for WebSocket
            msg = {"type": "security_event", "payload": event.to_dict()}

            await websocket.send_json(msg)

    except WebSocketDisconnect:
        logger.info("Observation stream disconnected")
    except Exception as e:
        logger.error(f"Observation stream error: {e}")
    finally:
        observation_service.event_bus.unsubscribe(queue)


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """Get observation metrics."""
    return {
        "active_subscribers": observation_service.event_bus.subscriber_count,
        "detector_health": DETECTOR_HEALTHY._value.get(),
    }


# Phase 2 Endpoints (Placeholders)


@router.get("/rules")
async def get_rules():
    """Get active safety rules (Project GUARDIAN)."""
    engine = get_guardian_engine()
    stats = engine.get_stats()
    rules = engine.registry.get_all()
    return {
        "count": len(rules),
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "severity": r.severity.value,
                "action": r.action.value if r.action else None,
                "enabled": r.enabled,
            }
            for r in rules
        ],
        "stats": stats,
    }


@router.post("/rules/dynamic")
async def inject_rule(rule: dict[str, Any]):
    """
    Inject dynamic rule into Project GUARDIAN.
    Saves to Redis to sync across all instances.
    """
    # Validation
    required = ["id", "patterns"]
    for field in required:
        if field not in rule:
            return JSONResponse(status_code=400, content={"error": f"Missing field: {field}"})

    # Defaults
    rule.setdefault("name", f"Dynamic Rule {rule['id']}")
    rule.setdefault("reason_code", rule["id"])
    rule.setdefault("severity", "high")
    rule.setdefault("event_type", "ai_input_blocked")

    try:
        client = await get_redis()
        # Save to Redis for global sync
        await client.sadd("guardian:dynamic_rules", json.dumps(rule))  # type: ignore[reportAwaitableReturnType]

        # Trigger local cache clear so new rules take effect
        get_guardian_engine().clear_cache()

        return {"status": "success", "rule_id": rule["id"]}
    except Exception as e:
        logger.error(f"Failed to inject dynamic rule: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
