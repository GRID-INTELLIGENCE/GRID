# Python Packaging Standards Analysis for GRID

## Current State Analysis

### pyproject.toml Configuration
Your project uses:
- **Build System**: Hatchling (modern, PEP 517/518 compliant ✓)
- **Project Name**: `grid` (matches package name ✓)
- **Python Version**: >=3.11 (modern ✓)
- **Dependencies**: Properly declared ✓

### Package Layout: Current Structure

**Flat Layout (Current):**
```
grid/
├── grid/              # Core package (installed)
├── application/       # Application layer (installed)
├── src/              # Legacy/transitional package
├── tools/            # Development tools (not in pyproject.toml)
└── tests/            # Test suite (standard location ✓)
```

**Key Observations:**
1. **Mixed Layout**: `grid/` at root (flat layout) while `src/` also exists (src layout hybrid)
2. **Package Discovery**: Hatchling by default finds packages at root level
3. **Test Isolation**: Current flat layout means tests run against installed code, not source
4. **Import Confusion**: Both `grid.*` and `src.grid.*` imports exist

## Industry Standards Research

### PEP 517/518/621 Compliance

**PEP 621** (pyproject.toml project metadata):
- ✓ You follow this: `[project]` section with name, version, dependencies
- ✓ Optional dependencies properly declared: `[project.optional-dependencies]`

**PEP 517** (Build backend):
- ✓ You use hatchling (standard, modern build backend)
- ✓ `[build-system]` properly declared

### src/ Layout vs Flat Layout

**Industry Trend (2024):**
- **src/ layout** increasingly preferred for:
  - Test isolation (tests import from installed package, not source)
  - Prevents accidental imports of source code during development
  - Clearer separation: source code in `src/`, everything else at root

**Flat Layout:**
- Simpler for small projects
- Direct imports during development (can lead to import errors in tests)
- Your current approach for `grid/` package

**Recommendation for GRID:**
Given you have:
- Multiple packages (`grid`, `application`)
- Complex custom domains
- Tests that need reliable imports
- Both `grid/` and `src/` existing (confusion)

**Option A: Migrate to src/ layout (preferred)**
```
src/
├── grid/           # Core intelligence layer
├── application/    # FastAPI applications
└── ...            # Other installable packages
```

**Option B: Stay flat but consolidate**
```
grid/              # Core (keep as-is)
application/       # Applications (keep as-is)
# Remove or consolidate src/
```

### Hatchling Best Practices

**Package Discovery:**
Hatchling auto-discovers packages. For multi-package projects:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/grid", "src/application"]  # Explicit if using src/
# OR (current flat layout)
packages = ["grid", "application"]  # Your current implicit discovery
```

**Your Current Setup:**
- Implicit package discovery (works for flat layout)
- Multiple packages handled correctly by hatchling

## Key Findings

1. **Current structure is functional** but has ambiguity (`grid/` + `src/`)
2. **Flat layout works** but `src/` layout offers better test isolation
3. **Multiple packages** (`grid`, `application`) are handled correctly by hatchling
4. **Package name matches directory** (`grid` package in `grid/` dir) - good practice ✓

## Recommendations

### Short-term (Non-breaking)
1. **Document the dual structure**: Clearly explain why both `grid/` and `src/` exist
2. **Consolidate gradually**: Migrate `src/` contents to `grid/` over time
3. **Standardize imports**: Prefer `from grid...` over `from src.grid...`

### Long-term (Clean Structure)
1. **Consider src/ layout** for better test isolation
2. **Single source of truth**: One package structure, not two
3. **Clear boundaries**: All installable packages in same location pattern
