# Optional Dependencies

This document describes optional dependencies in GRID and how the system handles their absence.

## Overview

GRID follows a **local-first** philosophy and uses graceful degradation for optional features. If an optional dependency is not installed, the system will:

1. Detect the missing dependency at import time
2. Provide a fallback implementation or disable the feature
3. Log a warning (in development) or fail gracefully (in production)

## Optional Dependencies

### Payment Processing

**Package**: `stripe`

**Location**: `application/mothership/services/payment/stripe_gateway.py`

**Behavior**:
- If `stripe` is not installed, the `StripeGateway` class will raise `ImportError` when instantiated
- Payment endpoints will fail if Stripe is required but not available
- Install with: `pip install stripe`

**CI/CD**: Stripe is listed in `requirements.txt` but CI may skip payment tests if not configured

### Machine Learning (Clustering)

**Package**: `scikit-learn` (imported as `sklearn`)

**Location**: `src/grid/analysis/clustering.py`

**Behavior**:
- Used for DBSCAN clustering in pattern recognition
- If not installed, clustering features will fail at runtime
- Test file `tests/unit/test_pattern_engine_dbscan.py` is skipped if sklearn is unavailable
- Install with: `pip install scikit-learn`

**CI/CD**: Tests are skipped with `--ignore=tests/unit/test_pattern_engine_dbscan.py`

### System Monitoring

**Package**: `psutil`

**Location**: `tests/async_stress_harness.py`

**Behavior**:
- Used for memory sampling during stress tests
- If not installed, stress harness runs without memory metrics
- Install with: `pip install psutil`

**CI/CD**: Optional for performance benchmarks

### Redis (Rate Limiting)

**Package**: `redis`

**Location**: `application/mothership/middleware/rate_limit_redis.py`

**Behavior**:
- Used for distributed rate limiting
- If not available, rate limiting falls back to in-memory implementation
- Install with: `pip install redis`

**CI/CD**: Listed in `requirements.txt` but has fallback

### Cognitive Layer Integrations

**Packages**: `ibm-watsonx-ai`, `cupy`, `torch`

**Location**: `light_of_the_seven/light_of_the_seven/src/light_of_the_seven/integration.py`

**Behavior**:
- IBM Watson integration: Optional cloud AI services
- CuPy: GPU acceleration (requires matching CUDA version)
- PyTorch: Deep learning capabilities
- All have graceful degradation with warnings

**CI/CD**: Not required for core functionality

## Handling Missing Dependencies

### Pattern: Try/Except Import

```python
try:
    import stripe
except ImportError:
    stripe = None  # type: ignore[assignment]

# Later in code
if stripe is None:
    raise ImportError("stripe package is required. Install with: pip install stripe")
```

### Pattern: Optional Feature Flag

```python
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

# Later in code
if PSUTIL_AVAILABLE and args.mem_sample_every > 0:
    mem_samples.append(psutil.Process().memory_info().rss)
```

## CI/CD Behavior

The GitHub Actions workflow:

- **Does not fail** if optional dependencies are missing (unless explicitly required by a test)
- **Skips tests** that require optional dependencies (e.g., DBSCAN tests)
- **Uses fallbacks** for features like rate limiting (Redis → in-memory)

## Development Recommendations

1. **For new optional features**: Always use try/except imports
2. **Document fallbacks**: Update this file when adding optional dependencies
3. **Test both paths**: Test with and without optional dependencies
4. **Clear error messages**: Provide installation instructions in error messages

## Required vs Optional

**Required** (in `requirements.txt`):
- `fastapi`, `pydantic`, `numpy`, `httpx` - Core runtime
- `pytest`, `pytest-asyncio` - Testing framework
- `sqlalchemy`, `alembic` - Database layer

**Optional** (graceful degradation):
- `stripe` - Payment processing
- `scikit-learn` - ML clustering
- `psutil` - System monitoring
- `redis` - Distributed rate limiting
- `ibm-watsonx-ai`, `cupy`, `torch` - Cognitive layer integrations
