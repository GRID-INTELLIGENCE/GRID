"""Search engine configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class SearchConfig(BaseSettings):
    """Configuration for the search engine, loaded from environment variables.

    Every algorithmic constant that tests may need to override is exposed
    here rather than hardcoded in individual modules.
    """

    model_config = {"env_prefix": "SEARCH_"}

    embedding_provider: str = "huggingface"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_store_backend: str = "in_memory"

    rrf_k: int = 60
    default_retrieval_size: int = 100
    retrieval_multiplier: int = 3

    ltr_model_path: str | None = None
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    cross_encoder_top_k: int = 20
    cross_encoder_enabled: bool = True

    default_page_size: int = 10
    max_page_size: int = 1000

    intent_similarity_threshold: float = 0.85
    intent_analytical_threshold: float = 0.5

    expansion_similarity_threshold: float = 0.75
    expansion_max_terms: int = 3

    facet_max_values: int = 20
    facet_histogram_buckets: int = 10

    popularity_fields: list[str] = Field(
        default=["popularity", "click_count", "impressions", "views"],
    )
    freshness_decay_hours: float = 24.0

    latency_window_size: int = 10_000

    # Guardrail configuration (auth, security, safety)
    guardrail_enabled: bool = True
    guardrail_auth_required: bool = True
    guardrail_rate_limit_per_minute: int = 60
    guardrail_audit_enabled: bool = True
    guardrail_pii_redact: bool = True
    guardrail_fail_open: bool = False  # if True, allow on guardrail error
    search_full_pipeline: bool = False  # if False, skip fusion/ranking/facets

    # Admin gating: when True, schema/index/delete routes require admin.
    # In production, set guardrail_admin_identities to a list of trusted identities;
    # when non-empty, header-only admin is disabled and identity must be in the list.
    guardrail_admin_gating: bool = False
    guardrail_admin_identities: list[str] = Field(default_factory=list)
    guardrail_admin_header: str = "X-Admin-Role"
    guardrail_admin_header_value: str = "admin"
