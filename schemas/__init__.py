"""
Schemas for the GRID framework.

JSON Schemas (Draft-07):
- batch_validation_schema.json: File validation reports, metrics, issue tracking
- progress_compass_schema.json: Mid-journey checkpoints, compass, signals
- knowledge_graph_schema.json: KG entities, relationships, ontology
- resonance_api_openapi.json: OpenAPI spec for Resonance API
- platform_integration_schema.json: External platform integrations
- sound_layer_schema.json: Audio/sound layer configuration
- vision_layer_schema.json: Visual layer configuration

Python Schemas:
- delegation_task.py: DelegationTask dataclass for machine-readable tasks
"""

from .delegation_task import DelegationTask

__all__ = ["DelegationTask"]
