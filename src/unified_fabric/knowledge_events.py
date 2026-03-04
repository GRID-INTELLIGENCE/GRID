"""
Unified Fabric - Knowledge Event Schemas
=========================================
Event schemas for federated knowledge queries between GRID and Pathways.
"""

from __future__ import annotations

from .event_schemas import EventSchema, register_schemas


def register_knowledge_schemas() -> None:
    """Register knowledge federation event schemas.

    These schemas are already registered in bootstrap_default_schemas()
    in event_schemas.py. This function exists as a named entry point
    for documentation and explicit registration if needed.
    """
    register_schemas(
        [
            EventSchema(
                event_type="pathways.knowledge.query",
                domain="pathways",
                required_keys=("question",),
                optional_keys=("top_k", "scope", "metadata"),
                description="Pathways knowledge query request",
            ),
            EventSchema(
                event_type="pathways.knowledge.result",
                domain="pathways",
                required_keys=("question", "results"),
                optional_keys=("scope", "metadata"),
                description="Pathways knowledge query result",
            ),
            EventSchema(
                event_type="grid.knowledge.federated",
                domain="grid",
                required_keys=("question", "sources"),
                optional_keys=("results", "patterns_applied", "metadata"),
                description="Federated knowledge query result combining GRID and Pathways",
            ),
        ]
    )
