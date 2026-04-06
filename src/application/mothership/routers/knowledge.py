"""
Knowledge Graph Ingestion Router.

Exposes POST /knowledge/ingest for feeding documents into the
GRID knowledge graph (entity extraction + vector indexing).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import time
from typing import Annotated, Any, Literal, NoReturn

from fastapi import APIRouter, Body, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field, ValidationError

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

GRAPH_DEFAULT_MAX_NODES = 2_000
GRAPH_HARD_MAX_NODES = 2_000
GRAPH_DEFAULT_MAX_EDGES = 8_000
GRAPH_HARD_MAX_EDGES = 20_000
GRAPH_DEFAULT_TIMEOUT_MS = 1_500
GRAPH_HARD_TIMEOUT_MS = 10_000

GraphDecisionCode = Literal[
    "SCHEMA_INVALID",
    "GRAPH_TOO_LARGE",
    "LAYOUT_TIMEOUT",
    "INCONSISTENT_GRAPH",
    "UNSUPPORTED_REQUEST",
]


class IngestRequest(BaseModel):
    """Request body for text-based ingestion."""

    text: str = Field(..., description="Raw text or markdown to ingest")
    source_name: str = Field(default="inline", description="Display name for the document")
    use_ollama: bool = Field(default=True, description="Use Ollama LLM for extraction (falls back to heuristic)")
    ollama_model: str = Field(default="ministral:latest", description="Ollama model for extraction")
    index_vectors: bool = Field(default=False, description="Also index into ChromaDB vector store")


class IngestResponse(BaseModel):
    """Response from ingestion."""

    document_id: str
    source: str
    entities_written: int
    relations_written: int
    chunks_indexed: int
    extraction_method: str
    success: bool
    errors: list[str]


class KnowledgeGraphStatsResponse(BaseModel):
    total_entities: int
    total_relationships: int
    entity_counts: dict[str, int]
    relationship_counts: dict[str, int]
    storage_path: str


class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: str
    subtitle: str = ""


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    label: str


class GraphLimits(BaseModel):
    requested_max_nodes: int | None = None
    applied_max_nodes: int
    max_edges: int
    timeout_ms: int
    export_ms: int


class GraphDecisionError(BaseModel):
    code: GraphDecisionCode
    message: str
    status: int
    suggested_actions: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    storage_path: str | None = None
    total_entities: int
    truncated: bool
    graph_hash: str
    limits: GraphLimits


def _run_ingest(source: str | Path, use_ollama: bool, ollama_model: str, index_vectors: bool) -> Any:
    """Import and run ingestion pipeline."""
    from grid.knowledge.ingest import IngestConfig, ingest  # noqa: PLC0415

    config = IngestConfig(
        use_ollama=use_ollama,
        ollama_model=ollama_model,
        index_vectors=index_vectors,
    )
    return ingest(source, config=config)


def _raise_graph_error(
    *,
    code: GraphDecisionCode,
    message: str,
    status_code: int,
    suggested_actions: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail=GraphDecisionError(
            code=code,
            message=message,
            status=status_code,
            suggested_actions=suggested_actions or [],
            details=details or {},
        ).model_dump(),
    )


def _export_graph_payload(max_nodes: int) -> dict[str, Any]:
    from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore  # noqa: PLC0415

    with PersistentJSONKnowledgeStore() as store:
        return store.export_graph_visualization(max_nodes=max_nodes)


def _validation_error_messages(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for item in exc.errors()[:6]:
        path = ".".join(str(x) for x in item.get("loc", []))
        msg = item.get("msg", "validation error")
        messages.append(f"{path}: {msg}" if path else str(msg))
    return messages


def _coerce_graph_payload(payload: Any, *, max_edges: int) -> tuple[list[GraphNode], list[GraphEdge], str | None, int, bool]:
    if not isinstance(payload, dict):
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph payload is not an object",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    raw_nodes = payload.get("nodes")
    raw_edges = payload.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph payload must include nodes and edges arrays",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    try:
        nodes = [GraphNode.model_validate(item) for item in raw_nodes]
        edges = [GraphEdge.model_validate(item) for item in raw_edges]
    except ValidationError as exc:
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph payload does not match schema",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details={"validation_errors": _validation_error_messages(exc)},
        )

    known_ids = {n.id for n in nodes}
    for edge in edges:
        if edge.source not in known_ids or edge.target not in known_ids:
            _raise_graph_error(
                code="INCONSISTENT_GRAPH",
                message="Graph edges reference nodes that are not present in the payload",
                status_code=status.HTTP_409_CONFLICT,
                suggested_actions=[
                    "Re-run ingestion for missing entities",
                    "Reduce max_nodes to a stable subset",
                ],
                details={"edge_id": edge.id, "source": edge.source, "target": edge.target},
            )

    if len(edges) > max_edges:
        _raise_graph_error(
            code="GRAPH_TOO_LARGE",
            message="Graph edge count exceeds the configured max_edges limit",
            status_code=status.HTTP_409_CONFLICT,
            suggested_actions=[
                "Lower max_nodes to reduce graph density",
                "Pass a higher max_edges value within allowed bounds",
            ],
            details={"edge_count": len(edges), "max_edges": max_edges},
        )

    storage_path = payload.get("storage_path")
    if storage_path is not None and not isinstance(storage_path, str):
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph storage_path must be a string when present",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    total_entities = payload.get("total_entities")
    if not isinstance(total_entities, int):
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph total_entities must be an integer",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    truncated = payload.get("truncated")
    if not isinstance(truncated, bool):
        _raise_graph_error(
            code="SCHEMA_INVALID",
            message="Knowledge graph truncated must be a boolean",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    return nodes, edges, storage_path, total_entities, truncated


def _stable_graph_hash(nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
    canonical_nodes = [item.model_dump() for item in sorted(nodes, key=lambda n: n.id)]
    canonical_edges = [
        item.model_dump()
        for item in sorted(
            edges,
            key=lambda e: (e.source, e.target, e.id),
        )
    ]
    digest = hashlib.sha256(
        json.dumps({"nodes": canonical_nodes, "edges": canonical_edges}, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return digest[:16]


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest a document into the knowledge graph",
    description=(
        "Extract concepts and relationships from text and store them in the "
        "GRID knowledge graph. Optionally also indexes into ChromaDB for vector search."
    ),
)
async def ingest_text(body: IngestRequest) -> IngestResponse:
    """Ingest raw text or markdown into the knowledge graph."""
    try:
        result = _run_ingest(
            source=body.text,
            use_ollama=body.use_ollama,
            ollama_model=body.ollama_model,
            index_vectors=body.index_vectors,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        document_id=result.document_id,
        source=result.source,
        entities_written=result.entities_written,
        relations_written=result.relations_written,
        chunks_indexed=result.chunks_indexed,
        extraction_method=result.extraction_method,
        success=result.success,
        errors=result.errors,
    )


@router.post(
    "/ingest/file",
    response_model=IngestResponse,
    summary="Ingest an uploaded file into the knowledge graph",
)
async def ingest_file(
    file: UploadFile,
    use_ollama: bool = True,
    ollama_model: str = "ministral:latest",
    index_vectors: bool = False,
) -> IngestResponse:
    """Ingest an uploaded file (markdown, text, etc.) into the knowledge graph."""
    import tempfile

    content = await file.read()
    suffix = Path(file.filename or "upload.txt").suffix

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = _run_ingest(
            source=tmp_path,
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            index_vectors=index_vectors,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc
    finally:
        await asyncio.to_thread(tmp_path.unlink, missing_ok=True)

    return IngestResponse(
        document_id=result.document_id,
        source=file.filename or "<upload>",
        entities_written=result.entities_written,
        relations_written=result.relations_written,
        chunks_indexed=result.chunks_indexed,
        extraction_method=result.extraction_method,
        success=result.success,
        errors=result.errors,
    )


@router.get(
    "/stats",
    response_model=KnowledgeGraphStatsResponse,
    summary="Knowledge graph statistics",
)
async def knowledge_stats() -> KnowledgeGraphStatsResponse:
    """Return current entity and relationship counts from the knowledge graph."""
    try:
        from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore  # noqa: PLC0415

        with PersistentJSONKnowledgeStore() as store:
            stats = store.get_graph_statistics()
        return KnowledgeGraphStatsResponse.model_validate(stats)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {exc}",
        ) from exc


@router.get(
    "/graph",
    response_model=KnowledgeGraphResponse,
    summary="Knowledge graph for visualization",
    description=(
        "Return nodes and edges from the persisted JSON knowledge graph for "
        "client-side rendering (e.g. force-directed layout). "
        "Optional max_nodes caps payload size (stable order by entity id)."
    ),
)
async def knowledge_graph(
    max_nodes: Annotated[
        int | None,
        Query(
            ge=1,
            description="Maximum entities to include; edges are filtered to endpoints in the set.",
        ),
    ] = None,
    max_edges: Annotated[
        int,
        Query(
            ge=1,
            description="Maximum edges allowed in the response. Exceeding this fails with GRAPH_TOO_LARGE.",
        ),
    ] = GRAPH_DEFAULT_MAX_EDGES,
    timeout_ms: Annotated[
        int,
        Query(
            ge=50,
            description="Maximum server export time budget in milliseconds.",
        ),
    ] = GRAPH_DEFAULT_TIMEOUT_MS,
) -> KnowledgeGraphResponse:
    """Export entities and relationships as nodes and edges."""
    if timeout_ms > GRAPH_HARD_TIMEOUT_MS:
        _raise_graph_error(
            code="UNSUPPORTED_REQUEST",
            message="Requested timeout exceeds allowed maximum",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"requested_timeout_ms": timeout_ms, "max_timeout_ms": GRAPH_HARD_TIMEOUT_MS},
        )

    effective_max_nodes = max_nodes if max_nodes is not None else GRAPH_DEFAULT_MAX_NODES
    if effective_max_nodes > GRAPH_HARD_MAX_NODES:
        _raise_graph_error(
            code="GRAPH_TOO_LARGE",
            message="Requested max_nodes exceeds allowed hard limit",
            status_code=status.HTTP_409_CONFLICT,
            suggested_actions=[
                "Lower max_nodes to the hard limit",
                "Apply server-side filtering before requesting visualization",
            ],
            details={"requested_max_nodes": effective_max_nodes, "hard_max_nodes": GRAPH_HARD_MAX_NODES},
        )

    if max_edges > GRAPH_HARD_MAX_EDGES:
        _raise_graph_error(
            code="GRAPH_TOO_LARGE",
            message="Requested max_edges exceeds allowed hard limit",
            status_code=status.HTTP_409_CONFLICT,
            suggested_actions=[
                "Lower max_edges to the hard limit",
                "Reduce max_nodes to lower graph density",
            ],
            details={"requested_max_edges": max_edges, "hard_max_edges": GRAPH_HARD_MAX_EDGES},
        )

    started = time.perf_counter()
    try:
        payload = _export_graph_payload(effective_max_nodes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export knowledge graph: {exc}",
        ) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    if elapsed_ms > timeout_ms:
        _raise_graph_error(
            code="LAYOUT_TIMEOUT",
            message="Knowledge graph export exceeded time budget",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            suggested_actions=[
                "Lower max_nodes and retry",
                "Retry with a higher timeout_ms value",
            ],
            details={
                "timeout_ms": timeout_ms,
                "export_ms": elapsed_ms,
                "max_nodes": effective_max_nodes,
            },
        )

    nodes, edges, storage_path, total_entities, truncated = _coerce_graph_payload(payload, max_edges=max_edges)
    graph_hash = _stable_graph_hash(nodes, edges)

    return KnowledgeGraphResponse(
        nodes=nodes,
        edges=edges,
        storage_path=storage_path,
        total_entities=total_entities,
        truncated=truncated,
        graph_hash=graph_hash,
        limits=GraphLimits(
            requested_max_nodes=max_nodes,
            applied_max_nodes=effective_max_nodes,
            max_edges=max_edges,
            timeout_ms=timeout_ms,
            export_ms=elapsed_ms,
        ),
    )


__all__ = ["router"]
