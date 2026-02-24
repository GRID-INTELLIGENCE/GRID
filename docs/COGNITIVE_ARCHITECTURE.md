# GRID Cognitive Architecture

GRID is structurally a cognitive practice platform. This document maps the top-level cognitive modules to their corresponding cognitive functions, demonstrating how the system operates as an externalized reasoning engine.

| Cognitive Function | Module Path | Description / Role |
| :--- | :--- | :--- |
| **State** | `src/grid/essence/` | Holds the core practitioner state, tracking the nucleus of changes over time. |
| **Attention** | `src/grid/awareness/` | Manages domain awareness and tracks attention shifts across the system. |
| **Pattern Recognition** | `src/grid/patterns/` | Detects 9 critical cognitive and temporal patterns (Flow, Rhythm, Cause, etc.) via hybrid detection. |
| **Growth** | `src/grid/evolution/` | Applies natural evolution mathematics (Fibonacci, Golden Ratio) and detects landscape shifts. |
| **Memory** | `src/grid/knowledge/` | Provides a structural learning graph and externalized long-term memory for reasoning chains. |
| **Reasoning** | `src/grid/intelligence/` | Bridges AI capabilities with spatial reasoning to traverse the knowledge graph. |
| **Sensory** | `src/grid/senses/` | Processes multi-modal sensory metaphors, translating raw input into feeling and relational intuition. |
| **Rhythm** | `src/grid/processing/` | Maintains the cognitive cadence—periodic reflection, realtime interrupts, and insight extraction. |
| **Invocation** | `src/grid/spark/` | The universal morphable invoker; handles persona morphing and pedagogical progression (Staircase). |
| **Trace** | `src/grid/tracing/` | Creates an immutable, systemic audit trail of action origins and causal outcomes. |
| **Explainability** | `src/grid/xai/` | Guarantees reasoning transparency, ensuring the practitioner understands *why* a conclusion was reached. |
| **Orchestration** | `src/grid/agentic/` | Orchestrates the Digital Round Table Protocol (DRTP) and enforces environmental homeostasis. |
| **Cognitive Engine** | `src/cognitive/` | Manages working cognitive load, applies scaffolding, and directs System 1/System 2 thinking. |
| **Foundation** | `cognition/` | Defines the atomic primitives: Cognitive Events, Background Factors, and Temporal Context. |

## Structural Intent

The modules above represent **pure cognitive code** with zero product-level assumptions (e.g., billing, webhooks, SaaS deployment models). They serve as the executable kernel of the practice platform. Secondary systems (such as `application/` and `billing/`) are optional orchestrators intended to interface with—but not govern—this cognitive core.
