---
description: global rules and workflow for the Grid + Cascade system
---

# Global Rules & Workflow

This document defines the **global layer** for the Grid system when used with Cascade. It encodes shared rules, input modes, and a repeatable problem-solving workflow.

## 1. Global Project Rules

### R1 – Language & Stack
- Default implementation language is **Python**.
- Respect the existing stack:
  - FastAPI for APIs.
  - SQLAlchemy for persistence.
  - Pydantic for models.
  - pytest for tests.

### R2 – Testing First
- No non-trivial change without considering tests.
- Prefer adding or adjusting tests alongside behavior changes.
- Always run `pytest` (or a targeted subset) after significant edits.
- Maintain overall coverage **≥ 80%**.

### R3 – Non-destructive Evolution
- Do not remove behavior that existing tests depend on unless explicitly agreed.
- Introduce new capabilities (e.g. relationship analyzer, formatter, RAG) in an **additive**, backwards-compatible way where possible.

### R4 – Two Canonical Input Modes
- **Conversational baseline**:
  - Single brief typed into chat/CLI → processed directly.
  - No heavy artifacts required.
- **`docs/` RAG mode**:
  - Markdown/notes/reports in `docs/` → normalized, chunked, embedded.
  - Retrieved as context for reasoning and NER.
- All new features must support the conversational baseline; RAG is an enhancement.

### R5 – Explicit Input → Process → Output
For every feature or analysis, be able to state:
- **Input**: where it comes from (chat, API, docs, DB).
- **Process**: which services/modules run (NER, pattern engine, rules engine, relationship analyzer, scenario analyzer, formatter, vector store).
- **Output**: entities, relationships, judgments, alerts, reports, scenarios.

### R6 – Logging & Traceability
- Use the existing logging utilities.
- Ensure outputs can be traced back to:
  - Source text (`event_id`, `chunk_id`).
  - Document (`doc_id`) if coming from `docs/`.
  - Time context (timestamps or time windows).

### R7 – Explainable Judgments
- Relationship judgments and alerts must expose:
  - A **label** (supportive, cooperative, neutral, competitive, adversarial, manipulative, etc.).
  - A numeric **score/confidence**.
  - A brief **explanation** and **evidence** (e.g. interaction counts, patterns, conflict/cooperation history).

---

## 2. Global Input Modes

### 2.1 Conversational Input (Baseline)
- You (the analyst) capture the client’s explanation directly:
  - Who/what is involved.
  - What is happening (problem description).
  - Timeframe and stakes.
  - What they want to know (friend/foe, risks, opportunities, decisions).
- This brief is treated as a **single event** and fed to the pipeline:
  - No external files are required.

### 2.2 `docs/`-Based Input (RAG / Embeddings)
- Richer context is stored under `docs/`:
  - `problem_brief.md`, strategy notes, historical reports, logs, transcripts.
- A **formatter**:
  - Normalizes text (strip markup noise, keep structure such as headings and sections).
  - Segments into sections (by headings or logical blocks).
  - Chunks into ~300-token windows with overlap.
  - Embeds and caches each chunk in a vector store with metadata:
    - `doc_id`, `chunk_id`, section title, approximate time range, tags.
- At query time, the system retrieves the most relevant chunks and uses them as context for NER, reasoning, and relationship judgments.

---

## 3. Global Problem-Solving Workflow

This is the standard Grid problem-solving loop for any client or scenario.

### Stage 0 – Setup & Context
- Confirm environment:
  - Tests are green; coverage ≥ 80%.
- Confirm which input modes will be used:
  - Conversational only, or
  - Conversational + `docs/` RAG.

### Stage 1 – Intake (Input)

1. **Collect conversational brief**
   - Capture the client’s explanation in free text.
   - Optionally mirror it into `docs/problem_brief.md` for future reference.

2. **Collect optional `docs/` artifacts**
   - Add any relevant documents to `docs/` when available:
     - Historical performance, emails, logs, strategy decks, reports.

### Stage 2 – Formatting & Normalization

1. **Conversational path**
   - Treat the brief as:
     - `Event.source = "client_brief"`.
     - `Event.raw_text = brief`.
     - Minimal `event_metadata` (client identifier, case identifier, time).

2. **Docs/RAG path**
   - Run the formatter over `docs/`:
     - Normalize + segment + chunk + embed + cache.
   - Store chunks and embeddings in a vector store, keyed by `doc_id` and `chunk_id`.

### Stage 3 – Grid Processing Pipeline (Process)

1. **Ingestion**
   - Conversational brief is ingested as an `Event`.
   - For `docs/`, either:
     - Ingest chunks as events, or
     - Retrieve relevant chunks and pass their text into services as context.

2. **NER & Normalization**
   - Use `NERService` / `NERPlugin` to extract:
     - Entities (ORG, PERSON, MONEY, etc.).
     - Relationships between entities.

3. **Pattern & Rule Evaluation**
   - Run `PatternEngine` to detect cognition patterns:
     - Spatial, temporal, deviation/surprise, combination patterns.
   - Run `RulesEngine` to evaluate:
     - Competitor rules.
     - Anomaly rules (e.g. frequency spikes, new entities).
     - Custom rules.

4. **Relationship Judgment**
   - For each `EntityRelationship`:
     - Use `RelationshipAnalyzer` to compute:
       - `polarity_score` (−1.0 to +1.0).
       - `polarity_label` (friend/foe/neutral spectrum).
       - `confidence`.
       - Explanation and evidence.

5. **Scenario Analysis (optional)**
   - Use `ScenarioAnalyzer` to explore:
     - What-if trajectories.
     - Escalation paths.
     - Risk/opportunity scenarios.

### Stage 4 – Outputs & Review (Output)

1. **Structured outputs**
   - Entities, relationships, pattern matches, alerts, judgments, and scenarios are written to the database.
   - API endpoints (e.g. `/ner/entities`, `/ner/relationships`, `/ner/alerts`) expose these as JSON.

2. **Analyst-facing summaries**
   - For each client/case, produce a short summary (often as Markdown in `docs/`):
     - Key entities and roles.
     - Relationship map (friend/foe/neutral, key dynamics).
     - Notable patterns and alerts.
     - Scenario highlights and recommendations.

3. **Validation & iteration**
   - Compare outputs against the analyst’s own judgment:
     - Do the labels and scores feel right?
     - Are important actors or conflicts missing?
   - Iterate by adjusting:
     - Relationship analyzer feature weights and thresholds.
     - Rules and pattern definitions.
     - Formatter/chunking settings for `docs/`.

---

## 4. How Cascade Uses This Layer

- Cascade reads these rules and workflow as the **global operating frame** for this repo.
- For each new client problem, Cascade will:
  1. Ask for or infer the **input mode(s)** (conversational, `docs/`, or both).
  2. Map the brief and/or docs into the **Grid processing pipeline**.
  3. Present outputs in the explicit **Input → Process → Output** framing.
  4. Support iterative tuning while preserving tests, coverage, and traceability.
