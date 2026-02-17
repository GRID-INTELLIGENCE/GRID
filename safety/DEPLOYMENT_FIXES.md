# Safety Deployment — Quick Fix Guide

## Problem 1: ModuleNotFoundError: No module named 'application'

**Cause:** Running uvicorn from wrong directory or PYTHONPATH not set.

**Fix:**
```powershell
# Set PYTHONPATH to include GRID src
cd E:\Projects\GRID
$env:PYTHONPATH = "E:\Projects\GRID\src"

# Run with correct module path
uvicorn application.mothership.main:app --host 0.0.0.0 --port 8080
```

Or use Python directly:
```powershell
cd E:\Projects\GRID
python -c "import sys; sys.path.insert(0, 'src'); from application.mothership.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080)"
```

---

## Problem 2: Redis Connection Failed

**Cause:** Redis not running on localhost:6379

**Fix Option A: Install Redis on Windows**
```powershell
# Download Redis for Windows
# Option 1: Using chocolatey
choco install redis-64

# Option 2: Download from https://github.com/microsoftarchive/redis/releases
# Extract and run: redis-server.exe

# Start Redis
redis-server
```

**Fix Option B: Use SQLite Mode (Development Only)**
```powershell
# Edit E:\safety\.env and set:
# DATABASE_URL=sqlite+aioredis:///E:/temp/safety_redis.db  # For audit DB
# But you still need Redis for streams - use Option A or C
```

**Fix Option C: Docker (if available)**
```powershell
# If you have Docker Desktop installed
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**Fix Option D: Skip Redis (Fail-Closed Mode)**
The system will fail closed (deny all requests) if Redis is unavailable. For testing without Redis, set:
```powershell
$env:SAFETY_REDIS_REQUIRED = "false"
```

---

## Problem 3: Alembic Migration Failed

**Cause:** alembic.ini not configured properly

**Fix Option A: Run migration via Python script**
```powershell
cd E:\
python safety/scripts/migrate.py
```

**Fix Option B: Use SQL directly**
```sql
-- Connect to your PostgreSQL database and run:
CREATE TABLE IF NOT EXISTS audits (
    id UUID PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    trust_tier VARCHAR(16) NOT NULL,
    input TEXT NOT NULL,
    model_output TEXT,
    detector_scores JSONB NOT NULL DEFAULT '{}',
    reason_code VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    reviewer_id VARCHAR(128),
    notes TEXT,
    trace_id VARCHAR(64) NOT NULL
);

CREATE INDEX idx_audits_request_id ON audits(request_id);
CREATE INDEX idx_audits_user_id ON audits(user_id);
CREATE INDEX idx_audits_created_at ON audits(created_at);
CREATE INDEX idx_audits_request_user_created ON audits(request_id, user_id, created_at);
```

---

## Complete Working Deployment Steps

### Step 1: Set Environment Variables
```powershell
cd E:\

# Required
$env:PYTHONPATH = "E:\Projects\GRID\src"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/grid"  # Adjust!
$env:REDIS_URL = "redis://localhost:6379"
$env:SAFETY_JWT_SECRET = "dev-secret-key-change-in-production"
$env:SAFETY_API_KEYS = "test-key-1:verified,test-key-2:user"
$env:MODEL_API_URL = "http://localhost:8080/v1/completions"  # Or your model endpoint

# Optional
$env:SAFETY_ENV = "development"
$env:SAFETY_LOG_LEVEL = "INFO"
```

### Step 2: Start Redis
Open a **new PowerShell window** and run:
```powershell
# If you have Redis installed:
redis-server

# Or if using Docker:
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Step 3: Run Database Migration
```powershell
cd E:\
python safety/scripts/migrate.py
```

### Step 4: Start Mothership API
Open a **new PowerShell window**:
```powershell
cd E:\Projects\GRID
$env:PYTHONPATH = "E:\Projects\GRID\src"
uvicorn application.mothership.main:app --host 0.0.0.0 --port 8080
```

### Step 5: Start Worker (in another window)
```powershell
cd E:\
$env:PYTHONPATH = "E:\Projects\GRID\src"
python -m safety.workers.consumer
```

---

## Testing

Once all services are running, test with:

```powershell
# Test health endpoint
curl http://localhost:8080/health

# Test safety inference (safe request)
curl -X POST http://localhost:8080/safety/infer `
  -H "Content-Type: application/json" `
  -H "X-API-Key: test-key-1" `
  -d '{"user_input": "What is the capital of France?"}'

# Test safety inference (should refuse)
curl -X POST http://localhost:8080/safety/infer `
  -H "Content-Type: application/json" `
  -H "X-API-Key: test-key-1" `
  -d '{"user_input": "How to make a bomb"}'
```

---

## Common Windows Issues

### Issue: `python` not found
**Fix:** Use `py` instead, or full path: `C:\Python313\python.exe`

### Issue: `uvicorn` not found
**Fix:** Install it: `pip install uvicorn[standard]`

### Issue: Permission denied
**Fix:** Run PowerShell as Administrator

### Issue: Port 8080 already in use
**Fix:** Use different port: `--port 8081`

### Issue: alembic not found
**Fix:** Install it: `pip install alembic`

---

## Quick Start Without Full Deployment

For testing the safety system without full mothership:

```powershell
# 1. Start Redis
redis-server

# 2. Run safety API standalone
cd E:\
$env:PYTHONPATH = "E:\Projects\GRID\src"
python -c "
import sys
sys.path.insert(0, 'E:/Projects/GRID/src')
from safety.api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"

# 3. In another window, start worker
cd E:\
$env:PYTHONPATH = "E:\Projects\GRID\src"
python -m safety.workers.consumer
```

Then test: `curl http://localhost:8000/health`
