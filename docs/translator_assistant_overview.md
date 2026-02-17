# Translator Assistant API (Era Bridge) – Overview

## Purpose

[assistant_translator_API](cci:1://file:///e:/grid/src/services/translator_assistant.py:119:0-274:5) is a context-aware translator/assistant model in the Grid codebase.

It focuses on **structured, explainable outputs** (summaries, briefs, research skeletons), not just raw translation. It is designed to be:

- **Deterministic** right now (no external calls).
- **Traceable** via explicit `mode`, `domain`, segments, and metadata.
- **Swappable**: you can later plug in real MT/LLM engines without changing the schema.

## Location

- Code: [src/services/translator_assistant.py](cci:7://file:///e:/grid/src/services/translator_assistant.py:0:0-0:0)
- Exports:
  - [TranslatorAssistantRequest](cci:2://file:///e:/grid/src/services/translator_assistant.py:7:0-68:5)
  - [TranslatorAssistantResponse](cci:2://file:///e:/grid/src/services/translator_assistant.py:82:0-116:5)
  - [TranslatorAssistantSegment](cci:2://file:///e:/grid/src/services/translator_assistant.py:71:0-79:33)
  - [assistant_translator_API](cci:1://file:///e:/grid/src/services/translator_assistant.py:119:0-274:5)
