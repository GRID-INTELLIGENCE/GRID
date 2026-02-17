# Migration to src/ Layout - Notes

## Status

Migration to `src/` layout completed on 2025-01-XX. This document tracks important notes and known issues.

## Structure Changes

- **Legacy src/** → `legacy_src/` (renamed to avoid collision)
- **grid/** → `src/grid/`
- **application/** → `src/application/`
- **tools/** → `src/tools/`

## Import Changes

All imports now use canonical paths:
- `from grid...` (finds packages in `src/grid/`)
- `from application...` (finds packages in `src/application/`)
- `from tools...` (finds packages in `src/tools/`)

## Python Path Configuration

To make imports work with `src/` layout:

1. **For development**: Install in editable mode:
   ```bash
   pip install -e .
   ```

2. **For scripts/tests**: Add `src/` to `PYTHONPATH` or `sys.path`:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
   ```

3. **For pytest**: Configured in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   pythonpath = ["src"]
   ```

## Known Issues

### Legacy Modules in legacy_src/

Some modules exist only in `legacy_src/` and are not yet migrated:
- `legacy_src/grid/analysis/clustering.py` - ClusteringService
- `legacy_src/grid/pattern/engine.py` - PatternEngine (legacy version)
- `legacy_src/services/` - Service implementations
- `legacy_src/kernel/` - Kernel modules

Tests that use these modules need special handling:
- Add `legacy_src/` to `sys.path` before importing
- Use `from src.grid...` (note: `src` refers to the legacy package structure)

### Entrypoint Updates

- `backend/server.py` - Updated to add `src/` to `sys.path`

### Remaining Work

1. Migrate or remove modules from `legacy_src/`:
   - Decide if `ClusteringService` should move to `src/grid/` or be removed
   - Migrate `PatternEngine` if it's still needed
   - Evaluate `services/` and `kernel/` modules

2. Update all import statements:
   - Replace any remaining `from src.grid...` with `from grid...`
   - Ensure tests can find modules in `src/`

3. Documentation:
   - Update README with new import patterns
   - Update architecture docs

## Testing

After migration:
```bash
# Test imports
python -c "import sys; sys.path.insert(0, 'src'); import grid; import application.mothership; import tools.rag"

# Run tests
pytest tests/
```

## pyproject.toml Configuration

Hatchling build configuration:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/grid", "src/application"]
```

This tells Hatchling to package `src/grid/` as `grid` and `src/application/` as `application` when building distributions.
