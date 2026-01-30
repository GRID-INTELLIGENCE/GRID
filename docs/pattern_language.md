# Pattern Language for Development

This guide translates the visual and conceptual patterns from our design system into concrete software engineering practices and architectural decisions for the **Throughput Engine**.

Using these "Books" as a mental model can help in naming, structuring, and debugging code.

## 🟩 1. Flow & Motion (Green Book)
**Code Concept:** **Data Streams & Pipelines**
*   **Focus:** How data moves through the system.
*   **Application:**
    *   Designing the `ArticulationPlugin` cycles (Input $\to$ Ring $\to$ Output).
    *   Optimizing Python generators and async streams.
    *   **Question:** "Is the data flowing smoothly, or is it bottlenecked?"

## 🟦 2. Spatial Relationships (Blue Book)
**Code Concept:** **Architecture & Topology**
*   **Focus:** Where things live and how they connect.
*   **Application:**
    *   Defining the Grid structure (nodes, edges, neighbors).
    *   Module boundaries and dependency injection (Clean Architecture).
    *   **Question:** "Are these components too tightly coupled? Is the 'distance' between them correct?"

## 🟨 3. Natural Rhythms (Yellow Book)
**Code Concept:** **Concurrency & Scheduling**
*   **Focus:** The heartbeat of the system.
*   **Application:**
    *   The main `tick()` loop of the simulation engine.
    *   `asyncio` event loops and background tasks.
    *   **Question:** "Is the system breathing (processing) at a sustainable pace?"

## 🟧 4. Color & Light (Orange Book)
**Code Concept:** **Observability & Logging**
*   **Focus:** Making the internal state visible.
*   **Application:**
    *   The Thermal Imaging Dashboard (Heatmaps).
    *   Structured logging and CLI output highlighting.
    *   **Question:** "Can I clearly 'see' the hot spots (errors/performance issues) in the system?"

## 🟪 5. Repetition & Habit (Purple Book)
**Code Concept:** **Standardization & Boilerplate**
*   **Focus:** Reliable, predictable code structures.
*   **Application:**
    *   CRUD operations and REST API endpoints.
    *   Unit test fixtures and reusable utility functions.
    *   **Question:** "Is this pattern consistent with the rest of the codebase?"

## 🟥 6. Deviation & Surprise (Red Book)
**Code Concept:** **Error Handling & Resilience**
*   **Focus:** Handling the unexpected.
*   **Application:**
    *   Circuit breakers and exception handling.
    *   Validating user input (e.g., `inject` command anomalies).
    *   **Question:** "What happens when the pattern breaks? Does it crash or recover?"

## 🟦 7. Cause & Effect (Teal Book)
**Code Concept:** **Event-Driven Architecture**
*   **Focus:** Action and Reaction.
*   **Application:**
    *   The `EventBus` system (`src/kernel/bus.py`).
    *   State changes triggering model switches (Lumped $\to$ Diffusive).
    *   **Question:** "If I touch this, what exactly reacts?"

## ⬜ 8. Temporal Patterns (Silver Book)
**Code Concept:** **State History & Caching**
*   **Focus:** Changes over time.
*   **Application:**
    *   Storing historical metrics for trend analysis.
    *   Caching expensive calculations.
    *   **Question:** "How does the system remember the past to optimize the future?"

## 🟨 9. Combination Patterns (Gold Book)
**Code Concept:** **Integration & Orchestration**
*   **Focus:** The system as a whole.
*   **Application:**
    *   Integration tests ensuring plugins work together.
    *   The `System Overload` scenario where all physics models interact.
    *   **Question:** "Do the individual parts harmonize into a working application?"
