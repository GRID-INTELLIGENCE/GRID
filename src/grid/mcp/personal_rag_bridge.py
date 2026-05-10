"""Bridge layer: grid-intelligence → personal-rag query_federated.

Same-host direct import — personal-rag runs under the same Python environment.
Falls back gracefully when personal-rag is unreachable or Ollama is down.
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

PERSONAL_RAG_DIR = Path.home() / "intelligence" / "personal-rag"


class PersonalRagBridgeError(Exception):
    """Raised when the bridge cannot reach personal-rag."""


def _ensure_importable() -> bool:
    """Add personal-rag to sys.path if not already present."""
    rag_str = str(PERSONAL_RAG_DIR)
    if rag_str not in sys.path:
        if not PERSONAL_RAG_DIR.exists():
            return False
        sys.path.insert(0, rag_str)
    return True


def query_personal_rag(
    query: str,
    digest_sha256: str,
    k: int = 5,
    source_filter: str = "",
    min_score: float = 0.65,
    governance_tier_filter: str = "",
) -> dict:
    """Call personal-rag's query_federated and optionally filter by governance tier.

    Args:
        query: Natural language query.
        digest_sha256: 12-char sha256 prefix from get_session_digest.
        k: Number of chunks to retrieve (1-50).
        source_filter: Comma-separated source types.
        min_score: Minimum similarity threshold.
        governance_tier_filter: Comma-separated tier filter (T0,T1,T2,T3).

    Returns:
        Parsed JSON dict with keys: system, query, total, chunks, provenance.

    Raises:
        PersonalRagBridgeError: When personal-rag is unreachable or returns an error.
    """
    if not _ensure_importable():
        raise PersonalRagBridgeError(
            f"personal-rag not found at {PERSONAL_RAG_DIR}"
        )

    try:
        from mcp_server import query_federated
    except ImportError as exc:
        raise PersonalRagBridgeError(
            f"Failed to import personal-rag: {exc}"
        ) from exc

    try:
        result_json = query_federated(
            query=query,
            digest_sha256=digest_sha256,
            k=k,
            source_filter=source_filter,
            min_score=min_score,
            rerank_by_gravity=True,
        )
    except Exception as exc:
        raise PersonalRagBridgeError(
            f"personal-rag query failed: {exc}"
        ) from exc

    data = json.loads(result_json)

    if "error" in data:
        raise PersonalRagBridgeError(data["error"])

    if governance_tier_filter:
        tiers = {t.strip().upper() for t in governance_tier_filter.split(",") if t.strip()}
        if tiers:
            data["chunks"] = [
                c for c in data.get("chunks", [])
                if c.get("governance_tier", "").upper() in tiers
            ]
            data["total"] = len(data["chunks"])
            data["governance_tier_filter"] = sorted(tiers)

    return data
