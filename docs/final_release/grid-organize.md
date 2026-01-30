# GRID: Organizing Intelligence (Taxonomy)
**Structural Rationale for a High-Complexity Ecosystem**

The GRID directory structure is designed for **Cognitive Grounding**, ensuring that both AI agents and human architects can rapidly locate high-signal data.

---

## 📂 Core Taxonomy

### 1. The Intelligence Layer
- **`grid/`**: The primary Python package containing internal intelligence logic.
- **`motion/`**: Dedicated module for B-spline trajectory diffusion and movement AI.
- **`tools/rag/`**: The vector search and retrieval engine.

### 2. The Operational Layer
- **`application/`**: Frontend dashboard (React/TypeScript) for synthesis visualization.
- **`backend/`**: API handlers and high-concurrency request management.
- **`infra/`**: Docker, Makefile, and deployment specifications.

### 3. The Contextual Layer
- **`.context/`**: High-signal summaries for AI grounding.
- **`.welcome/`**: Onboarding assets and visual themes.
- **`docs/`**: Technical specifications, roadmaps, and final release reports.

---

## 🏛️ Directory Evolution

| Legacy Path | New Path | Reason |
|-------------|----------|--------|
| `src/grid` | `grid/` | Direct package access for cleaner relative imports. |
| `analysis/clustering` | `grid/analysis/` | Package consolidation for the `PatternEngine`. |
| `test_*.py` (root) | `tests/unit/` | Standardized test hierarchy for CI/CD runners. |

---

## 🛠️ File Naming Conventions
- **`*.md`**: Documentation (Upper-case for index files, lower-case for feature docs).
- **`*.tsx`**: React Components (PascalCase).
- **`*.py`**: Python Modules (snake_case).
- **`.env.*`**: Environment-specific configurations.

---

**Authorized by**: GRID Nexus Taxonomy Board
**Last Updated**: 2026-01-06
