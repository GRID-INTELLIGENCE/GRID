# Research Brief: Competitors and Strategic Patterns

This brief defines the questions, tasks, and outputs expected from any deep research activity focused on the competitive landscape around Grid + the Throughput Engine.

## Research Goal

Produce a high-signal, structured analysis of competitors that can directly inform:

- Strategic positioning and messaging
- UX and interaction design (especially around dashboards and urgent states)
- AI-assisted workflows
- Short- and mid-term roadmap decisions

## Core Questions

For each major competitor or representative product:

1. Strategy and Positioning
   - How do they present themselves and to whom?
   - What problems do they claim to solve best?
   - What trade-offs do they accept (e.g., complexity vs. flexibility, fidelity vs. runtime, opinionation vs. freedom)?

2. Product and Feature Patterns
   - What are their main feature clusters?
   - What architectural patterns do they use (layers, plugins, DI, events, etc.)?
   - How do they handle auth, data, extensions, and integrations?
   - How do they approach experimentation and scenario-building (if applicable)?

3. UX Flows and Interaction Patterns
   - What are the key onboarding and “first success” flows?
   - How do they structure dashboards and main working surfaces?
   - How do users explore state, drill down, or compare runs/scenarios?
   - How do they support collaboration (roles, permissions, shared views)?

4. Urgent and Backup Behavior
   - How do they signal errors, overloads, or failures?
   - What degraded modes, safe fallbacks, or “break glass” flows exist?
   - How do they support diagnosis and recovery (logs, timelines, runbooks)?

5. Nuanced and Advanced Flows
   - For frameworks: how they guide best practices (architecture, testing, security) beyond documentation.
   - For simulation tools: parameter sweeps, ensembles, validation, calibration workflows.
   - For observability tools: cross-signals (metrics + logs + traces), incident retrospectives.
   - For AI tools: how AI is integrated into development or operations loops.

## Synthesis Tasks

Any deep research should at minimum produce the following synthesized outputs:

1. Pattern Library
   - Catalog of recurring patterns across competitors, grouped into:
     - Architecture patterns
     - Dashboard/UX patterns
     - Incident/urgent-state patterns
     - AI integration patterns
   - For each pattern: name, short description, example products, pros/cons.

2. Strategy Map vs Grid
   - Conceptual map (e.g., 2x2 or similar) showing where Grid sits relative to:
     - Web frameworks
     - Simulation/digital twin tools
     - Observability/control-plane tools
     - AI dev-assist tools
   - Explicitly call out:
     - Natural differentiators
     - Table-stakes features we should match
     - Unclaimed “white space” we can target

3. Design Recommendations
   - Concrete suggestions for:
     - Dashboard layouts and information hierarchy
     - Model-switch visualization and state timelines
     - Overload / degraded mode behavior for the engine and UI
     - AI-assisted flows tied to live metrics and code changes

4. Roadmap Ideas
   - 5–10 roadmap items where Grid can differentiate, each tagged with:
     - Effort (S/M/L)
     - Impact (low/medium/high)
     - Dependencies or prerequisites

## Style and Constraints

- Prefer concrete, evidence-backed observations over generic statements.
- Use clear headings and bullet lists; assume the reader is a technical founder/architect.
- When speculating, label it as inference rather than confirmed fact.

This brief should be read together with:
- `context_grid_throughput.md`
- `competitor_scope.md`

Those three files collectively define the research context, scope, and expectations.
