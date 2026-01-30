# Test & CI/CD Implementation Guide

**Status:** Ready for Execution
**Date:** November 30, 2025
**Goal:** Seamless green CI/CD pipeline with deterministic testing

---

## 📋 Quick Start

### 1. Verify Current State

```bash
# Check existing tests
pytest tests/ --collect-only -q

# Run existing tests
pytest tests/ -v --tb=short

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 2. Analyze Current Context

```bash
# Generate test context report
python scripts/analyze_tests.py

# Capture any failures
python scripts/capture_failures.py

# View reports
cat test_context_report.json
cat test_failures.json
```

### 3. Update Pytest Configuration

**File: `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, cross-module)
    slow: Slow running tests (> 1 second)
    asyncio: Async tests
    database: Tests requiring database
    event_bus: Event bus tests
    physics: Physics engine tests
    relationship: Relationship analyzer tests
    visual: Visual theme tests
    documentation: Documentation system tests
    critical: Critical path tests (must pass)
    flaky: Flaky tests (may fail intermittently)
```

### 4. Enhance Conftest

**File: `tests/conftest.py`** - Add new fixtures:

```python
import pytest
from datetime import datetime
from src.core.documentation_index import DocumentationIndex, Document, DocumentCategory
from src.core.events import EventBus, ArchitectureLayer
from src.physics.ubi_physics_engine import UBIPhysicsEngine
from src.services.relationship_analyzer import RelationshipAnalyzer
from src.services.visual_theme_analyzer import VisualThemeAnalyzer

# Documentation fixtures
@pytest.fixture
def documentation_index():
    return DocumentationIndex(
        total_documents=10,
        total_lines=1000,
        generated_date=datetime.now().isoformat(),
        documents=[]
    )

# Event bus fixtures
@pytest.fixture
def event_bus():
    return EventBus()

# Physics fixtures
@pytest.fixture
def physics_engine():
    return UBIPhysicsEngine()

# Relationship fixtures
@pytest.fixture
def relationship_analyzer():
    return RelationshipAnalyzer()

# Visual fixtures
@pytest.fixture
def visual_analyzer():
    return VisualThemeAnalyzer()

# Deterministic context
@pytest.fixture
def deterministic_seed():
    import random
    random.seed(42)
    return 42
```

---

## 🧪 Create Test Files

### Phase 1: Documentation Tests

**File: `tests/unit/core/test_documentation_index.py`**

```python
import pytest
from src.core.documentation_index import (
    DocumentationIndex, Document, DocumentCategory
)

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

    def test_search_by_topic(self, documentation_index):
        """Test searching by topic"""
        doc = Document(
            name="test.md",
            category=DocumentCategory.CORE,
            size_bytes=1024,
            lines=50,
            description="Test",
            key_topics=["api", "documentation"],
            file_path="docs/test.md"
        )
        documentation_index.documents.append(doc)

        results = documentation_index.search_by_topic("api")
        assert len(results) == 1
        assert results[0].name == "test.md"

    def test_get_total_size(self, documentation_index):
        """Test getting total size"""
        doc1 = Document(
            name="test1.md",
            category=DocumentCategory.CORE,
            size_bytes=1024,
            lines=50,
            description="Test 1",
            key_topics=["test"],
            file_path="docs/test1.md"
        )
        doc2 = Document(
            name="test2.md",
            category=DocumentCategory.CLI,
            size_bytes=2048,
            lines=100,
            description="Test 2",
            key_topics=["test"],
            file_path="docs/test2.md"
        )
        documentation_index.documents.extend([doc1, doc2])

        total = documentation_index.get_total_size()
        assert total == 3072
```

### Phase 2: Event Bus Tests

**File: `tests/unit/core/test_events.py`**

```python
import pytest
from src.core.events import EventBus, EventType, ArchitectureLayer

class TestEventBus:
    """Test event bus"""

    def test_publish_event(self, event_bus):
        """Test publishing an event"""
        event = {
            "event_type": "test_event",
            "layer": ArchitectureLayer.SECURITY.value,
            "payload": {"data": "test"}
        }
        event_bus.publish(event)

        assert len(event_bus.events) == 1
        assert event_bus.events[0]["event_type"] == "test_event"

    def test_subscribe_to_event(self, event_bus):
        """Test subscribing to events"""
        received_events = []

        def callback(event):
            received_events.append(event)

        event_bus.subscribe("test_event", callback)

        event = {
            "event_type": "test_event",
            "layer": ArchitectureLayer.SECURITY.value,
            "payload": {"data": "test"}
        }
        event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0]["event_type"] == "test_event"

    def test_event_history(self, event_bus):
        """Test event history"""
        for i in range(5):
            event = {
                "event_type": f"event_{i}",
                "layer": ArchitectureLayer.SECURITY.value,
                "payload": {"index": i}
            }
            event_bus.publish(event)

        history = event_bus.get_event_history(limit=3)
        assert len(history) == 3
```

### Phase 3: Physics Tests

**File: `tests/unit/physics/test_ubi_physics_engine.py`**

```python
import pytest
from src.physics.ubi_physics_engine import UBIPhysicsEngine

class TestUBIPhysicsEngine:
    """Test UBI physics engine"""

    def test_log_effort(self, physics_engine):
        """Test logging effort"""
        result = physics_engine.log_effort(10.0, "normal")

        assert result["effort_minutes"] == 10.0
        assert result["effort_score"] == 10.0
        assert result["heat_added"] == 20.0

    def test_tick_simulation(self, physics_engine):
        """Test physics tick"""
        physics_engine.log_effort(10.0, "normal")
        result = physics_engine.tick()

        assert result["heat_dissipated"] > 0
        assert result["credits_earned"] > 0
        assert result["current_heat"] < 20.0

    def test_throttle_hint(self, physics_engine):
        """Test throttle hint"""
        physics_engine.log_effort(10.0, "normal")
        throttle = physics_engine.get_throttle_hint()

        assert "heat_percentage" in throttle
        assert "recommended_concurrency" in throttle
        assert "status" in throttle
```

### Phase 4: Relationship Tests

**File: `tests/unit/services/test_relationship_analyzer.py`**

```python
import pytest
from src.services.relationship_analyzer import RelationshipAnalyzer

class TestRelationshipAnalyzer:
    """Test relationship analyzer"""

    def test_analyze_cooperative(self, relationship_analyzer):
        """Test analyzing cooperative relationship"""
        history = [
            {"type": "cooperation"},
            {"type": "cooperation"},
            {"type": "conflict"},
        ]
        judgment = relationship_analyzer.analyze("Alice", "Bob", history)

        assert judgment.source_entity == "Alice"
        assert judgment.target_entity == "Bob"
        assert judgment.polarity_score > 0
        assert judgment.polarity_label == "cooperative"

    def test_analyze_adversarial(self, relationship_analyzer):
        """Test analyzing adversarial relationship"""
        history = [
            {"type": "conflict"},
            {"type": "conflict"},
            {"type": "cooperation"},
        ]
        judgment = relationship_analyzer.analyze("Alice", "Bob", history)

        assert judgment.polarity_score < 0
        assert judgment.polarity_label == "adversarial"

    def test_confidence_calculation(self, relationship_analyzer):
        """Test confidence calculation"""
        history = [{"type": "cooperation"}] * 10
        judgment = relationship_analyzer.analyze("Alice", "Bob", history)

        assert judgment.confidence > 0.5
```

---

## 🚀 Run Tests Locally

### Step 1: Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,test]"
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Step 2: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/unit/core/test_documentation_index.py::TestDocumentationIndex::test_count_by_category -v

# Run with debugging
pytest tests/ -v --pdb
```

### Step 3: Analyze Results

```bash
# Generate context report
python scripts/analyze_tests.py

# Capture failures
python scripts/capture_failures.py

# View reports
cat test_context_report.json
cat test_failures.json
```

---

## 🔧 Configure CI/CD

### Step 1: Create Main Workflow

**File: `.github/workflows/main-ci.yml`** - Already created

### Step 2: Create Fast Feedback Workflow

**File: `.github/workflows/fast-feedback.yml`** - Already created

### Step 3: Verify Workflows

```bash
# List workflows
gh workflow list

# View workflow file
cat .github/workflows/main-ci.yml

# Test workflow locally (requires act)
act push -j lint
act push -j unit-tests
```

---

## 📊 Monitoring & Optimization

### Track Test Performance

```bash
# Run tests with timing
pytest tests/ -v --durations=10

# Run tests in parallel
pytest tests/ -n auto -v

# Generate performance report
pytest tests/ -v --benchmark
```

### Monitor Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Check CI/CD Status

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# View run logs
gh run view <run-id> --log
```

---

## ✅ Verification Checklist

### Local Testing
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] Coverage >= 80%: `pytest tests/ --cov=src`
- [ ] No linting errors: `flake8 src tests`
- [ ] Type checking passes: `mypy src`
- [ ] No test failures: `python scripts/capture_failures.py`

### CI/CD Configuration
- [ ] Main workflow created: `.github/workflows/main-ci.yml`
- [ ] Fast feedback workflow created: `.github/workflows/fast-feedback.yml`
- [ ] Pytest configuration updated: `pytest.ini`
- [ ] Conftest enhanced: `tests/conftest.py`
- [ ] Test context module created: `src/core/test_context.py`

### Test Suite
- [ ] Documentation tests created: `tests/unit/core/test_documentation_index.py`
- [ ] Event bus tests created: `tests/unit/core/test_events.py`
- [ ] Physics tests created: `tests/unit/physics/test_ubi_physics_engine.py`
- [ ] Relationship tests created: `tests/unit/services/test_relationship_analyzer.py`
- [ ] All tests marked with appropriate markers

### Monitoring
- [ ] Test context report generated: `test_context_report.json`
- [ ] Failure report generated: `test_failures.json`
- [ ] Coverage report generated: `htmlcov/index.html`
- [ ] Performance metrics tracked

### Documentation
- [ ] TEST_CI_CD_CONTEXT.md created
- [ ] IMPLEMENTATION_GUIDE.md created
- [ ] README updated with test commands
- [ ] CI/CD workflows documented

---

## 🎯 Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| All tests pass locally | 100% | ⏳ |
| All tests pass in CI/CD | 100% | ⏳ |
| Code coverage | >= 80% | ⏳ |
| Test execution time | < 5 min | ⏳ |
| Green CI/CD on push | 100% | ⏳ |
| No flaky tests | 0% | ⏳ |
| Clear failure messages | All documented | ⏳ |
| Deterministic tests | 100% reproducible | ⏳ |

---

## 📞 Quick Reference

### Common Commands

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/unit/core/test_documentation_index.py -v

# Debug test
pytest tests/ -v --pdb

# Generate reports
python scripts/analyze_tests.py
python scripts/capture_failures.py
```

### Workflow Commands

```bash
# List workflows
gh workflow list

# View runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

---

## 📚 Files Created/Modified

### Created Files
- `TEST_CI_CD_CONTEXT.md` - Comprehensive context guide
- `IMPLEMENTATION_GUIDE.md` - This file
- `scripts/analyze_tests.py` - Test analysis script
- `scripts/capture_failures.py` - Failure capture script
- `src/core/test_context.py` - Test context management
- `.github/workflows/main-ci.yml` - Main CI/CD workflow
- `.github/workflows/fast-feedback.yml` - Fast feedback workflow

### Modified Files
- `pytest.ini` - Enhanced configuration
- `tests/conftest.py` - New fixtures
- `tests/unit/core/test_documentation_index.py` - New tests
- `tests/unit/core/test_events.py` - New tests
- `tests/unit/physics/test_ubi_physics_engine.py` - New tests
- `tests/unit/services/test_relationship_analyzer.py` - New tests

---

## 🚀 Next Steps

1. **Run local tests** to establish baseline
2. **Analyze test context** to understand current state
3. **Create test files** for new modules
4. **Verify all tests pass** locally
5. **Push to GitHub** to trigger CI/CD
6. **Monitor workflows** to ensure green pipeline
7. **Optimize performance** if needed
8. **Document lessons learned**

---

**Status:** Ready for Implementation
**Last Updated:** November 30, 2025
**Next Action:** Execute Phase 1 - Local Test Infrastructure
