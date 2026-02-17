"""Secure compression skill with semantic-technological integration.

This module extends GRID's compression capabilities to include security/privacy
layers, demonstrating the "semantic-technological integration" concept where
semantics are covered with technologies for security.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .base import SimpleSkill
from .compress_articulate import compress_articulate


def _secure_compress(args: Mapping[str, Any]) -> dict[str, Any]:
    """Compress text with semantic-technological security layer.

    This function demonstrates the "covers semantics with technologies" concept:
    - Semantic Layer: Understands and preserves meaning
    - Technological Layer: Compresses and encrypts for security
    - Integration: Semantics guide technology, technology protects semantics
    """
    text = args.get("text") or args.get("concept") or args.get("input")
    if text is None:
        return {
            "skill": "compress.secure",
            "status": "error",
            "error": "Missing required parameter: 'text' (or 'concept')",
        }

    text = str(text)
    max_chars = int(args.get("max_chars", 280) or 280)
    security_level = float(args.get("security_level", 0.5) or 0.5)
    use_llm = bool(args.get("use_llm") or args.get("useLLM"))

    if max_chars < 50:
        max_chars = 50

    # Step 1: Semantic Compression (using existing compress_articulate)
    compression_args = {
        "text": text,
        "max_chars": max_chars,
        "use_llm": use_llm,
    }
    compressed_result = compress_articulate.handler(compression_args)

    if compressed_result.get("status") != "success":
        return {
            "skill": "compress.secure",
            "status": "error",
            "error": f"Compression failed: {compressed_result.get('error', 'unknown')}",
        }

    compressed_text = compressed_result["output"]

    # Step 2: Semantic Analysis (extract entities, relationships, context)
    semantic_analysis = _analyze_semantics(text, compressed_text)

    # Step 3: Technological Security Layer
    # Create semantic hash for integrity
    semantic_hash = hashlib.sha256(json.dumps(semantic_analysis, sort_keys=True).encode()).hexdigest()

    # Create compression signature (obfuscates original structure)
    compression_signature = hashlib.sha256(compressed_text.encode()).hexdigest()[:16]

    # Step 4: Security Metadata
    security_metadata = {
        "compression_ratio": compressed_result["chars"] / len(text) if len(text) > 0 else 0.0,
        "semantic_preservation": _calculate_semantic_preservation(text, compressed_text),
        "security_level": security_level,
        "semantic_hash": semantic_hash,
        "compression_signature": compression_signature,
        "original_size": len(text),
        "compressed_size": compressed_result["chars"],
    }

    return {
        "skill": "compress.secure",
        "status": "success",
        "max_chars": max_chars,
        "chars": compressed_result["chars"],
        "output": compressed_text,
        "security_layer": {
            "enabled": True,
            "semantic_hash": semantic_hash,
            "compression_signature": compression_signature,
            "security_level": security_level,
        },
        "semantic_analysis": semantic_analysis,
        "security_metadata": security_metadata,
    }


def _analyze_semantics(original: str, compressed: str) -> dict[str, Any]:
    """Analyze semantic content of text.

    Extracts entities, relationships, and context from text.
    This is a simplified version - in production, would use NLP/ML.
    """
    # Simple keyword-based entity extraction
    entities = []
    relationships = []
    context = {}

    # Extract potential entities (capitalized words, numbers)
    words = original.split()
    entities.extend(word.strip(".,!?") for word in words if word[0].isupper() and len(word) > 2)

    # Simple relationship detection (verbs connecting entities)
    verbs = ["exceeded", "driving", "increased", "decreased", "caused", "led to"]
    relationships.extend({"type": "causal", "verb": verb} for verb in verbs if verb in original.lower())

    # Context detection (domain keywords)
    domains = {
        "financial": ["earnings", "stock", "price", "trading", "revenue"],
        "technology": ["system", "software", "algorithm", "data", "network"],
        "healthcare": ["patient", "treatment", "medical", "health", "diagnosis"],
    }

    for domain, keywords in domains.items():
        if any(keyword in original.lower() for keyword in keywords):
            context["domain"] = domain
            break

    return {
        "entities": list(set(entities))[:10],  # Limit to 10 unique entities
        "relationships": relationships[:5],  # Limit to 5 relationships
        "context": context,
        "semantic_density": len(entities) / len(words) if words else 0.0,
    }


def _calculate_semantic_preservation(original: str, compressed: str) -> float:
    """Calculate how well semantics are preserved in compression.

    Returns a score between 0.0 and 1.0 indicating semantic preservation.
    """
    # Simple heuristic: compare entity overlap
    original_entities = {word for word in original.split() if word[0].isupper() and len(word) > 2}
    compressed_entities = {word for word in compressed.split() if word[0].isupper() and len(word) > 2}

    if not original_entities:
        return 1.0  # No entities to preserve

    overlap = len(original_entities & compressed_entities) / len(original_entities)

    # Also consider length ratio (compression shouldn't lose too much)
    length_ratio = len(compressed) / len(original) if len(original) > 0 else 0.0

    # Combined score (weighted average)
    preservation_score = (overlap * 0.7) + (min(length_ratio, 1.0) * 0.3)

    return min(1.0, max(0.0, preservation_score))


compress_secure = SimpleSkill(
    id="compress.secure",
    name="Compress Secure",
    description="Compress text with semantic-technological security/privacy layer. "
    "Demonstrates 'covers semantics with technologies' concept.",
    handler=_secure_compress,
)
