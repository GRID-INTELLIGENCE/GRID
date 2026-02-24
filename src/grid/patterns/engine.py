"""Pattern engine with RAG context retrieval, MIST detection, and match persistence."""

from __future__ import annotations

from typing import Any

from grid.exceptions import DataSaveError


class PatternEngine:
    """Core pattern engine supporting RAG context, MIST unknowable detection, and match saving."""

    def __init__(self, retrieval_service: Any | None = None) -> None:
        self.retrieval_service = retrieval_service

    def retrieve_rag_context(self, query: str) -> dict[str, Any]:
        """Retrieve context using RAG.

        Returns empty dict on error or when no retrieval service is configured.
        """
        if not self.retrieval_service:
            return {}
        try:
            return self.retrieval_service.retrieve_context(query)
        except Exception:
            return {}

    def detect_mist_pattern(self, matches: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Detect MIST (unknowable) pattern when no patterns match.

        Returns a MIST_UNKNOWABLE result when the match list is empty,
        indicating the input could not be classified by any known pattern.
        """
        if not matches:
            return {
                "pattern_code": "MIST_UNKNOWABLE",
                "confidence": 0.5,
                "description": "Pattern unknown or not yet understood",
            }
        return None

    def save_pattern_matches(self, entity_id: str, matches: list[dict[str, Any]]) -> list[Any]:
        """Validate and save pattern matches.

        Raises DataSaveError if required fields are missing.
        """
        for match in matches:
            if "confidence" not in match:
                raise DataSaveError("Missing 'confidence' in pattern match")
            if "pattern_code" not in match:
                raise DataSaveError("Missing 'pattern_code' in pattern match")

        saved = []
        for match in matches:
            obj = type("PatternMatch", (), {"entity_id": entity_id, **match})()
            saved.append(obj)

        return saved
