# Clean Structure Proposal: Professional Grade GRID Organization

## Overview

This document proposes a clean, professional project structure that harmonizes industry standards with GRID's unique cognitive/semantic domains. The proposal maintains your valuable custom code while following Python/FastAPI best practices.

## Current State Assessment

### Strengths ✓
- FastAPI structure follows industry best practices
- Custom domain names are semantically meaningful
- Layered architecture is properly implemented
- Package boundaries are mostly clear
- Security module organization is excellent

### Areas for Improvement ⚠
- Import ambiguity (`from grid...` vs `from src.grid...`)
- `src/` and `grid/` both exist (confusion)
- Research code mixed with production code
- Tools organization could be clearer

## Proposed Clean Structure

### Core Philosophy

**"Standard patterns for standard code, semantic clarity for custom domains"**

- Use **industry-standard patterns** for FastAPI/Python code
- Use **semantic domain names** for custom cognitive/semantic code
- Maintain **clear boundaries** (what's standard vs custom)
- Enable **intuitive discovery** (where do I find X?)

### Structure Diagram

```
grid/                                    # Root: Monorepo
│
├── 📦 grid/                             # Core Intelligence Package (INSTALLABLE)
│   ├── essence/                         # ⭐ CUSTOM: Quantum state transformations
│   ├── patterns/                        # ⭐ CUSTOM: 9 cognition patterns
│   ├── awareness/                       # ⭐ CUSTOM: Context/temporal/spatial
│   ├── evolution/                       # ⭐ CUSTOM: State evolution
│   ├── interfaces/                      # ⭐ CUSTOM: Quantum bridges
│   ├── skills/                          # ⭐ CUSTOM: Skills registry
│   ├── application.py                   # Orchestrator
│   └── __init__.py
│
├── 📦 application/                      # FastAPI Applications Package (INSTALLABLE)
│   ├── mothership/                      # Main API (STANDARD FastAPI structure)
│   │   ├── routers/                     # ✓ Standard: Route handlers
│   │   ├── services/                    # ✓ Standard: Business logic
│   │   ├── repositories/                # ✓ Standard: Data access
│   │   ├── models/                      # ✓ Standard: ORM models
│   │   ├── schemas/                     # ✓ Standard: Pydantic schemas
│   │   ├── middleware/                  # ✓ Standard: Middleware
│   │   ├── security/                    # ✓ Standard: Security module
│   │   ├── config.py                    # ✓ Standard: Settings
│   │   ├── dependencies.py              # ✓ Standard: DI
│   │   └── main.py                      # ✓ Standard: App factory
│   └── resonance/                       # Resonance API (CUSTOM concept, standard structure)
│       ├── api/                         # API layer
│       └── ...
│
├── 🧠 light_of_the_seven/               # Cognitive Layer (RESEARCH + PRODUCTION)
│   ├── cognitive_layer/                 # 📦 PRODUCTION: Cognitive layer (could be package)
│   │   ├── decision_support/            # ⭐ CUSTOM: Bounded rationality
│   │   ├── mental_models/               # ⭐ CUSTOM: Mental model tracking
│   │   ├── cognitive_load/              # ⭐ CUSTOM: Cognitive load management
│   │   └── integration/                 # Integration with GRID
│   └── research/                        # 📚 RESEARCH: Research documentation
│
├── ⚙️ tools/                            # Development Tools (MODULES, not package)
│   ├── rag/                             # Local RAG system (CUSTOM implementation)
│   └── ...                              # Other tools
│
├── ✅ tests/                            # Test Suite
│   ├── unit/                            # Unit tests
│   ├── integration/                     # Integration tests
│   └── ...
│
├── 📚 docs/                             # Documentation
│   ├── architecture/                    # Architecture docs
│   ├── deployment/                      # Deployment docs
│   ├── security/                        # Security docs
│   ├── research/                        # Research analysis
│   └── ...
│
├── 🔧 scripts/                          # Utility Scripts
├── 🔄 workflows/                        # CI/CD Workflows
├── 🏗️ infra/                           # Infrastructure Code
├── 📦 frontend/                         # Frontend Assets (if any)
│
├── 📋 pyproject.toml                    # Package Configuration
├── 📋 requirements.txt                  # Dependencies
├── 📋 README.md                         # Project Documentation
└── 📋 ...                               # Config files
```

## Structure Principles

### 1. Package Classification

**Installable Packages (in pyproject.toml):**
- `grid/` - Core intelligence package
- `application/` - FastAPI applications package

**Potential Packages (future consideration):**
- `light_of_the_seven/cognitive_layer/` - Could become `grid_cognitive/` package

**Non-Packages (utilities/modules):**
- `tools/` - Development tools (modules, not installable)
- `scripts/` - Utility scripts
- `docs/` - Documentation
- `tests/` - Test suite

### 2. Import Path Standards

**Canonical Import Paths (Preferred):**
```python
# Core domain (CUSTOM)
from grid.essence import EssentialState
from grid.patterns import PatternRecognition
from grid.awareness import Context
from grid.evolution import VersionState
from grid.interfaces import QuantumBridge
from grid.skills import SkillRegistry

# Applications (STANDARD)
from application.mothership.main import app
from application.mothership.routers import health_router
from application.mothership.services import CockpitService
from application.resonance.api import router

# Cognitive layer (CUSTOM)
from light_of_the_seven.cognitive_layer.decision_support import BoundedRationalityEngine
from light_of_the_seven.cognitive_layer.mental_models import ModelTracker

# Tools (INTERNAL)
from tools.rag import RAGEngine
from tools.rag.indexer import index_repository
```

**Deprecated (Remove Over Time):**
```python
from src.grid...          # ❌ Consolidate to from grid...
from src.services...      # ❌ Consolidate to appropriate package
```

### 3. Boundary Definitions

#### Standard Code (Follow Industry Patterns)
**Location:** `application/mothership/*`
- Routers, services, repositories, models, schemas
- Use standard naming conventions
- Follow FastAPI/Python best practices

#### Custom Domain Code (Semantic Names)
**Location:** `grid/*`, `light_of_the_seven/cognitive_layer/*`
- Custom domain concepts (essence, patterns, awareness)
- Use semantic domain names
- Document unique concepts

#### Infrastructure Code
**Location:** `tools/*`, `scripts/*`, `infra/*`
- Development tools, utilities, infrastructure
- Clear purpose, well-documented

### 4. Naming Conventions

**Package Names:**
- Use `lowercase_with_underscores` for package directories
- Match package name to directory name (`grid/` package in `grid/` directory)

**Module Names:**
- Use `lowercase_with_underscores` for Python modules
- Use semantic names for custom domains

**Class Names:**
- Use `PascalCase` for classes
- Use descriptive, domain-appropriate names

## Detailed Structure Rationale

### Tier 1: Core Domain Packages

#### `grid/` - Core Intelligence Package

**Purpose:** Core geometric resonance intelligence domain

**Why This Structure:**
- Installable package (in pyproject.toml)
- Clear domain boundary
- Semantic submodule names reflect domain concepts
- Self-contained intelligence layer

**Submodules:**
- `essence/` - Fundamental state (semantic name, custom domain)
- `patterns/` - Pattern recognition (semantic name, custom domain)
- `awareness/` - Context mechanics (semantic name, custom domain)
- `evolution/` - State evolution (semantic name, custom domain)
- `interfaces/` - Bridges (generic but works in context)
- `skills/` - Skills registry (clear, appropriate name)

**Import Pattern:**
```python
from grid.essence import EssentialState
from grid.patterns import PatternRecognition
```

#### `application/` - FastAPI Applications Package

**Purpose:** FastAPI application layer

**Why This Structure:**
- Installable package (in pyproject.toml)
- Follows FastAPI best practices
- Clear separation from core domain
- Standard structure for maintainability

**Submodules:**
- `mothership/` - Main API (standard FastAPI structure)
- `resonance/` - Resonance API (custom concept, standard structure)

**Import Pattern:**
```python
from application.mothership.main import app
from application.mothership.routers import health_router
```

### Tier 2: Domain Extensions

#### `light_of_the_seven/cognitive_layer/` - Cognitive Layer

**Purpose:** Cognitive decision support layer

**Why This Structure:**
- Extends core domain with cognitive science principles
- Could become a package in future
- Currently modules, not installable package
- Clear domain separation

**Submodules:**
- `decision_support/` - Bounded rationality (custom domain)
- `mental_models/` - Mental model tracking (custom domain)
- `cognitive_load/` - Cognitive load management (custom domain)
- `integration/` - GRID integration (integration code)

**Import Pattern:**
```python
from light_of_the_seven.cognitive_layer.decision_support import BoundedRationalityEngine
```

### Tier 3: Utilities and Infrastructure

#### `tools/` - Development Tools

**Purpose:** Development and infrastructure tools

**Why This Structure:**
- Not an installable package (just modules)
- Contains tools like RAG system
- Clear utility purpose
- Internal use primarily

**Import Pattern:**
```python
from tools.rag import RAGEngine
```

#### Other Utilities

- `scripts/` - Utility scripts (not importable)
- `docs/` - Documentation (not importable)
- `tests/` - Test suite (not importable)
- `infra/` - Infrastructure code (Terraform, etc.)

## Migration Path

### Phase 1: Documentation (Non-Breaking)

**Actions:**
1. Document structure rationale
2. Document canonical import paths
3. Create structure guide
4. Document standard vs custom code boundaries

**Impact:** None (documentation only)

### Phase 2: Import Consolidation (Low Risk)

**Actions:**
1. Update tests to use `from grid...` instead of `from src.grid...`
2. Update application code to use canonical imports
3. Document deprecated import paths
4. Add import linting rules

**Impact:** Low (internal code changes)

### Phase 3: Structure Consolidation (Medium Risk)

**Actions:**
1. Consolidate `src/` contents to `grid/` or appropriate package
2. Remove `src/` directory
3. Update all imports
4. Update documentation

**Impact:** Medium (requires careful migration)

### Phase 4: Optional Improvements (Future)

**Considerations:**
1. Migrate to `src/` layout (better test isolation)
2. Package cognitive layer separately
3. Create workspace configuration for multi-package structure

**Impact:** High (major restructuring, evaluate carefully)

## Validation Criteria

A clean structure should:

1. ✅ **Clear Package Boundaries:** Easy to identify what's a package vs utility
2. ✅ **Intuitive Imports:** Import paths are predictable and consistent
3. ✅ **Semantic Clarity:** Custom domains use meaningful names
4. ✅ **Industry Alignment:** Standard code follows conventions
5. ✅ **Scalable Organization:** Structure grows without breaking
6. ✅ **Developer Experience:** Easy to navigate and discover code

## Recommendations Summary

### Keep (Working Well)
- ✅ `grid/` package structure with semantic submodules
- ✅ `application/` FastAPI structure (follows standards)
- ✅ `cognitive_layer/` organization
- ✅ `tools/rag/` structure
- ✅ Security module organization

### Improve (Non-Breaking)
- 📝 Document structure and rationale
- 📝 Document canonical import paths
- 📝 Clarify standard vs custom boundaries

### Consolidate (Plan Carefully)
- 🔄 Consolidate `src/` → `grid/` over time
- 🔄 Standardize on `from grid...` imports
- 🔄 Remove deprecated import paths

### Consider (Future)
- 💭 Evaluate `src/` layout migration
- 💭 Consider packaging cognitive layer separately
- 💭 Workspace configuration for multi-package structure

## Conclusion

This proposed structure:

1. **Resonates with industry standards** for FastAPI/Python code
2. **Preserves semantic clarity** for custom cognitive/semantic domains
3. **Eliminates import confusion** through canonical paths
4. **Maintains clear boundaries** between standard and custom code
5. **Enables intuitive navigation** through logical organization
6. **Scales without breaking** through clear principles

The structure honors your custom domain concepts (essence, patterns, awareness) while following proven patterns for standard code (FastAPI applications). This creates a **professional, maintainable codebase** that is both **clean** and **semantically meaningful**.
