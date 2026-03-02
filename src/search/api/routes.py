"""FastAPI routes for the search service, matching the contract endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import SearchConfig
from ..engine import SearchEngine
from ..guardrail import GuardrailContext, GuardrailOrchestrator, create_default_registry
from ..models import Document, FieldSchema, IndexSchema, RequestContext
from .middleware import LatencyTracker

# ---------------------------------------------------------------------------
# Request / response schemas (Pydantic at the API boundary)
# ---------------------------------------------------------------------------


class SchemaCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    fields: dict[str, FieldSchema]


class IndexDocumentsRequest(BaseModel):
    documents: list[Document]


class SearchRequest(BaseModel):
    query: str = ""
    facet_fields: list[str] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=1000)


class HealthResponse(BaseModel):
    status: str = "ok"
    indices: list[str] = Field(default_factory=list)
    latency_stats: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_search_router(
    engine: SearchEngine | None = None,
    config: SearchConfig | None = None,
) -> APIRouter:
    """Create a FastAPI router wired to the given SearchEngine instance.

    If no engine is provided a default one is created with SearchConfig
    loaded from the environment. When guardrail_enabled is True, search
    requests are wrapped by the GuardrailOrchestrator.
    """
    if engine is None:
        engine = SearchEngine(config=config)
    cfg = config or SearchConfig()
    router = APIRouter(prefix="/api/search", tags=["search"])
    tracker = LatencyTracker()

    orchestrator: GuardrailOrchestrator | None = None
    if getattr(cfg, "guardrail_enabled", False):
        orchestrator = GuardrailOrchestrator(
            registry=create_default_registry(),
            config=cfg,
        )

    # -- Schema management --------------------------------------------------

    @router.put("/{index_name}/schema")
    def create_or_update_schema(index_name: str, req: SchemaCreateRequest) -> dict[str, str]:
        schema = IndexSchema(name=index_name, fields=req.fields)
        try:
            engine.create_index(schema)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "created", "index": index_name}

    # -- Document indexing --------------------------------------------------

    @router.post("/{index_name}/index")
    def index_documents(index_name: str, req: IndexDocumentsRequest) -> dict[str, Any]:
        try:
            count = engine.index_documents(index_name, req.documents)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"indexed": count}

    # -- Search -------------------------------------------------------------

    async def _search_with_guardrail(
        request: Request,
        index_name: str,
        req: SearchRequest,
    ) -> dict[str, Any]:
        identity = getattr(request.state, "identity", None) if request else None
        if identity is None and request:
            auth = request.headers.get("Authorization")
            if auth and (auth.startswith("Bearer ") or auth.startswith("ApiKey ")):
                identity = auth.split(" ", 1)[1].strip() or None
        client_host = request.client.host if request and request.client else None
        ctx = GuardrailContext(
            request=RequestContext(
                identity=identity,
                index_name=index_name,
                query_text=req.query,
                page=req.page,
                size=req.size,
                ip_address=client_host,
            ),
            config=cfg,
        )
        gr_result = await orchestrator.run_pre_query(ctx)
        if gr_result.blocked:
            reason = gr_result.block_reason or ""
            if "Rate limit" in reason or "rate limit" in reason:
                raise HTTPException(status_code=429, detail=reason)
            if "Authentication" in reason or "auth" in reason.lower():
                raise HTTPException(status_code=401, detail=reason)
            raise HTTPException(status_code=403, detail=reason)
        try:
            response = engine.search(
                index_name,
                query=req.query,
                facet_fields=req.facet_fields or None,
                page=req.page,
                size=req.size,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        ctx.response = response
        idx_state = engine._indices.get(index_name)
        ctx.schema = idx_state.schema if idx_state else None
        post_result = await orchestrator.run_post_query(ctx, response)
        if post_result.blocked:
            raise HTTPException(
                status_code=403,
                detail=post_result.block_reason or "Response blocked by guardrail",
            )
        tracker.record(response.took_ms)
        return response.model_dump()

    @router.post("/{index_name}/query")
    async def search(
        request: Request,
        index_name: str,
        req: SearchRequest,
    ) -> dict[str, Any]:
        try:
            if orchestrator is not None:
                return await _search_with_guardrail(request, index_name, req)
            response = engine.search(
                index_name,
                query=req.query,
                facet_fields=req.facet_fields or None,
                page=req.page,
                size=req.size,
            )
            tracker.record(response.took_ms)
            return response.model_dump()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    # -- Index management ---------------------------------------------------

    @router.delete("/{index_name}")
    def delete_index(index_name: str) -> dict[str, str]:
        try:
            engine.delete_index(index_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"status": "deleted", "index": index_name}

    @router.get("/{index_name}/stats")
    def index_stats(index_name: str) -> dict[str, Any]:
        try:
            return engine.get_index_stats(index_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    # -- Health -------------------------------------------------------------

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            indices=engine.list_indices(),
            latency_stats=tracker.stats(),
        )

    return router
