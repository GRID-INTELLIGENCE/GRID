# MYCELIUM — Pattern Recognition & Synthesis Instrument

> Synthesize complexity into simplicity. For any age, any expertise, any ability.

## What It Is

Mycelium is a **local-first, zero-dependency accessibility tool** that takes complex text — documents, articles, technical content — and produces accessible, layered output adapted to the reader.

It solves **cognitive overload** by applying the same principle that made human communication evolve from cave symbols to modern language: **compress meaning, not just length**. Extract the signal, discard the noise, present it through a lens that resonates with the specific person reading it.

## Three Missions

| # | Mission | Module | What It Does |
|---|---------|--------|-------------|
| 1 | **Understand the user** | `PersonaEngine` | Detects expertise, cognitive style, and attention span from interaction signals. Adapts automatically. User can always override. |
| 2 | **Extract what matters** | `Synthesizer` | Sentence scoring, keyword extraction, pattern detection. Produces gist, highlights, summary, explanation, analogy. |
| 3 | **Make knowledge accessible** | `Navigator` + `Scaffold` + `Sensory` | Multiple cognitive lenses per concept, adaptive depth control, 6 sensory profiles for accessibility needs. |

## Quick Start

```python
from mycelium import Instrument

m = Instrument()

# Synthesize complex text
result = m.synthesize("Your complex document text here...")
print(result.gist)          # one-line essence
print(result.highlights)    # key points extracted
print(result.summary)       # short summary
print(result.explanation)   # accessible explanation with scaffolding

# Explore a concept through pattern lenses
nav = m.explore("cache")
print(nav.lens.eli5)        # "A shelf next to you with stuff you use a lot."
print(nav.lens.analogy)     # geometric/natural metaphor

# Didn't click? Try another lens
nav2 = m.try_different("cache")

# Simplest possible explanation
print(m.eli5("recursion"))
# → "A box inside a box inside a box. Open one, find another."

# Adapt to the user
m.set_user(expertise="child", tone="playful")

# Give feedback — the tool adapts
m.feedback(too_complex=True)   # → scaffolding increases automatically

# Switch accessibility profile
m.set_sensory("cognitive")     # simplified punctuation, shorter lines, gentle tone
```

## Architecture

```
User
  │
  ▼
Instrument  ←──── single entry point, 3 verbs: synthesize / explore / simplify
  │
  ├─→ SafetyGuard ──── input validation, PII detection, bounds enforcement
  │
  ├─→ PersonaEngine ── expertise detection, cognitive style, feedback adaptation
  │
  ├─→ Synthesizer ──── sentence scoring, keyword extraction, pattern detection
  │
  ├─→ PatternNavigator ── concept lenses (flow, spatial, rhythm, cause, ...)
  │
  ├─→ AdaptiveScaffold ── depth control (NONE → MAXIMUM), 8 strategies
  │
  └─→ SensoryMode ──── 6 output profiles (default, low_vision, screen_reader, ...)
```

## Modules

| Module | File | Lines | Purpose |
|--------|------|-------|---------|
| **core** | `core.py` | ~210 | Foundation types: `Spore`, `PersonaProfile`, `SynthesisResult`, `Highlight`, enums |
| **persona** | `persona.py` | ~390 | User personality detection from interaction signals, vocabulary analysis, feedback adaptation |
| **synthesizer** | `synthesizer.py` | ~510 | TF-based keyword extraction, sentence scoring (4 heuristics), 6 pattern detectors |
| **navigator** | `navigator.py` | ~310 | 16 concepts × multiple geometric pattern lenses, resonance feedback, fuzzy lookup |
| **scaffolding** | `scaffolding.py` | ~410 | 5 depth levels, 8 strategies (chunking, simplification, step-by-step, analogy, ...) |
| **sensory** | `sensory.py` | ~310 | 6 profiles: DEFAULT, LOW_VISION, SCREEN_READER, COGNITIVE, FOCUS, CALM |
| **safety** | `safety.py` | ~340 | Input validation, PII detection, content sanitization, memory caps, parameter bounds |
| **instrument** | `instrument.py` | ~490 | User-facing entry point wiring everything together |

## API Reference

### `Instrument` — Main Entry Point

```python
m = Instrument(depth=None, sensory_profile="default")
```

#### Synthesis (Mission 2)

| Method | Returns | Description |
|--------|---------|-------------|
| `m.synthesize(text)` | `SynthesisResult` | Full synthesis: gist, highlights, summary, explanation, analogy |
| `m.summarize(text, sentences=3)` | `str` | Top N most important sentences |
| `m.simplify(text)` | `str` | Absolute simplest form (ELI5) |
| `m.keywords(text, top_n=10)` | `list[dict]` | Extracted keywords with priority and context |

#### Navigation (Mission 3)

| Method | Returns | Description |
|--------|---------|-------------|
| `m.explore(concept, pattern=None)` | `NavigationResult` | Explore concept through a cognitive lens |
| `m.try_different(concept, resonance)` | `NavigationResult` | Try a different lens after feedback |
| `m.eli5(concept)` | `str` | Simplest explanation of a concept |
| `m.concepts` | `list[str]` | All available concepts |

#### User Adaptation (Mission 1)

| Method | Returns | Description |
|--------|---------|-------------|
| `m.set_user(**traits)` | `PersonaProfile` | Set user traits explicitly |
| `m.observe(text)` | `None` | Feed text to learn about user's vocabulary |
| `m.feedback(too_complex=..., too_simple=...)` | `None` | Feedback adjusts future output |
| `m.user` | `PersonaProfile` | Current persona |

#### Accessibility

| Method | Returns | Description |
|--------|---------|-------------|
| `m.set_sensory(profile)` | `str` | Switch sensory profile |
| `m.sensory_info` | `str` | Description of active adaptations |

#### Extensibility

| Method | Returns | Description |
|--------|---------|-------------|
| `m.register_concept(name, lenses)` | `None` | Add custom concept lenses |
| `m.explain(topic)` | `str` | Plain-language explanation of any topic |

### `SynthesisResult` — Output Structure

```python
result = m.synthesize(text)
result.gist              # str — one-line essence
result.highlights        # list[Highlight] — key points with priority/context
result.summary           # str — multi-sentence summary
result.explanation       # str — scaffolded accessible explanation
result.analogy           # str — geometric/natural analogy
result.compression_ratio # float — gist_length / source_length
result.patterns_applied  # list[str] — detected text patterns
result.scaffolding_applied # list[str] — strategies used
result.as_dict()         # dict — serializable form
```

## Depth Levels

| Depth | Name | When | Output |
|-------|------|------|--------|
| `espresso` | Fast | Quick scan, child user | Gist + highlights only |
| `americano` | Balanced | Default, familiar user | Gist + summary + explanation |
| `cold_brew` | Full | Expert, deep analysis | Everything including analogy + full explanation |

## Sensory Profiles

| Profile | Line Width | Formatting | Punctuation | Urgency | Best For |
|---------|-----------|-----------|-------------|---------|----------|
| `default` | 80 | Preserved | Normal | Normal | General use |
| `low_vision` | 60 | Preserved | Normal | Normal | Larger text blocks, uppercase headings |
| `screen_reader` | 120 | Stripped | Simplified | Normal | TTS optimization |
| `cognitive` | 60 | Stripped | Simplified | Gentle | Reduced complexity, shorter chunks |
| `focus` | 50 | Stripped | Simplified | None | Single point at a time |
| `calm` | 70 | Preserved | Normal | None | Soft language, no urgency |

## Pattern Detection

The synthesizer detects 6 structural patterns in text:

| Pattern | What It Detects | Threshold |
|---------|----------------|-----------|
| **repetition** | Same words appearing ≥3 times | Word frequency |
| **rhythm** | Sentences of similar length | Coefficient of variation < 0.3 |
| **flow** | Logical progression (connectives) | ≥2 connective words |
| **deviation** | Contrast/exception language | ≥2 contrast words |
| **spatial** | Structural/organizational language | ≥2 spatial terms |
| **cause** | Causal relationships | ≥2 causal terms |

## Safety & Risk Mitigation

### Design Principles

- **Fail-closed**: Invalid input is rejected, not passed through
- **Non-punitive**: PII detection triggers warnings, not blocking (distress ≠ threat)
- **Privacy-first**: All processing local, no data transmitted, no storage without consent
- **Descriptive patterns**: Safety code uses nouns ("email address"), never imperative voice
- **Bounded resources**: All history lists are capped to prevent memory exhaustion

### Safety Invariants

| Invariant | Enforcement | Limit |
|-----------|------------|-------|
| **Input length** | Hard reject | 500,000 characters max |
| **Empty input** | Hard reject | Minimum 1 non-whitespace character |
| **Control characters** | Auto-sanitized | Null bytes, bell, backspace stripped |
| **PII detection** | Warn (not block) | Email, phone, SSN, credit card, IP patterns |
| **PII scan bound** | Capped | First 10KB only (prevents regex cost) |
| **Highlight count** | Clamped | 1–50 |
| **Sentence count** | Clamped | 1–20 |
| **Persona signals** | History cap | 500 max |
| **Word history** | History cap | 2,000 max |
| **Feedback history** | History cap | 200 max |
| **Resonance history** | History cap | 500 max |
| **Preferred patterns** | Cap | 50 max |
| **Concept name** | Length limit | 100 characters |
| **Registered concepts** | Count limit | 500 max |
| **Lenses per concept** | Count limit | 20 max |
| **Observation text** | Capped | 2,000 characters |

### Trust Layer Compliance

| Rule | Status | How |
|------|--------|-----|
| 1.1 No perpetrator voice | Compliant | All safety patterns use descriptive nouns |
| 1.2 Nominalization | Compliant | Actions converted to abstract nouns in patterns |
| 4.1 Care pathways | Compliant | PII = warn + local note, not block |
| 4.2 Non-punitive | Compliant | Detection triggers support, not punishment |
| 5.1 Refusal mechanism | Compliant | `SafetyGuard.validate_input()` rejects harmful inputs |
| 5.6 Action cascade protection | Compliant | Memory caps prevent unbounded growth |
| 5.8 Vibe coding sanitization | Compliant | All generated code tested with 174 assertions |
| 6.1 Contextual resilience | Compliant | Unicode/multilingual input supported |

## Test Suite

**174 tests across 8 files, all passing.**

```
uv run pytest tests/mycelium/ -q --tb=short
```

### Test Domains (grounded in physics)

| Domain | Ground Truth | What's Tested |
|--------|-------------|---------------|
| **EM Spectrum** | c = 299,792,458 m/s, E = hf | Signal transport, keyword extraction, compression |
| **Phase Transitions** | 0°C melting, 334 J/g fusion | State morphing, fact preservation, summarization |
| **Polar Thermodynamics** | Vostok −89.2°C, 26.5M km³ ice | Environmental patterns, albedo feedback loops |
| **Ecosystem Energy** | 10% trophic transfer, ~2% photosynthesis | Biological flow, thermodynamic law detection |

### Test Categories

| File | Tests | Coverage |
|------|-------|----------|
| `test_core.py` | 22 | Types, enums, serialization, TTL, fingerprints |
| `test_synthesizer.py` | 22 | Keywords, compression, patterns, summarize, simplify |
| `test_persona.py` | 19 | Expertise detection, style inference, feedback, reset |
| `test_navigator.py` | 16 | Lenses, resonance, persona-adaptive selection, fuzzy |
| `test_scaffolding.py` | 18 | Auto-depth, strategies, simplification, feedback bounds |
| `test_sensory.py` | 16 | All 6 profiles, formatting pipeline, info conservation |
| `test_instrument_integration.py` | 27 | End-to-end per physics domain, cross-persona |
| `test_safety.py` | 34 | Input bounds, PII, sanitization, memory caps, adversarial |

## Bugs Found & Fixed During Development

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Scaffolding simplification not applied | Vocabulary replacement ran on `sections` dict but not final `content` string | Moved simplification to run after content assembly |
| Pattern detection thresholds too high | Repetition=5 and flow=3 too strict for paragraph-length scientific text | Lowered to 3 and 2, expanded connective vocabulary |
| PII regex catastrophic backtracking | Phone number regex `(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?` caused exponential time on digit-heavy scientific text | Simplified to `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`, added 10KB scan cap |
| Persona memory cap ordering | `_enforce_caps()` ran before `_analyze_query()` appended words | Moved cap enforcement to after all analysis methods complete |

## Place in GRID Accessibility Features

Mycelium is GRID's **entry-level accessibility instrument** — the first tool a user touches when they need to understand something complex. It sits in the accessibility layer alongside GRID's existing cognitive patterns:

```
GRID Platform
  └─ Accessibility Layer
       ├─ Mycelium Instrument    ← THIS (synthesis, navigation, adaptation)
       ├─ CognitiveRouter        (expertise-based routing)
       ├─ ScaffoldingEngine      (11 content strategies)
       └─ PatternExplanation     (9-pattern human descriptions)
```

Mycelium extends these existing GRID components:
- **CognitiveRouter** → `PersonaEngine` adds vocabulary-based expertise detection
- **ScaffoldingEngine** → `AdaptiveScaffold` adds feedback-driven depth control
- **PatternExplanation** → `PatternNavigator` adds interactive multi-lens exploration

## Design Philosophy

1. **Organic engagement** — The tool adapts to the user through resonance feedback, not the user adapting to the tool
2. **Meaning before syntax** — Compress the meaning, not just the word count (cave-symbol principle)
3. **Need-based flow** — Like mycelium routing nutrients to stressed seedlings, scaffolding increases for users who need it
4. **Suggest, never impose** — Every recommendation is a suggestion; the user controls depth, style, and profile
5. **Zero config** — `Instrument()` works immediately; all adaptation is automatic
6. **Privacy absolute** — All processing local, no external calls, no data stored without explicit consent

## Running

```bash
# Run test suite
uv run pytest tests/mycelium/ -q --tb=short

# Quick smoke test
uv run python src/mycelium/_smoke_test.py

# Import and use
uv run python -c "from mycelium import Instrument; m = Instrument(); print(m.eli5('cache'))"
```
