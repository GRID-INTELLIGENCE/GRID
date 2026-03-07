# Phase 2 - Package Consolidation Plan

## Current Directory Analysis

### Root-Level Loose Directories to Address
Based on the current state, these directories should be moved into `src/`:
- `concept/` → Either merge into `src/concept/` or archive
- `ml/` → Merge into `src/ml/` (already exists)
- `Python/` → Unclear purpose, likely archive
- `transformer/` → Move to `src/transformer/` or consolidate
- `tools/` → Move to `src/tools/` (already exists in src)
- `utils/` → Move to `src/utils/` (already exists in src)
- `water_cutter/` → Likely experimental, archive or move to src/tools

### Directories to Isolate
- `Vision/` vs `src/vision/` → Resolve conflict (case-sensitive)
- `Atmosphere/` → Archive (unclear purpose)
- `GRID/` → Archive or merge
- `aiu-trace-analyzer/` → Large external tool, move to `external/`

### Infrastructure (Keep in Root)
- `.github/`, `.venv/`, `.vscode/`, `.cursor/`, `.windsurf/` - IDE/CI config
- `alembic/` - Database migrations
- `tests/` - Test suite
- `docs/` - Documentation
- `scripts/` - Build/dev scripts
- `_archive/` - Archived code

## Proposed Actions

### Action 1: Resolve Naming Conflicts
```bash
# Case-sensitive conflict: Vision/ vs src/vision/
# Check if they're the same
diff -r Vision/ src/vision/ > vision_diff.txt

# If different, archive the external one
mv Vision/ _archive/vision_external/

# If same, delete duplicate
rmdir Vision/
```

### Action 2: Consolidate Duplicate Top-Level Packages
```bash
# Move concept/ into src/concept/ (if src/concept exists)
# Or rename to avoid conflict
mv concept/ _archive/concept_root/

# Consolidate ml/
rsync -av ml/ src/ml/
rm -rf ml/

# Archive unclear directories
mv Python/ _archive/python_unclear/
mv Atmosphere/ _archive/atmosphere/
mv GRID/ _archive/grid_old/
```

### Action 3: Move Large External Tools
```bash
mkdir external/
mv aiu-trace-analyzer/ external/
mv water_cutter/ external/  # Or to _archive if not used
```

## Import Migration Script
After moving packages, run:
```python
# scripts/migrate_imports_phase2.py
import os
import re

MIGRATIONS = {
    "from concept.": "from src.analysis.concept.",
    "import concept.": "import src.analysis.concept.",
    # Add more as needed
}

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False
    for old, new in MIGRATIONS.items():
        if old in content:
            content = content.replace(old, new)
            changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

# Walk through all Python files
for root, dirs, files in os.walk('.'):
    # Skip venv and archive
    dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '_archive']]
    for file in files:
        if file.endswith('.py'):
            update_file(os.path.join(root, file))
```

## Validation Checklist
- [ ] No naming conflicts between root and src/
- [ ] All external tools in `external/` or `_archive/`
- [ ] Tests still pass after each move
- [ ] Import migration script run
- [ ] pyproject.toml updated if package names changed

## Ready to Execute?
Phase 2 is higher risk than Phase 1. Recommend:
1. Commit current state (Phase 1 complete)
2. Execute Phase 2 step-by-step with validation
3. Keep detailed migration log
