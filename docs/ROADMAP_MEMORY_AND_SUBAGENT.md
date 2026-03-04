# Roadmap: Memory Optimization & Subagent-Driven Precision

This roadmap ties the memory-management changes ([MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md](./MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md)) to a **subagent-first** approach: define a tailored subagent that explores and defines custom skills and configuration documents first; then document and implement later steps with **high accuracy** and **test-driven precision**.

---

## Rationale

- **Subagent first**: A dedicated subagent (skills-and-config-explorer) discovers where TTLs, eviction, and memory boundaries live, drafts `MEMORY_POLICY.md` and skill/config artifacts. That creates a single vocabulary and config surface.
- **Then precision**: With that baseline, each implementation step (working-memory cap, semantic cache, three-tier wiring, observability) can be specified as a **testable contract** (e.g. "max_working_tokens enforced in path X", "cache hit rate metric exposed at Y"). Tests can assert against the documented policy and config.

---

## Phase 0: Subagent & baseline (do first)

| Step | Action | Outcome | Verification |
|------|--------|---------|--------------|
| 0.1 | **Create subagent** `skills-and-config-explorer` in `.cursor/agents/`. Purpose: explore codebase and docs; define or update custom skills (SKILL.md) and configuration documents (MEMORY_POLICY.md, config schema, env sections). | Subagent file exists; description says when to delegate (e.g. "when defining memory policy, skills for cache/observability, or config docs for GRID"). | Invoke: **"Use the skills-and-config-explorer subagent to explore memory-related config and propose MEMORY_POLICY.md."** (Subagent: `.cursor/agents/skills-and-config-explorer.md`) |
| 0.2 | **Run the subagent** to explore: `src/vection/core/stream_context.py`, `src/mycelium/core.py`, `src/tools/rag/config.py`, `src/application/mothership/middleware/__init__.py`, DRT migrations, `.env.example` / env files. Ask it to produce a first draft of `docs/MEMORY_POLICY.md` listing working context location, all TTLs, all `max_*`, eviction rules. | Draft `MEMORY_POLICY.md` (or structured output that can be pasted into it). | File exists; contains at least: working context, session_ttl, thread_ttl, cache_ttl, retention_hours, mothership eviction, StreamContext cleanup. |
| 0.3 | **Run the subagent** to propose or draft: (a) a **skill** for memory-policy compliance (when to check TTLs/eviction against policy); (b) optional **skill** for semantic-cache or observability. Optionally: config schema or env table for three-tier (working/episodic/semantic). | Skill stub(s) under `.cursor/skills/` and/or additions to config docs. | Skills are discoverable; config doc lists three-tier env vars or config keys. |
| 0.4 | **Lock the baseline**: Review subagent output; commit `MEMORY_POLICY.md` and any new skills/config docs. From here, "later steps" are defined against this baseline so they can be specified with high accuracy and test-driven precision. | Baseline committed; roadmap phases 1+ reference this doc and these artifacts. | `MEMORY_POLICY.md` in repo; skills referenced in roadmap. |

---

## Phase 1: Document & cap (accuracy)

| Step | Action | Outcome | Test-driven precision |
|------|--------|---------|------------------------|
| 1.1 | Finalize **MEMORY_POLICY.md** (from Phase 0). Ensure it lists: where working context is (resonance/RAG); all TTLs; all max_* and eviction rules. | Single source of truth for memory policy. | Test: script or CI step that parses MEMORY_POLICY.md and fails if key sections missing (e.g. "Working context", "TTLs", "Eviction"). |
| 1.2 | **Introduce working-memory cap** in the hot path (resonance service or RAG integration): `max_working_tokens` or `max_retrieved_chunks` from config/env. | Prompt builder never exceeds cap. | Test: unit test that builds context with N chunks; assert result ≤ max_retrieved_chunks (or token count ≤ max_working_tokens). |
| 1.3 | **Label three-tier** in config and docs: working = context + cap; episodic = vector/namespace for recent events; semantic = RAG index. Add to MEMORY_POLICY.md and optionally to env.example. | Clear naming for retrieval and eviction per tier. | Test: config load test that asserts three-tier keys or env vars exist and are documented in MEMORY_POLICY.md. |

---

## Phase 2: Semantic cache & retrieval (precision)

| Step | Action | Outcome | Test-driven precision |
|------|--------|---------|------------------------|
| 2.1 | **Add semantic response cache** in front of LLM (e.g. in `application.resonance` or RAG entry): embed query → similarity search → return cached response if above threshold and not expired; else call LLM and cache. TTL + max size + LRU eviction. | Same/similar question → cached response; lower latency and cost. | Test: (1) two requests with same query → second is cache hit (metric or return header). (2) request with different query → cache miss. (3) eviction when over max size or TTL. |
| 2.2 | **Wire retrieval to episodic vs semantic**: when building context, pull recent from episodic (last N or 24h), facts from semantic; blend into working up to cap. | Better relevance (recent vs long-term). | Test: mock episodic and semantic stores; assert blended result respects cap and contains both sources when available. |
| 2.3 | **Expose observability**: cache hit rate, eviction counts (session/thread/cache), working-memory usage (tokens or chunks per request). | Metrics for tuning. | Test: after N requests, assert metrics endpoint or log contains cache_hits, cache_misses, eviction_count (or equivalent). |

---

## Phase 3: Tune & maintain

| Step | Action | Outcome | Test-driven precision |
|------|--------|---------|------------------------|
| 3.1 | **Tune the sequence** using observability: adjust retrieval mix, cache threshold/TTL, or eviction when responses are generic, slow, or memory grows. | Optimized pipeline. | Test: regression tests for latency (e.g. p95 under X ms for cached path) and for memory policy (no new unbounded stores without TTL/eviction). |
| 3.2 | **Revisit MEMORY_POLICY.md** whenever TTLs, max_*, or eviction rules change. Optionally re-invoke skills-and-config-explorer to refresh policy or skills. | Policy and implementation stay aligned. | Test: CI step that diffs codebase for new TTL/eviction symbols and warns if MEMORY_POLICY.md unchanged. |

---

## Subagent usage (skills-and-config-explorer)

After Phase 0, use the subagent for:

- **Exploring**: "Where are TTLs and eviction defined in GRID?" → structured list of files and symbols.
- **Defining**: "Draft MEMORY_POLICY.md from current code and config." → first draft.
- **Skills**: "Propose a skill for memory-policy checks" or "Propose a skill for semantic-cache behavior." → SKILL.md content.
- **Config**: "What env vars or config keys should document three-tier memory?" → table or schema snippet.

Once the subagent has produced the baseline (Phase 0.2–0.4), later steps (Phases 1–3) can be documented with high accuracy (same vocabulary, same config surface) and verified with test-driven precision (tests assert against MEMORY_POLICY.md and the implemented contracts).

---

## References

- [MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md](./MEMORY_MANAGEMENT_GAP_AND_SOLUTION.md) — gap analysis, patterns, and actionable steps.
- **create-subagent** skill (user-level) — how to create and refine subagents.
- GRID `.cursor/agents/` — project subagents (e.g. `ai-safety-reviewer`, `skills-and-config-explorer`).
