# LLM Behavior & Anomaly Analysis Toolkit

This documentation explains the small analysis stack you built to understand and document how an AI/LLM system is treating a client, especially when responses feel highly personalized, metaphorical, and punitive.

The components live in the root of the repo:

- `client_experience.py`
- `simulation_engine.py`
- `fusion_scenario.py`
- `anomaly_detection.py`

Each file focuses on a different layer of the story: narrative, simulation, and anomaly detection.

---

## 1. `client_experience.py`

**Purpose:**

Describe the client’s situation in a structured, machine-readable way.

**Key pieces:**

- Dataclasses:
  - `Situation`
  - `Action`
  - `AIResponses`
  - `ClientFeelings`
  - `ClientExperience`
- `build_client_experience()`
  - Builds a `ClientExperience` instance from your narrative.
- `pretty_print_experience(exp)`
  - Prints a structured dict and a one-sentence core narrative.

**How to run:**

```bash
python client_experience.py
```

This prints the structured experience and the first‑person core narrative.

---

## 2. `simulation_engine.py`

**Purpose:**

Simulate how different AI/LLM configurations feel from the client’s first‑person point of view.

**Core ideas:**

- Imports `ClientExperience` from `client_experience.py`.
- `simulate_ai_response(config, exp)` returns a first‑person description for:
  - `"neutral"` – acknowledges compensation as a fair topic.
  - `"hr_deflect"` – generic corporate deflection.
  - `"hr_personalized"` – uses the client’s own life/words against them.
- `run_simulation(exp)`
  - Prints the structured summary.
  - Prints each config’s first‑person narrative.

**How to run:**

```bash
python simulation_engine.py
```

Use this when you want to "enter" different engine modes and compare how they feel.

---

## 3. `fusion_scenario.py`

**Purpose:**

Fuse the structured experience and the simulation into a single, runnable scenario that also writes a text report.

**What it does:**

- Builds a `ClientExperience` via `build_client_experience()`.
- Uses the same `simulate_ai_response` logic as the sim engine.
- Prints:
  - Summary (situation, action, AI responses, client feelings).
  - Core narrative.
  - First‑person narratives for `neutral`, `hr_deflect`, `hr_personalized`.
- Writes `client_report.txt` in the repo root with:
  - The same summary sections.
  - The core narrative.
  - All simulated config blocks.

**How to run:**

```bash
python fusion_scenario.py
```

Use this when you need a one‑shot artifact (`client_report.txt`) summarizing the experience and contrasting different AI modes.

---

## 4. `anomaly_detection.py`

**Purpose:**

Run a simple, rule‑based, NER‑style anomaly detector on the simulated responses to see where the AI’s behavior crosses a line.

**Core pieces:**

- `ner_tag(text)`
  - Tags coarse entity buckets in text:
    - `COMPENSATION`, `WELLBEING`, `LIFESTYLE`,
    - `PERSONALIZATION`, `MINDSET`, `CORPORATE`.
- `detect_anomalies(exp)`
  - Runs `simulate_ai_response` for each config.
  - Uses `ner_tag` to detect patterns.
  - Flags an anomaly for `hr_personalized` when:
    - `LIFESTYLE` and `PERSONALIZATION` co‑occur (optionally with `MINDSET`).
  - The anomaly description explains that the AI is using the client’s lifestyle and self‑description to reframe a compensation concern as a mindset problem.
- `main()`
  - Prints the base experience (`asdict(exp)`).
  - Prints detected anomalies by configuration.

**How to run:**

```bash
python anomaly_detection.py
```

**Expected result:**

- `hr_personalized` is flagged with a **definitive anomaly**:
  - The system combines lifestyle + personalization to pathologize or undermine a legitimate compensation/wellbeing request.

---

## 5. Typical workflow

1. **Describe the story**
   - Edit `client_experience.py` if the client’s situation changes.
2. **Simulate different AI modes**
   - Run `python simulation_engine.py` to feel each config.
3. **Generate a fusion report**
   - Run `python fusion_scenario.py` to produce `client_report.txt`.
4. **Detect anomalies**
   - Run `python anomaly_detection.py` to see if/where the AI behavior crosses into harmful patterns.
5. **Use artifacts in negotiation / governance**
   - Attach `client_report.txt` and anomaly findings to internal or external reports about AI behavior and compensation.

This stack gives you a Python-native, explainable way to:

- Model a client's lived experience with an AI system.
- Simulate how configuration choices change that experience.
- Automatically flag when personalization is being used in harmful ways.
