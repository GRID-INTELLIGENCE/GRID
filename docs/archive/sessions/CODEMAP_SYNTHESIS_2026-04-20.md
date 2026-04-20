# Codemap Synthesis — 2026-04-20

Session: `ultrareview-prep-cross-repo-audit`
Branch: `review/ultrareview-2026-04-20`
Generated from: 4 active codemaps across GRID-main, CascadeProjects/Tools/MCPServers

---

## 1. W3C Trace Context — Status: ASPIRATIONAL (not implemented)

**Codemap:** W3C Trace Context Propagation System — Incomplete Analysis

### Finding

W3C trace context (`traceparent` / `tracestate` headers) is **not implemented** in any MCP server.
The codemap was unable to locate concrete implementation files. All location IDs point to directory
roots (`Tools/MCPServers:1`), not actual source files.

### What exists

- `mothership/main.py` — distributed tracing via OpenTelemetry/Jaeger (opt-in, env-gated)
- No cross-server `traceparent` injection or extraction in the TypeScript MCP fleet

### Gap

| Layer | Status |
|---|---|
| Spec / requirements | Documented in `SPEC.md` |
| Per-server header injection | **Missing** |
| Cross-server propagation | **Missing** |
| Sampling logic | **Missing** |

**Ultrareview action:** Decide whether W3C trace propagation is in scope for this cycle or deferred.
If deferred, remove from active codemaps to avoid confusion.

---

## 2. GRID MCP Fleet Security & RAG — Defense-in-Depth Architecture

**Codemaps:** GRID MCP RAG Security Architecture + GRID MCP Fleet Security and RAG Features

### Security Layer Stack (input → execution → output)

```
User Input
  │
  ├── PathValidator.validate_path()          path_validator.py:93
  │     └── target.is_relative_to(base)      path_validator.py:100
  │
  ├── InputSanitizer.sanitize_text_full()    input_sanitizer.py:258
  │     ├── Length + unicode validation
  │     ├── Compiled regex pattern scan      input_sanitizer.py:280
  │     │     ├── Threat detection           input_sanitizer.py:293
  │     │     └── Pattern removal            input_sanitizer.py:306
  │     └── HTML entity encoding (XSS)       input_sanitizer.py:311
  │
  ├── _sanitize_query() (RAG path)           rag_mcp_server.py:742
  │     └── Block on critical/high severity  rag_mcp_server.py:122
  │
  ├── AuditLogger.log_event()                audit_logger.py:187
  │
  └── AISecurityWrapper.secure_inference()   ai_security.py:301  [NEW this session]
        ├── InputValidator.validate_input()   ai_security.py:317
        ├── Block if not safe                 ai_security.py:326
        ├── Execute inference                 ai_security.py:334
        └── OutputSanitizer.sanitize_output() ai_security.py:336
```

### SQL Injection Prevention (two server paths)

| Server | Entry | Safety check | Parameterized |
|---|---|---|---|
| `workspace/mcp/servers/database/server.py` | `_query():235` | `_is_query_safe():55` | `cursor.execute(sql, params)` |
| `workspace/mcp/servers/database/production_server.py` | `_query():132` | `_is_query_safe():144` | `cursor.execute(sql, params):161` |

Both enforce SELECT-only + no semicolon compound statements. `production_server.py` adds keyword
blocking and a `_describe_table()` path with validated `PRAGMA` execution.

### LLM Provider Resolution — 3-Path Factory (updated this session)

```
get_llm_provider()                           factory.py:144
  │
  ├── Path 1: Catalog auto-select (opt-in)   factory.py:179
  │     RAG_LLM_MODE=auto + RAG_LLM_AUTO_SELECT=catalog
  │     └── try/except → falls through to Path 2 on failure  [NEW]
  │
  ├── Path 2: Fallback chain                 factory.py:199
  │     resolve_llm() → probe health → _to_resolved()
  │     └── _probe_provider() health cache   model_resolver.py:179
  │
  └── Path 3: Legacy explicit mode           factory.py:207
        └── API key validation per provider
```

**Key change this session:** Path 1 wrapped in try/except — catalog failures now fall through to
Path 2 instead of raising. Prevents hard failures when `auto_selector` is unavailable.

### RAG Query Security Flow

```
rag_query()                    rag_mcp_server.py:735
  ├── _sanitize_query()        :742  → block on high/critical
  ├── ensure_rag_engine()      :219  → config.ensure_local_only()
  ├── engine.query()           :755
  │     └── _filter_sources()  :760  → prompt injection pattern check
  └── Response formatting      :762
```

### MCP Config Validation

- `validate_mcp_config.py:145` — checks command executables, PYTHONPATH, working directories
- `tool_registry.py:282` — background health monitoring per server (5s probe timeout)

---

## 3. Automation & Pipeline Infrastructure

**Codemap:** Automation and Pipeline Infrastructure — Signal Processing, Envelope Execution, Anticipation

### echoes-server: Signal Automation Engine

```
SignalAutomationEngine.processSignal()       signal_automation.ts:453
  ├── generateDecoratedResponse()            :455
  │     ├── classifySignal()                 :176
  │     │     ├── CRITICAL_KEYWORDS scan     :142
  │     │     └── HIGH/MEDIUM keywords       :147
  │     └── Template interpolation           :219
  ├── storeSignal()                          :458
  └── emitAudit()                            :461
```

Risk levels: `critical` → `high` → `medium` — keyword-based classification, not ML.

### ori-server: Envelope Pipeline (phased test execution)

```
envelope()                                   envelope.ts:221
  ├── FOLD_1_CORE → FOLD_2_ANALYSIS → FOLD_3_INTEGRATION
  │     ├── Skip fold if previous was red    :234
  │     └── runFold() → execSync(vitest)     :151
  │           ├── parseVitestOutput()        :109
  │           ├── Hard halt check            :181
  │           └── advanceable flag           :172
  └── Overall verdict                        :276
        hasRed → "fail" | hasYellow → "warn" | else → "pass"
```

### ori-server: Anticipation Engine

```
analyzeRecentLogs()                          anticipation.ts:264
  ├── runProbe() side effects                :268
  ├── Group by project, calc risk score      :296
  │     └── critical×2 + warning ≥ threshold
  ├── Generate AnticipationSignal            :317
  └── store.appendSignal()                   :340
```

**TTL pruning fix (applied this session):**
- Old: `filter(s => s.generatedAt >= ttlCutoff)` — pruned by creation time
- New: `filter(s => (s.resolvedAt ?? s.generatedAt) >= ttlCutoff)` — prunes by resolution time
- Companion fix: `resolveSignal()` now sets `signal.resolvedAt = new Date().toISOString()`

### ori-server: Signal Router

```
evaluateSignals()                            router.ts:187
  ├── Filter matching entries                :200
  │     └── severity / pattern / source check  :78
  ├── Accumulate hits in time window         :204
  ├── Threshold + cooldown check             :226-232
  └── Execute actions                        :254
        probe | note | recommend | audit
  └── state.lastFiredAt / reset hits         :266-267
```

---

## 4. Cross-Cutting Gaps & Ultrareview Flags

| # | Area | Gap | Severity |
|---|---|---|---|
| G1 | W3C Trace Context | Not implemented in MCP fleet — codemap is aspirational | Medium |
| G2 | `anticipation.ts` TTL | Fixed this session — needs test coverage for `resolvedAt` path | Low |
| G3 | factory.py Path 1 | try/except fallthrough is correct but swallows all exceptions — consider narrowing to `ImportError` | Low |
| G4 | `production_server.py` PRAGMA | `f'PRAGMA table_info("{table}")'` — table name validated above but still an f-string; consider fully parameterized | Low |
| G5 | `ai_security.py` integration | `AISecurityWrapper` exists but not wired into any inference call site yet — new file, zero call sites | Medium |

---

## 5. Key Files by Domain

| Domain | Primary files |
|---|---|
| Security layer | `src/grid/security/ai_security.py`, `input_sanitizer.py`, `path_validator.py`, `audit_logger.py` |
| RAG factory | `src/tools/rag/llm/factory.py`, `auto_selector.py`, `model_catalog.py`, `model_resolver.py` |
| RAG server | `mcp-setup/server/rag_mcp_server.py` |
| DB MCP | `workspace/mcp/servers/database/server.py`, `production_server.py` |
| Anticipation | `Tools/MCPServers/ori-server/src/anticipation.ts` |
| Envelope | `Tools/MCPServers/ori-server/src/envelope.ts` |
| Signal router | `Tools/MCPServers/ori-server/src/router.ts` |
| Signal automation | `Tools/MCPServers/echoes-server/src/automation/signal_automation.ts` |
| Mothership startup | `src/application/mothership/main.py` |
