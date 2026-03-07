# Search Guardrail Migration Guide

This document outlines the changes introduced to the search guardrail system and the search pipeline.

## 1. Guardrail Enabled by Default

The `SEARCH_GUARDRAIL_ENABLED` flag is now set to `true` by default in `SearchConfig`.

### Impact
- All search requests will now pass through the guardrail orchestrator.
- Authentication, rate limiting, and sanitization are enforced by default.
- If you were relying on disabled guardrails for development, you can set `SEARCH_GUARDRAIL_ENABLED=false` in your environment.

## 2. Real Access Control Allowlists

The `AccessControl` guardrail tool now supports real index and field allowlists defined in `GuardrailProfile`.

### Configuring Allowlists
You can now define `allowed_indices` and `allowed_fields` for each profile in your policy configuration.

```python
from search.guardrail.models import GuardrailProfile

profile = GuardrailProfile(
    name="developer",
    allowed_indices=["products", "inventory"],
    allowed_fields={
        "products": ["title", "price", "description"],
        "inventory": ["sku", "quantity"]
    }
)
```

- If `allowed_indices` is provided, the profile is restricted to those indices.
- If `allowed_fields` is provided for an index, only those fields can be used in filters or facet requests.

## 3. Optional Search Pipeline

A new flag `SEARCH_FULL_PIPELINE` (default: `false`) allows skipping the resource-intensive parts of the search pipeline.

### Full Pipeline (`SEARCH_FULL_PIPELINE=true`)
- Query expansion (Semantic-based)
- Hybrid Fusion (Structured + Semantic + Keyword)
- Ranking (Cross-encoders)
- Facet Aggregation

### Basic Pipeline (`SEARCH_FULL_PIPELINE=false`)
- Skips Query expansion.
- Uses simple Keyword retrieval (while still honoring structured filters).
- Skips Ranking (returns raw keyword scores).
- Skips Facet aggregation.

This is useful for high-throughput/low-latency scenarios or when advanced ranking is not required.
