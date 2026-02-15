# Branch Organization Guide

## Branch: `claude/organize-branch-structure-LM7e9`

### Purpose

This branch is a **consolidation branch** that merges multiple feature branches into a unified, well-organized structure. It serves as the integration point for:

- Security hardening improvements
- Test suite overhaul
- Cognitive Privacy Shield features
- Application infrastructure
- Documentation enhancements
- Bug fixes and runtime improvements

### Branch Merge History

This branch consolidates the following feature branches:

1. **chore/coldstart-baseline-guardrails** - Runtime preflight checks and configuration templates
2. **feature/test-suite-overhaul** - Comprehensive test suite improvements (29 test failures resolved)
3. **authors-notes** - Cognitive Privacy Shield implementation and safety hardening
4. **Application** - Initial THE GRID monorepo Application branch foundation
5. **claude/add-claude-documentation-nHZSE** - AI assistant documentation (CLAUDE.md)
6. **claude/fix-usb-recognition-cUe5e** - WebUSB permissions policy fix
7. **claude/current-events-discussion-rOYNm** - Current Events Discussion Service for Arena API

### Current Branch Structure

```
claude/organize-branch-structure-LM7e9/
├── src/                          # Source code (layered architecture)
│   ├── grid/                     # Core intelligence (41 modules)
│   ├── application/              # FastAPI applications
│   ├── cognitive/                # Cognitive architecture (9 modules)
│   ├── tools/                    # Development tools (RAG system)
│   └── unified_fabric/           # Event bus & AI Safety bridge
│
├── tests/                        # Test suite (283+ tests passing)
│   ├── unit/                     # Fast unit tests
│   ├── integration/              # Integration tests
│   ├── api/                      # API endpoint tests
│   ├── auth/                     # Authentication tests
│   ├── billing/                  # Billing tests
│   ├── security/                 # Security tests
│   └── unified_fabric/           # Event bus tests
│
├── docs/                         # Documentation (150+ markdown files)
│   ├── structure/                # Repository structure guides
│   ├── security/                 # Security architecture
│   ├── architecture/             # Architecture documentation
│   └── guides/                   # Implementation guides
│
├── config/                       # Configuration files (22 files)
├── scripts/                      # Development and deployment scripts
├── schemas/                      # JSON schemas (31 files)
├── infrastructure/               # Infrastructure as code
├── frontend/                     # React 19 + TypeScript + Electron
├── landing/                      # Landing page (deployed on Netlify)
│
├── safety/                       # AI safety modules
├── security/                     # Security utilities
├── boundaries/                   # Boundary contracts & overwatch
│
├── .claude/                      # Claude AI configuration
│   └── rules/                    # Development rules and standards
├── .cursor/                      # Cursor AI configuration
│   ├── rules/                    # Cursor-specific rules
│   ├── skills/                   # Cursor skills
│   └── plans/                    # Cursor plans
├── .github/                      # GitHub workflows and templates
│   └── workflows/                # CI/CD pipelines
│
└── Root-level organization files
```

## Organization Strategy

### 1. Core Principles

- **Layered Architecture**: Strict separation of concerns (Application → Service → Core → Infrastructure)
- **Domain-Driven Design**: Clear domain boundaries with no circular dependencies
- **Local-First**: All AI operations use local Ollama models (no external APIs)
- **Production-Ready**: Enterprise-grade security, testing, and monitoring

### 2. Directory Structure Standards

#### `/src/` - All Source Code

**Subdirectories:**
- `grid/` - Core intelligence engine (geometric resonance patterns, skills, agentic system)
- `application/` - FastAPI applications (mothership, resonance, canvas)
- `cognitive/` - Cognitive architecture (9 modules for decision support)
- `tools/` - Development tools (RAG system, utilities)
- `unified_fabric/` - Event bus and distributed AI Safety bridge

#### `/tests/` - All Tests

**Organization by type:**
- `unit/` - Fast, isolated tests
- `integration/` - Cross-module tests
- `api/` - API endpoint tests
- Domain-specific: `auth/`, `billing/`, `security/`, `unified_fabric/`

#### `/docs/` - All Documentation

**Organization by category:**
- `structure/` - Repository structure and organization
- `security/` - Security architecture and guidelines
- `architecture/` - System architecture documentation
- `guides/` - Implementation and usage guides
- `decisions/` - Architectural decision records

#### `/config/` - Configuration Files

All configuration files (environment templates, pre-commit hooks, CI/CD configs)

#### Root-Level Files

**Essential files only:**
- `README.md` - Project overview and quick start
- `CLAUDE.md` - AI assistant guide
- `LICENSE` - MIT License
- `pyproject.toml` - Project configuration and dependencies
- `Makefile` - Development commands
- `uv.lock` - Locked dependencies

**Documentation files:**
- `BRANCH_ORGANIZATION.md` (this file)
- `ACKNOWLEDGEMENT.md`
- `SAFE_MERGES_COMPLETED.md`

**Project planning files:**
- `upnext.md` - Upcoming work and priorities

### 3. Files to Archive/Relocate

The following root-level files should be moved to appropriate directories:

#### Move to `/docs/security/`
- `COGNITIVE_PRIVACY_SHIELD_ANALYSIS.md`
- `PRIVACY_SHIELD_PLAN_VERIFICATION.md`
- `Enhance AI Safety and Review.md`
- `Finalizing Privacy Shield.md`

#### Move to `/docs/architecture/`
- `grep-tool-architecture.md`
- `project-structure.mmd`
- `resonance_architecture_reference.json`

#### Move to `/docs/guides/`
- `authors_notes.md`
- `authors_notes_visualization.md`

#### Remove (temporary/debug files)
- `1` (appears to be a temporary file)
- `plan.txt` (if superseded by documentation)
- Test result files (move to `/reports/` if needed):
  - `attack_results.json`
  - `daily_report.json`
  - `gh_report.json`
  - `integrated_report.json`
  - `parasite_analysis_report.json`
  - `security_validation_report.json`

#### Move to `/scripts/` or `/dev/`
- `parasite_analyzer.py`
- `secret_scanner.py`
- `validate_parasite_guard.py`
- `environment_audit.py`
- `run_verify_scan.py`
- All `drt_*.py` files (DRT = Dynamic Runtime Testing)
- `chaos_*.txt` files (move to `/reports/` or `/dev/logs/`)

### 4. Branch Workflow

#### Development Workflow

1. **Feature Development**: Create feature branches from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Consolidation**: Merge features into consolidation branch (this branch)
   ```bash
   git checkout claude/organize-branch-structure-LM7e9
   git merge feature/your-feature-name
   ```

3. **Testing**: Run full test suite before merging to main
   ```bash
   uv run pytest tests/ -v
   uv run ruff check .
   uv run mypy src/
   ```

4. **Merge to Main**: After all tests pass and code review
   ```bash
   git checkout main
   git merge claude/organize-branch-structure-LM7e9
   ```

#### Branch Naming Conventions

- `feature/` - New features
- `fix/` - Bug fixes
- `chore/` - Maintenance tasks
- `docs/` - Documentation updates
- `security/` - Security improvements
- `claude/` - Claude AI-generated branches (with session ID suffix)

### 5. Merge Strategy

This branch follows the **Safe Merge Strategy** documented in `SAFE_MERGES_COMPLETED.md`:

1. **No Force Operations**: Never use `git reset --hard` or force push
2. **Preserve History**: Maintain full merge history
3. **Test Before Merge**: Run full test suite on consolidation branch
4. **Review Changes**: Code review required for all merges
5. **Incremental Merges**: Small, focused merges over large batch merges

### 6. Quality Gates

Before this branch can be merged to `main`:

- ✅ All tests passing (283+ tests)
- ✅ Code coverage ≥80%
- ✅ No linting errors (`ruff check`)
- ✅ No type errors (`mypy src/`)
- ✅ Security scan passing (`bandit`, `pip-audit`)
- ✅ Documentation updated
- ✅ CHANGELOG.md updated with changes

### 7. Key Features in This Branch

#### Security Enhancements
- Comprehensive security hardening (8 vulnerability fixes)
- Path traversal protection
- Input validation improvements
- Safe serialization and error handling

#### Test Suite Improvements
- 29 test failures resolved
- Fair Play implementation with rate limiting
- Enhanced test coverage for safety modules
- Pre-check and developmental safety tests

#### Cognitive Privacy Shield
- Privacy-first cognitive architecture
- Bounded rationality engine
- Mental model representations
- Cognitive load management

#### Infrastructure
- Runtime preflight checks
- IDE configuration standards
- Development discipline rules
- Automated CI/CD pipelines

## Next Steps

### Immediate Actions (This Branch)

1. ✅ Create `BRANCH_ORGANIZATION.md` (this document)
2. ⏳ Update `README.md` with branch structure section
3. ⏳ Reorganize root-level files into appropriate directories
4. ⏳ Update documentation references
5. ⏳ Run full test suite to verify organization
6. ⏳ Commit and push organized structure

### Future Consolidations

- Continue merging feature branches as they're completed
- Maintain branch organization standards
- Update this document as structure evolves
- Regular cleanup of stale branches

## References

- **Repository Structure**: `docs/structure/README.md`
- **Safe Merge Strategy**: `SAFE_MERGES_COMPLETED.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Development Rules**: `.claude/rules/`
- **CI/CD Pipeline**: `.github/workflows/ci-main.yml`

---

**Last Updated**: 2026-02-15
**Branch**: `claude/organize-branch-structure-LM7e9`
**Status**: ✅ Active Consolidation Branch
