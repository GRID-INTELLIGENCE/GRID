"""
Migration Guide: APIGuard Integration with GRID

This guide provides step-by-step instructions for migrating GRID's
custom resilience implementations to APIGuard.

## Migration Overview

APIGuard replaces GRID's custom implementations with battle-tested patterns:
- Custom circuit breaker (623 lines) → APIGuard CircuitBreaker
- Redis rate limiting (236 lines) → APIGuard TokenBucket
- Scattered retry logic → APIGuard RetryHandler
- Multiple HTTP clients → Unified AsyncRateLimitedClient

## Phase 1: Dependency and Infrastructure

### 1.1 Add APIGuard Dependency
Already completed in pyproject.toml:
```toml
# API Resilience
"grid-apiguard>=0.1.0",
```

### 1.2 Install Dependencies
```bash
uv sync  # Will install APIGuard
```

## Phase 2: Middleware Replacement

### 2.1 Replace Circuit Breaker Middleware

**Current Implementation:**
```python
# src/application/mothership/middleware/circuit_breaker.py (623 lines)
from application.mothership.middleware.circuit_breaker import CircuitBreakerMiddleware
app.add_middleware(CircuitBreakerMiddleware, failure_threshold=5, recovery_timeout=30)
```

**APIGuard Implementation:**
```python
# New: Use APIGuard adapter
from application.mothership.middleware.apiguard_adapter import create_circuit_breaker_middleware

app.add_middleware(create_circuit_breaker_middleware(
    failure_threshold=5,
    recovery_timeout=30.0,
    cognitive_adjustment=True,  # GRID-specific feature
))
```

### 2.2 Replace Rate Limiting Middleware

**Current Implementation:**
```python
# src/application/mothership/middleware/rate_limit_redis.py (236 lines)
from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware
app.add_middleware(CognitiveRedisRateLimitMiddleware)
```

**APIGuard Implementation:**
```python
# New: Use APIGuard adapter
from application.mothership.middleware.apiguard_adapter import create_rate_limit_middleware

app.add_middleware(create_rate_limit_middleware(
    default_capacity=60,
    per_user=True,  # GRID-specific feature
))
```

## Phase 3: HTTP Client Migration

### 3.1 Replace httpx Usage in Routers

**Current Pattern:**
```python
# In various routers
import httpx

async def some_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://external-api.com/data")
    return response.json()
```

**APIGuard Pattern:**
```python
# New: Use resilient client
from application.mothership.middleware.apiguard_adapter import create_resilient_client

async def some_endpoint():
    async with create_resilient_client("external_api") as client:
        response = await client.get("https://external-api.com/data")
    return response.json()
```

### 3.2 Service-Specific Configurations

**RAG System (Conservative):**
```python
rag_client = create_resilient_client("rag")
# - 20 requests/minute capacity
# - 2.0 refill rate
# - 3 failure threshold
# - 60s recovery timeout
```

**Database Operations (High Throughput):**
```python
db_client = create_resilient_client("database")
# - 200 requests/minute capacity
# - 20.0 refill rate
# - 5 failure threshold
# - 15s recovery timeout
```

**External APIs (Balanced):**
```python
external_client = create_resilient_client("external_api")
# - 50 requests/minute capacity
# - 5.0 refill rate
# - 3 failure threshold
# - 120s recovery timeout
```

## Phase 4: Authentication Integration

### 4.1 Per-User Rate Limiting

**Current JWT Processing:**
```python
# In auth middleware
user_id = decode_jwt(token)
```

**APIGuard Integration:**
```python
# Automatic in APIGuardRateLimitMiddleware
# Uses JWT token hash or IP as bucket key
registry = BucketRegistry(default_capacity=100, default_refill_rate=10.0)
user_bucket = registry.get_bucket(user_id)
```

### 4.2 API Key Management

**New Pattern:**
```python
# Per-API-key rate limiting
api_key_registry = BucketRegistry(default_capacity=1000, default_refill_rate=100.0)
api_bucket = api_key_registry.get_bucket(api_key_hash)
```

## Phase 5: Testing Migration

### 5.1 Update Test Patterns

**Current Test Pattern:**
```python
# Mock custom circuit breaker
with patch('application.mothership.middleware.circuit_breaker.CircuitBreakerMiddleware'):
    response = client.get("/test")
```

**APIGuard Test Pattern:**
```python
# Mock APIGuard patterns
with patch('apiguard.CircuitBreaker'):
    response = client.get("/test")
```

### 5.2 Integration Test Coverage

Run the new test suite:
```bash
uv run pytest tests/integration/test_apiguard_integration.py -v
```

## Phase 6: Configuration and Tuning

### 6.1 Environment Variables

Add to `.env`:
```env
# APIGuard Configuration
APIGUARD_CIRCUIT_FAILURE_THRESHOLD=5
APIGUARD_CIRCUIT_RECOVERY_TIMEOUT=30
APIGUARD_RATE_LIMIT_CAPACITY=60
APIGUARD_RATE_LIMIT_REFILL_RATE=1.0
APIGUARD_RETRY_MAX_RETRIES=3
APIGUARD_RETRY_BASE_DELAY=1.0
```

### 6.2 Cognitive Load Integration

**GRID-Specific Feature:**
```python
# In APIGuardCircuitBreakerMiddleware
if cognitive_load > 0.8:  # High load
    # Reduce rate limits by 30%
    multiplier = 0.7
elif cognitive_load > 0.6:  # Medium load
    # Normal limits
    multiplier = 1.0
else:  # Low load
    # Increase limits by 50%
    multiplier = 1.5
```

## Phase 7: Monitoring and Observability

### 7.1 Structured Logging

APIGuard automatically integrates with GRID's logging:
```python
# Automatic structured logging
logger.info("circuit_state_changed", 
           state="OPEN", 
           failure_count=5,
           service="external-api")
```

### 7.2 Metrics Integration

Add to Prometheus metrics:
```python
# Circuit breaker state
circuit_breaker_state = prometheus_client.Gauge(
    'apiguard_circuit_breaker_state',
    'Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)',
    ['service', 'endpoint']
)

# Rate limit utilization
rate_limit_utilization = prometheus_client.Gauge(
    'apiguard_rate_limit_utilization',
    'Rate limit bucket utilization',
    ['user_id', 'endpoint']
)
```

## Phase 8: Rollout Strategy

### 8.1 Canary Deployment

1. **Deploy to staging environment**
2. **Run integration tests**
3. **Monitor metrics for 1 hour**
4. **Deploy to production with feature flag**

### 8.2 Feature Flag Implementation

```python
# In main application
import os
USE_APIGUARD = os.getenv("USE_APIGUARD", "false").lower() == "true"

if USE_APIGUARD:
    from application.mothership.middleware.apiguard_adapter import (
        create_circuit_breaker_middleware,
        create_rate_limit_middleware,
    )
    app.add_middleware(create_circuit_breaker_middleware())
    app.add_middleware(create_rate_limit_middleware())
else:
    # Use existing middleware
    from application.mothership.middleware.circuit_breaker import CircuitBreakerMiddleware
    from application.mothership.middleware.rate_limit_redis import CognitiveRedisRateLimitMiddleware
    app.add_middleware(CircuitBreakerMiddleware)
    app.add_middleware(CognitiveRedisRateLimitMiddleware)
```

## Phase 9: Cleanup

### 9.1 Remove Old Implementations

After successful migration:
```bash
# Remove old middleware files
git rm src/application/mothership/middleware/circuit_breaker.py
git rm src/application/mothership/middleware/rate_limit_redis.py

# Remove old tests
git rm tests/unit/test_circuit_breaker_middleware.py
git rm tests/unit/test_rate_limit_redis_middleware.py
```

### 9.2 Update Documentation

Update `docs/ARCHITECTURE.md`:
```markdown
## Resilience Patterns

GRID uses APIGuard for production-grade resilience:
- **Circuit Breaking**: Prevents cascading failures
- **Rate Limiting**: Token bucket with per-user tracking
- **Retry Logic**: Exponential backoff with jitter
- **HTTP Clients**: Unified resilient client pattern
```

## Verification Checklist

- [ ] APIGuard dependency installed
- [ ] Circuit breaker middleware replaced
- [ ] Rate limiting middleware replaced
- [ ] HTTP clients migrated to APIGuard
- [ ] Tests updated and passing
- [ ] Configuration tuned for GRID
- [ ] Monitoring integrated
- [ ] Feature flag implemented
- [ ] Canary deployment successful
- [ ] Old code removed
- [ ] Documentation updated

## Expected Benefits

- **750+ lines** of custom code removed
- **Standardized** resilience patterns
- **Better observability** with structured logging
- **Improved reliability** with battle-tested patterns
- **Easier testing** with mock-friendly interfaces
- **Consistent behavior** across all services

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure APIGuard is installed with `uv sync`
2. **Circuit Not Opening**: Check failure threshold configuration
3. **Rate Limiting Too Strict**: Adjust bucket capacity/refill rate
4. **Performance Impact**: Monitor middleware overhead

### Debug Commands

```bash
# Check APIGuard installation
uv run python -c "import apiguard; print(apiguard.__version__)"

# Run integration tests
uv run pytest tests/integration/test_apiguard_integration.py -v

# Check middleware order
uv run python -c "from fastapi import FastAPI; app = FastAPI(); print(app.middleware_stack)"
```

## Support

For issues during migration:
1. Check APIGuard documentation: `c:\Users\USER\CascadeProjects\apiguard\README.md`
2. Run tests: `uv run pytest tests/integration/test_apiguard_integration.py`
3. Monitor logs for structured APIGuard events
4. Create rollback plan with feature flags
