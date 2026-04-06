# Repository Sweep Analysis — 2026-04-06

## Executive Summary

**Scope:** 5 repositories (GRID, echoes, hogsmade, afloat, apiguard)  
**Objective:** Investigate PRs, branches, CI health, and merge status across ecosystem  
**Result:** 6 PRs merged, 9 closed (diverged), 5 closed (superseded), 1 systemic CI issue identified and resolved

**Key Achievement:** Resolved hogsmade CI infrastructure failure — root cause was stale `package-lock.json`, not CI infrastructure. All CI checks now passing after 3 commits to PR #78.

---

## Repository Landscape

| Repo | Open PRs | Merged Today | Closed Today | CI Status | Notes |
|------|----------|--------------|--------------|-----------|-------|
| **GRID** | 0 | 2 (#82, #92) | 3 (#91, #93, #94) | ✅ All green | All CI passing on main |
| **echoes** | 0 | 3 (#115, #117, #107) | 4 (#123-#126) | ✅ All green | langchain major bump merged safely |
| **hogsmade** | 0 | 1 (#78) | 5 (#71-#75) | ✅ All green | **CI infrastructure fixed** |
| **afloat** | 0 | 0 | 0 | ✅ Clean | No PRs, no stale branches |
| **apiguard** | 0 | 1 (#7) | 0 | ✅ All green | Trufflehog bump merged |

---

## Sort 1: Confidence → Difficulty → Steps

### Tier 1: Quick Wins (High Confidence, Low Difficulty, <10 steps)

| Item | Confidence | Difficulty | Steps | Result |
|------|-----------|------------|-------|--------|
| Regenerate root `package-lock.json` | HIGH | LOW | 5 | ✅ **DONE** — Fixed 4/5 CI failures |
| Add `react`/`react-dom` to root devDeps | HIGH | LOW | 5 | ✅ **DONE** — Fixed remaining 2 CI failures |
| Add `ignoreDeprecations: "6.0"` to tsconfig | HIGH | LOW | 3 | ✅ **DONE** — Fixed TS5101 deprecation error |
| Delete `feature/animated-mermaid` branch | HIGH | LOW | 2 | ⏸ Pending |

### Tier 2: Post-CI Cleanup (Medium Confidence, 15-30 steps)

| Item | Confidence | Difficulty | Steps | Result |
|------|-----------|------------|-------|--------|
| Re-target `feat/guard-merit-circuit-breaker` | MEDIUM | MEDIUM | 15-25 | ⏸ Blocked by CI (now resolved) |
| Re-target `fix/mcp-sdk-schema-shape` | MEDIUM | MEDIUM | 15-25 | ⏸ Blocked by CI (now resolved) |

### Tier 3: CI Infrastructure Investigation (Low Confidence, 50-100 steps)

| Item | Confidence | Difficulty | Steps | Result |
|------|-----------|------------|-------|--------|
| **hogsmade CI failures root cause** | LOW → HIGH | HIGH → MEDIUM | 50-100 → 3 | ✅ **RESOLVED** — Stale lockfile + missing react peer dep |
| **Cross-Project Smoke Test failure** | LOW | HIGH | 50-100 | ✅ **RESOLVED** — Same root cause as above |

### Tier 4: Large Feature Branches (Low Confidence, High Complexity, 30-100 steps)

| Item | Confidence | Difficulty | Steps | Status |
|------|-----------|------------|-------|--------|
| `workflows-macro-tests` (Echoes v3.0) | LOW | HIGH | 30-100 | ⏸ Assessment needed |
| `copilot/conduct-comprehensive-report` | LOW | HIGH | 25-50 | ⏸ Assessment needed |
| `refactor/assistant-ai-001` | LOW | MEDIUM | 20-40 | ⏸ Assessment needed |
| `automation/highrisk/temporary_503` | LOW | MEDIUM | 15-30 | ⏸ Assessment needed |
| `automation/lowrisk/hack_433` | LOW | MEDIUM | 15-30 | ⏸ Assessment needed |

---

## Sort 2: Actionability → Architecture Impact

### 🔴 Critical — High Impact Foundations

| Item | Actionability | Harden | Stabilize | Tighten | Perf | Architecture | Status |
|------|--------------|--------|-----------|---------|------|--------------|--------|
| **hogsmade CI failures** | HIGH | HIGH | CRITICAL | HIGH | MEDIUM | HIGH | ✅ **RESOLVED** |
| **Cross-Project Smoke Test** | HIGH | MEDIUM | HIGH | LOW | LOW | HIGH | ✅ **RESOLVED** |

### 🟡 High — Immediate Security & Stability Wins

| Item | Actionability | Harden | Stabilize | Tighten | Perf | Architecture | Status |
|------|--------------|--------|-----------|---------|------|--------------|--------|
| **Dependabot config PR** | HIGH | HIGH | MEDIUM | HIGH | LOW | MEDIUM | ⏸ Pending |
| **Artifact download path fix** | HIGH | LOW | MEDIUM | MEDIUM | LOW | LOW | ⏸ Pending |
| **Delete stale branch** | HIGH | N/A | MEDIUM | HIGH | N/A | MEDIUM | ⏸ Pending |

### 🟢 Medium — Post-CI Feature Recovery

| Item | Actionability | Harden | Stabilize | Tighten | Perf | Architecture | Status |
|------|--------------|--------|-----------|---------|------|--------------|--------|
| **Guard circuit breaker** | MEDIUM | HIGH | HIGH | MEDIUM | LOW | HIGH | ⏸ Post-CI |
| **MCP SDK schema** | MEDIUM | HIGH | MEDIUM | HIGH | MEDIUM | HIGH | ⏸ Post-CI |

### 🔵 Low — Large Feature Triage

| Item | Actionability | Harden | Stabilize | Tighten | Perf | Architecture | Status |
|------|--------------|--------|-----------|---------|------|--------------|--------|
| **Echoes v3.0** | LOW | UNKNOWN | MEDIUM | UNKNOWN | UNKNOWN | HIGH | ⏸ Assessment |
| **Glimpse audit report** | LOW | MEDIUM | LOW | MEDIUM | LOW | LOW | ⏸ Assessment |
| **Assistant refactor** | LOW | LOW-MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM | ⏸ Assessment |
| **WIP automation branches** | LOW | UNKNOWN | UNKNOWN | LOW | LOW | LOW | ⏸ Assessment |

---

## Master Sort → Findings → Analysis(G) → Structured Recommendations

### 🔴 Critical Path (Blocks Everything)

**Finding:** All 5 hogsmade Dependabot PRs (#71-75) + Cross-Project Smoke Test failing on identical 5 CI checks: `root-ts-ci`, `Shared Types Build`, `Glimpse Artifact Check`, `Glimpse Engine Verification`, `PR Ownership & Governance Checks`.

**Analysis(G):**
- **Initial hypothesis:** Git submodule/credential cleanup failure in runner
- **Evidence against:** Post-job cleanup logs show `conclusion: success` for all submodule operations
- **Actual root cause:** Stale root `package-lock.json` — Dependabot bumps updated `Applications/glimpse-artifact/package.json` but root lockfile was never regenerated
- **Error pattern:** `npm error 'npm ci' can only install packages when your package.json and package-lock.json are in sync. Missing: @vitejs/plugin-react@6.0.1 from lock file`
- **Secondary issue:** TypeScript 6.0 deprecation warning (`baseUrl` deprecated) causing `root-ts-ci` and `Glimpse Artifact Check` to fail even after lockfile fix
- **Tertiary issue:** `react` peer dependency not hoisted to root, causing `lucide-react` import failures in CI

**Structured Recommendations:**
1. ✅ Regenerate root `package-lock.json` (PR #78 commit 1)
2. ✅ Add `ignoreDeprecations: "6.0"` to `tsconfig.json` (PR #78 commit 2)
3. ✅ Add `react`/`react-dom` to root `devDependencies` (PR #78 commit 3)
4. ✅ Merge PR #78 — all CI checks now passing
5. ✅ Close superseded Dependabot PRs (#71-75) — all superseded by consolidated fix

### 🟡 High ROI (Immediate + Architectural)

**Finding:** Missing security automation in echoes (no Dependabot config), stale artifact download path, restore-point branch masquerading as feature.

**Analysis(G):**
- **Dependabot config:** Single-file addition (`dependabot.yml`) enables automated security scanning for echoes repo
- **Artifact download path:** One-line fix prevents nested `dist/dist/` directory confusion
- **Stale branch:** `feature/animated-mermaid` is a restore point from 2026-03-02, not an active feature branch

**Structured Recommendations:**
1. Create PR from `caraxesthebloodwyrm02-patch-1` (adds `dependabot.yml` to echoes)
2. Re-apply artifact download path fix as fresh PR against current main
3. Delete `feature/animated-mermaid` branch

### 🟢 Medium ROI (Post-CI Recovery + Patterns)

**Finding:** Two architectural improvements ready to merge after CI fix: guard circuit breaker and MCP SDK schema hardening.

**Analysis(G):**
- **Guard circuit breaker:** Implements circuit breaker pattern for merit guard system — prevents cascading failures in MCP server interactions
- **MCP SDK schema:** Hardens type definitions and schema validation — tightens boundaries between servers, prevents malformed data flow

**Structured Recommendations:**
1. Re-target `feat/guard-merit-circuit-breaker` as fresh PR against current `hogsmade`
2. Re-target `fix/mcp-sdk-schema-shape` as fresh PR (depends on #1)
3. Both should pass CI now that infrastructure is fixed

### 🔵 Assessment Required (Large Features)

**Finding:** 6 large feature branches with unknown status — may be abandoned, WIP, or critical architecture work.

**Analysis(G):**
- **`workflows-macro-tests`:** 31-branch Echoes v3.0 implementation — potentially major platform evolution or legacy dead code
- **`copilot/conduct-comprehensive-report`:** Glimpse audit documentation — may contain actionable security findings
- **`refactor/assistant-ai-001`:** Assistant refactoring — likely tech debt cleanup
- **WIP automation branches:** Unknown status, may be abandoned

**Structured Recommendations:**
1. Review each branch for relevance and completeness
2. Create PRs for viable branches, close abandoned ones
3. Prioritize based on current architectural needs

---

## Personalized Guidelines

### CI Investigation Guidelines

**When to suspect lockfile issues:**
- Multiple PRs fail on identical `npm ci` errors
- Error mentions "package.json and package-lock.json are not in sync"
- All failures occur at the first `npm ci` step, not during tests

**Investigation workflow:**
1. Check CI logs for `npm error` messages
2. Verify `package-lock.json` is in sync with workspace `package.json` files
3. Run `npm install` locally to regenerate lockfile
4. Commit and push lockfile changes
5. Re-trigger CI on affected PRs

**When to suspect peer dependency issues:**
- Error: `Cannot find module 'X'` where X is a peer dependency
- Module exists in workspace but not hoisted to root
- Common with React, ReactDOM, and UI library peer deps

**Fix workflow:**
1. Add missing peer deps to root `package.json` devDependencies
2. Run `npm install` to hoist them
3. Commit and push

### Rebase Guidelines

**When to rebase:**
- Branch is 1-3 commits behind main
- No merge conflicts expected
- CI is failing due to stale dependencies

**When to abort and re-apply:**
- Branch has 200+ file conflicts
- Branch is weeks/months old
- Change is small enough to re-apply manually

**Safe rebase workflow:**
```bash
git fetch origin
git checkout <branch>
git rebase origin/main
# If conflicts: git rebase --abort
# If clean: git push --force-with-lease
```

### PR Creation Guidelines

**Create PR when:**
- Branch is up-to-date with main
- CI passes or failures are understood and documented
- Change is complete and tested

**Close PR when:**
- Branch has diverged too far from main
- Change is superseded by another PR
- Branch is a restore point or experiment

**Re-apply when:**
- Change is small (1-3 files)
- Branch is too diverged to rebase
- Original intent is still relevant

### CI Decision Matrix

| Failure Pattern | Likely Cause | Fix Approach | Confidence |
|----------------|--------------|--------------|------------|
| `npm ci` sync error | Stale lockfile | Regenerate lockfile | HIGH |
| `Cannot find module 'X'` | Missing peer dep | Add to root devDeps | HIGH |
| `TS5101: baseUrl deprecated` | TypeScript 6.0 deprecation | Add `ignoreDeprecations: "6.0"` | HIGH |
| Submodule checkout fails | Broken submodule ref | Update submodule pointer | MEDIUM |
| Test timeout | Flaky test or CI load | Re-run CI, investigate if persistent | LOW |
| Multiple PRs fail identically | Shared infrastructure issue | Investigate root cause, not individual PRs | HIGH |

### Large Feature Triage Guidelines

**Assessment workflow:**
1. Check branch age and commit count
2. Review commit messages for scope and intent
3. Check if any files overlap with recent main changes
4. Attempt `git diff origin/main --stat` to see scope
5. Decide: PR, re-apply, or delete

**Decision criteria:**
- **PR:** Branch is <2 weeks old, <50 commits, no major conflicts
- **Re-apply:** Branch is old but change is small and still relevant
- **Delete:** Branch is >1 month old, abandoned, or superseded

---

## Execution Roadmap

### Phase 1: ✅ COMPLETED — CI Investigation & Fix
- **Duration:** ~30 minutes
- **Deliverables:**
  - Root cause identified: stale `package-lock.json`
  - 3 fixes applied to PR #78
  - All CI checks passing
  - PR #78 merged
  - 5 Dependabot PRs closed (superseded)

### Phase 2: Quick Wins (15-20 mins)
- Create PR from `caraxesthebloodwyrm02-patch-1`
- Re-apply artifact download path fix
- Delete `feature/animated-mermaid` branch

### Phase 3: Post-CI Recovery (30-60 mins)
- Re-target `feat/guard-merit-circuit-breaker`
- Re-target `fix/mcp-sdk-schema-shape`

### Phase 4: Large Feature Triage (2-5 hrs)
- Assess 6 large feature branches
- Create PRs or close as appropriate

---

## Priority Executive Summary

| Priority | Action | Effort | Status |
|----------|--------|--------|--------|
| **P0** | Fix hogsmade CI infrastructure | 30 mins | ✅ **DONE** |
| **P1** | Create Dependabot config PR for echoes | 5 mins | ⏸ Pending |
| **P1** | Re-apply artifact download path fix | 10 mins | ⏸ Pending |
| **P1** | Delete stale `feature/animated-mermaid` branch | 2 mins | ⏸ Pending |
| **P2** | Re-target guard circuit breaker PR | 30 mins | ⏸ Post-CI |
| **P2** | Re-target MCP SDK schema PR | 30 mins | ⏸ Post-CI |
| **P3** | Triage 6 large feature branches | 2-5 hrs | ⏸ Assessment |

---

## Appendices

### Appendix A: Full PR Details

| Repo | PR | Title | Status | Notes |
|------|----|-------|--------|-------|
| GRID | #82 | runbook accuracy fixes + flaky test registry + safety asyncio marks | ✅ Merged | Rebased to resolve conflict |
| GRID | #92 | feat(quality): synthesize key highlights and fix ruff config deprecation | ✅ Merged | Auto-merged after CI |
| GRID | #91 | fix: correct artifact download path | ❌ Closed | 200+ file conflicts |
| GRID | #93 | docs: add AGENTS.md | ❌ Closed | Diverged |
| GRID | #94 | fix: config test suite regressions | ❌ Closed | Diverged |
| echoes | #115 | deps: bump langchain 0.3.23 → 1.2.15 | ✅ Merged | Safe — not imported in prod |
| echoes | #117 | deps: bump packaging 24.1 → 26.0 | ✅ Merged | |
| echoes | #107 | deps: bump numba 0.64.0 → 0.65.0 | ✅ Merged | |
| echoes | #123-126 | 4 PRs from old branches | ❌ Closed | All diverged |
| hogsmade | #78 | fix(ci): regenerate lockfile + TS fix + react peer dep | ✅ Merged | **Resolved all CI failures** |
| hogsmade | #71-75 | 5 Dependabot PRs | ❌ Closed | Superseded by #78 |
| apiguard | #7 | deps: bump trufflehog 3.94.1 → 3.94.2 | ✅ Merged | |

### Appendix B: Full Branch Details

| Repo | Branch | Commits | Status | Notes |
|------|--------|---------|--------|-------|
| GRID | `feature/animated-mermaid` | 1 | ⏸ Stale | Restore point from 2026-03-02 |
| echoes | `automation/highrisk/temporary_503` | 3 | ⏸ WIP | High-risk PR automation |
| echoes | `automation/lowrisk/hack_433` | 3 | ⏸ WIP | Code quality improvements |
| echoes | `caraxesthebloodwyrm02-patch-1` | 2 | ⏸ Ready | Dependabot config addition |
| echoes | `copilot/conduct-comprehensive-report` | 3 | ⏸ WIP | Glimpse audit report |
| echoes | `refactor/assistant-ai-001` | 3 | ⏸ WIP | Assistant refactoring |
| echoes | `workflows-macro-tests` | 31 | ⏸ Large | Echoes v3.0 implementation |

### Appendix C: CI Failure Log Excerpts

**Root Cause 1: Stale Lockfile**
```
npm error `npm ci` can only install packages when your package.json and 
npm error package-lock.json or npm-shrinkwrap.json are in sync.
npm error Missing: @vitejs/plugin-react@6.0.1 from lock file
npm error Missing: @rolldown/pluginutils@1.0.0-rc.7 from lock file
```

**Root Cause 2: TypeScript Deprecation**
```
tsconfig.json(18,5): error TS5101: Option 'baseUrl' is deprecated and will stop functioning in TypeScript 7.0.
```

**Root Cause 3: Missing Peer Dependency**
```
Error: Cannot find module 'react'
Require stack:
- /home/runner/work/hogsmade/hogsmade/node_modules/lucide-react/dist/cjs/lucide-react.js
```

### Appendix D: Repository Configuration Notes

**hogsmade submodule structure:**
```
[submodule "GRID-main"]
    path = Projects/GRID-main
    url = https://github.com/GRID-INTELLIGENCE/GRID.git
    ignore = dirty
```

**Key CI workflows:**
- `root-ts-ci.yml` — Root TypeScript CI (lint, test, build)
- `ownership-gate.yml` — PR Ownership & Governance Checks
- `cross-project-smoke.yml` — Shared Types Build, Glimpse checks

**Workspace structure:**
- Root `package.json` — npm workspaces config
- `Applications/glimpse-artifact/` — React app with TypeScript 6.0
- `Applications/glimpse-engine/` — Glimpse engine package
- `Components/shared-types/` — Shared TypeScript types
- `Projects/GRID-main/` — Git submodule

---

## CI Fix Summary

**Problem:** All hogsmade CI checks failing across 5 Dependabot PRs + Cross-Project Smoke Test

**Root Causes (3):**
1. Stale root `package-lock.json` — Dependabot bumps not reflected in lockfile
2. TypeScript 6.0 `baseUrl` deprecation warning treated as error
3. `react` peer dependency not hoisted to root for `lucide-react`

**Fixes Applied (PR #78):**
1. Regenerated root `package-lock.json` (113 additions, 629 deletions)
2. Added `ignoreDeprecations: "6.0"` to `tsconfig.json`
3. Added `react`/`react-dom` to root `devDependencies`

**Result:** All CI checks passing — 16/16 checks green on PR #78

**Impact:** Unblocks all hogsmade development, resolves 5 Dependabot PRs (superseded), fixes Cross-Project Smoke Test
