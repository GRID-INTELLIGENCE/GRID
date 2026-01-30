# External AI Providers — Integration & Maintenance Guide

This guide explains where external provider code and domains appear in the codebase, collected authoritative links, and pragmatic, maintainable best practices for integrating providers (e.g., Mistral / Codestral, OpenAI, Azure AI, Hugging Face, IBM Watson).

---

## 1) Findings (from repository scan)
- Codestral / Mistral references:
  - `requirements.txt` and `requirements.codestral.txt` include `mistralai` and `python-dotenv`.
  - `src/grid/codestral_client.py` and `example_codestral_usage.py` implement a Codestral client and examples.
  - `setup_codestral_env.ps1` and `CODESTRAL_SETUP_WINDOWS11.md` updated to use `gridstral_code_api_key` as the canonical env var.

- OpenAI references present in tests and services (e.g., `src/services/ner_service.py` has references to `OpenAI` in unit tests and code paths).

- Dependencies and vendored packages in the virtual environment indicate other cloud or tooling mentions (Azure, Hugging Face, Google) in docs or third-party package metadata.

Notes:
- There are two places for a Codestral client in earlier history (root-level `codestral_client.py` and `src/grid/codestral_client.py`).  This repo now standardizes on `src/grid/codestral_client.py` and examples use the package import.

---

## 2) Authoritative docs and quick references (official docs)
- Mistral (Codestral): https://docs.mistral.ai/api  and https://docs.mistral.ai/models/codestral-25-08/
- OpenAI Platform: https://platform.openai.com/docs/api-reference
- Microsoft / Azure AI & Foundry: https://learn.microsoft.com/en-us/azure/ai-services/  and https://learn.microsoft.com/en-us/azure/ai-foundry/
- Hugging Face docs: https://huggingface.co/docs
- IBM Watson: https://cloud.ibm.com/docs/watson

Use these pages as the source of truth for auth flows, rate limits, recommended SDK versions, and reliability or cost considerations.

---

## 3) Recommended Best Practices (maintainable and safe)
This section is condensed into pragmatic, low-effort patterns that reduce surprises and keep onboarding minimal and repeatable.

1) Single source of truth
   - Keep provider clients inside a single canonical package path (e.g., `src/grid/codestral_client.py`). Avoid duplicate implementations in the repo root with the same module name.
   - If you must keep a root-level CLI or convenience script, make it a tiny shim that re-exports the package functionality.

2) Dependency isolation
   - Maintain minimal per-provider manifests (e.g., `requirements.codestral.txt`) for quick onboarding. This prevents accidentally inflating the base `requirements.txt` with unrelated packages.
   - CI and packaging should still use the canonical top-level `requirements.txt` for full test matrix; per-provider manifests are for opt-in onboarding.

3) Environment variables and secret handling
   - Standardize provider-specific env var naming with a clear prefix: e.g., `GRID_MISTRAL_API_KEY` or `gridstral_code_api_key` (we chose the latter in this project). Keep names documented in `CODESTRAL_SETUP_WINDOWS11.md`.
   - Never commit secrets or `.env` into VCS. Use `python-dotenv` for local developer convenience with `.env` listed in `.gitignore`.
   - Use platform secret stores (GitHub Actions secrets, Azure Key Vault, or similar) for CI and production.

4) Tests and mocking
   - Unit tests should mock provider APIs. For Python, use `unittest.mock` or libraries like `responses`, `pytest-mock`, or `httpretty` when testing code that calls external services.
   - Add a small test that verifies the client fails fast when API key is missing.

5) Client design and stability
   - Keep thin wrappers around provider SDKs that handle:
       - env var lookup and explicit overrides (function parameter)
       - safe initialization errors with useful messages (no secrets in traces)
       - retries with exponential backoff and error wrapping
       - deterministic non-blocking calls (timeouts and cancellation)
   - Cache or reuse clients with a simple factory (e.g., lru_cache) and make clients easy to mock.

6) Rate limiting and quotas
   - Implement useful default retry/backoff policies and surface quota errors clearly to calling code so higher-level flows can back off or queue work.
   - Monitor usage using provider dashboards and instrument the app (metrics) to track per-key usage.

7) Maintainability & onboarding
   - Document per-provider setup steps in `docs/` (we added `CODESTRAL_SETUP_WINDOWS11.md` and this guidance doc)
   - Keep provider-specific example scripts small and isolated to the provider folder/module.
   - Add a `requirements.<provider>.txt` file for each integration (e.g., `requirements.codestral.txt`) so developers can pip install only what they need.

8) CI/PR guidance
   - In PRs that add or update provider integrations, require tests that run with mocks and a short README entry explaining environment variables, dependency changes, and any cost implications.

---

## 4) Quick actions we implemented (how to use)
- Minimal manifest added: `requirements.codestral.txt` containing `mistralai` and `python-dotenv`.
- Example and client moved/standardized to `src/grid/codestral_client.py` and `example_codestral_usage.py` updated to import from `grid.codestral_client`.
- Environment variable standardized: `gridstral_code_api_key` (fallbacks ok for `MISTRAL_API_KEY`).

---

## 5) Suggested follow-ups (low effort)
1. Convert any root-level duplicate client script into a shim that re-exports the package client to avoid confusion.
2. Add a tiny unit test verifying client initialization fails without an API key, and that `get_codestral_client` returns a cached instance (mocking Mistral imports).
3. Add a CI check that ensures per-provider manifests are present when new provider code is added.
4. Optional: add a short Linter/Pre-commit rule to detect duplicate modules with the same name in root vs package.

---

## 6) Reference links (again, for easy copy/paste)
- Mistral API (Codestral): https://docs.mistral.ai/api  & https://docs.mistral.ai/models/codestral-25-08/
- OpenAI API: https://platform.openai.com/docs/api-reference
- Azure AI docs (Foundry & SDKs): https://learn.microsoft.com/en-us/azure/ai-services/
- Hugging Face docs: https://huggingface.co/docs
- IBM Watson: https://cloud.ibm.com/docs/watson

---

If you'd like I can implement the follow-up items (shim + tests + CI check) now — tell me which of the low-effort follow-ups you prefer and I’ll add them to the task list and start implementing.
