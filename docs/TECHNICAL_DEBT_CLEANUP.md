# GRID Technical Debt Remediation - Incremental Cleanup

**Subject:** Technical Debt
**Version:** v1.0
**Canonical:** Yes

## Problem Statement
The GRID project suffers from:
1. **Inconsistency**: 26 top-level packages with unclear boundaries
1. **Productivity Bottlenecks**: Root directory clutter (30+ loose scripts)
1. **Cascading Technical Debt**: Duplicate files, abandoned experiments, scattered configs

## Incremental Cleanup Strategy

### Phase 1: Root Directory Cleanup (Immediate - 1 day)

#### 1.1 Archive Experimental/Debug Scripts
```bash
mkdir -p _archive/experiments
mkdir -p _archive/debug

# Move debug scripts
mv debug_*.py _archive/debug/
mv comprehensive_fixer*.py _archive/experiments/
mv batch_fixer.py _archive/experiments/

# Move one-off experiments
mv watch_module_*.py _archive/experiments/
mv phase1_collect_context.py _archive/experiments/
mv ner_upgrade_plan.py _archive/experiments/
```

#### 1.2 Consolidate Test Artifacts
```bash
mkdir -p test_results/databases

# Move test databases
mv test.db test_results/databases/
mv test_integration.db test_results/databases/

# Move test outputs
mv output*.json test_results/
mv test_baseline_summary.json test_results/
```

#### 1.3 Organize Standalone Tools
```bash
# Keep these in scripts/ (already exist there or should move)
mv generate_task_calendar.py scripts/
mv train_ner.py scripts/ml/
mv scoring.py scripts/analysis/
```

**Expected Outcome**: Root directory reduced from 30+ files to ~10 essential files (pyproject.toml, Dockerfile, Makefile, README, LICENSE)

---

### Phase 2: Package Consolidation (Medium - 3 days)

#### Current State (26 packages)
From dependency analysis, many packages have **zero internal dependencies**, suggesting they could be consolidated:

**Core Business Logic** (Keep):
1. `core` - Core logic
1. `services` - Business services
1. `database` - Persistence
1. `api` - REST API

**Domain Modules** (Consolidate):
1. `concept` + `pattern_engine` → `analysis/` (both do pattern/concept analysis)
1. `kernel` + `throughput_engine` → `orchestration/`
1. `workflow_engine` + `nl_dev` → `automation/`

**Infrastructure** (Keep as-is):
1. `cli` - Keep separate
1. `plugins` - Keep for extensibility
1. `utils` - Keep for shared code

**External/Vendored** (Isolate):
1. `ares` - Move to `external/ares/` (large external framework)
1. `vision` - Move to `external/vision/` (separate concern)

**Cleanup Candidates** (Archive or delete):
1. `demos` - Move to `examples/` or archive
1. `ml` - Either flesh out or merge into `services`
1. `bridge`, `transformer`, `valuation` - Unclear purpose, assess and consolidate

#### Proposed Structure
```
src/
├── core/           # Core business logic
├── services/       # Business services
├── database/       # Persistence
├── api/            # REST API
├── cli/            # CLI interface
├── analysis/       # Concept + Pattern analysis
│   ├── concept/
│   └── patterns/
├── orchestration/  # Kernel + Throughput
│   ├── kernel/
│   └── throughput/
├── automation/     # Workflows + NL Dev
│   ├── workflows/
│   └── nl_dev/
├── plugins/        # Plugin system
├── utils/          # Shared utilities
└── external/       # External/vendored code
    ├── ares/
    └── vision/
```

**Migration Script** (Phase 2):
```python
# scripts/migrate_packages.py
import shutil
import os

def migrate_package(old_path, new_path):
    """Move package and update imports."""
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.move(old_path, new_path)
    # TODO: Run import updater on new_path

# Consolidations
migrate_package("src/concept", "src/analysis/concept")
migrate_package("src/pattern_engine.py", "src/analysis/patterns.py")
# ... etc
```

---

### Phase 3: Configuration Cleanup (Low Risk - 1 day)

#### 3.1 Fix Duplicate pyproject.toml Sections
**Issue**: Lines 100-114 duplicate lines 156-169 (mypy config)

**Fix**:
```toml
# Remove lines 156-174 (duplicate mypy + new exclude)
# Keep lines 100-114 (original mypy config)
# Add exclude to original section:

[tool.mypy]
python_version = "3.10"
# ... existing config ...
exclude = [
    "venv",
    ".venv",
    "site-packages"
]
```

#### 3.2 Consolidate Dependencies
**Current**: Dependencies scattered in `docs/requirements.txt` and `pyproject.toml`

**Fix**: Delete `docs/requirements.txt`, ensure all deps are in `pyproject.toml`

---

### Phase 4: Establish Guardrails (Ongoing)

#### 4.1 Update CONTRIBUTING.md
Add section:
```markdown
## Package Organization Rules
1. New features go in existing packages if possible
1. New top-level packages require architecture review
1. Experimental code goes in `_archive/experiments/`
1. No loose scripts in root directory
```

#### 4.2 Pre-commit Hook
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-root-clutter
      name: Check for files in root
      entry: python scripts/check_root_clutter.py
      language: python
      pass_filenames: false
```

---

## Success Metrics

### Immediate (Phase 1)
- [ ] Root directory: 30+ files → 10 files
- [ ] Zero loose .py scripts in root
- [ ] All test artifacts in test_results/

### Medium Term (Phase 2)
- [ ] Package count: 26 → 12
- [ ] Zero packages with unclear purpose
- [ ] Dependency graph complexity reduced by 50%

### Long Term (Phase 3-4)
- [ ] Single source of truth for dependencies
- [ ] Automated guardrails prevent regression
- [ ] Developer productivity: faster navigation, clearer module boundaries

---

## Rollback Plan
Each phase is reversible:
1. **Phase 1**: `git revert` or restore from `_archive/`
1. **Phase 2**: Keep record of all `mv` operations in `migration_log.txt`
1. **Phase 3**: Config changes are   in version control

---

## Next Steps
1. Review and approve Phase 1 cleanup list
1. Execute Phase 1 (takes ~2 hours)
1. Run tests to verify no breakage
1. Repeat for Phase 2-4
