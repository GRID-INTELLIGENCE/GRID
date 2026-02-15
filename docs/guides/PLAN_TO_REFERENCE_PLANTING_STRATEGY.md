# Plan-to-Reference Planting Strategy

This document defines how the **Plan-to-Reference** system will be "planted" (integrated and deployed) into the development workflow of THE GRID. The strategy focuses on multiple independent "seed points" that grow into a cohesive ecosystem of plan-aware tooling.

## Planting Strategy Definition

The system is not a monolithic tool but a distributed set of capabilities that activate at specific moments in the development lifecycle. "Planting" means identifying these moments and embedding the Plan-to-Reference logic there.

The strategy follows a **"Detect, Resolve, Verify"** loop:
1.  **Detect** user intent or plan-like structures.
2.  **Resolve** abstract plan items to concrete code references.
3.  **Verify** the resolution against the actual codebase state.

---

## Seed Points

We have identified 10 key seed points where the system takes root.

### 1. Explicit Activation
**Definition**: The user consciously invokes the system to map a plan.

*   **Scenario**: A developer has a rough list of tasks in their head and wants to know exactly which files to touch. They explicitly ask the agent to "resolve this plan."
*   **Example**: "Here is my implementation plan for the auth system. Please resolve these steps to file references."
*   **Analogy**: **Hailing a Taxi**. You stand on the curb and wave your hand; the service stops specifically for you because you asked for it.

### 2. Plan Pattern Detection
**Definition**: The system passively monitors conversation and auto-suggests resolution when it sees a plan.

*   **Scenario**: The user types a numbered list of technical steps during a brainstorming session. The system recognizes this structure as a "Plan" and offers to resolve it.
*   **Example**: User types: "I'm going to: 1. Update api.py, 2. Add a test." -> System responds: "I see a plan. Would you like me to map these to strict file paths?"
*   **Analogy**: **Metal Detector**. The device is always on, sweeping the ground. It beeps automatically when it detects something valuable (metal/plan), without you telling it to look at that specific spot.

### 3. Conversation Context
**Definition**: Inheriting plan context from previous turns or valid "Plan" artifacts in the chat history.

*   **Scenario**: The user says "Go ahead with step 3." The system must look back, find the active plan, resolve "Step 3" to a specific file/function, and execute.
*   **Example**: "Regarding the plan we discussed yesterday, let's execute the 'Update Auth' item."
*   **Analogy**: **Continuing a Phone Conversation**. You don't say "Hello, this is John" every time you speak; the connection is open, and context is preserved across the flow of time.

### 4. Board Import
**Definition**: Ingesting plans from external project management tools (Jira, GitHub Projects, Trello).

*   **Scenario**: A Product Manager has defined a sprint in a project board. The developer imports this list, and the system instantly converts "Card #123" into "File: `src/main.py`".
*   **Example**: "Import the 'Q3 Security Board' tasks and map them to our codebase."
*   **Analogy**: **Plugging in a USB Drive**. You take completely external data (files on a stick/tasks on a board) and plug it into your system, where it becomes readable and usable native data.

### 5. IDE Verification Chain
**Definition**: A post-resolution check that ensures every resolved reference actually points to a real, valid symbol.

*   **Scenario**: The system looks at a resolved plan item "Update `auth.py`" but sees `auth.py` does not exist. It flags this before any code is written.
*   **Example**: "Item 3 maps to `src/auth.py`, but that file is deleted. Did you mean `src/authentication.py`?"
*   **Analogy**: **Quality Control Line**. Before a product (plan) leaves the factory (agent), it goes through a sensor that kicks out defective units (broken links) so the customer never sees them.

### 6. Config Reviewer
**Definition**: Using the resolved plan to check for compliance with project configuration standards.

*   **Scenario**: A plan involves checking "Is this config change allowed?" The system cross-references the targeted files against `.claude/rules`.
*   **Example**: "This plan modifies `pyproject.toml`. Does it adhere to our dependency management standards?"
*   **Analogy**: **Code Review**. Just as a senior engineer reviews code for style, this seed point reviews *intent* against the "law" of the project configuration.

### 7. Documentation Enhancement
**Definition**: Identifying gaps where a plan item is "Update Docs" but no corresponding documentation file exists.

*   **Scenario**: A plan has a step "Document API changes," but the resolved reference returns `None`. The system suggests creating a new doc or updating an existing one.
*   **Example**: "Step 4 is 'Update Docs', but I found no relevant markdown file. Should I create `docs/api_changes.md`?"
*   **Analogy**: **A Librarian**. They notice a gap in the bookshelf where volume 4 should be and order a replacement, ensuring the collection (documentation) remains complete.

### 8. Development Discipline
**Definition**: Enforcing that *every* code change must track back to a resolved plan item.

*   **Scenario**: A developer opens a file that isn't in the agreed-upon plan. The system warns them or asks for justification, preventing scope creep.
*   **Example**: "You are editing `payment_gateway.py`, but that is not in the current 'Auth System' plan. Please add it to the plan first."
*   **Analogy**: **Building Inspector**. They check the construction site. If you're building a wall that isn't on the blueprints, they stop you. "If it's not on the print, it doesn't get built."

### 9. Error Recovery
**Definition**: Gracefully handling cases where references break or change during execution (file moves, renames).

*   **Scenario**: Mid-execution, `utils.py` is renamed to `common.py`. The plan reference breaks. The system detects this and dynamically updates the map to the new location.
*   **Example**: "Reference `utils.py` lost. Fuzzy search found `common.py` with 90% similarity. Updating plan map."
*   **Analogy**: **GPS Rerouting**. You miss a turn or the road is closed. The GPS doesn't give up; it instantly calculates a new route to get you to the same destination.

### 10. Format Pivot
**Definition**: Converting the resolved plan data into various formats for different stakeholders (CSV, Mermaid, JSON, Markdown).

*   **Scenario**: The developer needs a checklist, the manager needs a Gantt chart, and the script needs JSON. The system "pivots" the same core data into these views.
*   **Example**: "Export this resolved plan as a CSV for the weekly report."
*   **Analogy**: **Universal Travel Adapter**. The electricity (data) is the same, but the plug shape (format) changes depending on which country (user/tool) you are plugging into.
