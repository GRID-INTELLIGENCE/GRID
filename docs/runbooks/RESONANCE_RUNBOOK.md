# Resonance API Runbook

**Service**: Resonance API
**Version**: 1.0.0
**On-Call Escalation**: Grid Platform Team

---

## Overview

The Resonance API provides the "canvas flip" communication layer for the GRID system. It exposes endpoints under `/api/v1/resonance/` that orchestrate context, path triage, and skill execution.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/resonance/process` | POST | Process activity with resonance feedback |
| `/api/v1/resonance/definitive` | POST | Canvas flip checkpoint (~65% progress) |
| `/api/v1/resonance/context` | GET | Fast context retrieval |
| `/api/v1/resonance/paths` | GET | Path triage options |
| `/api/v1/resonance/envelope/{activity_id}` | GET | ADSR envelope metrics |

---

## Alert Response Procedures

### ALERT: Resonance API 5xx Error Rate > 1%

**Severity**: High
**SLO Impact**: Yes

#### Symptoms
- HTTP 500 responses from `/api/v1/resonance/*` endpoints
- Error logs with `Error running definitive step` or similar

#### Diagnosis Steps

1. **Check logs for error details**:
   ```powershell
   # Search for recent errors in logs
   Get-Content E:\grid\logs\mothership.log -Tail 100 | Select-String "Error running"
   ```

2. **Check if skills registry is healthy**:
   ```powershell
   .\.venv\Scripts\python.exe -m grid skills list
   ```

3. **Check if RAG index is corrupt** (if `use_rag=true` requests failing):
   ```powershell
   .\.venv\Scripts\python.exe -m tools.rag.cli status
   ```

4. **Check service memory/CPU**:
   ```powershell
   Get-Process python | Select-Object CPU, WorkingSet64
   ```

#### Remediation

1. **Restart the service** (if memory/CPU exhaustion):
   ```powershell
   # Stop the service
   Stop-Process -Name python -Force

   # Start fresh
   .\.venv\Scripts\python.exe -m application.mothership.main
   ```

2. **Disable the endpoint via feature flag** (if issue is in definitive step):
   ```powershell
   $env:RESONANCE_DEFINITIVE_ENABLED = "false"
   # Then restart
   ```

3. **Rebuild RAG index** (if RAG-related):
   ```powershell
   .\.venv\Scripts\python.exe -m tools.rag.cli index . --rebuild
   ```

---

### ALERT: Resonance API Latency p95 > 500ms

**Severity**: Medium
**SLO Impact**: Potential

#### Symptoms
- Slow responses from `/api/v1/resonance/definitive`
- High `elapsed_ms` in logs

#### Diagnosis Steps

1. **Check if LLM mode is enabled** (`use_llm=true` is slower):
   - Review recent requests in logs for `use_llm` parameter

2. **Check Ollama status** (if LLM mode enabled):
   ```powershell
   curl http://localhost:11434/api/tags
   ```

3. **Profile skill execution times**:
   - Check `skills` field in response for timing data

#### Remediation

1. **Recommend clients use `use_llm=false`** for faster heuristic-only mode
2. **Scale Ollama resources** if LLM latency is the bottleneck
3. **Review and optimize skill implementations**

---

### ALERT: Resonance API Rate Limit Exceeded

**Severity**: Low
**SLO Impact**: No (expected behavior)

#### Symptoms
- HTTP 429 responses
- Logs showing rate limit triggers

#### Diagnosis Steps

1. Identify the client triggering rate limits
2. Review if rate limit settings are appropriate

#### Remediation

1. **Increase rate limits** (if legitimate traffic):
   ```powershell
   $env:MOTHERSHIP_RATE_LIMIT_REQUESTS = "200"
   ```

2. **Block abusive clients** at load balancer level

---

## Health Checks

### Manual Health Check

```powershell
# Check API is responding
Invoke-WebRequest -Uri http://localhost:8080/health -UseBasicParsing

# Check resonance endpoint specifically
Invoke-WebRequest -Uri "http://localhost:8080/api/v1/resonance/context?query=test" -UseBasicParsing
```

### Automated Health Check (for monitoring)

```powershell
$response = Invoke-RestMethod -Uri http://localhost:8080/api/v1/resonance/definitive -Method POST -Body '{"query":"health check"}' -ContentType "application/json"
if ($response.activity_id) { exit 0 } else { exit 1 }
```

---

## Rollback Procedure

If the Resonance API is causing issues:

1. **Quick disable** (feature flag):
   ```powershell
   $env:RESONANCE_DEFINITIVE_ENABLED = "false"
   ```

2. **Full rollback** (use rollback script):
   ```powershell
   .\.venv\Scripts\python.exe scripts\rollback_resonance.py
   ```

3. **Git rollback** (if code changes are the issue):
   ```powershell
   git revert HEAD  # Or specific commit
   ```

---

## Contacts

| Role | Contact |
|------|---------|
| Primary On-Call | Grid Platform Team |
| Secondary On-Call | Application Team |
| Escalation | Engineering Lead |

---

## Related Documentation

- [Resonance API Documentation](../RESONANCE_API.md)
- [Skills Quickstart](../SKILLS_RAG_QUICKSTART.md)
- [Architecture](../architecture.md)
