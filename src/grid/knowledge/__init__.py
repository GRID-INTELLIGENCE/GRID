"""Knowledge graph and structural learning package."""

from .graph_store import EntityId, RelationshipId, SearchContext
from .ingest import IngestConfig, IngestResult, ingest, ingest_many
from .persistent_store import PersistentJSONKnowledgeStore as _PersistentJSONKnowledgeStoreLegacy
from .sqlite_store import PersistentSQLiteKnowledgeStore

# Transparent alias: all consumers importing PersistentJSONKnowledgeStore
# now receive the SQLite-backed implementation. The original JSON class is
# still importable directly from grid.knowledge.persistent_store if needed.
PersistentJSONKnowledgeStore = PersistentSQLiteKnowledgeStore
from .structural_learning import (
    AdaptiveRelationshipModel,
    Entity,
    EntityType,
    EntityTypingFramework,
    HierarchyEvolutionTracker,
    HierarchyLevel,
    Relationship,
    StructuralLearningLayer,
)

__all__ = [
    "Entity",
    "Relationship",
    "HierarchyLevel",
    "EntityType",
    "EntityTypingFramework",
    "AdaptiveRelationshipModel",
    "HierarchyEvolutionTracker",
    "StructuralLearningLayer",
    "PersistentJSONKnowledgeStore",
    "PersistentSQLiteKnowledgeStore",
    "EntityId",
    "RelationshipId",
    "SearchContext",
    "IngestConfig",
    "IngestResult",
    "ingest",
    "ingest_many",
]
