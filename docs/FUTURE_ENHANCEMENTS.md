# Future Enhancements for GRID v2.2.0+

This document outlines planned enhancements for the GRID system, including dynamic model loading, validation, logging, and fault tolerance.

## Overview

Current v2.1.0 provides basic GRID_AI_MODEL configuration. Future versions will add:
1. Dynamic model loading (per-request override)
2. Configuration validation at startup
3. Comprehensive structured logging
4. Model aliasing and fallback
5. Performance monitoring

## 1. Dynamic Model Loading (v2.2.0)

### Feature: Per-Request Model Override

**Current Behavior:**
- Model set via `GRID_AI_MODEL` environment variable
- Applied globally to all requests
- Cannot change per-request without restart

**Proposed Enhancement:**
- Allow specifying model in API request context
- Override global configuration on per-request basis
- Useful for A/B testing, gradual rollouts

**Implementation:**

```python
# Updated endpoint signature
@router.post("/grid/analyze")
async def analyze(
    request: AnalyzeRequest,  # data + context
    override_model: Optional[str] = Query(None)
) -> Dict:
    """
    Analyze with optional model override.

    ?override_model=gpt-4-turbo will use that model instead of GRID_AI_MODEL
    """
    engine = GridEngine()

    # Use override or fall back to configured model
    model = override_model or settings.grid.ai_model

    return await engine.process(request.data, {
        **request.context,
        "model": model,  # Pass to engine
        "model_override": override_model is not None
    })
```

**API Usage:**
```bash
# Use default model
curl -X POST http://localhost:8000/grid/analyze \
  -d '{"data": "test", "context": {}}'

# Override with specific model
curl -X POST "http://localhost:8000/grid/analyze?override_model=gpt-4" \
  -d '{"data": "test", "context": {}}'
```

**Tracking:**
- Track which model was used in response
- Monitor override frequency
- Alert if specific model has issues

**Benefits:**
- ✅ A/B testing without restart
- ✅ Gradual migration between models
- ✅ Testing with new models in production
- ✅ Performance comparison

**Timeline:** v2.2.0 (Q2 2025)

## 2. Startup Configuration Validation (v2.2.0)

### Feature: Validate GRID_AI_MODEL on Application Startup

**Current Behavior:**
- Configuration loaded lazily on first use
- Invalid model not caught until first request
- No validation of model format or availability

**Proposed Enhancement:**
- Validate GRID_AI_MODEL format on startup
- Check if model endpoint is reachable
- Fail fast if configuration is invalid
- Log warnings for unusual configurations

**Implementation:**

```python
# New validation module: src/core/config_validator.py
from typing import List
import asyncio
import httpx

class ConfigValidator:
    """Validate GRID configuration on startup."""

    KNOWN_MODELS = {
        "claude-haiku-4.5": {"provider": "anthropic", "max_tokens": 8192},
        "gpt-4": {"provider": "openai", "max_tokens": 8192},
        "gpt-4-turbo": {"provider": "openai", "max_tokens": 128000},
        "llama-2-70b": {"provider": "together", "max_tokens": 4096},
    }

    @classmethod
    def validate_model(cls, model: str) -> bool:
        """Validate GRID_AI_MODEL format and value."""

        # Check for empty
        if not model or len(model.strip()) == 0:
            raise ValueError("GRID_AI_MODEL cannot be empty")

        # Check length
        if len(model) > 256:
            raise ValueError(f"GRID_AI_MODEL too long: {len(model)} > 256")

        # Check for valid characters
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/")
        invalid = set(model) - valid_chars
        if invalid:
            raise ValueError(f"Invalid characters in GRID_AI_MODEL: {invalid}")

        # Log if model is not in known list
        if model not in cls.KNOWN_MODELS and not model.startswith("http"):
            import warnings
            warnings.warn(f"Unknown GRID_AI_MODEL: {model} (not in known models list)")

        return True

    @classmethod
    async def validate_endpoint(cls, model: str) -> bool:
        """Check if custom endpoint is reachable."""
        if not model.startswith("http"):
            return True  # Skip for non-URL models

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(model, timeout=5.0)
                return response.status_code < 500
        except Exception as e:
            import warnings
            warnings.warn(f"Cannot reach GRID_AI_MODEL endpoint: {e}")
            return False

# Usage in main.py
from src.core.config import settings
from src.core.config_validator import ConfigValidator

# Validate on startup
try:
    ConfigValidator.validate_model(settings.grid.ai_model)
    logger.info(f"✓ Configuration validated: GRID_AI_MODEL={settings.grid.ai_model}")
except ValueError as e:
    logger.error(f"✗ Invalid configuration: {e}")
    raise SystemExit(1) from e
```

**Validation Checks:**
- ✅ Not empty
- ✅ Valid characters (a-z, 0-9, -, _, :, /, .)
- ✅ Length < 256 characters
- ✅ Known model or valid URL format
- ✅ Endpoint reachable (for URLs)
- ⚠️ Warn if unknown model

**Error Messages:**
```
✗ GRID_AI_MODEL cannot be empty
✗ GRID_AI_MODEL too long: 512 > 256
✗ Invalid characters in GRID_AI_MODEL: {'@', '!'}
⚠️ Unknown GRID_AI_MODEL: my-custom-model (not in known models list)
⚠️ Cannot reach GRID_AI_MODEL endpoint: Connection refused
```

**Benefits:**
- ✅ Fail fast on configuration errors
- ✅ Clear error messages for debugging
- ✅ No silent failures
- ✅ Production confidence

**Timeline:** v2.2.0 (Q2 2025)

## 3. Comprehensive Structured Logging (v2.2.0+)

### Feature: Structured Logging for Request Tracing

**Current Behavior:**
- Minimal logging
- No structured format
- Hard to trace requests through system

**Proposed Enhancement:**
- Structured JSON logging
- Request tracing across modules
- Performance metrics
- Error tracking with context

**Implementation:**

```python
# New logging module: src/core/logging.py
import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict

class StructuredLogFormatter(logging.Formatter):
    """Format logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "model"):
            log_data["model"] = record.model
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Setup logging in main.py
def setup_logging():
    """Configure structured logging."""
    handler = logging.StreamHandler()
    formatter = StructuredLogFormatter()
    handler.setFormatter(formatter)

    # Configure GRID logger
    grid_logger = logging.getLogger("grid")
    grid_logger.addHandler(handler)
    grid_logger.setLevel(logging.INFO)

    return grid_logger

# Usage in GridEngine
logger = logging.getLogger("grid.engine")

class GridEngine:
    async def process(self, data: Any, context: Dict) -> Dict:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            logger.info(
                "Processing request",
                extra={
                    "request_id": request_id,
                    "model": context.get("model", "unknown"),
                    "data_size": len(str(data))
                }
            )

            result = await self._execute_with_retries(data, context)

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status": "success",
                    "duration_ms": duration_ms
                }
            )

            return result
        except Exception as exc:
            logger.error(
                f"Request failed: {exc}",
                extra={
                    "request_id": request_id,
                    "status": "failed",
                    "duration_ms": int((time.time() - start_time) * 1000)
                },
                exc_info=True
            )
            raise
```

**Log Output Example:**
```json
{"timestamp": "2025-01-15T10:00:00.000Z", "level": "INFO", "logger": "grid.engine", "message": "Processing request", "request_id": "abc123", "model": "claude-haiku-4.5", "data_size": 256}
{"timestamp": "2025-01-15T10:00:00.150Z", "level": "INFO", "logger": "grid.engine", "message": "Request completed", "request_id": "abc123", "status": "success", "duration_ms": 150}
```

**Benefits:**
- ✅ Machine-readable logs
- ✅ Request tracing
- ✅ Performance monitoring
- ✅ Error correlation
- ✅ Integration with log aggregation (ELK, Datadog, etc.)

**Timeline:** v2.2.0+ (Q2-Q3 2025)

## 4. Model Aliasing and Fallback (v2.3.0)

### Feature: Model Aliases and Automatic Fallback

**Current Behavior:**
- Must use exact model name
- No fallback if model unavailable
- Long model names in context

**Proposed Enhancement:**
- Define model aliases
- Automatic fallback chain
- Priority-based model selection

**Implementation:**

```python
# Configuration in src/core/config.py
class ModelAliasSettings(BaseSettings):
    """Model alias and fallback configuration."""

    aliases: Dict[str, str] = Field(
        default={
            "default": "claude-haiku-4.5",
            "fast": "claude-haiku-4.5",
            "powerful": "gpt-4-turbo",
            "cheap": "llama-2-70b",
        },
        description="Model name aliases"
    )

    fallback_chain: List[str] = Field(
        default=[
            "claude-haiku-4.5",
            "gpt-4",
            "llama-2-70b",
        ],
        description="Fallback models if primary unavailable"
    )

    model_config = ConfigDict(env_prefix="GRID_MODEL_")

class GridSettings(BaseSettings):
    # ... existing fields ...
    aliases: ModelAliasSettings = Field(default_factory=ModelAliasSettings)

# Usage
def resolve_model(model_request: str, settings: Settings) -> str:
    """Resolve model request to actual model name."""

    # Check if it's an alias
    if model_request in settings.grid.aliases.aliases:
        return settings.grid.aliases.aliases[model_request]

    # Otherwise use as-is
    return model_request

async def get_available_model(
    preferred: str,
    settings: Settings
) -> str:
    """Get first available model from fallback chain."""

    models_to_try = [preferred] + settings.grid.aliases.fallback_chain

    for model in models_to_try:
        if await is_model_available(model):
            return model

    # Return last resort
    return models_to_try[-1]
```

**Configuration:**
```bash
export GRID_MODEL_ALIASES='{"fast": "claude-haiku-4.5", "powerful": "gpt-4"}'
export GRID_MODEL_FALLBACK_CHAIN='["claude-haiku-4.5", "gpt-4"]'
```

**API Usage:**
```bash
# Use alias
curl -X POST "http://localhost:8000/grid/analyze?model=fast"

# Use with fallback
curl -X POST "http://localhost:8000/grid/analyze?model=powerful&fallback=true"
```

**Benefits:**
- ✅ Shorter, memorable model names
- ✅ Automatic failover
- ✅ Easy model migrations
- ✅ A/B testing with fallback

**Timeline:** v2.3.0 (Q3 2025)

## 5. Performance Monitoring (v2.3.0+)

### Feature: Built-in Metrics and Monitoring

**Metrics to Collect:**
- Response times by endpoint
- Model usage frequency
- Error rates by model
- Retry frequency
- Fear intensity distribution

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
model_requests = Counter(
    "grid_model_requests_total",
    "Total requests by model",
    ["model"]
)

request_duration = Histogram(
    "grid_request_duration_seconds",
    "Request duration by endpoint",
    ["endpoint"]
)

retry_attempts = Histogram(
    "grid_retry_attempts",
    "Retry attempts distribution"
)

fear_intensity = Gauge(
    "grid_fear_intensity_current",
    "Current fear intensity"
)
```

**Benefits:**
- ✅ Real-time monitoring
- ✅ Prometheus integration
- ✅ Identify bottlenecks
- ✅ Track model performance

**Timeline:** v2.3.0+ (Q3 2025)

## Implementation Timeline

| Feature | Version | Timeline | Priority |
|---------|---------|----------|----------|
| Dynamic Model Loading | v2.2.0 | Q2 2025 | High |
| Startup Validation | v2.2.0 | Q2 2025 | High |
| Structured Logging | v2.2.0+ | Q2-Q3 2025 | Medium |
| Model Aliasing | v2.3.0 | Q3 2025 | Medium |
| Performance Monitoring | v2.3.0+ | Q3 2025 | Low |

## Testing Strategy

For each feature:
1. Unit tests for core logic
2. Integration tests for API changes
3. Performance benchmarks
4. Edge case coverage
5. Backwards compatibility verification

## Breaking Changes

None proposed. All enhancements are backward compatible.

## Decision Points

1. **Model Validation**: Should we validate at startup or on-demand?
   - Recommendation: On startup (fail fast)

2. **Logging Format**: JSON or human-readable?
   - Recommendation: Structured JSON (machine-readable, integrates with log aggregation)

3. **Fallback Strategy**: Automatic or manual?
   - Recommendation: Configurable (both options)

## Next Steps

1. Gather team feedback on priorities
2. Create detailed RFC for v2.2.0 features
3. Design API contracts
4. Implement and test
5. Create migration guide for users

## Questions for Review

- Should dynamic model loading support context parameters or just query params?
- Should validation happen on every request or only on startup?
- What metrics are most important for your use case?
- Should model aliasing be global or per-user?
