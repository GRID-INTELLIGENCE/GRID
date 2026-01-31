# GRID Quick Reference - Developer & Operator Guide

## Developer Quick Reference

### Core Commands
```powershell
# Basic analysis
python -m grid analyze "Your text here"

# JSON output
python -m grid analyze "Your text here" --output json

# Show timing
python -m grid analyze "Your text here" --timings

# From file
python -m grid analyze --file input.txt --output yaml

# With RAG
python -m grid analyze "Your text here" --use-rag

# Full benchmark suite
python scripts/benchmark_grid.py

# List skills
python -m grid skills list

# Run a skill
python -m grid skills run transform.schema_map --args-json "{text:'...', target_schema:'default', use_llm:false}"

# Build curated RAG index
python -m tools.rag.cli index . --rebuild --curate

# Query RAG
python -m tools.rag.cli query "Where is the skills registry implemented?"
```

### Performance Targets
| Scenario | Target | Command |
|----------|--------|---------|
| Small text | < 15ms | `analyze TEXT --timings` |
| Medium text | < 50ms | `analyze TEXT --max-entities 15 --timings` |
| Large text | < 200ms | `analyze TEXT --max-entities 10 --use-rag --timings` |
| Accuracy focus | P95 < 100ms | `analyze TEXT --confidence 0.5 --max-entities 50` |
| Speed focus | P50 < 20ms | `analyze TEXT --confidence 0.9 --max-entities 5` |

### Common Issues
| Problem | Solution |
|---------|----------|
| "No module named grid" | Run from `e:\grid` root |
| "IndentationError in logging" | ✅ Fixed (renamed file) |
| Slow performance | Use `--max-entities 5` and `--confidence 0.9` |
| Need OpenAI | Set `OPENAI_API_KEY` env var or use `--openai-key` |

### VS Code Tasks
Press `Ctrl+Shift+B` and select:
- `█ PERF · Benchmark GRID (Full Suite)` - Full perf test (~2 min)
- `█ PERF · Analyze Quick` - Small input baseline (~10ms)
- `█ PERF · Analyze with RAG` - Test RAG enhancement (~50ms)

---

## Operator Quick Reference

### Knowledge Management
```powershell
# Full synchronization (updates RAG + knowledge graph)
python -m tools.slash_commands.sync

# RAG index only
python -m tools.slash_commands.sync --rag-only

# Knowledge graph only
python -m tools.slash_commands.sync --graph-only

# Quick sync (recent changes only)
python -m tools.slash_commands.sync --quick

# Quality check
python -m tools.slash_commands.sync --quality
```

### RAG Operations
```powershell
# Build index from docs
python -m tools.rag.cli index docs/ --rebuild

# Query with RAG
python -m tools.rag.cli query "What are the core components?"

# Get RAG stats
python -m tools.rag.cli stats
```

### Knowledge Graph
```powershell
# Refresh graph
python -m tools.knowledge_graph.refresh

# Get graph stats
python -m tools.knowledge_graph.stats

# Visualize graph
python -m tools.knowledge_graph.visualize
```

---

## Environment Setup

### Python Environment
```powershell
# Setup environment (Python 3.13.11)
uv venv --python 3.13 --clear && .\.venv\Scripts\Activate.ps1 && uv sync --group dev --group test

# Linting/Formatting
ruff check .              # Lint
ruff check --fix .        # Auto-fix
black .                   # Format
mypy src/                 # Type check
```

### Key Dependencies
- **Python**: 3.13.11 (enforced)
- **FastAPI**: >=0.104.0
- **scikit-learn**: ==1.8.0
- **ChromaDB**: >=1.4.1
- **Pydantic**: v2

---

## Troubleshooting

### Common Issues
| Problem | Solution |
|---------|----------|
| Import errors | Check Python version (3.13.11) |
| Missing dependencies | Run `uv sync --group dev --group test` |
| RAG not working | Verify ChromaDB installation |
| Graph issues | Check knowledge graph configuration |

### Performance Issues
- Use `--max-entities 5` for faster analysis
- Set `--confidence 0.9` for speed focus
- Run with `--timings` to identify bottlenecks

---

## File Structure Reference

### Key Directories
- `src/grid/` - Core intelligence layer
- `src/application/` - FastAPI application
- `src/cognitive/` - Cognitive patterns
- `src/tools/` - RAG system, utilities
- `docs/` - Documentation
- `tests/` - Test suite

### Configuration Files
- `pyproject.toml` - Project config
- `DEPENDENCY_MATRIX.md` - Version constraints
- `AGENTS.md` - Agent behavior guidelines

---

## Support Resources

### Documentation
- **Architecture**: `docs/architecture.md`
- **Setup**: `docs/INSTALLATION.md`
- **Development**: `docs/DEVELOPMENT_GUIDE.md`
- **API**: `docs/API_DOCUMENTATION.md`

### Tools
- **RAG System**: `tools/rag/`
- **Knowledge Graph**: `tools/knowledge_graph/`
- **Skills**: `tools/skills/`

### Quick Links
- View architecture: `docs/ARCHITECTURE_EXECUTIVE_SUMMARY.md`
- Check dependencies: `DEPENDENCY_MATRIX.md`
- Agent guidelines: `AGENTS.md`

---

## Quality Status Indicators

### Sync Quality
- **Excellent** (0.8-1.0): Full RAG + graph with high connectivity
- **Good** (0.6-0.8): RAG working, moderate graph connectivity
- **Fair** (0.4-0.6): Partial RAG or limited graph
- **Poor** (0-0.4): No RAG chunks or graph nodes

### RAG Quality Factors
- **Total chunks**: > 50 for good quality
- **Semantic density**: > 0.5 average
- **Chunk diversity**: > 3 chunk types

### Graph Quality Factors
- **Total nodes**: > 10 for good connectivity
- **Edge density**: > 0.1 for strong connections
- **Avg connectivity**: > 2 for good knowledge flow

---

## Test & CI/CD Quick Reference

**Last Updated:** February 1, 2026

---

### 🚀 Quick Start (5 minutes)

```bash
# 1. Setup environment
uv venv --python 3.13
.venv\\Scripts\\Activate.ps1
uv sync --group dev --group test

# 2. Run tests
uv run pytest tests/ -v

# 3. Check coverage
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# 4. Analyze results
uv run python scripts/analyze_tests.py

# 5. Push to GitHub
git add .
git commit -m "Add tests"
git push
```

---

### 📋 Common Commands

#### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest tests/unit/core/test_documentation_index.py -v

# Specific test function
uv run pytest tests/unit/core/test_documentation_index.py::TestDocumentationIndex::test_count_by_category -v

# Tests matching pattern
uv run pytest tests/ -k "documentation" -v

# Tests with specific marker
uv run pytest tests/ -m "critical" -v

# Stop on first failure
uv run pytest tests/ -v -x

# Show slowest 10 tests
uv run pytest tests/ -v --durations=10

# Parallel execution (opt-in)
uv run pytest tests/ -n auto -v
```

#### Coverage

```bash
# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report
uv run pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold
uv run pytest tests/ --cov=src --cov-fail-under=80
```

#### Debugging

```bash
# Verbose output
uv run pytest tests/ -vv

# Show print statements
uv run pytest tests/ -v -s

# Drop into debugger
uv run pytest tests/ -v --pdb

# Show local variables
uv run pytest tests/ -v -l

# Detailed traceback
uv run pytest tests/ -v --tb=long
```

#### Analysis

```bash
# Analyze test context
uv run python scripts/analyze_tests.py

# Capture failures
uv run python scripts/capture_failures.py

# View reports
cat test_context_report.json
cat test_failures.json
```

---

### 🔧 Test Markers

```python
@pytest.mark.unit              # Fast, isolated
@pytest.mark.integration       # Slower, cross-module
@pytest.mark.slow              # > 1 second
@pytest.mark.critical          # Must pass
@pytest.mark.flaky             # May fail intermittently
@pytest.mark.database          # Needs database
@pytest.mark.event_bus         # Event bus tests
@pytest.mark.physics           # Physics tests
@pytest.mark.relationship      # Relationship tests
@pytest.mark.visual            # Visual tests
@pytest.mark.documentation     # Documentation tests
```

---

### 📊 Test Structure

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

### 🔄 CI/CD Workflows

#### Main Pipeline (main-ci.yml)

**Triggers:** Push to main/develop, PRs

**Jobs:**
1. Lint (ruff, mypy, black)
2. Unit Tests (Python 3.13)
3. Integration Tests
4. Coverage Check (>= 80%)
5. Critical Tests
6. Summary

**Time:** ~10-15 minutes

#### Fast Feedback (fast-feedback.yml)

**Triggers:** PRs only

**Jobs:**
1. Quick Check (lint + unit tests)

**Time:** ~2-3 minutes

---

### 📈 Fixtures

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

### 🎯 Test Example

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

### 🐛 Debugging Workflow

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

### 📊 Monitoring

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

### ✅ Pre-Push Checklist

- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] Coverage >= 80%: `uv run pytest tests/ --cov=src`
- [ ] No lint errors: `uv run ruff check .`
- [ ] Formatting OK: `uv run black --check .`
- [ ] Type check passes: `uv run mypy src`
- [ ] No failures: `uv run python scripts/capture_failures.py`
- [ ] Commit message clear
- [ ] Branch up to date

---

### 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests fail locally | Run `uv run pytest tests/ -vv -s --tb=long` |
| Coverage low | Add tests for uncovered code |
| CI/CD slow | Opt-in to parallel execution with `uv run pytest -n auto` |
| Flaky tests | Mark with `@pytest.mark.flaky` |
| Import errors | Check `sys.path` in conftest.py |
| Database issues | Use in-memory SQLite in tests |

---

### 📚 Documentation

- `TEST_CI_CD_CONTEXT.md` - Full guide (700+ lines)
- `IMPLEMENTATION_GUIDE.md` - Step-by-step
- `TEST_IMPLEMENTATION_SUMMARY.md` - Overview
- `QUICK_REFERENCE.md` - This card

---

### 🎯 Success Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Tests Pass | 100% | `uv run pytest tests/ -v` |
| Coverage | >= 80% | `uv run pytest tests/ --cov=src` |
| Execution | < 5 min | `uv run pytest tests/ --durations=10` |
| Lint | 0 errors | `uv run ruff check .` |
| Types | 0 errors | `uv run mypy src` |

---

### 🔗 Quick Links

- [Pytest Docs](https://docs.pytest.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Codecov](https://docs.codecov.io/)
- [Python Testing](https://docs.python-guide.org/writing/tests/)

---

### 💡 Pro Tips

1. **Use markers** - Organize tests with `@pytest.mark.unit`, etc.
2. **Parallel execution (opt-in)** - Use `pytest -n auto` only when you understand concurrency risks
3. **Deterministic seeds** - Use `seed=42` for reproducibility
4. **Fixtures** - Reuse test setup with fixtures
5. **Parametrize** - Test multiple inputs with `@pytest.mark.parametrize`
6. **Skip tests** - Use `@pytest.mark.skip` for WIP
7. **Xfail tests** - Use `@pytest.mark.xfail` for known failures
8. **Coverage reports** - Generate HTML with `--cov-report=html`

---

## 📚 Operator Guidance

- **Test isolation**: Ensure tests are independent and don't interfere with each other.
- **Test naming**: Use descriptive names for tests and test functions.
- **Test structure**: Organize tests into logical groups and use fixtures for setup and teardown.
- **Test debugging**: Use `--pdb` and `--tb=long` for debugging test failures.

---

**Ready to test! 🚀**

<<<<<<< E:/grid/docs/QUICK_REFERENCE.md
Print this card and keep it handy!
||||||| C:/Users/irfan/.windsurf/worktrees/grid/grid-41d47f67/docs/QUICK_REFERENCE.md.base
Print this card and keep it handy!
=======
Print this card and keep it handy!
<<<<<<< E:/grid/docs/QUICK_REFERENCE.md

---

## See also

- `TESTING.md`
- `CI_CD_GUIDE.md`
- `CLI_REFERENCE.md`
- `GRID_QUICK_REFERENCE.md`
>>>>>>> C:/Users/irfan/.windsurf/worktrees/grid/grid-41d47f67/docs/QUICK_REFERENCE.md
||||||| C:/Users/irfan/.windsurf/worktrees/grid/grid-41d47f67/docs/QUICK_REFERENCE.md.base
=======

---

## See also

- `TESTING.md`
- `CI_CD_GUIDE.md`
- `CLI_REFERENCE.md`
- `GRID_QUICK_REFERENCE.md`
>>>>>>> C:/Users/irfan/.windsurf/worktrees/grid/grid-41d47f67/docs/QUICK_REFERENCE.md
