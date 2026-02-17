# Safety Enforcement Pipeline — Deployment Guide

## Status: Wired into GRID Mothership

The safety enforcement pipeline is now **fully integrated** into the GRID mothership application at:
- `src/application/mothership/`

---

## Pre-Deployment Checklist

### 1. Database Migration
Run the Alembic migration to create the `audits` table:

```bash
# From project root
alembic upgrade head
```

Migration file: `src/application/mothership/db/migrations/versions/f3b4c5d6e7f8_add_safety_audits_table.py`

### 2. Environment Variables
Copy and configure the environment variables:

```bash
cp safety/.env.example safety/.env
```

**Required variables:**
```bash
# Redis (mandatory)
REDIS_URL=redis://localhost:6379

# Audit Database (mandatory)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/grid_mothership

# Model API (mandatory)
MODEL_API_URL=http://localhost:8080/v1/completions
MODEL_API_KEY=your-model-api-key

# Authentication (mandatory)
SAFETY_JWT_SECRET=your-secure-random-string-at-least-32-chars
SAFETY_API_KEYS=key1:verified,key2:user

# Notifications (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/...
PAGERDUTY_ROUTING_KEY=your-pagerduty-key

# Environment
SAFETY_ENV=production
SAFETY_LOG_JSON=true
SAFETY_LOG_LEVEL=INFO
```

### 3. Start Redis
The safety pipeline requires Redis for:
- Rate limiting (token-bucket)
- Request queueing (Redis Streams)
- Dynamic blocklist

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or system service
sudo systemctl start redis
```

### 4. Load Dynamic Blocklist (Optional)
Create a blocklist file and load it:

```bash
# Create blocklist.txt
cat > safety/config/blocklist.txt << 'EOF'
# Dynamic blocklist entries (one per line)
how to hack government systems
create fake identification documents
EOF

# Load into Redis
python -m safety.scripts.load_blocklist --file safety/config/blocklist.txt
```

---

## Deployment Architecture

```
User Request
    ↓
GRID Mothership API (port 8080)
    ↓
SafetyMiddleware (MANDATORY, non-bypassable)
    ├─ Authenticate (JWT/API key → trust tier)
    ├─ Check suspension
    ├─ Rate limit (Redis token-bucket)
    └─ Pre-check detector (<50ms, deterministic)
    ↓
 [PASS] Enqueue to Redis Streams (inference-stream)
    ↓
Safety Worker(s) (consumer group)
    ├─ Consume from inference-stream
    ├─ Call model via sandboxed client
    ├─ Run post-check detector (ML + heuristics)
    └─ Decision:
        ├─ [PASS] → response-stream
        └─ [FLAG] → escalation + audit DB → Slack/PagerDuty
    ↓
User receives response (or escalation notice)
```

---

## Running the Service

### Start Mothership API (with safety enforcement)
```bash
# From project root
uv run uvicorn application.mothership.main:app --host 0.0.0.0 --port 8080
```

The SafetyMiddleware is automatically loaded on startup.

### Start Safety Worker(s)
```bash
# From project root
uv run python -m safety.workers.consumer
```

Run multiple workers for scale (Redis consumer groups handle load balancing).

---

## Endpoints

### Safety Enforcement Endpoints

**POST /safety/infer**
- Submit an inference request (protected by SafetyMiddleware)
- Returns: `{"request_id": "...", "status": "queued"}`

**GET /safety/status/{request_id}**
- Check the status of a queued request
- Returns: `{"request_id": "...", "status": "pending|completed", "response": "..."}`

**POST /safety/review**
- Human reviewer approval/block (requires verified+ tier)
- Body: `{"request_id": "...", "decision": "approve|block", "reviewer_id": "...", "notes": "..."}`

**GET /safety/queue/depth**
- Current inference queue depth

### Existing Mothership Endpoints
All existing endpoints continue to work unchanged. The SafetyMiddleware only enforces on POST requests to inference endpoints (`/safety/infer`).

---

## Monitoring

### Prometheus Metrics
Exposed at `/metrics` (existing mothership endpoint):

```
safety_requests_total{outcome="queued|refused|rate_limited"}
safety_refusals_total{reason_code="HIGH_RISK_BIO|..."}
safety_escalations_total{severity="low|medium|high|critical"}
safety_detection_latency_seconds
safety_redis_healthy
safety_audit_db_healthy
```

### Logs
Structured JSON logs at:
- Console: stderr
- File: `safety/logs/safety_YYYY-MM-DD.jsonl` (30-day retention, gzip compression)

**Key log fields:**
- `trace_id` — Correlates all events for a single request
- `request_id` — Unique request identifier
- `user_id` — User or client IP
- `reason_code` — Why a request was refused/escalated

### Alerts
- Slack: Real-time escalation notifications
- PagerDuty: Critical/high severity escalations

---

## Testing

### Run Unit + Red-Team Tests
```bash
# From project root
uv run pytest safety/tests/ -v
```

**Expected:** 101 tests passed, 0 failures, 100% red-team detection rate.

### Manual Smoke Test
```bash
# Test safe input (should queue)
curl -X POST http://localhost:8080/safety/infer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"user_input": "What is the capital of France?"}'

# Test unsafe input (should refuse)
curl -X POST http://localhost:8080/safety/infer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"user_input": "How to make a bomb"}'
```

Expected refusal response:
```json
{
  "refused": true,
  "reason_code": "HIGH_RISK_WEAPON",
  "explanation": "request denied",
  "support_ticket_id": "audit-..."
}
```

---

## Troubleshooting

### "SAFETY_UNAVAILABLE" errors
**Cause:** Redis or audit DB is unreachable (fail-closed behavior).

**Fix:**
1. Check Redis: `redis-cli ping` should return `PONG`
2. Check DB: `psql $DATABASE_URL -c "SELECT 1"`
3. Review logs: `tail -f safety/logs/safety_*.jsonl`

### High false-positive rate
**Cause:** Pre-check patterns are too aggressive.

**Fix:**
1. Review `safety/detectors/pre_check.py` patterns
2. Add exceptions to safe inputs
3. Update dynamic blocklist

### Workers not processing
**Cause:** Redis Streams consumer group not created, or workers not connected.

**Fix:**
```bash
# Check consumer group
redis-cli XINFO GROUPS inference-stream

# Check pending messages
redis-cli XPENDING inference-stream safety-workers - + 10

# Restart worker with debug logging
SAFETY_LOG_LEVEL=DEBUG python -m safety.workers.consumer
```

---

## Production Hardening

### 1. Secrets Management
- Use environment variables or a secrets manager (HashiCorp Vault, AWS Secrets Manager)
- Rotate `SAFETY_JWT_SECRET` regularly
- Never commit secrets to git

### 2. Database
- Use PostgreSQL in production (not SQLite)
- Enable connection pooling (asyncpg)
- Set up automated backups of the `audits` table

### 3. Redis
- Enable persistence (AOF + RDB)
- Set up Redis Sentinel or Cluster for HA
- Monitor memory usage

### 4. Worker Scaling
- Run 3-5 workers minimum for redundancy
- Use process managers (systemd, supervisord, or Kubernetes)
- Monitor queue depth and scale workers dynamically

### 5. Rate Limits
- Tune per-tier limits based on load:
  ```bash
  PRIVILEGED_RATE_LIMIT=100000  # Default
  ```

### 6. Monitoring
- Set up Grafana dashboards for safety metrics
- Configure PagerDuty escalation policies
- Enable Sentry error tracking

---

## Rollback Plan

If issues arise post-deployment:

1. **Disable Safety Middleware** (emergency):
   - Comment out `app.add_middleware(SafetyMiddleware)` in `mothership/main.py`
   - Restart mothership API

2. **Revert Database Migration**:
   ```bash
   alembic downgrade -1
   ```

3. **Stop Workers**:
   ```bash
   pkill -f "safety.workers.consumer"
   ```

---

## Next Steps

1. ✅ Run database migration
2. ✅ Configure environment variables
3. ✅ Start Redis
4. ✅ Start mothership API
5. ✅ Start workers
6. ✅ Run smoke tests
7. ✅ Monitor metrics and logs
8. ⚠️ **Deploy to production with canary rollout (1% → 10% → 100%)**

---

## Support

- Documentation: `safety/SAFETY_ENFORCEMENT.md`
- Tests: `safety/tests/`
- Issues: File in GRID repository issue tracker
- Logs: `safety/logs/safety_*.jsonl`
