# Translator Assistant – Era Presets & Demos

## Era Presets

We define era presets as thin wrappers over [TranslatorAssistantRequest](cci:2://file:///e:/grid/src/services/translator_assistant.py:7:0-68:5).

### Pre‑electricity Scientist

- Era key: `pre_electricity`
- Domain: `scientific_research`
- Prefix added to `source_text`:
  - `"As a 19th century naturalist before electricity, "`
- Typical layout:
  - Research Summary (Overview / Findings / Uncertainties).
- Mood:
  - Light mode, lab notebook, observational.

### French Painting Salon

- Era key: `french_painting`
- Domain: `homosapiens`
- Prefix:
  - `"As a French impressionist painter, "`
- Typical layout:
  - Research-style scaffold, but framed as interpretation of scenes, light, and mood.

### Disco Era Product Pitch

- Era key: `disco`
- Domain: `design_development`
- Prefix:
  - `"As a 1970s disco club promoter, "`
- Typical layout:
  - Feature / Change Summary (Dev / UX / Stakeholder).
- Mood:
  - Dark theme, neon, product storytelling.

## Helper Function (pseudo-code)

```python
from src.services.translator_assistant import TranslatorAssistantRequest

def build_era_request(selected_text: str, era: str) -> TranslatorAssistantRequest:
    if era == "pre_electricity":
        domain = "scientific_research"
        prefix = "As a 19th century naturalist before electricity, "
    elif era == "french_painting":
        domain = "homosapiens"
        prefix = "As a French impressionist painter, "
    elif era == "disco":
        domain = "design_development"
        prefix = "As a 1970s disco club promoter, "
    else:
        domain = "general"
        prefix = ""

    return TranslatorAssistantRequest(
        source_text=prefix + selected_text,
        source_language="en",
        target_language="en",
        mode="bridge",
        domain=domain,
        context_tags=["era_bridge"],
    )
```
