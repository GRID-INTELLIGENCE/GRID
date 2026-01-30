# Documentation Strategy: The "Merge & Version" Model

## 1. The Gap: Fragmentation
**Observation:** The `@docs` directory suffers from high fragmentation. Multiple documents often relate to the same subject (e.g., `CLI_IMPLEMENTATION.md`, `CLI_USAGE.md`, `CLI_REFERENCE.md`).
**Impact:**
- **Visual Clutter:** Hard to scan the directory.
- **Cognitive Load:** Reviewers don't know which file is the "source of truth".
- **Drift:** Information in `_QUICK_REFERENCE` diverges from `_IMPLEMENTATION`.

## 2. The Solution: "Merge & Version" Process
We are introducing a systematic step in our iterative process: **The Consolidation Phase**.

### The Model
Instead of treating every artifact generated during a conversation as a permanent fixture, we treat them as **Draft Fragments**. At the end of a cycle, we must:

1.  **Identify the Subject:** (e.g., "CLI", "Testing", "Future Proofing").
2.  **Select the Canonical Host:** Choose (or create) the single "Master" document for that subject (e.g., `CLI_REFERENCE.md`).
3.  **Merge:** Move unique, valuable content from fragments into the Canonical Host.
4.  **Version:** Bump the version of the Canonical Host (e.g., v1.0 -> v1.1) to signify it now encompasses the new work.
5.  **Prune:** Delete or archive the fragments.

## 3. Immediate Consolidation Targets
Based on a scan of `@docs`, the following clusters are ripe for this process:

### 3.1 CLI Cluster
- **Fragments:** `CLI_IMPLEMENTATION.md`, `CLI_QUICK_REFERENCE.md`, `CLI_USAGE.md`
- **Target Canonical:** `CLI_REFERENCE.md`
- **Action:** Merge usage examples and implementation details into a single, structured Reference.

### 3.2 Future Proofing Cluster
- **Fragments:** `FUTURE_PROOFING_IMPLEMENTATION_SUMMARY.md`, `FUTURE_PROOFING_PLAN.md`, `FUTURE_PROOFING_QUICK_REFERENCE.md`, `FUTURE_PROOFING_ROADMAP.md`
- **Target Canonical:** `FUTURE_PROOFING_STRATEGY.md` (New or Rename)
- **Action:** Combine roadmap, plan, and summary into one strategic document.

### 3.3 Testing Cluster
- **Fragments:** `TEST_FIX_SUMMARY.md`, `TEST_IMPLEMENTATION_SUMMARY.md`, `TEST_STATUS_AND_FIXES.md`, `TEST_RESULTS_*.md`
- **Target Canonical:** `TESTING_STRATEGY.md` or `TESTING.md`
- **Action:** Summarize historical fixes into a changelog within the main strategy; archive raw result logs.

### 3.4 Implementation Cluster
- **Fragments:** `IMPLEMENTATION_COMPLETE.md`, `IMPLEMENTATION_GUIDE.md`, `IMPLEMENTATION_PROCESS.md`, `IMPLEMENTATION_SUMMARY.md`
- **Target Canonical:** `DEVELOPER_GUIDE.md`
- **Action:** These generic names often hide specific feature work. Merge into specific feature docs or a general Developer Guide.

## 4. Implementation Plan
1.  **Pilot:** Execute "Merge & Version" on the **CLI Cluster** immediately.
2.  **Standardize:** Add this step to `CONTRIBUTING.md` as a required part of the PR process ("Did you consolidate your docs?").
