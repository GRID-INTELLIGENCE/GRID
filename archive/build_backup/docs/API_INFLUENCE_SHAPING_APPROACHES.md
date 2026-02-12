# API Influence & Outcomes: Shaping Approaches for the Future

**Purpose:** Forward-looking principles and practices for designing APIs and features so that influence stays transparent, user-aligned, and within safety boundaries.  
**Context:** [API_TARGETED_INFLUENCE_AUDIT_REPORT_2026_02_06.md](API_TARGETED_INFLUENCE_AUDIT_REPORT_2026_02_06.md) — audit found no current manipulation; this doc shapes how we keep it that way.

---

## 1. Principles

| Principle | Meaning |
|-----------|--------|
| **Transparency for adaptations** | When responses are simplified, expanded, or routed (e.g. cognitive load, scaffolding), the *reason* for the adaptation is available (e.g. XAI explanations). No hidden “why we showed you this.” |
| **Opt-in for influence** | Any API or feature that *influences* user choices or outcomes (recommendations, motivational routing, similar-case suggestions) requires explicit user opt-in and clear labeling. Default is *informational*, not *steering*. |
| **Personalization = UX clarity by default** | Personalization is tied to comprehension, workload, and clarity—not to changing user decisions or persuasion goals. If it affects *what* the user decides (not just *how* it’s presented), treat it as influence and gate it. |
| **Track capability drift** | Internal capabilities (recommendations, motivational scoring, similar-case retrieval) must not silently become public influence. New endpoints that consume these need a deliberate design and review step. |

---

## 2. Design Gates (When Adding or Changing APIs)

Before **exposing** any of the following via public or partner-facing APIs, apply these gates:

- **Recommendation-style outputs** (similar cases, “you might also,” outcome-based suggestions)  
  → Require **explicit opt-in** and **label** responses as recommendations (not facts).  
  → Document in API spec that the endpoint is recommendation/influence and may vary by user.

- **Motivational or urgency routing** (scores, priority, “what to do next”)  
  → Either keep **internal-only** or expose only with **transparency**: user sees that ordering/urgency is system-generated and can ignore or override.  
  → Avoid per-user *targeting* of motivation (e.g. steering toward specific outcomes).

- **User or cohort segmentation** for **content or ordering**  
  → If segmentation affects *what* or *in what order* options are shown (beyond pure UX clarity), treat as influence: opt-in + transparency.

- **Outcome or success data** driving **what we show**  
  → Using success/failure to *bias* suggestions = influence. Gate behind opt-in and label; do not use for silent steering.

**Simple gate question:** *Could this endpoint change what the user decides or does, not just how clearly they see it?*  
If yes → opt-in, labeling, and documentation.

---

## 3. Review Checklist (Capability Drift)

When reviewing code or design that touches these areas, do a quick check:

- [ ] Does any **new or changed public API** call `get_recommendations()`, `find_similar_cases()`, or motivational routing?
- [ ] Does any **new endpoint** use **user_id** or **profile** for *ordering*, *filtering*, or *prioritization* of content (beyond auth/scope)?
- [ ] Is **outcome data** (success/failure, conversions) used to **change** what we show in this API (rather than only for analytics)?
- [ ] Are **adaptations** (simplified vs detailed, routing) **explainable** to the user where relevant?

If any box is checked, confirm: opt-in and/or transparency is in place and documented.

---

## 4. Defaults to Embed in Design

- **Public APIs:** No recommendation or motivational output unless explicitly added as an opt-in, labeled feature.
- **Internal tools:** Can use similar-case retrieval and motivational routing for **productivity/analytics**; do not wire these to public endpoints without going through the design gates above.
- **Personalization:** Default to **clarity and workload** (e.g. cognitive load, scaffolding). Any move toward **outcome-oriented** personalization (e.g. “show this so the user is more likely to X”) must be opt-in and transparent.
- **New integrations:** If a third-party or new product consumes our APIs for “recommendations” or “next best action,” contract and docs should state that such use is influence and subject to user consent and labeling.

---

## 5. Capability-Adjacent Areas (Ongoing Monitoring)

From the audit, keep an eye on:

- **Canvas/Resonance** — motivational routing and urgency; keep internal or make transparent if exposed.
- **Similar-case retrieval / AgenticSystem.get_recommendations()** — do not expose in public APIs without opt-in and “recommendation” labeling.
- **Cognitive/router and scaffolding** — keep scoped to UX clarity; if any future change ties them to *outcome* goals, re-run the gate.

---

## 6. When in Doubt

- **Prefer:** Explainable, opt-in, labeled influence.  
- **Avoid:** Silent steering, unlabeled recommendations, or outcome-targeted personalization by default.  
- **Escalate:** Any design that uses user or cohort data to *change* decisions or ordering in a way that isn’t clearly disclosed—treat as influence and apply these shaping approaches.

---

*Last updated: 2026-02-07. Linked from API_TARGETED_INFLUENCE_AUDIT_REPORT_2026_02_06.md.*
