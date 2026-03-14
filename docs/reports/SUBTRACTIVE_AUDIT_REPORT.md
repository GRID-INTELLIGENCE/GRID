# Subtractive Analyst Audit Report

**Date:** 2026-03-02  
**Scope:** Recent workspace changes across 10 git repositories  
**Focus:** Governance, safety, harmful patterns, bugs

---

## Minuend / Subtrahend / Remainder

| Step | Description |
|------|-------------|
| **Minuend** | All uncommitted and untracked changes across workspace roots |
| **Subtrahend** | Identified harmful patterns, bugs, governance violations, safety gaps |
| **Remainder** | Sanitized codebase ready for CI/CD review |

---

## 1. Findings by Category

### 1.1 Harmful Patterns (Security)

| Repo | Location | Finding | Severity | Remediation |
|------|----------|---------|----------|-------------|
| echoes | `app/resilience/rate_limit.py` | API keys used raw in Redis rate-limit keys; Redis compromise could expose credentials | **High** | Hashed API keys with SHA-256 before use in key function |
| echoes | `redis.conf` | `bind 0.0.0.0` exposes Redis to all interfaces without production guidance | **Medium** | Added security comment: restrict bind and require password in production |
| GRID-main | `guardrail/tools/pii.py`, `sanitize.py` | Profile regex patterns from config compiled with `re.compile()`—ReDoS risk from malicious or complex patterns | **Medium** | Added `MAX_PROFILE_PATTERN_LENGTH=500`; reject longer patterns |

### 1.2 Bugs

| Repo | Location | Finding | Severity | Remediation |
|------|----------|---------|----------|-------------|
| — | — | None requiring code fix in audited diff scope | — | — |

### 1.3 Governance Violations

| Repo | Finding | Severity | Remediation |
|------|---------|----------|-------------|
| GRID-main | `guardrail_enabled` default changed `False` → `True` | **Medium** | Documented in `docs/SEARCH_GUARDRAIL_MIGRATION.md`; set `SEARCH_GUARDRAIL_ENABLED=false` for prior behavior |
| echoes | Rate limiting moved from custom middleware to SlowApi; in-memory → optional Redis | **Low** | Behavior preserved; Redis optional |

### 1.4 Safety Gaps

| Repo | Location | Finding | Severity | Remediation |
|------|----------|---------|----------|-------------|
| echoes | `/metrics` | Prometheus metrics endpoint unauthenticated | **Low** | Documented; restrict via network/firewall in production |
| Language_Library | `rag_armor.py` | `pickle.load()` on cache files; untrusted cache dir could allow code execution | **Low** | Ensure `.cache/` is in `.gitignore`; use trusted cache dir only |
| Language_Library | `.gitignore` | `.cache/` not ignored; pickle cache could be committed | **Low** | Added `.cache/` to `.gitignore` |

---

## 2. Repositories Audited (No Remediation Required)

| Repo | Changes | Notes |
|------|---------|-------|
| Understory/Tools/Python | mypy.ini, pytest.ini deleted | Config consolidation; no security impact |
| light_of_the_seven | `scripts/GRID-workspace-template.jsonc` | Added `python-envs.workspaceSearchPaths`; benign |
| veridisquo | manifest.json untracked | N/A |
| Vision | Large restructure (Vision/ prefix) | Structural only |
| ai_advisor | pytest.ini deleted, manifest.json, uv.lock | Config/deps only |
| assistive-tool-contract | contract.json, docs, BUILD_MAP | Contract schema; no code risk |
| afloat | schema untracked | N/A |

---

## 3. Remediations Applied

| Repo | File | Change |
|------|------|--------|
| echoes | `app/resilience/rate_limit.py` | Hash API keys (SHA-256) before use in rate-limit keys |
| echoes | `redis.conf` | Added production security comment for bind and password |
| GRID-main | `src/search/guardrail/tools/sanitize.py` | ReDoS mitigation: reject profile patterns > 500 chars |
| GRID-main | `src/search/guardrail/tools/pii.py` | ReDoS mitigation: reject profile patterns > 500 chars |
| Language_Library | `.gitignore` | Added `.cache/` to avoid committing pickle cache |

---

## 4. Staged for CI/CD

- **echoes:** `app/resilience/rate_limit.py`, `redis.conf`
- **GRID-main:** `src/search/guardrail/tools/sanitize.py`, `src/search/guardrail/tools/pii.py`
- **Language_Library:** `.gitignore`

---

## 5. Recommendations (Not Implemented)

1. **Prometheus /metrics:** Restrict `/metrics` by network (e.g. internal-only) or optional auth in production.
2. **Pickle cache:** Keep `rag_armor` cache dir permissions tight; consider signing/validating cache files if accepting external cache dirs.
3. **Guardrail default:** If rolling back behavior, set `SEARCH_GUARDRAIL_ENABLED=false` in env.

---

*Steps completed: 1 ✓ 2 ✓ 3 ✓ 4 ✓ 5 ✓*
