"""
GRID Knowledge Ingestion Pipeline.

Bridges document ingestion across two stores:
  1. ChromaDB (vector store) — for semantic similarity search
  2. PersistentJSONKnowledgeStore (graph store) — for entity/relationship traversal

Usage:
    from grid.knowledge.ingest import ingest, IngestConfig, IngestResult

    result = ingest("path/to/paper.md")
    print(result.entities_written, result.relations_written)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from .concept_extractor import (
    ExtractionResult,
    build_concept_entities,
    build_relationship_entities,
    extract_heuristic,
    extract_with_ollama,
)
from .graph_schema import EntityType, RelationType
from .graph_store import Entity, EntityId, Relationship
from .persistent_store import PersistentJSONKnowledgeStore

logger = structlog.get_logger(__name__)


@dataclass
class IngestConfig:
    """Configuration for the ingestion pipeline."""

    # Extraction mode
    use_ollama: bool = True
    ollama_model: str = "ministral:latest"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: float = 60.0

    # Vector indexing (ChromaDB)
    index_vectors: bool = True

    # Graph store path (None = default dev/knowledge_graph.json)
    store_path: str | None = None


@dataclass
class IngestResult:
    """Result of a single ingestion operation."""

    document_id: str
    source: str
    entities_written: int = 0
    relations_written: int = 0
    chunks_indexed: int = 0
    extraction_method: str = "heuristic"
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = [
            f"Document : {self.source}",
            f"ID       : {self.document_id}",
            f"Method   : {self.extraction_method}",
            f"Entities : {self.entities_written}",
            f"Relations: {self.relations_written}",
            f"Chunks   : {self.chunks_indexed}",
        ]
        if self.errors:
            lines.append(f"Errors   : {'; '.join(self.errors)}")
        return "\n".join(lines)


def _detect_content_type(source: str | Path) -> str:
    """Detect content type from file extension."""
    path = Path(source)
    suffix = path.suffix.lower()
    return {
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "text",
        ".rst": "text",
        ".py": "code",
        ".ts": "code",
        ".js": "code",
    }.get(suffix, "text")


def _read_source(source: str | Path) -> tuple[str, str]:
    """Read content from file path or treat source as raw text. Returns (content, display_name)."""
    # Fast-path: if source is already a Path object, or a short string without newlines,
    # attempt to resolve as a file path.
    if isinstance(source, Path):
        if source.exists():
            return source.read_text(encoding="utf-8"), str(source)
        return str(source), str(source)

    raw = str(source)
    # If the string contains newlines or exceeds OS path length limits, treat as raw text
    if "\n" in raw or len(raw) > 4096:
        return raw, "<inline text>"

    path = Path(raw)
    try:
        if path.exists():
            return path.read_text(encoding="utf-8"), str(path)
    except OSError:
        pass
    return raw, "<inline text>"


def _document_id(source: str, content: str) -> str:
    """Generate a stable document ID from source + content hash."""
    digest = hashlib.sha256((source + content[:500]).encode()).hexdigest()[:12]
    return f"doc_{digest}"


def _build_document_entity(
    doc_id: str,
    name: str,
    source: str,
    content_type: str,
    chunk_count: int,
) -> Entity:
    now = datetime.now(UTC)
    return Entity(
        entity_id=doc_id,
        entity_type=EntityType.DOCUMENT,
        properties={
            "id": doc_id,
            "name": name,
            "source": source,
            "content_type": content_type,
            "chunk_count": chunk_count,
            "created_at": now.isoformat(),
            "metadata": {},
        },
        created_at=now,
        updated_at=now,
        labels={"document"},
    )


def _build_explains_relationships(
    document_id: str,
    concept_entities: list[Entity],
) -> list[Relationship]:
    """Create EXPLAINS edges from document to each concept."""
    now = datetime.now(UTC)
    relationships = []
    for concept in concept_entities:
        excerpt = concept.properties.get("metadata", {}).get("excerpt", "")
        confidence = concept.properties.get("metadata", {}).get("confidence", 1.0)
        relationships.append(
            Relationship(
                relationship_id=str(uuid4()),
                from_entity_id=document_id,
                to_entity_id=concept.entity_id,
                relationship_type=RelationType.EXPLAINS,
                properties={"excerpt": excerpt[:200], "confidence": confidence},
                created_at=now,
                updated_at=now,
            )
        )
    return relationships


def _try_index_vectors(content: str, source: str, config: IngestConfig) -> int:
    """Attempt to index content into ChromaDB. Returns chunk count or 0 on failure."""
    if not config.index_vectors:
        return 0
    try:
        from tools.rag.indexing.comprehensive_indexer import comprehensive_index  # type: ignore[import]

        path = Path(source)
        if not path.exists():
            return 0
        result = comprehensive_index(str(path.parent), file_patterns=[path.name])
        return result.get("chunks_indexed", 0) if isinstance(result, dict) else 0
    except Exception as exc:
        logger.debug("Vector indexing skipped", reason=str(exc))
        return 0


def ingest(
    source: str | Path,
    *,
    config: IngestConfig | None = None,
    store: PersistentJSONKnowledgeStore | None = None,
) -> IngestResult:
    """
    Ingest a document into the GRID knowledge graph.

    Reads the source, extracts concepts and relationships, writes
    them to the persistent JSON graph store, and optionally indexes
    chunks into ChromaDB for vector search.

    Args:
        source: File path or raw text string.
        config: Ingestion configuration. Defaults to IngestConfig().
        store: Existing store instance. Creates a new one if None.

    Returns:
        IngestResult with counts and status.
    """
    cfg = config or IngestConfig()
    content, display_name = _read_source(source)
    doc_id = _document_id(display_name, content)
    content_type = _detect_content_type(source)
    name = Path(display_name).name if display_name != "<inline text>" else doc_id

    log = logger.bind(document_id=doc_id, source=display_name)
    log.info("Starting ingestion")

    result = IngestResult(document_id=doc_id, source=display_name)

    # --- 1. Vector indexing (ChromaDB) ---
    chunk_count = _try_index_vectors(content, display_name, cfg)
    result.chunks_indexed = chunk_count

    # --- 2. Concept extraction ---
    try:
        if cfg.use_ollama:
            extraction: ExtractionResult = extract_with_ollama(
                content,
                model=cfg.ollama_model,
                base_url=cfg.ollama_base_url,
                timeout=cfg.ollama_timeout,
            )
        else:
            extraction = extract_heuristic(content)
        result.extraction_method = extraction.method
    except Exception as exc:
        msg = f"Extraction failed: {exc}"
        log.error(msg)
        result.errors.append(msg)
        return result

    log.info(
        "Extraction complete",
        concepts=len(extraction.concepts),
        relations=len(extraction.relations),
        method=extraction.method,
    )

    # --- 3. Build graph entities ---
    concept_entities = build_concept_entities(extraction.concepts, doc_id)
    concept_relations = build_relationship_entities(extraction.relations, concept_entities)
    doc_entity = _build_document_entity(doc_id, name, display_name, content_type, chunk_count)
    explains_relations = _build_explains_relationships(doc_id, concept_entities)

    # --- 4. Write to knowledge graph store ---
    own_store = store is None
    if own_store:
        store_path = cfg.store_path or "dev/knowledge_graph.json"
        store = PersistentJSONKnowledgeStore(storage_path=store_path)

    try:
        store.connect()  # type: ignore[union-attr]

        # Write document entity
        store.store_entity(doc_entity)  # type: ignore[union-attr]

        # Write concept entities
        for entity in concept_entities:
            try:
                store.store_entity(entity)  # type: ignore[union-attr]
                result.entities_written += 1
            except ValueError as exc:
                log.warning("Skipping concept entity", name=entity.properties.get("name"), error=str(exc))

        # Write EXPLAINS relationships (doc → concepts)
        for rel in explains_relations:
            try:
                store.relationships[rel.relationship_id] = rel  # type: ignore[union-attr]
                result.relations_written += 1
            except Exception as exc:
                log.warning("Skipping explains relation", error=str(exc))

        # Write CONNECTS_TO relationships (concept → concept)
        for rel in concept_relations:
            try:
                store.relationships[rel.relationship_id] = rel  # type: ignore[union-attr]
                result.relations_written += 1
            except Exception as exc:
                log.warning("Skipping concept relation", error=str(exc))

        store._save_to_disk()  # type: ignore[union-attr]

    except Exception as exc:
        msg = f"Store write failed: {exc}"
        log.error(msg)
        result.errors.append(msg)
    finally:
        if own_store:
            store.disconnect()  # type: ignore[union-attr]

    log.info(
        "Ingestion complete",
        entities=result.entities_written,
        relations=result.relations_written,
        errors=len(result.errors),
    )
    return result


def ingest_many(
    sources: list[str | Path],
    *,
    config: IngestConfig | None = None,
) -> list[IngestResult]:
    """Ingest multiple documents, sharing a single store connection."""
    cfg = config or IngestConfig()
    store_path = cfg.store_path or "dev/knowledge_graph.json"
    store = PersistentJSONKnowledgeStore(storage_path=store_path)
    store.connect()

    results = []
    try:
        for source in sources:
            result = ingest(source, config=cfg, store=store)
            results.append(result)
        store._save_to_disk()
    finally:
        store.disconnect()

    return results


__all__ = [
    "IngestConfig",
    "IngestResult",
    "ingest",
    "ingest_many",
]
