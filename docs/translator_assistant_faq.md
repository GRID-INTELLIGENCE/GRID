# Translator Assistant – FAQ

## Basics

**Q: What is [assistant_translator_API](cci:1://file:///e:/grid/src/services/translator_assistant.py:119:0-274:5) in one sentence?**
A context-aware translator/assistant API that turns text into structured, explainable summaries and briefs based on `mode` and `domain`.

**Q: Does it do real translation right now?**
No. `mode="translate"` is an identity stub. The design assumes a real MT/LLM engine will be plugged in later behind the same schema.

**Q: How is this different from a normal translator?**
- It produces **sections** (e.g., Dev / UX / Stakeholder, or Overview / Findings / Uncertainties).
- It exposes `explanation`, `notes`, `segments`, and `metadata` for traceability.
- It aligns with Grid’s logging and event/document tracing rules.

## Use Cases

- **Product / Design / Dev**
  - Paste a feature or change description.
  - Use `mode="bridge"`, `domain="design_development"`.
  - Get a scaffold for Dev, UX, and Stakeholders.

- **Research / Field Notes / Archeology**
  - Paste a field note, abstract, or site report.
  - Use `mode="bridge"` with `domain` in:
    - `"scientific_research"`, `"animals"`, `"plants"`, `"homosapiens"`, `"archeology"`.
  - Get a Research Summary skeleton.

- **Era Storyboard**
  - Run the same text through different era presets:
    - `pre_electricity`, `french_painting`, `disco`.
  - Compare how explanations change by era and domain.

## Integration

- The schema is stable and testable today (no external calls).
- When ready, plug in real models inside [assistant_translator_API](cci:1://file:///e:/grid/src/services/translator_assistant.py:119:0-274:5) branches:
  - Keep the same Pydantic models and structures.
  - Preserve tests that assert on sections, modes, domains, and semantics.
