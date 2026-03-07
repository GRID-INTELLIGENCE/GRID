# GRID: Master Workflow & Governance
**Standard Operating Procedures (SOP)**

The Master Workflow ensures that all updates to the GRID core maintain 100% stability and visual resonance.

---

## 🛠️ The Core Development Loop

### 1. Resonance Alignment (Design First)
Before functional changes, verify alignment with the **Navy Amber** aesthetic.
- UI elements must use the `grid-` Tailwind prefix.
- Animations must follow the `zoom-in-95` / `duration-1000` standard.

### 2. Pattern Matching (Implementation)
- New logic must be scaffolded with B-spline compatible interfaces if involving motion.
- All RAG-relevant files must be tagged with `@intel` in docstrings for the auto-indexer.

### 3. The "Tension Loop" (Verification)
- [ ] **Lint**: Run `ruff check` on all modified Python files.
- [ ] **Test**: Execute `pytest tests/unit/test_[module].py`.
- [ ] **Benchmark**: Run `grid-grep` benchmark if modifying search logic.

---

## 🏛️ Governance Rules

| Rule | Description |
|------|-------------|
| **Stability Guard** | No merge allowed if P0 test coverage falls below 95%. |
| **Aesthetic Guard** | No UI modifications without an accompanying `design_aesthetics.md` update. |
| **Legacy Protection** | All `legacy_src` modifications must include a fallback bridge. |
| **Doc-Sync** | Any file change requires a corresponding update in the `docs/` index. |

---

## 🧭 Master Navigation Commands

- **`git branch -m feature/[nexus-id]`**: Dedicated feature branches.
- **`make build`**: Complete system resynthesis (Backend + Frontend).
- **`make stabilize`**: Automated repair of common import and syntax errors.

---

**Classification**: Internal Standard
**Governance Level**: Level 4 (Nexus Protocol)
