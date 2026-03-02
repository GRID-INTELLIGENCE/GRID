"""Core data models for the search engine.

API-boundary types (Document, SearchResponse, FieldSchema, etc.) use Pydantic
BaseModel for validation and serialisation.  Internal data-transfer objects
(ScoredCandidate, FilterClause) use @dataclass to match the GRID-main
convention established in tools.rag.intelligence and grid.patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FieldType(StrEnum):
    TEXT = "text"
    KEYWORD = "keyword"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"


class FilterOp(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"


class QueryIntent(StrEnum):
    NAVIGATIONAL = "navigational"
    EXPLORATORY = "exploratory"
    ANALYTICAL = "analytical"


# ---------------------------------------------------------------------------
# Pydantic models – API boundary / user-facing configuration
# ---------------------------------------------------------------------------


class FieldSchema(BaseModel):
    """Per-field configuration within an index schema."""

    type: FieldType
    searchable: bool = False
    filterable: bool = False
    facetable: bool = False
    weight: float = Field(default=1.0, ge=0.0)
    sensitive: bool = False  # when True, redacted in search results


class IndexSchema(BaseModel):
    """Defines the field layout for a search index."""

    name: str = Field(min_length=1)
    fields: dict[str, FieldSchema]

    def searchable_fields(self) -> dict[str, FieldSchema]:
        return {k: v for k, v in self.fields.items() if v.searchable}

    def filterable_fields(self) -> dict[str, FieldSchema]:
        return {k: v for k, v in self.fields.items() if v.filterable}

    def facetable_fields(self) -> dict[str, FieldSchema]:
        return {k: v for k, v in self.fields.items() if v.facetable}


class Document(BaseModel):
    """A structured record to be indexed and searched."""

    id: str = Field(min_length=1)
    fields: dict[str, Any]


class SearchHit(BaseModel):
    """A single search result returned to the caller."""

    document: Document
    score: float = 0.0
    highlights: dict[str, list[str]] = Field(default_factory=dict)
    explanation: dict[str, Any] = Field(default_factory=dict)


class FacetValue(BaseModel):
    """A single value within a facet bucket."""

    value: Any
    count: int


class FacetResult(BaseModel):
    """Aggregated facet for a single field."""

    field: str
    values: list[FacetValue] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Complete search response with hits, facets, and metadata."""

    hits: list[SearchHit] = Field(default_factory=list)
    facets: dict[str, FacetResult] = Field(default_factory=dict)
    total: int = 0
    page: int = 1
    size: int = 10
    took_ms: float = 0.0


# ---------------------------------------------------------------------------
# Dataclasses – internal data-transfer objects
# ---------------------------------------------------------------------------


@dataclass
class FilterClause:
    """A single filter condition on a field."""

    field: str
    op: FilterOp = FilterOp.EQ
    value: Any = None


@dataclass
class ScoredCandidate:
    """Intermediate result from a retriever with a relevance score."""

    doc_id: str
    score: float = 0.0
    source: str = ""


@dataclass
class RequestContext:
    """Context for guardrail processing (identity, index, request metadata)."""

    identity: str | None = None  # caller identity from auth
    index_name: str = ""
    query_text: str = ""
    filters: list[FilterClause] = dc_field(default_factory=list)
    page: int = 1
    size: int = 10
    ip_address: str | None = None
    tenant_id: str | None = None


@dataclass
class SearchQuery:
    """Parsed and enriched search query (internal representation)."""

    raw_text: str = ""
    text: str = ""
    filters: list[FilterClause] = dc_field(default_factory=list)
    facet_fields: list[str] = dc_field(default_factory=list)
    intent: QueryIntent = QueryIntent.EXPLORATORY
    intent_confidence: float = 0.5
    expanded_terms: list[str] = dc_field(default_factory=list)
    page: int = 1
    size: int = 10
