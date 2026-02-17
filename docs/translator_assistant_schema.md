# Translator Assistant – Schema

## Request: [TranslatorAssistantRequest](cci:2://file:///e:/grid/src/services/translator_assistant.py:7:0-68:5)

Key fields:

- `source_text: str`
  Main text to translate / transform / explain.

- `source_language: str = "auto"`
  Source language code or `"auto"`.

- `target_language: str | list[str]`
  Single target language or list of targets.

- `mode: str`
  - `"translate"` – translation stub.
  - `"generate"` – draft wrapper.
  - `"bridge"` – structured explanation.

- `domain: str`
  - `"general"`
  - `"design_development"`
  - `"scientific_research"`
  - `"archeology"`
  - `"biology"`
  - `"animals"`
  - `"plants"`
  - `"homosapiens"`

- Context & shaping:
  - `code_context: Optional[str]`
  - `context_tags: list[str]`
  - `constraints: Optional[str]`
  - `bridge_from: Optional[str]`
  - `bridge_to: Optional[str]`

## Response: [TranslatorAssistantResponse](cci:2://file:///e:/grid/src/services/translator_assistant.py:82:0-116:5)

- `result_text: str`
  Main structured output.

- `target_language: str | list[str]`

- `explanation: Optional[str>`
  How and why the output was shaped (mode, domain, context).

- `notes: list[str]`
  Caveats and implementation hints.

- `segments: Optional[list[TranslatorAssistantSegment]]`
  Each segment:
  - `source: str`
  - `result: str`
  - `comment: Optional[str]`

- `mode: str`, `domain: str`
- `code_context_used: bool`
- `metadata: dict` (for `event_id`, `doc_id`, `chunk_id`, etc.)
