# Server-Side Usage Guide - Agentic System

## Overview

This guide covers server-side usage of the Agentic System, including API endpoints, security best practices, and maintainability patterns based on WebdriverIO and industry standards.

## API Endpoints

### Base URL

```
http://localhost:8080/api/v1/agentic
```

### Authentication

The API supports multiple authentication methods:

1. **API Key** (Header: `X-API-Key`)
2. **JWT Bearer Token** (Header: `Authorization: Bearer <token>`)
3. **Development Mode** (no authentication required)

### Endpoints

#### 1. Create Case

```http
POST /api/v1/agentic/cases
Content-Type: application/json
X-API-Key: your-api-key

{
  "raw_input": "Add contract testing to CI pipeline",
  "user_id": "user123",
  "examples": ["Similar setup in project X"],
  "scenarios": ["Run tests on every PR"]
}
```

**Response:**
```json
{
  "case_id": "CASE-abc123",
  "status": "categorized",
  "category": "testing",
  "priority": "high",
  "confidence": 0.85,
  "reference_file_path": ".case_references/CASE-abc123_reference.json",
  "events": ["case.created", "case.categorized", "case.reference_generated"],
  "created_at": "2025-01-08T10:00:00Z"
}
```

#### 2. Get Case

```http
GET /api/v1/agentic/cases/{case_id}
X-API-Key: your-api-key
```

#### 3. Enrich Case

```http
POST /api/v1/agentic/cases/{case_id}/enrich
Content-Type: application/json
X-API-Key: your-api-key

{
  "additional_context": "We use GitHub Actions",
  "examples": ["See .github/workflows/test.yml"],
  "scenarios": ["Tests run on push and PR"]
}
```

#### 4. Execute Case

```http
POST /api/v1/agentic/cases/{case_id}/execute
Content-Type: application/json
X-API-Key: your-api-key

{
  "agent_role": "Executor",
  "task": "/execute",
  "force": false
}
```

#### 5. Get Reference File

```http
GET /api/v1/agentic/cases/{case_id}/reference
X-API-Key: your-api-key
```

#### 6. Get Agent Experience

```http
GET /api/v1/agentic/experience
X-API-Key: your-api-key
```

## Security Best Practices

### 1. Authentication & Authorization

**Always authenticate requests:**

```python
# Good: Require authentication
@router.post("/cases")
async def create_case(
    request: CaseCreateRequest,
    auth: Auth = Depends(require_authentication)
):
    # Only authenticated users can create cases
    pass

# Bad: No authentication
@router.post("/cases")
async def create_case(request: CaseCreateRequest):
    # Anyone can create cases - security risk
    pass
```

**Use role-based access control:**

```python
# Require specific permissions
@router.post("/cases/{case_id}/execute")
async def execute_case(
    case_id: str,
    auth: AdminAuth = Depends(require_admin)  # Only admins
):
    pass
```

### 2. Input Validation

**Validate all inputs using Pydantic:**

```python
from pydantic import BaseModel, Field, validator

class CaseCreateRequest(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = Field(None, max_length=255)
    examples: Optional[List[str]] = Field(default_factory=list, max_items=10)

    @validator('raw_input')
    def validate_input(cls, v):
        # Custom validation
        if not v.strip():
            raise ValueError("Input cannot be empty")
        # Sanitize input
        return v.strip()

    @validator('examples')
    def validate_examples(cls, v):
        # Limit example length
        for example in v:
            if len(example) > 1000:
                raise ValueError("Example too long")
        return v
```

### 3. Rate Limiting

**Implement rate limiting to prevent abuse:**

```python
from application.mothership.dependencies import RateLimited

@router.post("/cases")
async def create_case(
    request: CaseCreateRequest,
    _: RateLimited = Depends(check_rate_limit)  # Rate limited
):
    pass
```

**Configure rate limits:**

```python
# In config.py
security:
  rate_limit_enabled: true
  rate_limit_requests: 100  # Requests per window
  rate_limit_window_seconds: 60  # 1 minute window
```

### 4. HTTPS/TLS

**Always use HTTPS in production:**

```python
# In config.py
server:
  host: "0.0.0.0"
  port: 443  # HTTPS port
  ssl_certfile: "/path/to/cert.pem"
  ssl_keyfile: "/path/to/key.pem"
```

### 5. CORS Configuration

**Configure CORS properly:**

```python
# In config.py
security:
  cors_origins: ["https://yourdomain.com"]  # Specific origins
  cors_allow_credentials: true
  cors_allow_methods: ["GET", "POST", "PUT", "DELETE"]
  cors_allow_headers: ["Content-Type", "Authorization", "X-API-Key"]
```

### 6. Secret Management

**Never expose secrets in code:**

```python
# Good: Environment variables
api_token = os.getenv("DATABRICKS_ACCESS_TOKEN")
if not api_token:
    raise ValueError("DATABRICKS_ACCESS_TOKEN not set")

# Bad: Hardcoded secrets
api_token = "YOUR_TOKEN_HERE"  # Never do this
```

**Use secrets management:**

```python
# Use AWS Secrets Manager, Azure Key Vault, etc.
import boto3

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='databricks-token')
api_token = secret['SecretString']
```

### 7. Request Size Limits

**Limit request size to prevent DoS:**

```python
# In config.py
security:
  max_request_size_bytes: 10485760  # 10MB limit
```

### 8. SQL Injection Prevention

**SQLAlchemy automatically prevents SQL injection, but be cautious:**

```python
# Good: Parameterized queries (SQLAlchemy default)
case = await repository.get_case(case_id)  # Safe

# Bad: Raw SQL with string formatting
# result = await session.execute(f"SELECT * FROM cases WHERE id = '{case_id}'")
```

### 9. XSS Prevention

**Sanitize user input:**

```python
import html

def sanitize_input(text: str) -> str:
    # Escape HTML entities
    return html.escape(text)
```

### 10. Error Handling

**Don't expose internal errors:**

```python
# Good: Generic error messages
try:
    case = await repository.get_case(case_id)
except Exception as e:
    logger.error(f"Error getting case: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"  # Generic message
    )

# Bad: Expose internal errors
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=str(e)  # Exposes internal details
    )
```

## Maintainability Best Practices

### 1. Code Organization

**Follow the layered architecture:**

```
application/mothership/
├── routers/          # API endpoints
├── schemas/          # Request/response models
├── repositories/     # Data access layer
├── services/         # Business logic
└── db/              # Database models
```

### 2. Error Handling

**Use consistent error handling:**

```python
from application.mothership.exceptions import MothershipError

class CaseNotFoundError(MothershipError):
    code = "CASE_NOT_FOUND"
    status_code = 404
    message = "Case not found"

# Use in endpoints
@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    case = await repository.get_case(case_id)
    if not case:
        raise CaseNotFoundError(details={"case_id": case_id})
    return case
```

### 3. Logging

**Use structured logging:**

```python
import logging

logger = logging.getLogger(__name__)

# Good: Structured logging
logger.info(
    "Case created",
    extra={
        "case_id": case_id,
        "category": category,
        "user_id": user_id
    }
)

# Bad: String formatting
logger.info(f"Case {case_id} created by {user_id}")
```

### 4. Testing

**Write comprehensive tests:**

```python
import pytest
from fastapi.testclient import TestClient

def test_create_case(client: TestClient):
    response = client.post(
        "/api/v1/agentic/cases",
        json={"raw_input": "Test input"},
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 201
    assert "case_id" in response.json()
```

### 5. Documentation

**Document all endpoints:**

```python
@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="""
    Create a new case through the receptionist workflow.

    The case will be:
    1. Categorized automatically
    2. A reference file will be generated
    3. Events will be emitted

    Returns the case ID and initial status.
    """,
    responses={
        201: {"description": "Case created successfully"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def create_case(request: CaseCreateRequest):
    pass
```

### 6. Configuration Management

**Use environment-based configuration:**

```python
# In config.py
class MothershipSettings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

### 7. Dependency Injection

**Use FastAPI's dependency injection:**

```python
# Good: Dependency injection
@router.post("/cases")
async def create_case(
    request: CaseCreateRequest,
    repository: AgenticRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus)
):
    pass

# Bad: Global variables
repository = AgenticRepository()  # Hard to test
```

### 8. Async Operations

**Use async/await for I/O operations:**

```python
# Good: Async
async def get_case(case_id: str):
    case = await repository.get_case(case_id)
    return case

# Bad: Blocking
def get_case(case_id: str):
    case = repository.get_case(case_id)  # Blocks event loop
    return case
```

### 9. Monitoring

**Add monitoring and metrics:**

```python
import time
from prometheus_client import Counter, Histogram

case_created_counter = Counter('cases_created_total', 'Total cases created')
case_duration_histogram = Histogram('case_processing_duration_seconds', 'Case processing duration')

@router.post("/cases")
async def create_case(request: CaseCreateRequest):
    start_time = time.perf_counter()
    try:
        result = await process_case(request)
        case_created_counter.inc()
        return result
    finally:
        duration = time.perf_counter() - start_time
        case_duration_histogram.observe(duration)
```

### 10. Health Checks

**Implement health check endpoints:**

```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "event_bus": await check_event_bus()
    }
```

## WebdriverIO-Inspired Best Practices

### 1. Configuration Management

**Use environment-based configuration (similar to WebdriverIO):**

```python
# wdio.conf.js equivalent
class AgenticConfig(BaseSettings):
    # Environment
    environment: str = "development"

    # Database
    database_url: str
    database_pool_size: int = 10

    # Event Bus
    redis_host: str = "localhost"
    redis_port: int = 6379
    use_redis: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    class Config:
        env_file = ".env"
```

### 2. Service Integration

**Use service pattern (similar to WebdriverIO services):**

```python
# Similar to @wdio/testingbot-service
class AgenticService:
    def __init__(self, config):
        self.config = config
        self.repository = None
        self.event_bus = None

    async def on_start(self):
        """Initialize service"""
        self.repository = await create_repository()
        self.event_bus = await create_event_bus()

    async def on_stop(self):
        """Cleanup service"""
        await self.repository.close()
        await self.event_bus.close()
```

### 3. Reporter Pattern

**Implement reporters for test results (similar to WebdriverIO reporters):**

```python
# Similar to @testplanit/wdio-reporter
class CaseReporter:
    def __init__(self, config):
        self.config = config
        self.api_token = config.api_token

    async def on_case_completed(self, case):
        """Report case completion"""
        await self.send_to_external_system(case)
```

### 4. Visual Testing

**Implement visual regression testing (similar to SmartUI):**

```python
# Similar to LambdaTest SmartUI
class VisualCaseValidator:
    async def validate_case_output(self, case_id: str):
        """Compare case output with baseline"""
        current = await self.capture_case_output(case_id)
        baseline = await self.get_baseline(case_id)
        diff = await self.compare(current, baseline)
        return diff
```

## Performance Optimization

### 1. Connection Pooling

**Configure connection pools:**

```python
# Similar to WebdriverIO capabilities
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
```

### 2. Async Operations

**Use async for all I/O:**

```python
# All database operations are async
async def process_case(case_id: str):
    case = await repository.get_case(case_id)
    result = await execute_case(case)
    await repository.update_case(case_id, result)
```

### 3. Caching

**Cache frequently accessed data:**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_reference_file(case_id: str):
    return await load_reference_file(case_id)
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**: Increase `pool_timeout` in config
2. **Rate Limit Exceeded**: Adjust rate limit settings
3. **Authentication Failed**: Check API key or JWT token
4. **Database Error**: Check database connectivity and credentials

### Debugging

**Enable debug logging:**

```python
# In config.py
logging:
  level: "DEBUG"
  database_echo: true  # Log SQL queries
```

## References

- **API Router**: `application/mothership/routers/agentic.py`
- **Schemas**: `application/mothership/schemas/agentic.py`
- **Repository**: `application/mothership/repositories/agentic.py`
- **Config**: `application/mothership/config.py`
- **WebdriverIO Docs**: https://webdriver.io/docs/
