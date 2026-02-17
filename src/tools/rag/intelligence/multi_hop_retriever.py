"""
Multi-Hop Retriever for Intelligent RAG.

This module implements multi-hop retrieval, allowing the RAG system to follow
references across documents (e.g., following an import or a documentation link)
to build a more complete context for complex queries.
"""

import logging
import re
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


class MultiHopRetriever:
    """
    Expands retrieval by following cross-references found in initial search results.

    This is particularly useful for:
    1. Following imports in code (e.g., finding the definition of an imported class).
    2. Following links in documentation (e.g., "see ARCHITECTURE.md").
    3. Connecting related concepts that aren't in the same chunk.
    """

    def __init__(self, base_retriever: Any, max_hops: int = 2, min_relevance_for_hop: float = 0.4):
        """
        Initialize the multi-hop retriever.

        Args:
            base_retriever: The underlying retriever (e.g., HybridRetriever or RAGEngine).
            max_hops: Maximum number of expansion steps.
            min_relevance_for_hop: Minimum score required for a document to trigger a hop.
        """
        self.base_retriever = base_retriever
        self.max_hops = max_hops
        self.min_relevance_for_hop = min_relevance_for_hop

        # Patterns to find "hops" in different file types
        self.reference_patterns = {
            "python_import": r"(?:from|import)\s+([\w\.]+)",
            "doc_link": r"\[\[([^\]]+)\]\]|\[[^\]]+\]\(([^\)]+\.md)\)",
            "file_ref": r"\b([\w\-/]+\.(?:py|md|toml|yaml|json|sh))\b",
            "backtick_ref": r"`([^`]+)`",
        }

    async def async_retrieve(self, query: str, top_k: int = 10) -> dict[str, Any]:
        """
        Perform multi-hop retrieval starting from an initial query.
        """
        # 1. Initial retrieval
        results = await self.base_retriever.async_search(query, top_k=top_k)

        all_ids = list(results.get("ids", []))
        all_docs = list(results.get("documents", []))
        all_metas = list(results.get("metadatas", []))
        all_dists = list(results.get("distances", []))

        seen_ids = set(all_ids)

        # 2. Perform hops
        current_hop_docs = list(all_docs)

        for hop in range(self.max_hops):
            new_queries = self._extract_references(current_hop_docs)
            if not new_queries:
                break

            logger.info(f"Multi-hop iteration {hop + 1}: Found {len(new_queries)} new references")

            hop_results_list = []
            for ref_query in new_queries[:5]:  # Limit expansion breadth
                # Skip if query is just a stopword or too short
                if len(ref_query) < 3:
                    continue

                res = await self.base_retriever.async_search(ref_query, top_k=3)
                hop_results_list.append(res)

            # Merge new results
            new_hop_docs = []
            for res in hop_results_list:
                for i, doc_id in enumerate(res.get("ids", [])):
                    if doc_id not in seen_ids:
                        all_ids.append(doc_id)
                        all_docs.append(res["documents"][i])
                        all_metas.append(res["metadatas"][i])
                        all_dists.append(res["distances"][i])

                        new_hop_docs.append(res["documents"][i])
                        seen_ids.add(doc_id)

            if not new_hop_docs:
                break

            current_hop_docs = new_hop_docs

        return {
            "ids": all_ids,
            "documents": all_docs,
            "metadatas": all_metas,
            "distances": all_dists,
            "hops_performed": hop + 1 if "hop" in locals() else 0,
        }

    def _extract_references(self, documents: list[str]) -> list[str]:
        """Extract potential search terms from document content."""
        references = set()

        for doc in documents:
            # Try each pattern
            for pattern in self.reference_patterns.values():
                matches = re.findall(pattern, doc)
                for m in matches:
                    # Handle groups (some regex have multiple groups)
                    if isinstance(m, tuple):
                        for group in m:
                            if group:
                                references.add(group)
                    else:
                        references.add(m)

        # Filter out common false positives and noise
        filtered = []
        for ref in references:
            # Clean path references
            if "/" in ref:
                ref = ref.split("/")[-1]

            # Skip noise
            if ref.lower() in {"py", "md", "true", "false", "none", "self"}:
                continue

            filtered.append(ref)

        return list(set(filtered))


def create_multi_hop_retriever(base_retriever: Any, config: Any = None) -> MultiHopRetriever:
    """Factory function for multi-hop retriever."""
    max_hops = 2
    if config:
        max_hops = getattr(config, "multi_hop_max_depth", 2)

    return MultiHopRetriever(base_retriever=base_retriever, max_hops=max_hops)
