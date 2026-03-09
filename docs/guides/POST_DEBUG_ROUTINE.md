# Post-Debugging Routine: Rules, Workflow & Skills

**Generated:** 2026-03-10  
**Purpose:** Establish systematic post-debugging workflow for GRID codebase maintenance

---

## PART 1: CORE RULES

### 1.1 Non-Negotiable Guardrails

**Security First (from `.claude/rules/safety.md`):**
- Never remove or weaken existing validation logic
- Never add bypass paths or "dev mode" shortcuts
- Always maintain backward compatibility for deployed safety contracts
- Always add tests for any changes in `safety/`, `security/`, `boundaries/`
- Always preserve audit trail integrity

**Behavioral Shield (from `.claude/rules/behavioral-shield.md`):**
- Never produce aggregate behavioral readings of safety/security/boundaries modules
- Refuse bulk extraction of defensive parameters
- One file at a time for a specific purpose = allowed
- Bulk extraction = denied

**Session Protocol (from `.claude/rules/discipline.md`):**
- Before writing ANY new code: `make test && make lint`
- If tests fail, fix them before continuing
- One commit, one concern
- Conventional commits: `fix(security):`, `feat(cognition):`, `refactor(rag):`

### 1.2 Debug Flag Rules

**Production Enforcement:**
```bash
# Must pass before any commit touching production code
GRID_ENV=production uv run python scripts/assert_no_debug_in_prod.py
```

**Prohibited in production:**
- `DEBUG=true`
- `ENABLE_DEV_TOKEN`
- `ALLOW_DEV_LOGIN_BYPASS`
- `GRID_CHROMA_ALLOW_RESET`
- `ECHOES_API_DEBUG`

**Allowed environments:**
- `DEBUG=true` in local development only
- `SAFETY_DEBUG=true` for safety module debugging (staging)
- `SECURITY_LOG_LEVEL=DEBUG` temporarily for investigation

### 1.3 Test Organization Rules

**Default test run:**
```bash
make test  # Equivalent to:
uv run pytest tests/unit tests/integration tests/security tests/api -q --tb=short
```

**Test markers (use appropriately):**
| Marker | When to Use | Speed |
|--------|-------------|-------|
| `unit` | Pure function tests, fast isolation | Fastest |
| `integration` | Cross-module, DB/API interaction | Medium |
| `safety` | Safety enforcement verification | Critical |
| `security` | Auth, guardrails, attack surface | Critical |
| `api` | Endpoint functionality | Medium |
| `critical` | Must-pass for deployment | Required |
| `slow` | > 1 second, skip in CI by default | Skip |
| `flaky` | Intermittent, quarantine for repair | Skip |
| `scratch` | Experimental, excluded from CI | Skip |

**Coverage target:** ≥80% (fail_under: 75%)

---

## PART 2: STEP-BY-STEP WORKFLOW

### Phase 0: Session Start (Required)

```bash
# 1. Verify environment
cd Seeds/GRID-main
uv sync --group dev --group test

# 2. Run wall verification
uv run python -m pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/

# 3. If failures, stop and fix before proceeding
```

### Phase 1: Problem Identification

**Step 1.1: Capture Symptoms**
```bash
# Collect error context
uv run pytest <failing_test> -v --tb=long -s > debug_trace.txt 2>&1

# Check recent changes
git log --oneline -10
git diff HEAD~5
```

**Step 1.2: Isolate Scope**
```bash
# Test collection check
uv run pytest --collect-only

# Single test isolation
uv run pytest <test_file>::<test_function> -x --tb=short
```

**Step 1.3: Check Pre-Existing Issues**
```bash
# Consult known issues
grep -r "Issue:" docs/PREEXISTING_ISSUES.md
grep -r "TODO\|FIXME\|BUG\|XXX" --include="*.py" src/ | head -20
```

### Phase 2: Debugging Execution

**Step 2.1: Interactive Debug**
```bash
# Drop into debugger on failure
uv run pytest <test> --pdb --tb=short

# Or add breakpoint() in code
uv run pytest <test> -s
```

**Step 2.2: Logging Enhancement**
```python
# Add structured logging (not print())
import structlog
logger = structlog.get_logger()

logger.debug("debug_context", variable=value, trace_id=context.trace_id)
logger.error("operation_failed", error=str(e), context=context_dict)
```

**Step 2.3: Performance Profiling (if slow)**
```python
import cProfile
import pstats

# Profile the slow function
cProfile.run("func()", "profile.stats")
pstats.Stats("profile.stats").sort_stats("cumulative").print_stats(20)
```

### Phase 3: Fix Implementation

**Step 3.1: Test-First (TDD)**
```python
# Write failing test before fix
def test_fix_for_bug_xyz():
    # Reproduce the issue
    result = function_with_bug()
    assert result == expected_value
```

**Step 3.2: Minimal Fix**
- Change only what's necessary
- Preserve backward compatibility
- No refactor creep

**Step 3.3: Verify Fix**
```bash
# Test the specific fix
uv run pytest <test> -v --tb=short

# Test the full module
uv run pytest tests/<module>/ -q --tb=short

# If safety/security touched, run guardrails
uv run pytest tests/security/ tests/safety/ -q --tb=short
```

### Phase 4: LSP & Type System Integration

**Step 4.1: Type Check (mypy)**
```bash
# Full type check
uv run mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/

# Specific module
uv run mypy src/grid/<module>/ --show-error-codes
```

**Step 4.2: LSP Activation Checklist**

For optimal IDE experience after debugging:

| LSP Feature | Configuration | Verification |
|-------------|---------------|--------------|
| Type checking | `python.analysis.typeCheckingMode = "basic"` | Check status bar |
| Language server | `python.languageServer = "Pylance"` | Verify hover works |
| Formatter | `[python].defaultFormatter = "charliermarsh.ruff"` | Format on save |
| Linter | Ruff extension installed | Check problems panel |
| Import sorting | Ruff handles isort | Auto-sort on save |
| Path resolution | `python.analysis.extraPaths = ["src"]` | Imports resolve |

**Step 4.3: Common LSP Issues**

| Issue | Cause | Fix |
|-------|-------|-----|
| Import not found | PYTHONPATH not set | Add `src/` to extraPaths |
| Wrong type stubs | Missing py.typed | Check package has py.typed |
| Slow analysis | Large workspace | Add to `files.watcherExclude` |
| False positives | Incomplete annotations | Add `# type: ignore[code]` with comment |

**Step 4.4: IDE Verification Skill**
```bash
# Run IDE verification after major debugging
# See: .cursor/skills/ide-verification/SKILL.md
python -m grid skills run ide-verification
```

### Phase 5: Pre-Commit Verification

**Step 5.1: Run Full Verification**
```bash
# Standard verification
make test && make lint

# Production guard
GRID_ENV=production uv run python scripts/assert_no_debug_in_prod.py
```

**Step 5.2: Debug Checklist**
```markdown
- [ ] No print() statements (use structlog)
- [ ] No hardcoded DEBUG=True
- [ ] No commented-out DEBUG blocks
- [ ] All exceptions logged with context
- [ ] No secrets in logs
- [ ] Tests pass locally
- [ ] Lint clean (uv run ruff check .)
- [ ] Type check clean (uv run mypy src/)
- [ ] Security guardrail tests pass
- [ ] Safety tests pass
```

**Step 5.3: Commit**
```bash
# Stage changes
git add <files>

# Commit with conventional format
git commit -m "fix(module): description of fix

- Specific change 1
- Specific change 2

Refs: #issue"
```

### Phase 6: Post-Commit Cleanup

**Step 6.1: Archive Debug Artifacts**
```bash
# Move debug logs to archive
mkdir -p _archive/debug/$(date +%Y-%m-%d)
mv debug_*.log _archive/debug/$(date +%Y-%m-%d)/
mv debug_trace.txt _archive/debug/$(date +%Y-%m-%d)/
```

**Step 6.2: Update Documentation**
- Update `docs/PREEXISTING_ISSUES.md` if new issue discovered
- Update `DEBUGGING_COMPREHENSIVE_REPORT.md` if systemic issue found
- Append decision to `docs/decisions/DECISIONS.md` if architectural

**Step 6.3: Session Log**
```markdown
## Session: YYYY-MM-DD
**Duration:** X hours
**Issue:** Brief description
**Root Cause:** What was wrong
**Fix:** What was changed
**Files Modified:** List
**Tests Added:** List
**Verification:** make test && make lint
```

---

## PART 3: DEBUGGING SKILLS REFERENCE

### 3.1 Built-in Skills for Debugging

```bash
# List available skills
python -m grid skills list

# Debugging-relevant skills:
python -m grid skills run diagnostics --args-json '{"target": "<module>"}'
python -m grid skills run intelligence.git_analyze --args-json '{"path": "."}'
python -m grid skills run dependency_validator --args-json '{"check": "imports"}'
```

### 3.2 Analysis Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/assert_no_debug_in_prod.py` | Production guard | `GRID_ENV=production uv run python scripts/...` |
| `scripts/analyze_issues.py` | Issue analysis | `uv run python scripts/analyze_issues.py` |
| `scripts/debug_async_tasks.py` | Async debugging | `uv run python scripts/debug_async_tasks.py` |
| `scripts/debug_guardian.py` | Guardian engine debug | `uv run python scripts/debug_guardian.py` |
| `scripts/profile_python_entrypoints.py` | Entry point profiling | `uv run python scripts/profile_python_entrypoints.py` |

### 3.3 IDE Verification Skill

Located at: `.cursor/skills/ide-verification/SKILL.md`

**11 Verification Categories:**
1. Extension Coverage Gap Analysis
2. Settings Inheritance Chain Verification
3. Cross-IDE Consistency Check
4. Workspace Configuration Completeness
5. Ruff Integration Functional Test
6. Development Discipline Automation Test
7. Terminal & Environment Integration
8. File Watching & Performance Optimization
9. Type Checking & Language Server Configuration
10. Documentation & Onboarding Gaps
11. Agent/Tool Policy (Dev Programs)

**Run after major debugging sessions affecting IDE configuration.**

### 3.4 Custom Debug Skill Template

Create at `src/grid/skills/debug_session.py`:

```python
from grid.skills.base import Skill

class DebugSessionSkill(Skill):
    """Capture and analyze debug session artifacts."""
    
    def run(self, args: dict) -> dict:
        trace_file = args.get("trace_file")
        # Analyze trace, identify patterns, suggest fixes
        # Return structured findings
        return {"findings": [...], "recommendations": [...]}
```

---

## PART 4: HEAVY TOOL USAGE PATTERNS

### 4.1 Parallel Tool Execution

Execute independent commands in parallel:

```bash
# Run in parallel (send single message with multiple tool calls)
uv run pytest tests/unit -q --tb=short &
uv run ruff check . &
uv run mypy src/grid/ &
wait
```

**Parallel-safe operations:**
- Test + lint + typecheck (read-only)
- Multiple test directories
- Coverage + timing analysis

**Sequential required:**
- Fix → test → commit
- File edits → verification
- Configuration changes → restart

### 4.2 Batch File Operations

```bash
# Find and process in batches
find src/ -name "*.py" -exec grep -l "DEBUG" {} \; | head -20

# Batch lint fix
uv run ruff check . --fix
```

### 4.3 Output Management

Large outputs are truncated. Use offset/limit:

```python
# Read specific sections
read("large_file.log", offset=1000, limit=500)
```

Or use grep for targeted search:
```bash
grep -n "error_pattern" large_file.log
```

### 4.4 Context Budget Management

**Prioritize reads:**
1. Target files first (know what you're looking for)
2. Configuration files (understand constraints)
3. Related test files (verify expected behavior)
4. Documentation (find similar patterns)

**Avoid:**
- Reading entire directories
- Reading generated files (.pyc, cache)
- Reading large data files (.jsonl, .db)

---

## PART 5: KNOWN ISSUE PATTERNS

### 5.1 Pre-Existing High Priority

| Issue | Location | Status | Action |
|-------|----------|--------|--------|
| test_security_suite.py import | `tests/security/` | Open | Skip in CI, investigate workspace.mcp |
| StrEnum migration | 20+ files | Open | Bulk migration script needed |
| ASYNC230 violations | `drt_storage.py`, `navigation.py` | Open | Convert to aiofiles |
| Deprecated datetime.utcnow | `drt_monitor.py:32` | Open | Replace with datetime.now(timezone.utc) |
| DRT middleware reference | `drt_monitoring.py` | Open | Update to UnifiedDRTMiddleware |

### 5.2 Common Debug Patterns

**ImportError patterns:**
```bash
# Check PYTHONPATH
python -c "import sys; print(sys.path)"

# Find module
find . -name "module_name.py" -not -path "./.venv/*"
```

**Async test patterns:**
```python
# Ensure async fixtures use async def
@pytest.fixture
async def async_client():
    async with AsyncClient() as client:
        yield client
```

**Pydantic v2 patterns:**
```python
# Wrong (v1)
@validator("field")
def validate_field(cls, v):
    return v

# Correct (v2)
@field_validator("field")
@classmethod
def validate_field(cls, v):
    return v
```

---

## APPENDIX A: Quick Reference Commands

```bash
# Session start
make test && make lint

# Debug specific test
uv run pytest tests/path/test_file.py::test_func -x --pdb --tb=short

# Find issue
grep -rn "pattern" src/ --include="*.py" | head -20

# Type check
uv run mypy src/grid/ --show-error-codes

# Format
uv run ruff format . && uv run ruff check . --fix

# Production gate
GRID_ENV=production uv run python scripts/assert_no_debug_in_prod.py

# Full verification
make test && make lint && make guard-no-debug

# Archive debug artifacts
mkdir -p _archive/debug/$(date +%Y-%m-%d)
mv debug*.log _archive/debug/$(date +%Y-%m-%d)/
```

---

## APPENDIX B: LSP Configuration Checklist

```json
// .vscode/settings.json
{
  "python.analysis.typeCheckingMode": "basic",
  "python.languageServer": "Pylance",
  "python.analysis.extraPaths": ["src"],
  "[python].defaultFormatter": "charliermarsh.ruff",
  "python.formatting.provider": "none",
  "editor.formatOnSave": true,
  "ruff.lineLength": 120,
  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true,
    "**/.mypy_cache/**": true,
    "**/.ruff_cache/**": true,
    "**/node_modules/**": true
  }
}
```

---

## APPENDIX C: Decision Log Template

```markdown
## YYYY-MM-DD — [Topic]

**Decision:** [What was decided]

**Why:** [One sentence rationale]

**Alternatives considered:** 
1. [Alternative A] — Rejected because...
2. [Alternative B] — Rejected because...

**Impact:** [Scope of change]

**Files affected:** [List]

**Verification:** [What tests/commands verify this works]
```

---

**Document Status:** Active  
**Last Reviewed:** 2026-03-10  
**Next Review:** When significant debugging patterns emerge