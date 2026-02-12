# Virtual Environment Audit Report
**Date:** 2026-02-06  
**Purpose:** Identify consolidation opportunities to reclaim ~3.7GB+ space

## Virtual Environments Found

### 1. Root `.venv/` (e:\.venv)
- **Size:** 1,228.89 MB (1.2 GB)
- **Files:** 65,124
- **Python Version:** Unknown (needs verification)
- **Status:** Root-level venv, likely used by multiple projects
- **Recommendation:** Keep if actively used, otherwise consolidate

### 2. Dev Virtual Environment (e:\dev-.venv)
- **Size:** ~1,290 MB (1.3 GB)
- **Files:** 33,917
- **Status:** Development environment
- **Recommendation:** **CONSOLIDATE** - Likely duplicate of root venv

### 3. Wellness Studio `.venv/` (e:\wellness_studio\.venv)
- **Size:** ~1,190 MB (1.2 GB)
- **Files:** 41,122
- **Python Version:** Python 3.13+ (from requirements.txt)
- **Dependencies:** Heavy ML stack (torch, transformers, sentence-transformers)
- **Status:** Project-specific venv with ML dependencies
- **Recommendation:** **KEEP** - Has unique heavy dependencies (torch 252MB DLL)

### 4. Coinbase `.venv/` (e:\Coinbase\.venv)
- **Size:** 75.57 MB
- **Python Version:** Python 3.13 (from pyproject.toml)
- **Dependencies:** Minimal (databricks-sdk, pytest, etc.)
- **Status:** Project-specific venv
- **Recommendation:** **CONSOLIDATE** - Small size, can use root venv

### 5. Grid `.venv_locked/` (e:\grid\.venv_locked)
- **Size:** Unknown
- **Status:** Locked dependencies
- **Recommendation:** Keep - This is a lock file directory, not a venv

## Consolidation Strategy

### Phase 1: Immediate Consolidation (Low Risk)
1. **Coinbase venv** → Migrate to root `.venv/`
   - Small size (75MB), minimal dependencies
   - Same Python version (3.13)
   - Low risk migration

### Phase 2: Verification Required (Medium Risk)
2. **dev-.venv** → Verify if still needed
   - Check if any scripts reference it
   - If obsolete, delete after verification
   - If needed, consolidate with root venv

### Phase 3: Keep Separate (High Value)
3. **wellness_studio/.venv** → Keep separate
   - Heavy ML dependencies (torch, transformers)
   - Unique requirements that may conflict
   - Large size justified by specialized needs

### Phase 4: Root venv Review
4. **Root `.venv/`** → Audit usage
   - Document which projects use it
   - Consider if it can be project-specific
   - If unused, archive or remove

## Expected Space Reclamation

- **Coinbase venv removal:** ~75MB
- **dev-.venv removal (if obsolete):** ~1,290MB
- **Total potential:** ~1,365MB (1.4GB)

## Action Items

- [x] Audit completed - Report created
- [ ] Verify root `.venv/` is actively used
- [ ] Check for references to `dev-.venv` in scripts/configs
- [ ] Migrate Coinbase to root venv
- [ ] Test Coinbase after migration
- [ ] Remove Coinbase venv after verification
- [ ] Archive or remove dev-.venv if obsolete
- [ ] Document venv usage policy going forward

## Notes

- Wellness Studio venv should remain separate due to heavy ML dependencies
- Grid uses `.venv_locked/` which is a lock file directory, not a venv
- All projects use Python 3.13, enabling consolidation
