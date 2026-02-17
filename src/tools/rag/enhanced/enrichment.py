"""
RAG Metadata Enrichment - Cross-referencing RAG chunks with Knowledge Graph entities.
"""

import json
import logging
import re
from typing import Any

from grid.knowledge import PersistentJSONKnowledgeStore

logger = logging.getLogger(__name__)


class RAGMetadataEnricher:
    """Enriches RAG metadata with Knowledge Graph entity references."""

    def __init__(self, store: PersistentJSONKnowledgeStore | None = None):
        self.store = store or PersistentJSONKnowledgeStore()
        self.entity_map: dict[str, str] = {}  # name -> entity_id
        self._initialized = False

    def _initialize(self):
        """Load entity names for matching."""
        try:
            self.store.connect()
            for eid, entity in self.store.entities.items():
                name = entity.properties.get("name")
                if name:
                    self.entity_map[name.lower()] = eid
            self._initialized = True
            logger.info(f"RAGMetadataEnricher initialized with {len(self.entity_map)} entities.")
        except Exception as e:
            logger.error(f"Failed to initialize enricher: {e}")

    def enrich_metadata(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Scan text for entity mentions and add them to metadata.
        """
        if not self._initialized:
            self._initialize()

        if not self.entity_map:
            return metadata

        mentions = []
        text_lower = text.lower()

        for name, eid in self.entity_map.items():
            # Use word boundaries for matching
            pattern = rf"\b{re.escape(name)}\b"
            if re.search(pattern, text_lower):
                mentions.append({"entity_id": eid, "name": name, "type": self.store.entities[eid].entity_type.value})

        if mentions:
            metadata["kg_entities"] = json.dumps(mentions)
            metadata["kg_entity_ids"] = json.dumps([m["entity_id"] for m in mentions])
            metadata["kg_entity_count"] = len(mentions)
            logger.debug(f"Enriched chunk with {len(mentions)} KG entities.")

        return metadata
