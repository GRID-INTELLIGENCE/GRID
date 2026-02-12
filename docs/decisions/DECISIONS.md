# Architecture Decision Log

Running log of architectural decisions for THE GRID.
Append new entries at the top. One decision per entry.

---

## 2026-02-12 — Fail-closed boundary engine

**Decision**: Unknown boundary/guardrail IDs now return deny instead of allow.
**Why**: Fail-open on missing config is a security hole — typos or removed configs silently grant access.
**Alternatives considered**: Raising an exception (too disruptive to callers), logging-only (doesn't prevent access).

## 2026-02-12 — Redis-backed misuse tracking

**Decision**: Migrated misuse tracker from in-memory dict to Redis sorted sets with in-memory fallback.
**Why**: In-memory tracking is per-process — multi-instance deployments can't detect distributed abuse.
**Alternatives considered**: Shared file (too slow), PostgreSQL (overkill for sliding window counters).

## 2026-02-12 — PII auto-redaction in audit logs

**Decision**: SQLAlchemy `before_insert` event listener auto-redacts email, phone, SSN, credit card, IP from audit records.
**Why**: Audit logs store full user input — PII retention violates privacy principles and GDPR.
**Alternatives considered**: Application-level redaction (easy to forget), database triggers (less portable).

## 2026-02-12 — GRID_ENV gating for security bypasses

**Decision**: `DISABLE_NETWORK_SECURITY` and API docs bypass now require `GRID_ENV=development|dev|test`.
**Why**: Single env var bypass is too easy to accidentally or maliciously enable in production.
**Alternatives considered**: Removing bypass entirely (breaks local dev workflow).

## 2026-02-12 — Bounded body streaming in middleware

**Decision**: Read request body via `request.stream()` with 50KB limit instead of `request.body()`.
**Why**: `request.body()` loads entire payload into memory before any size check — OOM vector.
**Alternatives considered**: Nginx/reverse proxy limit (defense-in-depth, but app should self-protect).
