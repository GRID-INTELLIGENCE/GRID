from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from application.mothership.dependencies import Auth, RateLimited, RequestContext
from application.mothership.schemas import ApiResponse, ResponseMeta
from grid.application import IntelligenceApplication

router = APIRouter(tags=["intelligence"])

_APP: IntelligenceApplication | None = None


def _get_app() -> IntelligenceApplication:
    global _APP
    if _APP is None:
        _APP = IntelligenceApplication()
    return _APP


class IntelligenceProcessRequest(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    include_evidence: bool = True
    reset_session: bool = False


@router.post("/process", response_model=ApiResponse[dict[str, Any]])
async def process_intelligence(
    payload: IntelligenceProcessRequest,
    _: RateLimited,
    auth: Auth,
    request_context: RequestContext,
) -> ApiResponse[dict[str, Any]]:
    app = _get_app()

    if payload.reset_session:
        app.reset()

    ctx = dict(payload.context)
    if auth and isinstance(auth, dict):
        ctx.setdefault("user_id", auth.get("user_id"))

    t0 = time.perf_counter()
    result = await app.process_input(payload.data, ctx, include_evidence=payload.include_evidence)
    t1 = time.perf_counter()

    if payload.include_evidence:
        result.setdefault("timings_ms", {})
        result["timings_ms"].setdefault("api_total_ms", (t1 - t0) * 1000.0)
        result["interaction_count"] = len(app.interaction_log)

    response = ApiResponse(
        success=True,
        data=result,
        meta=ResponseMeta(
            request_id=(request_context or {}).get("request_id"),
        ),
    )
    return response
