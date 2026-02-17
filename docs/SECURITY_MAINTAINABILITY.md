# Security and Maintainability Best Practices

## Overview

This document outlines security and maintainability best practices for the Agentic System, incorporating patterns from WebdriverIO and industry standards.

## Security Best Practices

### 1. Authentication & Authorization

#### API Key Management

**Store API keys securely:**

```python
# Good: Environment variables
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY not set")

# Bad: Hardcoded
api_key = "sk_live_1234567890"  # Never do this
```

**Rotate API keys regularly:**

```python
# Implement key rotation
class APIKeyManager:
    async def rotate_key(self, user_id: str):
        """Rotate API key for user"""
        old_key = await self.get_key(user_id)
        new_key = await self.generate_key(user_id)
        await self.revoke_key(old_key)
        return new_key
```

#### JWT Token Management

**Use secure JWT configuration:**

```python
# In config.py
security:
  secret_key: "${JWT_SECRET_KEY}"  # From environment
  algorithm: "HS256"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
```

**Validate tokens properly:**

```python
from jose import jwt, JWTError

async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Input Validation & Sanitization

#### Pydantic Validation

**Validate all inputs:**

```python
from pydantic import BaseModel, Field, validator
import html

class CaseCreateRequest(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = Field(None, max_length=255, regex="^[a-zA-Z0-9_-]+$")

    @validator('raw_input')
    def sanitize_input(cls, v):
        # Sanitize HTML
        v = html.escape(v)
        # Remove control characters
        v = ''.join(char for char in v if ord(char) >= 32)
        return v.strip()
```

#### SQL Injection Prevention

**SQLAlchemy automatically prevents SQL injection:**

```python
# Good: Parameterized queries (automatic)
case = await repository.get_case(case_id)  # Safe

# Bad: Raw SQL (never do this)
# query = f"SELECT * FROM cases WHERE id = '{case_id}'"  # Vulnerable
```

#### XSS Prevention

**Sanitize output:**

```python
from markupsafe import Markup, escape

def render_case(case: dict) -> str:
    # Escape user input
    raw_input = escape(case['raw_input'])
    return f"<div>{raw_input}</div>"
```

### 3. Rate Limiting

**Implement rate limiting:**

```python
from application.mothership.dependencies import RateLimited

@router.post("/cases")
async def create_case(
    request: CaseCreateRequest,
    _: RateLimited = Depends(check_rate_limit)
):
    # Rate limited endpoint
    pass
```

**Configure rate limits:**

```python
# In config.py
security:
  rate_limit_enabled: true
  rate_limit_requests: 100  # Per window
  rate_limit_window_seconds: 60
  rate_limit_by_user: true  # Per user, not IP
```

### 4. HTTPS/TLS

**Always use HTTPS in production:**

```python
# In config.py
server:
  ssl_certfile: "/path/to/cert.pem"
  ssl_keyfile: "/path/to/key.pem"
  ssl_ca_certs: "/path/to/ca.pem"
```

**Validate certificates:**

```python
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
```

### 5. CORS Configuration

**Configure CORS properly:**

```python
# In config.py
security:
  cors_origins: ["https://yourdomain.com"]  # Specific origins only
  cors_allow_credentials: true
  cors_allow_methods: ["GET", "POST", "PUT", "DELETE"]
  cors_allow_headers: ["Content-Type", "Authorization", "X-API-Key"]
  cors_max_age: 3600
```

### 6. Secret Management

**Use secrets management services:**

```python
# AWS Secrets Manager
import boto3

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='agentic-secrets')
secrets = json.loads(secret['SecretString'])

# Azure Key Vault
from azure.keyvault.secrets import SecretClient

client = SecretClient(vault_url="https://vault.vault.azure.net/", credential=credential)
secret = client.get_secret("databricks-token")
```

**Never commit secrets:**

```gitignore
# In .gitignore
.env
.env.local
*.pem
*.key
secrets/
```

### 7. Request Size Limits

**Limit request size:**

```python
# In config.py
security:
  max_request_size_bytes: 10485760  # 10MB
```

**Validate file uploads:**

```python
from fastapi import UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile):
    # Check file size
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "File too large")

    # Check file type
    if not file.content_type.startswith("application/json"):
        raise HTTPException(400, "Invalid file type")
```

### 8. Error Handling

**Don't expose internal errors:**

```python
# Good: Generic error messages
try:
    case = await repository.get_case(case_id)
except Exception as e:
    logger.error(f"Error getting case: {e}", exc_info=True)
    if settings.environment == "production":
        raise HTTPException(500, "Internal server error")
    else:
        raise HTTPException(500, str(e))  # Only in dev

# Bad: Always expose errors
except Exception as e:
    raise HTTPException(500, str(e))  # Security risk
```

### 9. Logging Security

**Don't log sensitive data:**

```python
# Good: Sanitize logs
logger.info(
    "Case created",
    extra={
        "case_id": case_id,
        "user_id": hash_user_id(user_id),  # Hash sensitive data
        "category": category
    }
)

# Bad: Log sensitive data
logger.info(f"Case created by {user_id} with token {api_token}")  # Security risk
```

### 10. Database Security

**Use connection encryption:**

```python
# Databricks uses TLS by default
url = "databricks://token:token@hostname:443/default"  # Port 443 = HTTPS
```

**Use parameterized queries:**

```python
# SQLAlchemy does this automatically
case = await repository.get_case(case_id)  # Safe
```

**Limit database permissions:**

```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT SELECT ON agentic_cases TO readonly_user;

-- Create read-write user
CREATE USER readwrite_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON agentic_cases TO readwrite_user;
```

## Maintainability Best Practices

### 1. Code Organization

**Follow layered architecture:**

```
application/mothership/
├── routers/          # API endpoints (thin layer)
├── schemas/          # Request/response models
├── services/         # Business logic
├── repositories/     # Data access layer
└── db/              # Database models
```

**Separate concerns:**

```python
# Router: Handle HTTP
@router.post("/cases")
async def create_case(request: CaseCreateRequest):
    return await case_service.create_case(request)

# Service: Business logic
class CaseService:
    async def create_case(self, request: CaseCreateRequest):
        # Business logic here
        pass

# Repository: Data access
class AgenticRepository:
    async def create_case(self, case_data: dict):
        # Database operations here
        pass
```

### 2. Testing

**Write comprehensive tests:**

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_create_case(client: TestClient):
    response = client.post(
        "/api/v1/agentic/cases",
        json={"raw_input": "Test input"},
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 201
    assert "case_id" in response.json()

def test_create_case_unauthorized(client: TestClient):
    response = client.post(
        "/api/v1/agentic/cases",
        json={"raw_input": "Test input"}
        # No API key
    )
    assert response.status_code == 401
```

**Use test fixtures:**

```python
@pytest.fixture
async def repository():
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        yield AgenticRepository(session)

@pytest.mark.asyncio
async def test_get_case(repository):
    case = await repository.get_case("CASE-001")
    assert case is not None
```

### 3. Configuration Management

**Use environment-based configuration:**

```python
class AgenticSettings(BaseSettings):
    # Environment
    environment: Environment = Environment.DEVELOPMENT

    # Database
    database_url: str
    database_pool_size: int = 10

    # Security
    secret_key: str
    api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

**Validate configuration:**

```python
def validate_config(settings: AgenticSettings):
    """Validate configuration on startup"""
    if settings.environment == "production":
        if not settings.secret_key:
            raise ValueError("SECRET_KEY required in production")
        if len(settings.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
```

### 4. Logging

**Use structured logging:**

```python
import logging
import json

logger = logging.getLogger(__name__)

# Good: Structured logging
logger.info(
    "Case created",
    extra={
        "case_id": case_id,
        "category": category,
        "user_id": hash_user_id(user_id),
        "duration_ms": duration * 1000
    }
)

# Bad: String formatting
logger.info(f"Case {case_id} created")  # Hard to parse
```

**Configure log levels:**

```python
# In config.py
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "json"  # Structured JSON logs
  file: "logs/agentic.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### 5. Monitoring

**Add metrics:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
cases_created = Counter('cases_created_total', 'Total cases created')
case_duration = Histogram('case_processing_duration_seconds', 'Case processing duration')
active_cases = Gauge('active_cases', 'Number of active cases')

@router.post("/cases")
async def create_case(request: CaseCreateRequest):
    start_time = time.perf_counter()
    try:
        result = await process_case(request)
        cases_created.inc()
        active_cases.inc()
        return result
    finally:
        duration = time.perf_counter() - start_time
        case_duration.observe(duration)
```

### 6. Error Handling

**Use custom exceptions:**

```python
from application.mothership.exceptions import MothershipError

class CaseNotFoundError(MothershipError):
    code = "CASE_NOT_FOUND"
    status_code = 404
    message = "Case not found"

class CaseExecutionError(MothershipError):
    code = "CASE_EXECUTION_FAILED"
    status_code = 500
    message = "Case execution failed"
```

**Handle errors consistently:**

```python
@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    try:
        case = await repository.get_case(case_id)
        if not case:
            raise CaseNotFoundError(details={"case_id": case_id})
        return case
    except CaseNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

### 7. Documentation

**Document all endpoints:**

```python
@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="""
    Create a new case through the receptionist workflow.

    The case will be automatically:
    - Categorized
    - Assigned a priority
    - A reference file will be generated
    - Events will be emitted

    **Authentication Required**: API Key or JWT Token
    """,
    responses={
        201: {
            "description": "Case created successfully",
            "model": CaseResponse
        },
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    },
    tags=["agentic"]
)
async def create_case(request: CaseCreateRequest):
    pass
```

### 8. Dependency Injection

**Use FastAPI's dependency injection:**

```python
# Good: Dependency injection
async def get_repository() -> AgenticRepository:
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        yield AgenticRepository(session)

@router.post("/cases")
async def create_case(
    request: CaseCreateRequest,
    repository: AgenticRepository = Depends(get_repository)
):
    pass

# Bad: Global variables
repository = AgenticRepository()  # Hard to test, not thread-safe
```

### 9. Async Operations

**Use async for all I/O:**

```python
# Good: Async
async def process_case(case_id: str):
    case = await repository.get_case(case_id)
    result = await execute_case(case)
    await repository.update_case(case_id, result)
    return result

# Bad: Blocking
def process_case(case_id: str):
    case = repository.get_case(case_id)  # Blocks event loop
    result = execute_case(case)  # Blocks
    repository.update_case(case_id, result)  # Blocks
    return result
```

### 10. Health Checks

**Implement health checks:**

```python
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    checks = {
        "status": "healthy",
        "database": await check_database(),
        "event_bus": await check_event_bus(),
        "timestamp": datetime.now().isoformat()
    }

    if not all(checks.values()):
        raise HTTPException(503, "Service unhealthy")

    return checks

async def check_database() -> bool:
    try:
        async with sessionmaker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

## WebdriverIO-Inspired Patterns

### 1. Service Pattern

**Similar to WebdriverIO services:**

```python
class AgenticService:
    """Service for agentic operations"""

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
        if self.repository:
            await self.repository.close()
        if self.event_bus:
            await self.event_bus.close()
```

### 2. Reporter Pattern

**Similar to WebdriverIO reporters:**

```python
class CaseReporter:
    """Report case results to external systems"""

    def __init__(self, config):
        self.config = config
        self.api_token = config.api_token

    async def on_case_completed(self, case: dict):
        """Report case completion"""
        await self.send_to_external_system(case)

    async def send_to_external_system(self, case: dict):
        """Send case data to external system"""
        # Implementation
        pass
```

### 3. Configuration Management

**Similar to WebdriverIO config:**

```python
class AgenticConfig(BaseSettings):
    """Configuration for agentic system"""

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
        env_file_encoding = "utf-8"
```

## References

- **Security**: `docs/SECURITY_MAINTAINABILITY.md` (this file)
- **Database**: `docs/DATABASE_USAGE.md`
- **Server**: `docs/SERVER_SIDE_USAGE.md`
- **WebdriverIO**: https://webdriver.io/docs/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
