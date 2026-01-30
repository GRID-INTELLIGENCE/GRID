# Test & CI/CD Quick Reference Card

**Last Updated:** November 30, 2025

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,test]"

# 2. Run tests
pytest tests/ -v

# 3. Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# 4. Analyze results
python scripts/analyze_tests.py

# 5. Push to GitHub
git add .
git commit -m "Add tests"
git push
```

---

## 📋 Common Commands

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/core/test_documentation_index.py -v

# Specific test function
pytest tests/unit/core/test_documentation_index.py::TestDocumentationIndex::test_count_by_category -v

# Tests matching pattern
pytest tests/ -k "documentation" -v

# Tests with specific marker
pytest tests/ -m "critical" -v

# Stop on first failure
pytest tests/ -v -x

# Show slowest 10 tests
pytest tests/ -v --durations=10

# Parallel execution
pytest tests/ -n auto -v
```

### Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold
pytest tests/ --cov=src --cov-fail-under=80
```

### Debugging

```bash
# Verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -v -s

# Drop into debugger
pytest tests/ -v --pdb

# Show local variables
pytest tests/ -v -l

# Detailed traceback
pytest tests/ -v --tb=long
```

### Analysis

```bash
# Analyze test context
python scripts/analyze_tests.py

# Capture failures
python scripts/capture_failures.py

# View reports
cat test_context_report.json
cat test_failures.json
```

---

## 🔧 Test Markers

```python
@pytest.mark.unit              # Fast, isolated
@pytest.mark.integration       # Slower, cross-module
@pytest.mark.slow              # > 1 second
@pytest.mark.critical          # Must pass
@pytest.mark.flaky             # May fail intermittently
@pytest.mark.asyncio           # Async tests
@pytest.mark.database          # Needs database
@pytest.mark.event_bus         # Event bus tests
@pytest.mark.physics           # Physics tests
@pytest.mark.relationship      # Relationship tests
@pytest.mark.visual            # Visual tests
@pytest.mark.documentation     # Documentation tests
```

---

## 📊 Test Structure

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_documentation_index.py
│   │   ├── test_events.py
│   │   ├── test_architecture.py
│   │   └── ...
│   ├── physics/
│   │   ├── test_heat_state.py
│   │   ├── test_credit_system.py
│   │   └── test_ubi_physics_engine.py
│   └── services/
│       ├── test_relationship_analyzer.py
│       └── test_visual_theme_analyzer.py
├── integration/
│   ├── test_event_bus_integration.py
│   ├── test_physics_integration.py
│   └── ...
└── conftest.py
```

---

## 🔄 CI/CD Workflows

### Main Pipeline (main-ci.yml)

**Triggers:** Push to main/develop, PRs

**Jobs:**
1. Lint (flake8, mypy, black, isort)
2. Unit Tests (Python 3.10, 3.11, 3.12)
3. Integration Tests
4. Coverage Check (>= 80%)
5. Critical Tests
6. Summary

**Time:** ~10-15 minutes

### Fast Feedback (fast-feedback.yml)

**Triggers:** PRs only

**Jobs:**
1. Quick Check (lint + unit tests)

**Time:** ~2-3 minutes

---

## 📈 Fixtures

```python
# Documentation
@pytest.fixture
def documentation_index():
    return DocumentationIndex(...)

# Event Bus
@pytest.fixture
def event_bus():
    return EventBus()

# Physics
@pytest.fixture
def physics_engine():
    return UBIPhysicsEngine()

# Relationship
@pytest.fixture
def relationship_analyzer():
    return RelationshipAnalyzer()

# Visual
@pytest.fixture
def visual_analyzer():
    return VisualThemeAnalyzer()

# Deterministic
@pytest.fixture
def deterministic_seed():
    return 42
```

---

## 🎯 Test Example

```python
import pytest
from src.core.documentation_index import DocumentationIndex, Document, DocumentCategory

class TestDocumentationIndex:
    """Test documentation index"""

    def test_count_by_category(self, documentation_index):
        """Test counting documents by category"""
        doc = Document(
            name="test.md",
            category=DocumentCategory.CORE,
            size_bytes=1024,
            lines=50,
            description="Test",
            key_topics=["test"],
            file_path="docs/test.md"
        )
        documentation_index.documents.append(doc)

        counts = documentation_index.count_by_category()
        assert counts[DocumentCategory.CORE.value] == 1
```

---

## 🐛 Debugging Workflow

```
Test fails locally
    ↓
Run with -vv -s --tb=long
    ↓
Add print statements
    ↓
Run with --pdb to debug
    ↓
Check test_failures.json
    ↓
Fix issue
    ↓
Run tests again
    ↓
Verify fix
    ↓
Commit and push
```

---

## 📊 Monitoring

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# View run logs
gh run view <run-id> --log

# View job logs
gh run view <run-id> --log --job <job-id>

# Rerun failed workflow
gh run rerun <run-id>
```

---

## ✅ Pre-Push Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >= 80%: `pytest tests/ --cov=src`
- [ ] No lint errors: `flake8 src tests`
- [ ] Type check passes: `mypy src`
- [ ] No failures: `python scripts/capture_failures.py`
- [ ] Commit message clear
- [ ] Branch up to date

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests fail locally | Run `pytest tests/ -vv -s --tb=long` |
| Coverage low | Add tests for uncovered code |
| CI/CD slow | Use `pytest -n auto` for parallel |
| Flaky tests | Mark with `@pytest.mark.flaky` |
| Import errors | Check `sys.path` in conftest.py |
| Database issues | Use in-memory SQLite in tests |

---

## 📚 Documentation

- `TEST_CI_CD_CONTEXT.md` - Full guide (700+ lines)
- `IMPLEMENTATION_GUIDE.md` - Step-by-step
- `TEST_IMPLEMENTATION_SUMMARY.md` - Overview
- `QUICK_REFERENCE.md` - This card

---

## 🎯 Success Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Tests Pass | 100% | `pytest tests/ -v` |
| Coverage | >= 80% | `pytest tests/ --cov=src` |
| Execution | < 5 min | `pytest tests/ --durations=10` |
| Lint | 0 errors | `flake8 src tests` |
| Types | 0 errors | `mypy src` |

---

## 🔗 Quick Links

- [Pytest Docs](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Codecov](https://docs.codecov.io/)
- [Python Testing](https://docs.python-guide.org/writing/tests/)

---

## 💡 Pro Tips

1. **Use markers** - Organize tests with `@pytest.mark.unit`, etc.
2. **Parallel execution** - `pytest -n auto` for speed
3. **Deterministic seeds** - Use `seed=42` for reproducibility
4. **Fixtures** - Reuse test setup with fixtures
5. **Parametrize** - Test multiple inputs with `@pytest.mark.parametrize`
6. **Skip tests** - Use `@pytest.mark.skip` for WIP
7. **Xfail tests** - Use `@pytest.mark.xfail` for known failures
8. **Coverage reports** - Generate HTML with `--cov-report=html`

---

**Ready to test! 🚀**

Print this card and keep it handy!
