from __future__ import annotations

import os
from dataclasses import dataclass, field


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


@dataclass
class CacheSettings:
    backend: str = "memory"
    ttl: int = 300

    @classmethod
    def from_env(cls) -> CacheSettings:
        env = os.environ
        return cls(
            backend=env.get("CACHE_BACKEND", "memory"),
            ttl=int(env.get("CACHE_TTL", "300")),
        )


@dataclass
class SecuritySettings:
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    @classmethod
    def from_env(cls) -> SecuritySettings:
        env = os.environ
        return cls(
            secret_key=env.get("MOTHERSHIP_SECRET_KEY", ""),
            algorithm=env.get("MOTHERSHIP_JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(env.get("MOTHERSHIP_ACCESS_TOKEN_EXPIRE", "30")),
            refresh_token_expire_days=int(env.get("MOTHERSHIP_REFRESH_TOKEN_EXPIRE", "7")),
            rate_limit_enabled=_parse_bool(env.get("MOTHERSHIP_RATE_LIMIT_ENABLED"), True),
            rate_limit_requests=int(env.get("MOTHERSHIP_RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window_seconds=int(env.get("MOTHERSHIP_RATE_LIMIT_WINDOW", "60")),
        )


@dataclass
class PaymentSettings:
    stripe_secret_key: str = ""
    stripe_enabled: bool = False

    @classmethod
    def from_env(cls) -> PaymentSettings:
        env = os.environ
        return cls(
            stripe_secret_key=env.get("STRIPE_SECRET_KEY", ""),
            stripe_enabled=_parse_bool(env.get("STRIPE_ENABLED")),
        )


@dataclass
class BillingSettings:
    free_tier_relationship_analyses: int = 100
    free_tier_entity_extractions: int = 1000
    starter_tier_relationship_analyses: int = 1000
    starter_tier_entity_extractions: int = 10000
    pro_tier_relationship_analyses: int = 10000
    pro_tier_entity_extractions: int = 100000
    free_tier_resonance_events: int = 1000
    free_tier_high_impact_events: int = 50
    starter_tier_resonance_events: int = 10000
    starter_tier_high_impact_events: int = 500
    pro_tier_resonance_events: int = 100000
    pro_tier_high_impact_events: int = 5000
    starter_monthly_price: int = 4900
    pro_monthly_price: int = 19900
    relationship_analysis_overage_cents: int = 5
    entity_extraction_overage_cents: int = 1
    resonance_event_overage_cents: int = 1
    high_impact_event_overage_cents: int = 5
    billing_cycle_days: int = 30

    @classmethod
    def from_env(cls) -> BillingSettings:
        env = os.environ
        return cls(
            free_tier_relationship_analyses=int(env.get("BILLING_FREE_RELATIONSHIP_ANALYSES", "100")),
            free_tier_entity_extractions=int(env.get("BILLING_FREE_ENTITY_EXTRACTIONS", "1000")),
            starter_tier_relationship_analyses=int(env.get("BILLING_STARTER_RELATIONSHIP_ANALYSES", "1000")),
            starter_tier_entity_extractions=int(env.get("BILLING_STARTER_ENTITY_EXTRACTIONS", "10000")),
            pro_tier_relationship_analyses=int(env.get("BILLING_PRO_RELATIONSHIP_ANALYSES", "10000")),
            pro_tier_entity_extractions=int(env.get("BILLING_PRO_ENTITY_EXTRACTIONS", "100000")),
            free_tier_resonance_events=int(env.get("BILLING_FREE_RESONANCE_EVENTS", "1000")),
            free_tier_high_impact_events=int(env.get("BILLING_FREE_HIGH_IMPACT_EVENTS", "50")),
            starter_tier_resonance_events=int(env.get("BILLING_STARTER_RESONANCE_EVENTS", "10000")),
            starter_tier_high_impact_events=int(env.get("BILLING_STARTER_HIGH_IMPACT_EVENTS", "500")),
            pro_tier_resonance_events=int(env.get("BILLING_PRO_RESONANCE_EVENTS", "100000")),
            pro_tier_high_impact_events=int(env.get("BILLING_PRO_HIGH_IMPACT_EVENTS", "5000")),
            starter_monthly_price=int(env.get("BILLING_STARTER_PRICE_CENTS", "4900")),
            pro_monthly_price=int(env.get("BILLING_PRO_PRICE_CENTS", "19900")),
            relationship_analysis_overage_cents=int(env.get("BILLING_RELATIONSHIP_OVERAGE_CENTS", "5")),
            entity_extraction_overage_cents=int(env.get("BILLING_ENTITY_OVERAGE_CENTS", "1")),
            resonance_event_overage_cents=int(env.get("BILLING_RESONANCE_OVERAGE_CENTS", "1")),
            high_impact_event_overage_cents=int(env.get("BILLING_HIGH_IMPACT_OVERAGE_CENTS", "5")),
            billing_cycle_days=int(env.get("BILLING_CYCLE_DAYS", "30")),
        )


@dataclass
class RuntimeSettings:
    security: SecuritySettings = field(default_factory=SecuritySettings.from_env)
    cache: CacheSettings = field(default_factory=CacheSettings.from_env)
    payment: PaymentSettings = field(default_factory=PaymentSettings.from_env)
    billing: BillingSettings = field(default_factory=BillingSettings.from_env)

    @classmethod
    def from_env(cls) -> RuntimeSettings:
        return cls()
