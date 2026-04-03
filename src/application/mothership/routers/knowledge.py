"""
Knowledge Graph Ingestion Router.

Exposes POST /knowledge/ingest for feeding documents into the
GRID knowledge graph (entity extraction + vector indexing).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


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


def _run_ingest(source: str | Path, use_ollama: bool, ollama_model: str, index_vectors: bool) -> Any:
    """Import and run ingestion pipeline."""
    from grid.knowledge.ingest import IngestConfig, ingest  # noqa: PLC0415

    config = IngestConfig(
        use_ollama=use_ollama,
        ollama_model=ollama_model,
        index_vectors=index_vectors,
    )
    return ingest(source, config=config)


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
    summary="Knowledge graph statistics",
)
async def knowledge_stats() -> dict[str, Any]:
    """Return current entity and relationship counts from the knowledge graph."""
    try:
        from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore  # noqa: PLC0415

        store = PersistentJSONKnowledgeStore()
        store.connect()
        stats = store.get_graph_statistics()
        store.disconnect()
        return stats
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {exc}",
        ) from exc


@router.get(
    "/graph",
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
            le=10_000,
            description="Maximum entities to include; edges are filtered to endpoints in the set.",
        ),
    ] = None,
) -> dict[str, Any]:
    """Export entities and relationships as nodes and edges."""
    try:
        from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore  # noqa: PLC0415

        store = PersistentJSONKnowledgeStore()
        store.connect()
        payload = store.export_graph_visualization(max_nodes=max_nodes)
        store.disconnect()
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export knowledge graph: {exc}",
        ) from exc


__all__ = ["router"]
