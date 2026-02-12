# Large Binary File Cleanup Report
**Date:** 2026-02-06

## torch_cpu.dll Files Found

### Locations and Sizes
1. **Root `.venv/`**: 250.49 MB (from 2026-02-04)
   - Location: `e:\.venv\Lib\site-packages\torch\lib\torch_cpu.dll`
   - Status: Most recent version
   - Recommendation: **KEEP** - Root venv may be used by multiple projects

2. **dev-.venv/**: 252.67 MB (from 2026-01-23)
   - Location: `e:\dev-.venv\Lib\site-packages\torch\lib\torch_cpu.dll`
   - Status: Oldest version, candidate for consolidation
   - Recommendation: **REMOVE** - If dev-.venv is consolidated/removed

3. **wellness_studio/.venv/**: 252.67 MB (from 2026-01-31)
   - Location: `e:\wellness_studio\.venv\Lib\site-packages\torch\lib\torch_cpu.dll`
   - Status: Project-specific venv with ML dependencies
   - Recommendation: **KEEP** - Required for wellness_studio project

## Antigravity.exe

- **Location:** `e:\.worktrees\copilot-worktree-2026-02-01T20-18-14\Antigravity.exe`
- **Size:** 152.44 MB
- **Date:** 2026-02-02
- **Status:** In active worktree
- **Recommendation:** **KEEP** - Part of active worktree, verify if needed before removing

## Other Large DLLs

### lancedb DLL
- **Location:** `e:\dev-.venv\Lib\site-packages\lancedb\_lancedb.pyd`
- **Size:** ~150 MB
- **Status:** In dev-.venv
- **Recommendation:** **REMOVE** - If dev-.venv is consolidated

### llvmlite DLL
- **Location:** `e:\wellness_studio\.venv\Lib\site-packages\llvmlite\binding\llvmlite.dll`
- **Size:** ~101 MB
- **Status:** In wellness_studio venv
- **Recommendation:** **KEEP** - Required for wellness_studio

## Consolidation Strategy

### Phase 1: Remove dev-.venv duplicates
If dev-.venv is consolidated/removed:
- Remove torch_cpu.dll (252.67 MB)
- Remove lancedb DLL (~150 MB)
- **Total reclaimable:** ~402 MB

### Phase 2: Review Antigravity.exe
- Verify if Antigravity.exe is needed in worktree
- If obsolete, remove to reclaim 152 MB
- **Total potential:** 152 MB

### Phase 3: Keep wellness_studio separate
- Keep all wellness_studio venv files (project-specific ML dependencies)
- No action needed

## Expected Space Reclamation

- **From dev-.venv consolidation:** ~402 MB (torch + lancedb)
- **From Antigravity.exe removal (if obsolete):** 152 MB
- **Total potential:** ~554 MB

## Action Items

- [x] Audit completed - Report created
- [ ] Verify dev-.venv usage before removal
- [ ] Remove dev-.venv torch DLL after consolidation
- [ ] Review Antigravity.exe necessity
- [ ] Document final decisions
