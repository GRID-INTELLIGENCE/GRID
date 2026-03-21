# External AI Provider Policy

> **Baseline rule:** Prefer local-first AI tooling; do not use external AI APIs unless explicitly requested.
> — `.dev-rules.md`, Tooling section

---

## Scope

This document reconciles the local-first policy with GRID's existing integration surfaces for external AI providers (OpenAI, Anthropic, Google Gemini). It defines when external providers are acceptable, what safeguards apply, and how exceptions are tracked.

---

## Integration surfaces in GRID

| Surface | Providers | Default | Module path |
|---------|-----------|---------|-------------|
| **RAG LLM backends** | Ollama, OpenAI, Anthropic, Gemini | Ollama (local) | `src/tools/rag/llm/` |
| **RAG embeddings** | Ollama, OpenAI | Ollama (local) | `src/tools/rag/embeddings/` |
| **AI safety evaluation** | OpenAI, Anthropic | Disabled | `src/grid/skills/ai_safety/providers/` |
| **Inference service** | Ollama, OpenAI | Ollama (local) | `src/grid/services/inference.py` |
| **Model router** | Multi-provider | Local fallback | `src/tools/rag/model_router.py` |

---

## Exception rules

### 1. External providers are opt-in, never default

All provider selection is driven by environment variables (`RAG_LLM_MODE`, `RAG_EMBEDDING_PROVIDER`, etc.). The default configuration uses Ollama for both LLM inference and embeddings. No external API call is made unless the operator explicitly configures it.

### 2. API keys must come from environment variables

No API key may be hard-coded in source. Keys are loaded via:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY` / `GEMINI_API_KEY`

The `secrets_loader.py` module enforces this pattern. The security scanners (`input_sanitizer.py`, `vulnerability_scanner.py`) flag hard-coded credentials.

### 3. External calls require explicit user/operator intent

An external provider is acceptable when:
- The operator sets the provider via environment variable or config.
- The use case requires capabilities not available locally (e.g., specific model families, safety evaluation benchmarks).
- The data being sent does not contain PII or sensitive information without appropriate consent.

### 4. Fallback behavior

If an external provider is configured but unavailable, the system should:
- Log the failure clearly.
- Fall back to local provider if possible (`model_router.py` resilience layer).
- Never silently switch to an external provider as a fallback for a local-only configuration.

### 5. AI safety providers are evaluation-only

The `ai_safety/providers/` integrations (OpenAI, Anthropic) are used exclusively for safety evaluation and red-teaming — not for primary inference or user-facing responses.

---

## Tracking

Any new external AI integration must:
1. Be added to the table above.
2. Default to disabled/local.
3. Source credentials from environment variables.
4. Be covered by the `/legal-compliance-check` workflow before release.

---

## References

- `.dev-rules.md` — local-first tooling rule
- `src/tools/rag/config.py` — provider configuration
- `src/grid/security/secrets_loader.py` — credential loading
- `mcp-setup/mcp_config.json` — MCP server environment defaults
