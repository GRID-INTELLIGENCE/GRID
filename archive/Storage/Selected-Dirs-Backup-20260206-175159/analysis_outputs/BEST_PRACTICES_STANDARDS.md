# Stratagem Intelligence Studio - Best Practices & Industry Standards

**Document Version:** 1.0  
**Date:** 2026-01-23  
**Status:** Production-Ready

---

## Table of Contents

1. [Architecture & Design Principles](#architecture--design-principles)
2. [Code Quality Standards](#code-quality-standards)
3. [Security & AI Safety Best Practices](#security--ai-safety-best-practices)
4. [Testing & Quality Assurance](#testing--quality-assurance)
5. [Deployment & Operations](#deployment--operations)
6. [Performance & Monitoring](#performance--monitoring)
7. [Documentation & Communication](#documentation--communication)

---

## Architecture & Design Principles

### 1. Apps-as-Harness Orchestration Pattern

**Principle:** The Apps repository serves as the central intelligence harness that coordinates all specialized subsystems (grid, EUFLE, pipeline) through normalized ProjectGraph schema.

**Implementation Standards:**

```python
# ✅ GOOD: Service layer exports functions, not classes
from services.harness_service import harvest_all_repos

# ❌ BAD: Importing classes from services
from services.harness_service import HarnessService
harness = HarnessService()  # Don't instantiate

# ✅ GOOD: Clean async/await pattern
async def harvest_codebase_in_run(run_id: str, repo_name: str) -> Optional[ProjectGraphBase]:
    """Orchestrates tiered harvest (Tier 1 → 2 → 3)"""
    graph = await harvest_codebase(repo_name, repo_path, run_id)
    return normalize_codebase_in_run(run_id, repo_name)

# ✅ GOOD: Error handling with context
from grid.tracing import get_trace_manager, TraceOrigin

trace_mgr = get_trace_manager()
with trace_mgr.trace_action(origin=TraceOrigin.SAFETY_ANALYSIS):
    # Safety-sensitive operations
    pass
```

**Enforcement:**
- All routers in `backend/routers/` must import from `backend/services/`
- Services must be stateless functions, not singleton classes
- Every critical operation must use grid tracing system
- Run-based artifacts stored with immutable run_id (format: `YYYYMMDD-HHMMSSZ_<uuid8>`)

---

### 2. Tiered Artifact Harvesting Architecture

**Tier 1: Fast Path** - Load existing artifacts from `analysis_outputs/`
- **Speed:** < 1 second
- **Reliability:** 100% (assume artifacts are valid)
- **Use case:** Frequent re-runs within 24 hours

**Tier 2: Deep Path** - Trigger `analyze_repo.py` for fresh analysis
- **Speed:** 5-20 minutes (depends on repo size)
- **Reliability:** ~95% (can fail due to timeouts, dependencies)
- **Use case:** Initial analysis, refresh after code changes
- **Async execution:** Returns job_id for polling

**Tier 3: Fallback Path** - Lightweight collection of READMEs, configs, entrypoints
- **Speed:** < 5 seconds
- **Reliability:** 99% (minimal I/O)
- **Use case:** When Tier 1/2 fail

**Implementation Standards:**

```python
# ✅ GOOD: Check refresh threshold before deciding tier
should_refresh = should_refresh_artifacts(repo_path, artifact_path)

if not should_refresh:
    # Use Tier 1 (fast)
    result = await harvest_codebase_tier1(repo_name, artifact_path, run_id)
else:
    # Attempt Tier 2 (deep), fallback to Tier 3 (safe)
    result = await harvest_codebase_tier2(repo_name, repo_path, run_id)
    if result["status"] == "failed":
        result = await harvest_codebase_tier3(repo_name, repo_path, run_id)

# ✅ GOOD: Store immutable run snapshot
create_artifact_manifest(run_id, repo_name, artifact_manifest)
```

**Enforcement:**
- 24-hour refresh threshold is non-negotiable
- Tier 3 artifacts marked as "degraded" in manifest
- All runs archived with timestamps
- Artifact compression enforced for files > 1MB

---

### 3. Modular Service Layer Pattern

**Structure:**

```
backend/
├── routers/
│   ├── harness.py       # POST /api/harness/*
│   ├── payments.py      # POST /api/payment/*
│   ├── agents.py        # POST /api/agents/*
│   └── ...
├── services/
│   ├── harness_service.py           # Orchestration logic
│   ├── normalization_service.py     # Schema conversion
│   ├── ai_safety_analyzer.py        # Safety scanning
│   ├── config_service.py            # Configuration management
│   └── ...
└── models/
    ├── database.py                  # SQLAlchemy ORM models
    └── ...
```

**Import Pattern:**

```python
# ✅ GOOD: Router imports specific functions from service
from services.harness_service import harvest_codebase, harvest_all_repos

@app.post("/api/harness/run")
async def create_harness_run(request: HarnessRequest) -> Dict:
    result = await harvest_all_repos(run_id, refresh=request.refresh)
    return result

# ❌ BAD: Importing entire module or service class
from services import harness_service
result = harness_service.HarnessService().run()  # Don't do this
```

**Enforcement:**
- Each service file exports public functions only
- Service functions are stateless and reusable
- Configuration accessed via `get_config_service()` singleton
- Database sessions managed via dependency injection (FastAPI)

---

## Code Quality Standards

### 1. Type Safety & Pydantic v2 Compliance

**Standard:**
- All models inherit from `pydantic.BaseModel`
- All function parameters and returns have type hints
- Pydantic v2 field definition syntax required

**Pydantic v2 Migration Checklist:**

```python
# ✅ GOOD: Pydantic v2 syntax
from pydantic import BaseModel, Field, field_validator

class ProjectGraphRequest(BaseModel):
    repo_name: str = Field(..., min_length=1, description="Repository name")
    refresh: bool = Field(default=False, description="Force refresh")
    
    @field_validator('repo_name')
    @classmethod
    def validate_repo_name(cls, v):
        if not v.isalnum():
            raise ValueError("Repo name must be alphanumeric")
        return v

# ❌ BAD: Old Pydantic v1 syntax
class ProjectGraphRequest(BaseModel):
    repo_name: str = Field(..., alias="repoName")  # alias deprecated
    
    class Config:  # Config class deprecated; use model_config
        allow_population_by_field_name = True
    
    @validator('repo_name')  # validator decorator deprecated
    def validate_repo_name(cls, v):
        return v
```

**Enforcement:**
- Pyright strict mode enabled (see `pyrightconfig.json`)
- Target: < 50 type errors across all repos
- All optional types must have null guards:

```python
# ✅ GOOD: Safe optional access
if user_data and user_data.get("email"):
    send_email(user_data["email"])

# ✅ GOOD: Type assertion
user_email = user_data.email if user_data else None
if user_email is not None:
    send_email(user_email)

# ❌ BAD: Unguarded optional access
send_email(user_data.email)  # Crashes if user_data is None
```

---

### 2. Async/Await Standards

**Principle:** All I/O operations must be asynchronous; no blocking calls in FastAPI handlers.

**Implementation Standards:**

```python
# ✅ GOOD: Pure async execution
async def process_harness_run(run_id: str) -> Dict:
    # Use asyncio for subprocess
    proc = await asyncio.create_subprocess_exec(
        "python", "analyze_repo.py", run_id
    )
    stdout, stderr = await proc.communicate()
    return json.loads(stdout)

# ✅ GOOD: Async database queries
from sqlalchemy.ext.asyncio import create_async_engine
async with async_session() as session:
    result = await session.execute(select(User).where(User.id == 123))
    user = result.scalar_one_or_none()

# ❌ BAD: Blocking subprocess call
import subprocess
proc = subprocess.run(["python", "analyze_repo.py"])  # Blocks event loop

# ❌ BAD: Synchronous database query in async context
from sqlalchemy import create_engine
session = Session()
user = session.query(User).filter(User.id == 123).first()  # Blocks

# ❌ BAD: Blocking I/O in async context
with open("large_file.json", "r") as f:  # Can block
    data = json.load(f)
```

**Enforcement:**
- All FastAPI routes must use `async def`
- Zero `time.sleep()` calls; use `await asyncio.sleep()`
- Zero `subprocess.run()` calls; use `asyncio.create_subprocess_exec()`
- Database queries only via async ORM (SQLAlchemy 2.0 with asyncpg)

---

### 3. Error Handling & Observability

**Standard:** Every operation must be traceable and errors must include context.

```python
# ✅ GOOD: Error with tracing and context
from grid.tracing import get_trace_manager, TraceOrigin

trace_mgr = get_trace_manager()
try:
    with trace_mgr.trace_action(
        origin=TraceOrigin.SAFETY_ANALYSIS,
        input_data={"repo": repo_name}
    ) as trace:
        result = await analyze_safety(repo_name)
        trace.output_data = {"safety_score": result.prompt_security_score}
        trace.risk_level = result.risk_level
except Exception as e:
    trace.metadata["error"] = str(e)
    # Also send to Sentry
    from sentry_sdk import capture_exception
    capture_exception(e)
    raise HTTPException(status_code=500, detail=f"Safety analysis failed: {str(e)}")

# ❌ BAD: Silent failure
try:
    result = analyze_safety(repo_name)
except:  # Swallows error
    pass

# ❌ BAD: Generic error message
except Exception as e:
    raise HTTPException(status_code=500, detail="Something went wrong")
```

**Enforcement:**
- Grid tracing system used for all critical operations
- Sentry integration active in production
- Error responses include actionable detail
- Warnings logged for degraded/fallback operations

---

## Security & AI Safety Best Practices

### 1. AI Model Usage Declaration

**Standard:** All model providers must be declared and tracked in artifacts.

**Implementation:**

```python
# From ai_safety_analyzer.py - detect all model usage
MODEL_USAGE_DETECTION = {
    "openai": ["openai.", "gpt-", "from openai"],
    "anthropic": ["anthropic.", "claude"],
    "ollama": ["Ollama", "ollama.", "from ollama"],
    "huggingface": ["transformers", "HfApi"],
    "local": ["local.*model", "on.*premise"]
}

# ✅ GOOD: Explicit model provider specification
async def invoke_model(provider: Literal["openai", "anthropic", "ollama"]):
    """Explicitly declare model provider for tracing"""
    trace_mgr.trace_action(
        input_data={"model_provider": provider}
    )
    # ... invoke model
    
# ✅ GOOD: Log model usage for safety audit
AI_MODEL_USAGE = {
    "providers": ["openai", "anthropic"],
    "last_updated": datetime.now(),
    "evidence": [
        {"file": "services/ai_safety_analyzer.py", "pattern": "openai.ChatCompletion"},
        {"file": "backend/routers/agents.py", "pattern": "from anthropic import Anthropic"}
    ]
}
```

**Enforcement:**
- Every model invocation traced with provider name
- Monthly audit of model usage patterns
- Fallback to local/Ollama if cloud provider unavailable
- Cost tracking for cloud models (OpenAI, Anthropic)

---

### 2. Prompt Security & Injection Prevention

**Standard:** All user-provided input to LLMs must be sanitized and templated.

```python
# ✅ GOOD: Template-based prompts with parameter substitution
SAFE_PROMPT_TEMPLATE = """
You are a code analysis assistant.
Analyze the following code and identify safety issues:

CODE:
{code_block}

CONSTRAINTS:
- Output only JSON
- No shell commands
"""

def analyze_code_safely(code_block: str) -> Dict:
    # Sanitize input: remove shell metacharacters
    safe_code = sanitize_input(code_block, allowed_chars=r"[\w\s\{\}\[\]\(\)\n\t\-\+\*/=<>!]")
    
    prompt = SAFE_PROMPT_TEMPLATE.format(code_block=safe_code)
    # Invoke LLM with templated prompt (no injection vector)
    response = await llm_client.create_chat_completion(messages=[
        {"role": "system", "content": "You are a code analysis assistant."},
        {"role": "user", "content": prompt}
    ])
    return json.loads(response.content)

# ❌ BAD: Direct f-string with user input
user_code = request.code  # User-provided
prompt = f"Analyze this code:\n{user_code}"  # INJECTION VECTOR!

# ❌ BAD: String concatenation
prompt = "Analyze this code:\n" + user_code  # Vulnerable
```

**Enforcement:**
- Use only templated prompts for user input
- Sanitize all inputs before LLM invocation
- Validate LLM output schema before using
- Implement output filtering for sensitive content

---

### 3. Data Privacy & PII Handling

**Standard:** PII must be redacted, encrypted, and audited.

```python
# ✅ GOOD: PII detection and redaction
from services.pii_redactor import redact_pii

def process_user_data(data: Dict) -> Dict:
    # Detect and redact PII before storage/logging
    redacted = redact_pii(data, fields=["email", "phone", "ssn"])
    
    # Store with encryption
    encrypted = encrypt_sensitive_fields(redacted, key=get_encryption_key())
    
    # Audit trail
    log_data_access(user_id, "process_user_data", timestamp=now())
    
    return encrypted

# ✅ GOOD: Privacy-aware logging
logger.info(
    "User created",
    extra={
        "user_id": user.id,  # OK to log
        "email": "[REDACTED]",  # Never log plain email
        "phone": "[REDACTED]"  # Never log plain phone
    }
)

# ❌ BAD: Logging PII in plain text
logger.info(f"User {user.email} created with phone {user.phone}")

# ❌ BAD: Storing PII unencrypted
user_data = {"email": user.email, "ssn": user.ssn}  # Vulnerable
database.save(user_data)
```

**Enforcement:**
- PII field whitelist: email, phone, ssn, credit_card, name, address
- All PII encrypted at rest using AES-256
- Logging redacts PII automatically
- Monthly privacy audit using grid tracing system
- GDPR compliance documented in artifacts

---

### 4. AI Safety Guardrails

**Standard:** All AI operations protected by graduated guardrails.

**Guardrail Layers (from grid/safety/guardrails.py):**

1. **Aegis Health Checks** - Verify model availability and responsiveness
2. **Compressor Rate Limiting** - Prevent resource exhaustion
3. **Overwatch Circuit Breaker** - Stop cascading failures
4. **Output Validation** - Ensure LLM output matches safety constraints

```python
# ✅ GOOD: Multi-layer guardrails
from grid.safety.guardrails import Aegis, Compressor, Overwatch, OutputValidator

class SafeModelInvoker:
    def __init__(self):
        self.aegis = Aegis()  # Health checks
        self.compressor = Compressor(rate_limit=100/60)  # 100 req/min
        self.overwatch = Overwatch(failure_threshold=5)  # Fail after 5 errors
        self.validator = OutputValidator(schema=ExpectedOutputSchema)
    
    async def invoke_with_guardrails(self, prompt: str) -> Dict:
        # Layer 1: Health check
        await self.aegis.check_model_health()
        
        # Layer 2: Rate limiting
        await self.compressor.acquire_permit()
        
        # Layer 3: Circuit breaker check
        if self.overwatch.is_open():
            raise Exception("Circuit breaker open - service unavailable")
        
        try:
            # Invoke model
            response = await self.model.generate(prompt)
            
            # Layer 4: Output validation
            validated = self.validator.validate(response)
            
            self.overwatch.record_success()
            return validated
        except Exception as e:
            self.overwatch.record_failure()
            raise
```

**Enforcement:**
- All model invocations must pass through guardrails
- Guardrails configured per model (openai, anthropic, ollama)
- Failures logged and alert on threshold breach
- Circuit breaker breaks on 5 consecutive failures

---

## Testing & Quality Assurance

### 1. Test Coverage Requirements

**Minimum Coverage Standards:**

| Component | Target Coverage | Critical Paths |
|-----------|-----------------|-----------------|
| Backend Services | 80% | Harness, normalization, safety |
| Frontend Components | 60% | Dashboard, data visualization |
| Database Layer | 90% | ORM queries, migrations |
| AI Safety Analysis | 95% | Model detection, PII redaction |

**Test Organization:**

```
tests/
├── unit/
│   ├── test_harness_service.py      # Service layer unit tests
│   ├── test_normalization.py        # Schema conversion tests
│   └── test_ai_safety_analyzer.py   # Safety logic tests
├── integration/
│   ├── test_harness_e2e.py          # Full harness workflow
│   ├── test_api_endpoints.py        # FastAPI integration
│   └── test_async_operations.py     # Async/await correctness
├── performance/
│   ├── test_artifact_performance.py # Tier 1/2/3 timing
│   └── test_normalization_perf.py   # Schema conversion speed
└── security/
    ├── test_pii_redaction.py        # PII detection accuracy
    └── test_guardrails.py           # Safety enforcement
```

**Testing Standards:**

```python
# ✅ GOOD: Unit test with clear structure
def test_harvest_tier1_loads_existing_artifacts():
    """Test that Tier 1 loads cached artifacts"""
    # Arrange
    run_id = "20260123-001234Z_abc12345"
    repo_path = Path("e:\\test_repo")
    artifact_path = Path("e:\\analysis_outputs\\test_repo")
    
    # Act
    result = asyncio.run(harvest_codebase_tier1("test_repo", artifact_path, run_id))
    
    # Assert
    assert result["status"] == "completed"
    assert result["tier"] == "tier1"
    assert len(result["artifacts_loaded"]) > 0

# ✅ GOOD: Async test with fixture
@pytest.mark.asyncio
async def test_harvest_tier2_triggers_analysis(mock_subprocess):
    """Test that Tier 2 triggers fresh analysis"""
    # Arrange
    mock_subprocess.return_value = {"status": "completed", "job_id": "job123"}
    
    # Act
    result = await harvest_codebase_tier2("grid", "e:\\grid", "run123")
    
    # Assert
    assert result["status"] == "completed"
    mock_subprocess.assert_called_once()

# ✅ GOOD: Property-based test for safety
@given(code=st.text(alphabet=st.characters(blacklist_categories=['Cc'])))
def test_prompt_sanitization_removes_shell_chars(code):
    """Test that prompt sanitization prevents injection"""
    sanitized = sanitize_input(code)
    # No shell metacharacters
    assert not re.search(r'[;|&$(){}[\]`]', sanitized)
```

**Enforcement:**
- All pull requests require 80%+ coverage
- Critical paths (harness, safety) require 95%+ coverage
- Test failures block merge
- Performance tests tracked over time (regression prevention)

---

### 2. Continuous Integration & Testing

**CI Pipeline (GitHub Actions):**

```yaml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pytest
        run: pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  test-typescript:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: "20"
      - name: Install dependencies
        run: npm install
      - name: Run vitest
        run: npm run test
      - name: Build
        run: npm run build

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit (Python security)
        run: bandit -r . -f json -o bandit-report.json
      - name: AI Safety Scan
        run: python run_comprehensive_analysis.py
```

**Enforcement:**
- All CI checks must pass before merge
- Coverage reports tracked and trended
- Security scans (Bandit, safety) required
- AI safety analysis required for backend changes

---

## Deployment & Operations

### 1. Environment Configuration

**Standard:** Configuration via environment variables and `.env` files.

```bash
# .env.local (Development)
GEMINI_API_KEY=your_gemini_key_here
VITE_API_URL=http://localhost:8000
VITE_SENTRY_DSN=https://...@sentry.io/...
DATABASE_URL=sqlite:///app.db

# .env.production (Production)
GEMINI_API_KEY=prod_gemini_key
VITE_API_URL=https://api.eufle.com
VITE_SENTRY_DSN=https://prod_sentry_dsn
DATABASE_URL=postgresql+asyncpg://user:pass@db-host/dbname
STRIPE_SECRET_KEY=sk_live_...
SENTRY_ENVIRONMENT=production
```

**Enforcement:**
- No hardcoded secrets anywhere
- `.env.example` kept in version control
- Secrets rotated quarterly
- Access to prod env vars logged and audited

---

### 2. Deployment Pipeline

**Staging → Production Workflow:**

```bash
# 1. Build & Test (Automated)
npm run build                # Frontend build
pytest tests/                # Backend tests
npm run test:ui              # Frontend tests

# 2. Deploy to Staging
vercel deploy --prebuilt     # Frontend to Vercel staging
docker build -t app:latest .  # Backend Docker image
kubectl apply -f k8s/staging/ # Deploy to staging cluster

# 3. Smoke Tests
pytest tests/integration/ --env=staging  # Integration tests
curl https://staging.eufle.com/api/health  # Health check

# 4. Deploy to Production
# After manual approval
vercel deploy --prod          # Frontend production
kubectl set image deployment/app app=app:latest # Backend production

# 5. Monitor Rollout
# Check Sentry, metrics dashboards, error rates
```

**Enforcement:**
- Zero-downtime deployments via blue-green strategy
- Automated rollback on error rate spike (> 5%)
- Health checks before serving traffic
- Deployment logs retained for audit trail

---

### 3. Configuration Management Best Practices

**Standard:** From [backend/services/config_service.py](e:\Apps\backend\services\config_service.py)

```python
# ✅ GOOD: Config service with validation
from services.config_service import get_config_service

config = get_config_service()

# Type-safe config access
grid_path = config.get_repo_path("grid")  # Returns path or None
enabled_repos = config.get_enabled_repos()  # Dict of enabled repos

# Config service validates paths
# - Prevents path traversal attacks (checks for ".." in paths)
# - Restricts to allowed base directories
# - Resolves relative paths against configured base
# - Overridable via environment variables (REPO_GRID_PATH, etc.)

# ❌ BAD: Hardcoded paths
grid_path = "e:\\grid"  # Not configurable, not validated
```

**Enforcement:**
- All repo paths managed via config_service.py
- Environment variable overrides supported
- Path validation enforced (no traversal, allowed dirs only)
- Configuration changes logged and audited

---

## Performance & Monitoring

### 1. Performance Baselines

**Established Metrics (from Phase 4 Analysis):**

```json
{
  "codebase_metrics": {
    "total_lines_of_code": 13276760,
    "total_python_files": 33621,
    "async_functions": 7562,
    "average_file_size": 394,
    "largest_files": [
      ["grid/src/...", 50000],
      ["EUFLE/...", 45000]
    ]
  },
  "harness_performance": {
    "tier1_artifact_load_ms": 200,
    "tier2_analysis_trigger_ms": 50,
    "tier2_analysis_execution_min": 300,
    "tier3_fallback_ms": 1200,
    "normalization_ms": 500
  },
  "async_operations": {
    "fastapi_route_overhead_ms": 5,
    "database_query_ms": 50,
    "subprocess_spawn_ms": 100
  }
}
```

**Monitoring Targets:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time (p99) | 500ms | > 2000ms |
| Harness Tier 1 Load Time | 200ms | > 1000ms |
| Harness Tier 2 Timeout | 20min | > 25min |
| Database Query Time (p99) | 100ms | > 500ms |
| Error Rate | < 1% | > 5% |
| Memory Usage | < 2GB | > 4GB |

**Enforcement:**
- Performance tests run on every commit
- Regressions block merge
- Monthly performance report generated
- Optimization roadmap updated quarterly

---

### 2. Observability & Tracing

**Standard:** Grid tracing system with 18 trace origins.

```python
# ✅ GOOD: Comprehensive tracing
from grid.tracing import get_trace_manager, TraceOrigin

trace_mgr = get_trace_manager()

# Trace all critical operations
trace_origins = [
    TraceOrigin.API_REQUEST,           # FastAPI route entry
    TraceOrigin.DATABASE_QUERY,        # Database access
    TraceOrigin.ARTIFACT_HARVEST,      # Harness operations
    TraceOrigin.NORMALIZATION,         # Schema conversion
    TraceOrigin.AI_MODEL_INVOCATION,   # LLM calls
    TraceOrigin.SAFETY_ANALYSIS,       # Safety checks
    TraceOrigin.ERROR_HANDLING,        # Exceptions
    TraceOrigin.PERFORMANCE_PROFILE,   # Timing measurements
]

with trace_mgr.trace_action(
    origin=TraceOrigin.ARTIFACT_HARVEST,
    action_name="harvest_codebase",
    input_data={"repo": "grid", "tier": 1},
) as trace:
    result = await harvest_codebase_tier1(...)
    trace.output_data = {"artifacts_loaded": len(result["artifacts_loaded"])}
    trace.safety_score = 0.85
    trace.risk_level = "low"
```

**Enforcement:**
- All critical operations traced
- Trace data exported to Sentry & DataDog
- Distributed tracing enabled for microservices
- Trace retention policy: 30 days

---

### 3. Alerting & On-Call

**Alert Categories:**

| Category | Condition | Response |
|----------|-----------|----------|
| **Critical** | Error rate > 5% | Page on-call immediately |
| **Critical** | API latency p99 > 5s | Page on-call immediately |
| **High** | Error rate > 2% | Notify Slack #alerts |
| **High** | Memory > 80% | Notify Slack #alerts |
| **Medium** | Test coverage < 70% | PR blocked |
| **Low** | Performance regression > 10% | CI warning |

**Enforcement:**
- Alerting configured in Sentry + DataDog
- On-call rotation documented
- Incident response playbook maintained
- RTO target: < 5 minutes for critical issues

---

## Documentation & Communication

### 1. Code Documentation Standards

**Docstring Format (Google Style):**

```python
async def harvest_codebase(
    repo_name: str,
    repo_path: str,
    run_id: str,
    refresh: bool = False,
    force_tier2: bool = False
) -> Dict[str, Any]:
    """
    Orchestrates tiered codebase artifact harvesting.
    
    Implements three-tier strategy:
    - Tier 1: Load cached artifacts (< 1s, 100% reliable)
    - Tier 2: Trigger fresh analysis (5-20min, 95% reliable)
    - Tier 3: Lightweight fallback (< 5s, 99% reliable)
    
    Args:
        repo_name: Name of repository (e.g., "grid", "EUFLE")
        repo_path: Absolute filesystem path to repo
        run_id: Unique run identifier (format: YYYYMMDD-HHMMSSZ_<uuid8>)
        refresh: If True, skip Tier 1 and go to Tier 2 (default: False)
        force_tier2: Force Tier 2 execution even if artifacts exist (default: False)
    
    Returns:
        Dict with harvest result:
        {
            "tier": "tier1" | "tier2" | "tier3",
            "status": "completed" | "pending" | "failed",
            "artifacts_loaded": List[str],
            "error": str | None,
            "job_id": str | None  # If async (Tier 2)
        }
    
    Raises:
        ValueError: If repo_path doesn't exist
        TimeoutError: If Tier 2 analysis exceeds 20 minutes
    
    Examples:
        >>> result = await harvest_codebase("grid", "e:\\grid", "20260123-001234Z_abc123")
        >>> print(result["tier"])
        'tier1'
        >>> print(len(result["artifacts_loaded"]))
        42
    
    Note:
        - Artifacts stored immutably at E:/analysis_outputs/{repo_name}/
        - Run data stored at E:/Apps/data/harness/runs/{run_id}/
        - Manifest.json updated with harvest results
        - Degraded status set if Tier 3 fallback used
    
    See Also:
        - harvest_codebase_tier1(): Fast path implementation
        - harvest_codebase_tier2(): Deep analysis path
        - harvest_codebase_tier3(): Lightweight fallback
        - should_refresh_artifacts(): Refresh threshold logic
    """
    # Implementation...
```

**Enforcement:**
- All public functions must have docstrings
- All parameters and returns documented
- Examples included for complex functions
- Type hints on all function signatures

---

### 2. Architecture Decision Records (ADRs)

**Template for Major Decisions:**

```markdown
# ADR-001: Three-Tier Artifact Harvesting Architecture

## Status
Accepted (2026-01-23)

## Context
Codebase analysis can take 5-20 minutes, causing poor user experience.

## Decision
Implement three-tier harvest strategy:
1. Tier 1: Load cached artifacts (fast)
2. Tier 2: Trigger fresh analysis if needed (accurate)
3. Tier 3: Lightweight fallback if analysis fails (safe)

## Rationale
- Tier 1 provides 200ms response for cached repos
- Tier 2 ensures freshness when code changes
- Tier 3 prevents complete failure

## Consequences
- **Positive**: 99% availability, 200ms median latency
- **Negative**: Must manage three code paths, cache invalidation
- **Risk**: Tier 3 may miss important details

## Alternatives Considered
1. **Single synchronous analysis**: Too slow (20+ minutes)
2. **Cache-only (Tier 1)**: Would miss code changes
3. **Async-only (Tier 2)**: Would have poor responsiveness

## Related
- Decision: ProjectGraph normalization schema
- Decision: Run-based immutable snapshots
- Decision: 24-hour refresh threshold
```

**Enforcement:**
- Major architectural decisions documented as ADRs
- ADRs reviewed before implementation
- ADR index maintained in docs/ADR_INDEX.md

---

### 3. Runbooks & Troubleshooting

**Format: Operational Runbook**

```markdown
# Harness Service Troubleshooting Runbook

## Symptoms: Analysis Hangs (> 25 minutes)

### Step 1: Determine Tier
```bash
# Check run manifest
cat E:\Apps\data\harness\runs\<run_id>\manifest.json | grep tier
```

### Step 2: Check Tier 2 Job Status
```bash
# If Tier 2 (deep analysis)
python -c "
from services.analysis_executor import get_job_status
status = get_job_status('<job_id>')
print(f'Status: {status}')
"
```

### Step 3: Fallback to Tier 3
```bash
# Manually trigger lightweight harvest
await harvest_codebase_tier3('repo', 'path', 'run_id')
```

### Step 4: Check Logs
```bash
# Check error logs
grep ERROR E:\Apps\data\harness\runs\<run_id>\logs.txt
```

## Resolution: Timeout Configuration
- Tier 2 timeout: 20 minutes (configurable in harness_service.py)
- Tier 3 timeout: 5 seconds (non-configurable, fast)
```

**Enforcement:**
- Runbook created for each component
- Runbooks tested quarterly
- Updated when new issues discovered

---

## Implementation Checklist

- [x] Installed missing dependencies (torch, manim, redis, etc.)
- [x] Comprehensive analysis generated (33,621 Python files, 13.2M LOC)
- [x] Type safety standards documented
- [x] Async/await standards documented
- [x] AI safety & guardrails documented
- [x] Testing coverage targets established (80%+ backend, 60%+ frontend)
- [x] Performance baselines established
- [ ] Update all existing code to comply with standards
- [ ] Implement CI/CD checks for compliance
- [ ] Create ADR index and maintain
- [ ] Create operational runbooks for all components
- [ ] Establish on-call rotation and alerting
- [ ] Monthly compliance audit schedule

---

## Reference Materials

- **AI Safety Analyzer**: [backend/services/ai_safety_analyzer.py](e:\Apps\backend\services\ai_safety_analyzer.py)
- **Harness Service**: [backend/services/harness_service.py](e:\Apps\backend\services\harness_service.py)
- **Normalization Service**: [backend/services/normalization_service.py](e:\Apps\backend\services\normalization_service.py)
- **Config Service**: [backend/services/config_service.py](e:\Apps\backend\services\config_service.py)
- **Grid Tracing**: `e:\grid\src\grid\tracing\action_trace.py`
- **Grid Safety Guardrails**: `e:\grid\src\grid\safety\guardrails.py`

---

**Document Status:** Ready for Implementation  
**Next Review:** 2026-02-23 (30 days)  
**Owner:** Architecture Team  
**Version:** 1.0
