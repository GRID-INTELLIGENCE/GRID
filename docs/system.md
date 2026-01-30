# Grid System Overview

A cognitive, test-first Python system for reasoning about entities, patterns, and relationships across text and events. Grid combines:

- Deterministic testing and CI/CD (80%+ coverage, seeded runs).
- Cognitive pattern engines (spatial, temporal, flow, rhythms, etc.).
- Relationship and scenario analyzers for friend/foe/neutral judgments.
- A translator assistant for code-aware translation, generation, and bridges.

## Core Principles

- **Determinism** – Fixed seeds, reproducible runs, stable CI.
- **Traceability** – Every judgment and translation can be traced to events, docs, or code context (event_id, doc_id, chunk_id).
- **Explainability** – Outputs include labels, scores, and short explanations with evidence.
- **Cognitive Alignment** – Engines implement the 9 cognition patterns defined in the Grid docs (flow, contrast, repetition, etc.).

## Execution Pipeline (High Level)

1. **Ingest**
   - Conversational briefs or docs from `docs/` become Events.
   - Optional code/document snippets are passed as `code_context`.

2. **Analyze**
   - NER & pattern engines detect entities, patterns, and anomalies.
   - Rules and relationship analyzers assign polarity labels and scores.

3. **Translate / Bridge (Translator Assistant)**
   - `TranslatorAssistantRequest` captures:
     - `source_text`, languages, `mode` (`translate|generate|bridge`),
     - `domain` (e.g. `design_development`, `scientific_research`),
     - optional `code_context`, `context_tags`, and bridge helpers.
   - `assistant_translator_API` shapes `TranslatorAssistantResponse` with:
     - `result_text`, `segments`, `notes`, `explanation`, and `metadata`.

4. **Verify**
   - Pytest suite with markers (`unit`, `integration`, `critical`, etc.).
   - GitHub Actions main CI workflow enforces coverage and deterministic behavior.

## Testing & CI/CD

- **Local** – `pytest tests/ -v --cov=src --cov-fail-under=80`.
- **CI** – Single canonical workflow `.github/workflows/main-ci.yml`:
  - Lint & type-check.
  - Unit tests across 3 Python versions.
  - Integration tests.
  - Coverage check with threshold.
  - Critical-path tests and final summary.

## Outputs

- Structured JSON-like models (Pydantic) for requests, responses, reports.
- JSON schemas (artifacts/schemas) for external tools and integrations.
- Markdown reports in `docs/` describing implementation, verification, and execution roadmaps.
