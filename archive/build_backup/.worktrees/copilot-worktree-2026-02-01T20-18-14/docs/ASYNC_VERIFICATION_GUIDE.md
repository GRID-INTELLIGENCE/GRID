# 5-Step Verification Guide: `deny_request` Async Function

Follow this checklist to verify the `deny_request` async function works correctly in your project.

---

## Step 1️⃣: Install / Import (≈ 20%)

**Goal**: Ensure the module is importable in the environment where you'll run the test.

**Code**:
```python
# From e:/app/async_boolean.py
import asyncio
from app.async_boolean import deny_request  # ← import the coroutine

# Or if running from tests directory:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
from async_boolean import deny_request
```

**Verify**:
```bash
# 1️⃣ Ensure the file is in your PYTHONPATH
python -c "from app.async_boolean import deny_request; print('✅ Import successful')"
```

---

## Step 2️⃣: Run a Simple Event Loop (≈ 20%)

**Goal**: Execute the coroutine directly with `asyncio.run` to see the raw return value.

**Code**:
```python
import asyncio
from app.async_boolean import deny_request

result = asyncio.run(deny_request())
print("Result:", result)  # Expected output: Result: 0
```

**Verify**:
```bash
# 2️⃣ Run the coroutine directly
python -c "import asyncio; from app.async_boolean import deny_request; print(asyncio.run(deny_request()))"
# → prints 0
```

---

## Step 3️⃣: Add an Assertion (≈ 20%)

**Goal**: Verify the returned value is exactly 0. This catches regressions early.

**Code**:
```python
import asyncio
from app.async_boolean import deny_request

result = asyncio.run(deny_request())
assert result == 0, f"Expected 0, got {result}"
print("✅ Assertion passed – function returns 0")
```

**Verify**:
```bash
# 3️⃣ Run with assertions
python -c "import asyncio; from app.async_boolean import deny_request; result = asyncio.run(deny_request()); assert result == 0; print('✅ Assertion passed – function returns 0')"
```

---

## Step 4️⃣: Write an Async Test (pytest-asyncio) (≈ 20%)

**Goal**: Embed the check in an automated test suite so it runs on every pass.

**Code** (already in `tests/test_async_boolean.py`):
```python
# tests/test_async_boolean.py
import pytest
import asyncio
from app.async_boolean import deny_request

@pytest.mark.asyncio
async def test_deny_request_returns_zero():
    assert await deny_request() == 0
```

**Verify**:
```bash
# 4️⃣ Run the pytest suite from project root
cd e:/
pytest tests/test_async_boolean.py -v
# → should show 1 passed test
```

---

## Step 5️⃣: Integrate into CI / CI-Friendly Runner (≈ 20%)

**Goal**: Add the test file to your CI configuration (e.g., GitHub Actions).

**Configuration** (save to `.github/workflows/async-tests.yml`):
```yaml
# .github/workflows/async-tests.yml
name: Async Function Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-asyncio
      - name: Run async tests
        run: pytest tests/test_async_boolean.py -v
```

**Verify**:
```bash
# 5️⃣ Run the pytest suite locally
pytest -q
# → should show tests passed
```

---

## Quick Reference: Command Checklist

```bash
# From project root (e:/)

# Step 1: Test import
python -c "from app.async_boolean import deny_request; print('✅ Import successful')"

# Step 2: Run coroutine
python -c "import asyncio; from app.async_boolean import deny_request; print('Result:', asyncio.run(deny_request()))"

# Step 3: Run with assertion
python -c "import asyncio; from app.async_boolean import deny_request; result = asyncio.run(deny_request()); assert result == 0; print('✅ Assertion passed')"

# Step 4: Run pytest
pytest tests/test_async_boolean.py -v

# Step 5: Full test suite
pytest -q
```

---

## Project Layout

```
e:/
├── app/
│   ├── async_boolean.py          # ← The deny_request module
│   ├── __init__.py
│   └── ...
├── tests/
│   ├── test_async_boolean.py      # ← Async function tests
│   ├── test_endpoints.py
│   └── __init__.py
├── .github/
│   └── workflows/
│       └── async-tests.yml        # ← CI configuration (optional)
└── ...
```

---

## Expected Results

| Step | Command | Expected Output |
|------|---------|-----------------|
| 1 | Import | `✅ Import successful` |
| 2 | Run coroutine | `Result: 0` |
| 3 | Assertion | `✅ Assertion passed – function returns 0` |
| 4 | pytest | `1 passed` |
| 5 | CI | All checks pass on push/PR |
