# GRID Test & CI/CD Context Instruction
## Deterministic Testing & Seamless Pipeline Configuration

**Version:** 1.0
**Date:** November 30, 2025
**Status:** Implementation Guide
**Goal:** Seamless green CI/CD pipeline with all jobs passing, simplified workflow configuration

---

## 📋 Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Test Retrieval & Context](#test-retrieval--context)
3. [Test Suite Update Strategy](#test-suite-update-strategy)
4. [Local Test Execution](#local-test-execution)
5. [Bug Detection & Failure Analysis](#bug-detection--failure-analysis)
6. [CI/CD Deterministic Design](#cicd-deterministic-design)
7. [GitHub Actions Workflow](#github-actions-workflow)
8. [Implementation Checklist](#implementation-checklist)

---

## 🔍 Current State Analysis

### Existing Test Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| **Pytest Config** | ✅ Exists | `Python/pytest.ini` |
| **Conftest (Unit)** | ✅ Exists | `tests/conftest.py` (220 lines) |
| **Conftest (Integration)** | ✅ Exists | `tests/integration/conftest.py` (116 lines) |
| **CI/CD Workflows** | ✅ Exists | `.github/workflows/` (4 files) |
| **Tox Config** | ✅ Exists | `tox.ini` |
| **Test Files** | ✅ Exists | `tests/` directory |

### Existing Workflows

1. **ci.yml** - Main CI/CD pipeline (140 lines)
   - Tests on Python 3.10, 3.11, 3.12
   - Linting, type checking, coverage
   - Runs on push to main/master/develop

2. **testing.yml** - Multi-OS tests (52 lines)
   - Tests on Ubuntu, macOS, Windows
   - Python 3.11, 3.12
   - Codecov integration

3. **core-tests.yml** - Core package tests (34 lines)
   - Triggered on src/core/** changes
   - Python 3.11, 3.12

4. **translator-assistant-tests.yml** - Translator tests (47 lines)
   - Triggered on translator_assistant/** changes
   - Python 3.11, 3.12

### Current Pytest Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

---

## 🎯 Test Retrieval & Context

### Step 1: Retrieve Current Test Results

```bash
# Run all tests with verbose output and capture results
pytest tests/ -v --tb=short --collect-only > test_collection.txt

# Run tests with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html > test_results.txt 2>&1

# Run tests by category
pytest tests/unit/ -v --tb=short > test_results_unit.txt
pytest tests/integration/ -v --tb=short > test_results_integration.txt

# Generate JSON report for analysis
pytest tests/ -v --json-report --json-report-file=test_report.json
```

### Step 2: Analyze Test Context

**Create `scripts/analyze_tests.py`:**

```python
"""Analyze test results and generate context report"""
import json
import subprocess
from pathlib import Path
from collections import defaultdict

def collect_test_metadata():
    """Collect all test metadata"""
    result = subprocess.run(
        ["pytest", "tests/", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )

    test_data = {
        "total_tests": 0,
        "by_category": defaultdict(int),
        "by_module": defaultdict(list),
        "markers": defaultdict(list),
    }

    for line in result.stdout.split('\n'):
        if '::test_' in line:
            test_data["total_tests"] += 1
            module = line.split('::')[0]
            test_data["by_module"][module].append(line)

    return test_data

def run_tests_with_context():
    """Run tests and capture context"""
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "--cov=src", "--cov-report=json"],
        capture_output=True,
        text=True
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def generate_context_report():
    """Generate comprehensive context report"""
    metadata = collect_test_metadata()
    test_results = run_tests_with_context()

    report = {
        "metadata": metadata,
        "results": test_results,
        "status": "PASS" if test_results["returncode"] == 0 else "FAIL",
    }

    # Save report
    with open("test_context_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    report = generate_context_report()
    print(f"Tests: {report['metadata']['total_tests']}")
    print(f"Status: {report['status']}")
```

### Step 3: Document Test Context

**Create `TEST_CONTEXT.json`:**

```json
{
  "test_environment": {
    "python_versions": ["3.10", "3.11", "3.12"],
    "os": ["ubuntu-latest", "macos-latest", "windows-latest"],
    "test_framework": "pytest",
    "coverage_target": 80
  },
  "test_categories": {
    "unit": {
      "path": "tests/unit/",
      "marker": "unit",
      "count": 0,
      "expected_duration": "< 30s"
    },
    "integration": {
      "path": "tests/integration/",
      "marker": "integration",
      "count": 0,
      "expected_duration": "< 60s"
    },
    "slow": {
      "marker": "slow",
      "count": 0,
      "expected_duration": "> 60s"
    }
  },
  "critical_modules": [
    "src/core/",
    "src/services/",
    "src/kernel/",
    "src/physics/"
  ]
}
```

---

## 🔧 Test Suite Update Strategy

### Phase 1: Inventory Existing Tests

**Create `scripts/inventory_tests.sh`:**

```bash
#!/bin/bash

echo "=== TEST INVENTORY ==="
echo ""

echo "Unit Tests:"
find tests/unit -name "test_*.py" -type f | wc -l
echo ""

echo "Integration Tests:"
find tests/integration -name "test_*.py" -type f | wc -l
echo ""

echo "Test Functions:"
grep -r "def test_" tests/ | wc -l
echo ""

echo "Test Classes:"
grep -r "class Test" tests/ | wc -l
echo ""

echo "Markers Used:"
grep -r "@pytest.mark" tests/ | cut -d: -f2 | sort | uniq -c
echo ""

echo "Fixtures:"
grep -r "@pytest.fixture" tests/ | wc -l
```

### Phase 2: Create New Test Files for New Modules

**For Phase 1-8 implementations, create:**

```
tests/unit/core/
├── test_documentation_index.py
├── test_documentation_scanner.py
├── test_events.py
├── test_architecture.py
├── test_input_handler.py
├── test_output_handler.py
└── test_grid_system.py

tests/unit/physics/
├── test_heat_state.py
├── test_credit_system.py
└── test_ubi_physics_engine.py

tests/unit/services/
├── test_relationship_analyzer.py
└── test_visual_theme_analyzer.py

tests/integration/
├── test_event_bus_integration.py
├── test_physics_integration.py
├── test_relationship_integration.py
└── test_visual_integration.py
```

### Phase 3: Update Conftest with New Fixtures

**Enhance `tests/conftest.py`:**

```python
"""Enhanced pytest configuration with deterministic fixtures"""

import pytest
from datetime import datetime
from src.core.documentation_index import DocumentationIndex, Document, DocumentCategory
from src.core.events import EventBus, EventType, ArchitectureLayer
from src.physics.ubi_physics_engine import UBIPhysicsEngine
from src.services.relationship_analyzer import RelationshipAnalyzer
from src.services.visual_theme_analyzer import VisualThemeAnalyzer

# ============================================================================
# DOCUMENTATION FIXTURES
# ============================================================================

@pytest.fixture
def documentation_index():
    """Create a test documentation index"""
    return DocumentationIndex(
        total_documents=10,
        total_lines=1000,
        generated_date=datetime.now().isoformat(),
        documents=[]
    )

@pytest.fixture
def sample_document():
    """Create a sample document"""
    return Document(
        name="test.md",
        category=DocumentCategory.CORE,
        size_bytes=1024,
        lines=50,
        description="Test document",
        key_topics=["test", "example"],
        file_path="docs/test.md"
    )

# ============================================================================
# EVENT BUS FIXTURES
# ============================================================================

@pytest.fixture
def event_bus():
    """Create a test event bus"""
    return EventBus()

@pytest.fixture
def sample_event():
    """Create a sample event"""
    return {
        "event_type": "effort_logged",
        "layer": ArchitectureLayer.WORKFLOW.value,
        "timestamp": datetime.now().isoformat(),
        "payload": {"effort_minutes": 10.0, "difficulty": "normal"}
    }

# ============================================================================
# PHYSICS FIXTURES
# ============================================================================

@pytest.fixture
def physics_engine():
    """Create a test physics engine"""
    return UBIPhysicsEngine()

@pytest.fixture
def physics_engine_with_heat():
    """Create a physics engine with some heat"""
    engine = UBIPhysicsEngine()
    engine.log_effort(effort_minutes=10.0, difficulty="normal")
    return engine

# ============================================================================
# RELATIONSHIP FIXTURES
# ============================================================================

@pytest.fixture
def relationship_analyzer():
    """Create a test relationship analyzer"""
    return RelationshipAnalyzer()

@pytest.fixture
def sample_interaction_history():
    """Create sample interaction history"""
    return [
        {"type": "cooperation"},
        {"type": "cooperation"},
        {"type": "conflict"},
    ]

# ============================================================================
# VISUAL FIXTURES
# ============================================================================

@pytest.fixture
def visual_analyzer():
    """Create a test visual theme analyzer"""
    return VisualThemeAnalyzer()

# ============================================================================
# DETERMINISTIC FIXTURES
# ============================================================================

@pytest.fixture
def deterministic_seed():
    """Set deterministic seed for reproducible tests"""
    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)
    return 42

@pytest.fixture
def test_context(deterministic_seed):
    """Comprehensive test context"""
    return {
        "seed": deterministic_seed,
        "timestamp": datetime.now().isoformat(),
        "environment": "testing",
        "database": "sqlite:///:memory:",
    }
```

### Phase 4: Configure Test Markers

**Update `pytest.ini`:**

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

---

## 🚀 Local Test Execution

### Step 1: Setup Test Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install test dependencies
pip install -e ".[dev,test]"
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist

# Verify installation
pytest --version
```

### Step 2: Run Tests Locally

**Create `scripts/run_tests.sh`:**

```bash
#!/bin/bash

set -e

echo "=========================================="
echo "GRID Test Execution"
echo "=========================================="
echo ""

# Configuration
COVERAGE_THRESHOLD=80
PYTHON_VERSION=$(python --version)

echo "Python Version: $PYTHON_VERSION"
echo "Coverage Threshold: $COVERAGE_THRESHOLD%"
echo ""

# Step 1: Collect tests
echo "Step 1: Collecting tests..."
pytest tests/ --collect-only -q
echo ""

# Step 2: Run unit tests
echo "Step 2: Running unit tests..."
pytest tests/unit/ -v --tb=short -m "not slow" --durations=10
UNIT_RESULT=$?
echo ""

# Step 3: Run integration tests
echo "Step 3: Running integration tests..."
pytest tests/integration/ -v --tb=short -m "not slow" --durations=10
INTEGRATION_RESULT=$?
echo ""

# Step 4: Run with coverage
echo "Step 4: Running all tests with coverage..."
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
COVERAGE_RESULT=$?
echo ""

# Step 5: Check coverage threshold
echo "Step 5: Checking coverage threshold..."
COVERAGE=$(grep -oP 'TOTAL\s+\d+\s+\d+\s+\K\d+' coverage_report.txt || echo "0")
if [ "$COVERAGE" -lt "$COVERAGE_THRESHOLD" ]; then
    echo "❌ Coverage $COVERAGE% is below threshold $COVERAGE_THRESHOLD%"
    exit 1
else
    echo "✅ Coverage $COVERAGE% meets threshold"
fi
echo ""

# Summary
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "Unit Tests: $([ $UNIT_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Integration Tests: $([ $INTEGRATION_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Coverage: $([ $COVERAGE_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo ""

# Exit with failure if any test failed
if [ $UNIT_RESULT -ne 0 ] || [ $INTEGRATION_RESULT -ne 0 ] || [ $COVERAGE_RESULT -ne 0 ]; then
    exit 1
fi

echo "✅ All tests passed!"
exit 0
```

### Step 3: Run Tests with Different Configurations

```bash
# Run only unit tests (fast)
pytest tests/unit/ -v -m "not slow"

# Run only integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/core/test_documentation_index.py -v

# Run specific test function
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -v

# Run tests matching pattern
pytest tests/ -k "documentation" -v

# Run tests with specific marker
pytest tests/ -m "critical" -v

# Run tests in parallel (faster)
pytest tests/ -n auto -v

# Run tests with detailed output
pytest tests/ -vv --tb=long

# Run tests with print statements visible
pytest tests/ -v -s

# Run tests and stop on first failure
pytest tests/ -v -x

# Run tests and show slowest 10
pytest tests/ -v --durations=10

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run tests and generate report
pytest tests/ -v --html=report.html --self-contained-html
```

---

## 🐛 Bug Detection & Failure Analysis

### Step 1: Capture Test Failures

**Create `scripts/capture_failures.py`:**

```python
"""Capture and analyze test failures"""
import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_tests_capture_failures():
    """Run tests and capture failures"""
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "--json-report", "--json-report-file=test_report.json"],
        capture_output=True,
        text=True
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timestamp": datetime.now().isoformat(),
    }

def analyze_failures(test_output):
    """Analyze test failures"""
    failures = []

    for line in test_output["stdout"].split('\n'):
        if 'FAILED' in line:
            failures.append({
                "test": line.split('::')[1] if '::' in line else line,
                "status": "FAILED",
                "timestamp": test_output["timestamp"],
            })

    return failures

def generate_failure_report(failures):
    """Generate failure report"""
    report = {
        "total_failures": len(failures),
        "failures": failures,
        "timestamp": datetime.now().isoformat(),
    }

    # Save report
    Path("test_failures.json").write_text(json.dumps(report, indent=2))

    return report

def main():
    """Main execution"""
    print("Running tests and capturing failures...")
    test_output = run_tests_capture_failures()

    print(f"Test run completed with return code: {test_output['returncode']}")

    failures = analyze_failures(test_output)
    print(f"Found {len(failures)} failures")

    report = generate_failure_report(failures)
    print(f"Failure report saved to test_failures.json")

    # Print failures
    for failure in failures:
        print(f"  - {failure['test']}")

if __name__ == "__main__":
    main()
```

### Step 2: Debug Failed Tests

```bash
# Run failed test with verbose output
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -vv -s

# Run failed test with pdb debugger
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -vv --pdb

# Run failed test and show local variables on failure
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -vv -l

# Run failed test with traceback
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -vv --tb=long

# Run failed test and capture output
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -vv -s > debug_output.txt 2>&1
```

### Step 3: Create Failure Handlers

**Create `tests/conftest.py` additions:**

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test failure details"""
    outcome = yield
    rep = outcome.get_result()

    if rep.failed:
        # Log failure details
        print(f"\n❌ FAILURE: {item.name}")
        print(f"   File: {item.fspath}")
        print(f"   Line: {item.lineno}")
        print(f"   Error: {rep.longrepr}")

        # Save to file
        with open("test_failures.log", "a") as f:
            f.write(f"\n❌ {item.name}\n")
            f.write(f"   {rep.longrepr}\n")

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "flaky: mark test as flaky (may fail intermittently)"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on test name
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
```

---

## 🔄 CI/CD Deterministic Design

### Principle 1: Reproducibility

**Every test run should produce identical results given the same inputs:**

```python
# ✅ GOOD: Deterministic
@pytest.fixture
def deterministic_data():
    return {
        "seed": 42,
        "timestamp": "2025-11-30T00:00:00Z",
        "data": [1, 2, 3, 4, 5]
    }

# ❌ BAD: Non-deterministic
@pytest.fixture
def random_data():
    import random
    return [random.randint(1, 100) for _ in range(5)]
```

### Principle 2: Isolation

**Each test should be independent and not affect others:**

```python
# ✅ GOOD: Isolated
def test_add_document(documentation_index):
    """Test adding a document"""
    initial_count = len(documentation_index.documents)
    # ... test logic ...
    assert len(documentation_index.documents) == initial_count + 1

# ❌ BAD: Dependent on test order
def test_add_document():
    """Test adding a document"""
    global_index.add_document(...)
    assert global_index.count() == 5  # Depends on previous tests
```

### Principle 3: Consistency

**Tests should pass consistently across environments:**

```python
# ✅ GOOD: Environment-agnostic
def test_heat_calculation():
    engine = UBIPhysicsEngine()
    engine.log_effort(10.0, "normal")
    assert engine.heat.current_heat == 20.0  # Same everywhere

# ❌ BAD: Environment-dependent
def test_file_operations():
    with open("/tmp/test.txt", "w") as f:  # Fails on Windows
        f.write("test")
```

### Principle 4: Clarity

**Test failures should clearly indicate what went wrong:**

```python
# ✅ GOOD: Clear assertion messages
def test_polarity_calculation():
    analyzer = RelationshipAnalyzer()
    judgment = analyzer.analyze("A", "B", [{"type": "cooperation"}])
    assert judgment.polarity_score > 0, \
        f"Expected positive polarity, got {judgment.polarity_score}"

# ❌ BAD: Unclear assertion
def test_polarity_calculation():
    analyzer = RelationshipAnalyzer()
    judgment = analyzer.analyze("A", "B", [{"type": "cooperation"}])
    assert judgment.polarity_score > 0
```

### Implementation: Test Context Manager

**Create `src/core/test_context.py`:**

```python
"""Deterministic test context management"""
from contextlib import contextmanager
from datetime import datetime
import random
import numpy as np

class TestContext:
    """Manages deterministic test context"""

    def __init__(self, seed=42):
        self.seed = seed
        self.timestamp = datetime.now().isoformat()
        self.environment = "testing"
        self.database_url = "sqlite:///:memory:"

    def initialize(self):
        """Initialize deterministic environment"""
        random.seed(self.seed)
        np.random.seed(self.seed)

    def get_context(self):
        """Get test context"""
        return {
            "seed": self.seed,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "database_url": self.database_url,
        }

@contextmanager
def deterministic_test_context(seed=42):
    """Context manager for deterministic tests"""
    context = TestContext(seed)
    context.initialize()
    try:
        yield context
    finally:
        # Cleanup
        pass
```

---

## 🔧 GitHub Actions Workflow

### Simplified Main Workflow

**Create `.github/workflows/main.yml`:**

```yaml
name: Main CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: "3.11"
  COVERAGE_THRESHOLD: 80

jobs:
  # ========================================================================
  # LINT & TYPE CHECK
  # ========================================================================
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 mypy black isort

      - name: Lint with flake8
        run: |
          flake8 src tests --count --select=E9,F63,F7,F82 --show-source
          flake8 src tests --count --exit-zero --max-complexity=10

      - name: Type check with mypy
        run: mypy src --ignore-missing-imports
        continue-on-error: true

      - name: Check formatting
        run: |
          black --check src tests
          isort --check-only src tests

  # ========================================================================
  # UNIT TESTS
  # ========================================================================
  unit-tests:
    name: Unit Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --tb=short -m "not slow" \
            --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unit-tests
          fail_ci_if_error: false

  # ========================================================================
  # INTEGRATION TESTS
  # ========================================================================
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v --tb=short \
            --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: integration-tests
          fail_ci_if_error: false

  # ========================================================================
  # COVERAGE CHECK
  # ========================================================================
  coverage:
    name: Coverage Check
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Run all tests with coverage
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD }}

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: coverage
          fail_ci_if_error: true

  # ========================================================================
  # CRITICAL PATH TESTS
  # ========================================================================
  critical-tests:
    name: Critical Path Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Run critical tests
        run: |
          pytest tests/ -v -m "critical" --tb=short

  # ========================================================================
  # SUMMARY
  # ========================================================================
  summary:
    name: Test Summary
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, coverage, critical-tests]
    if: always()

    steps:
      - name: Check job statuses
        run: |
          if [ "${{ needs.lint.result }}" = "failure" ]; then
            echo "❌ Lint failed"
            exit 1
          fi
          if [ "${{ needs.unit-tests.result }}" = "failure" ]; then
            echo "❌ Unit tests failed"
            exit 1
          fi
          if [ "${{ needs.integration-tests.result }}" = "failure" ]; then
            echo "❌ Integration tests failed"
            exit 1
          fi
          if [ "${{ needs.coverage.result }}" = "failure" ]; then
            echo "❌ Coverage check failed"
            exit 1
          fi
          if [ "${{ needs.critical-tests.result }}" = "failure" ]; then
            echo "❌ Critical tests failed"
            exit 1
          fi
          echo "✅ All checks passed!"
```

### Fast Feedback Workflow

**Create `.github/workflows/fast-feedback.yml`:**

```yaml
name: Fast Feedback (PR)

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  fast-check:
    name: Quick Check
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,test]"

      - name: Quick lint
        run: flake8 src tests --count --select=E9,F63,F7,F82

      - name: Quick unit tests
        run: pytest tests/unit/ -v -x --tb=short -m "not slow"
```

---

## 📋 Implementation Checklist

### Phase 1: Local Test Infrastructure

- [ ] Create `scripts/analyze_tests.py`
- [ ] Create `scripts/run_tests.sh`
- [ ] Create `scripts/capture_failures.py`
- [ ] Create `scripts/inventory_tests.sh`
- [ ] Update `pytest.ini` with new markers
- [ ] Update `tests/conftest.py` with new fixtures
- [ ] Create `src/core/test_context.py`
- [ ] Run `pytest tests/ --collect-only` to verify setup
- [ ] Run `pytest tests/unit/ -v` to verify unit tests
- [ ] Run `pytest tests/integration/ -v` to verify integration tests

### Phase 2: Test Suite Creation

- [ ] Create `tests/unit/core/test_documentation_index.py`
- [ ] Create `tests/unit/core/test_documentation_scanner.py`
- [ ] Create `tests/unit/core/test_events.py`
- [ ] Create `tests/unit/core/test_architecture.py`
- [ ] Create `tests/unit/core/test_input_handler.py`
- [ ] Create `tests/unit/core/test_output_handler.py`
- [ ] Create `tests/unit/core/test_grid_system.py`
- [ ] Create `tests/unit/physics/test_heat_state.py`
- [ ] Create `tests/unit/physics/test_credit_system.py`
- [ ] Create `tests/unit/physics/test_ubi_physics_engine.py`
- [ ] Create `tests/unit/services/test_relationship_analyzer.py`
- [ ] Create `tests/unit/services/test_visual_theme_analyzer.py`
- [ ] Create `tests/integration/test_event_bus_integration.py`
- [ ] Create `tests/integration/test_physics_integration.py`
- [ ] Create `tests/integration/test_relationship_integration.py`
- [ ] Create `tests/integration/test_visual_integration.py`

### Phase 3: Local Test Execution

- [ ] Run all unit tests: `pytest tests/unit/ -v`
- [ ] Run all integration tests: `pytest tests/integration/ -v`
- [ ] Run with coverage: `pytest tests/ --cov=src --cov-report=html`
- [ ] Verify coverage >= 80%
- [ ] Run critical tests: `pytest tests/ -m critical -v`
- [ ] Document any failures in `TEST_FAILURES.md`

### Phase 4: Bug Detection & Analysis

- [ ] Run `scripts/capture_failures.py` to identify failures
- [ ] Debug each failure using pytest debugging tools
- [ ] Create regression tests for bugs found
- [ ] Document bug fixes in `BUG_FIXES.md`
- [ ] Verify all tests pass locally

### Phase 5: CI/CD Configuration

- [ ] Create `.github/workflows/main.yml`
- [ ] Create `.github/workflows/fast-feedback.yml`
- [ ] Update `.github/workflows/core-tests.yml` if needed
- [ ] Update `.github/workflows/translator-assistant-tests.yml` if needed
- [ ] Test workflows locally using `act` tool
- [ ] Push to GitHub and verify workflows run

### Phase 6: Verification & Optimization

- [ ] Verify all GitHub Actions workflows pass
- [ ] Check coverage reports on Codecov
- [ ] Optimize slow tests (target < 1 second per test)
- [ ] Parallelize tests using pytest-xdist
- [ ] Document test execution times
- [ ] Create performance baseline

### Phase 7: Documentation

- [ ] Create `TESTING.md` with testing guidelines
- [ ] Create `CI_CD.md` with workflow documentation
- [ ] Create `DEBUGGING.md` with debugging guide
- [ ] Update `README.md` with test commands
- [ ] Create `TEST_CONTEXT.md` with context information

### Phase 8: Continuous Improvement

- [ ] Monitor CI/CD pipeline health
- [ ] Track test execution times
- [ ] Identify and fix flaky tests
- [ ] Improve coverage for untested code
- [ ] Optimize workflow performance
- [ ] Document lessons learned

---

## 🎯 Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| **All tests pass locally** | 100% | ⏳ |
| **All tests pass in CI/CD** | 100% | ⏳ |
| **Code coverage** | >= 80% | ⏳ |
| **Test execution time** | < 5 minutes | ⏳ |
| **Workflow simplicity** | Single main.yml | ⏳ |
| **Green CI/CD on push** | 100% | ⏳ |
| **No flaky tests** | 0% flakiness | ⏳ |
| **Clear failure messages** | All failures documented | ⏳ |

---

## 📞 Quick Reference

### Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/unit/core/test_documentation_index.py::test_count_by_category -v

# Run with debugging
pytest tests/ -v --pdb

# Run in parallel
pytest tests/ -n auto -v

# Run and stop on first failure
pytest tests/ -v -x

# Generate HTML report
pytest tests/ -v --html=report.html --self-contained-html
```

### Workflow Status

```bash
# Check workflow status
gh workflow list

# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# View run logs
gh run view <run-id> --log
```

---

## 📚 References

- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Status:** ✅ Ready for Implementation
**Last Updated:** November 30, 2025
**Next Step:** Execute Phase 1 - Local Test Infrastructure
