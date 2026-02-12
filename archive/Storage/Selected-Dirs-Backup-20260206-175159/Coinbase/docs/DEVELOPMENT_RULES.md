# Development Rules - GRID Agentic System

## Purpose

These rules establish clear boundaries and constraints for development to prevent unintended changes and scope creep. All development must adhere to these rules unless explicitly overridden by the user.

---

## Core Constraints

### 1. Execution Model

**Rule:** **Synchronous Execution Only**

- ❌ No `async def` functions
- ❌ No `await` keywords
- ❌ No `asyncio` imports
- ❌ No `pytest-asyncio` dependency
- ✅ All functions must be synchronous
- ✅ Use `time.sleep()` for delays (not `asyncio.sleep()`)

**Rationale:** User requirement "asyncio denied" - system must be synchronous for predictability and simplicity.

**Enforcement:** All code reviews must check for async/await. Tests must not use async.

---

### 2. Python Version

**Rule:** **Python 3.13 Only**

- ✅ Minimum version: Python 3.13
- ✅ Maximum version: Python 3.13
- ❌ No Python 3.14 features
- ❌ No Python 3.12 or earlier
- ✅ `requires-python = ">=3.13,<3.14"`

**Rationale:** Enforced by `.python-version` and `pyproject.toml`.

**Enforcement:** Type checking with mypy configured for Python 3.13.

---

### 3. Dependencies

**Rule:** **Minimal Dependencies**

**Allowed Dependencies:**
- `click>=8.1.0` (CLI)
- `pytest>=7.0.0` (testing)
- `pytest-cov>=4.0.0` (coverage)
- `ruff>=0.1.0` (linting)
- `black>=23.0.0` (formatting)
- `mypy>=1.0.0` (type checking)

**Prohibited Dependencies:**
- ❌ Any async libraries (asyncio, aiohttp, etc.)
- ❌ Database drivers (use standard library)
- ❌ Web frameworks (use standard library)
- ❌ Machine learning libraries (use standard library)

**Rationale:** Keep system lightweight and portable.

**Enforcement:** Manual review of `pyproject.toml` changes.

---

### 4. Code Style

**Rule:** **Strict Code Style**

- ✅ Line length: 100 characters
- ✅ Use `black` for formatting
- ✅ Use `ruff` for linting
- ✅ Type hints required on all functions
- ✅ Docstrings required on all public functions
- ✅ PEP 8 compliant

**Enforcement:** Pre-commit hooks with black and ruff.

---

### 5. Testing

**Rule:** **100% Test Coverage**

- ✅ All modules must have tests
- ✅ All functions must be tested
- ✅ All edge cases must be covered
- ✅ Tests must be synchronous
- ✅ Tests must pass before committing

**Enforcement:** CI/CD pipeline with pytest.

---

### 6. Architecture

**Rule:** **7-Layer Architecture**

**Fixed Layers:**
1. User Layer (CLI, Entry Point)
2. Orchestration Layer (AgenticSystem, EventBus, AgentExecutor, CognitiveEngine)
3. Execution Layer (RuntimeBehaviorTracer, RecoveryEngine, ErrorClassifier)
4. Learning Layer (SkillGenerator, LearningCoordinator, Skill Store)
5. Analysis Layer (CryptoSkillsRegistry, Skills)
6. Scoring Layer (VersionScorer, VersionMetrics, Version History)
7. Output Layer (Performance Metrics, Execution Results, Generated Skills)

**Enforcement:** No new layers allowed without explicit user approval.

---

### 7. Component Boundaries

**Rule:** **Fixed Component Set**

**Allowed Components (9 core modules):**
1. `tracer.py` - RuntimeBehaviorTracer
2. `events.py` - EventBus
3. `error_recovery.py` - RecoveryEngine
4. `skill_generator.py` - SkillGenerator
5. `learning_coordinator.py` - LearningCoordinator
6. `agent_executor.py` - AgentExecutor
7. `agentic_system.py` - AgenticSystem
8. `version_scoring.py` - VersionScorer
9. `cognitive_engine.py` - CognitiveEngine

**Prohibited:**
- ❌ Adding new core modules without approval
- ❌ Removing existing modules
- ❌ Changing module responsibilities

**Enforcement:** Code review for any module additions/removals.

---

### 8. Skill Boundaries

**Rule:** **Fixed Skill Set (8 Skills)**

**Allowed Skills:**
1. Crypto Data Normalization
2. Crypto Data Validation
3. Price Trend Analysis
4. Volume Analysis
5. Strategy Backtesting
6. Chart Pattern Detection
7. Risk Assessment
8. Report Generation

**Prohibited:**
- ❌ Adding new skills without approval
- ❌ Removing existing skills
- ❌ Changing skill interfaces

**Enforcement:** Code review for skill additions/removals.

---

### 9. Documentation

**Rule:** **Complete Documentation**

**Required Documentation:**
- ✅ README.md (setup, usage)
- ✅ rules.md (system rules)
- ✅ workflow.md (analysis workflow)
- ✅ STATUS.md (status summary)
- ✅ EVALUATION.md (process evaluation)
- ✅ PROGRESS.md (progress summary)
- ✅ diagrams/data_flow.md (data flow)
- ✅ diagrams/architecture.md (architecture)

**Enforcement:** Documentation must be updated with code changes.

---

### 10. Version Control

**Rule:** **Git Workflow**

**Commit Rules:**
- ✅ Commit message format: "scope: description"
- ✅ Atomic commits (one logical change)
- ✅ Tests must pass before commit
- ✅ Documentation must be updated

**Branch Rules:**
- ✅ Main branch: `main`
- ✅ Feature branches: `feature/description`
- ✅ No direct commits to main (use PRs)

**Enforcement:** Pre-commit hooks for tests.

---

## Scope Boundaries

### In Scope (Allowed)

- ✅ Implementing skill handlers (currently placeholders)
- ✅ Adding integration tests
- ✅ Performance optimization
- ✅ Bug fixes
- ✅ Documentation updates
- ✅ Dependency updates (security patches)
- ✅ Test improvements

### Out of Scope (Prohibited)

- ❌ Adding async/await support
- ❌ Changing to Python 3.14
- ❌ Adding new core modules
- ❌ Removing existing modules
- ❌ Adding new skills
- ❌ Changing architecture layers
- ❌ Adding new dependencies
- ❌ Removing existing dependencies
- ❌ Changing test framework
- ❌ Removing tests

---

## Change Request Process

### Minor Changes (Allowed Without Approval)

- Bug fixes
- Documentation updates
- Test improvements
- Performance optimizations
- Dependency security patches

### Major Changes (Require Approval)

- Adding new modules
- Removing existing modules
- Adding new skills
- Changing architecture
- Adding new dependencies
- Removing existing dependencies
- Changing execution model
- Changing Python version

**Process for Major Changes:**
1. Submit change request with rationale
2. Wait for user approval
3. Implement only after approval
4. Update documentation
5. Add tests
6. Commit with descriptive message

---

## Enforcement Mechanisms

### 1. Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
uv run pytest tests/ -q
uv run ruff check .
uv run black --check .
uv run mypy coinbase/
```

### 2. Code Review Checklist

- [ ] No async/await keywords
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Tests pass (100%)
- [ ] Documentation updated
- [ ] No new dependencies
- [ ] No new modules (unless approved)
- [ ] No new skills (unless approved)

### 3. Continuous Integration

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: uv sync
      - run: uv run pytest tests/ -v
      - run: uv run ruff check .
      - run: uv run black --check .
      - run: uv run mypy coinbase/
```

---

## Emergency Override

In case of critical issues that require breaking these rules:

1. Document the emergency situation
2. Explain why the rule must be broken
3. Get explicit user approval
4. Implement minimal change
5. Document the exception
6. Plan to restore compliance

---

## Summary

These rules ensure:
- ✅ No unintended changes mid-process
- ✅ Clear boundaries for development
- ✅ Predictable system behavior
- ✅ Maintainable codebase
- ✅ High quality standards
- ✅ Alignment with user requirements

**Remember:** The "asyncio denied" rule is the prime example of why these rules exist - to prevent scope creep and maintain alignment with user requirements.

---

**Last Updated:** January 26, 2026
**Version:** 1.0
