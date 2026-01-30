# Translator Assistant – Behaviors by Mode & Domain

## Modes

### 1. `mode="translate"`

- Behavior:
  - Identity translation: `result_text == source_text`.
  - Explicitly marked as a **placeholder** (no real MT yet).
- Purpose:
  - Keep the contract stable while you wire actual translation engines later.

### 2. `mode="generate"`

- Behavior:
  - Wraps text into a draft scaffold:

    ```text
    # Generated Draft (placeholder)

    Original:
    <source_text>

    Draft (same as original; replace with real generation):
    <source_text>
    ```

- Purpose:
  - Emphasize structure (original vs draft) without committing to real generation yet.

### 3. `mode="bridge"`

Behavior depends heavily on `domain`.

#### `domain="design_development"`

- Output scaffold:

  ```text
  ## Feature / Change Summary (placeholder)

  ### Source Brief
  <source_text>

  ### For Developers
  - Placeholder: implementation notes.

  ### For Designers / UX
  - Placeholder: UX implications.

  ### For Stakeholders
  - Placeholder: impact summary.
