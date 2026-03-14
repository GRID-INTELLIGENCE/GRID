# GRID Mothership API Reference

> **Version:** 2.6.1 | **Base URL:** `http://localhost:8080/api/v1` | **Auth:** API key via `X-API-Key` header

---

## Health & System

### `GET /health`
Health check for monitoring and Kubernetes probes.

**Response:** `200 OK`
```json
{ "status": "healthy", "checks": { "database": "ok", "ollama": "ok", "chromadb": "ok" } }
```

### `GET /health/ready`
Readiness probe — confirms all dependencies are connected.

### `GET /health/live`
Liveness probe — confirms process is running.

---

## Cockpit

### `GET /cockpit/state`
Returns full cockpit state: sessions, operations, components, alerts.

**Auth:** Required

### `GET /cockpit/summary`
Lightweight summary: active sessions count, running ops, system state.

### `POST /cockpit/mode`
Change cockpit operation mode.

**Body:**
```json
{ "mode": "maintenance" | "online" | "degraded" }
```

### `GET /cockpit/diagnostics`
Run diagnostic checks across all components.

**Auth:** Write access required

---

## Sessions

### `POST /cockpit/sessions`
Create a new session.

**Body:**
```json
{
  "user_id": "string",
  "permissions": ["read", "write"],
  "ttl_minutes": 60,
  "metadata": {}
}
```

**Response:** `201 Created`
```json
{
  "id": "session_a1b2c3d4e5f6",
  "user_id": "user-001",
  "status": "active",
  "expires_at": "2026-03-14T17:15:00Z",
  "connection_type": "http"
}
```

### `POST /cockpit/sessions/{session_id}/touch`
Extend session expiration (sliding window). Each touch resets the TTL.

**Response:** `200 OK` — returns updated session with new `expires_at`.

### `DELETE /cockpit/sessions/{session_id}`
Terminate a session.

---

## Auth

### `POST /auth/login`
Authenticate and receive session token.

**Body:**
```json
{ "username": "string", "password": "string" }
```

### `POST /auth/refresh`
Refresh an expiring token.

### `POST /auth/logout`
Invalidate current session.

---

## Inference

### `POST /inference/`
Submit a prompt for AI inference.

**Body:**
```json
{
  "prompt": "Explain the architecture of GRID",
  "model": null,
  "max_tokens": 1024,
  "temperature": 0.7,
  "context": {}
}
```

**Response:** `200 OK`
```json
{
  "result": "GRID is a full-stack AI framework...",
  "model": "llama3:latest",
  "tokens_used": 245,
  "processing_time": 1.82,
  "metadata": {}
}
```

### `POST /inference/async`
Submit async inference — returns task ID for polling.

### `GET /inference/tasks/{task_id}`
Poll async inference task status.

---

## Privacy

### `POST /privacy/redact`
Redact PII from text.

**Body:**
```json
{ "text": "Contact john@example.com for details", "types": ["email", "phone"] }
```

### `GET /privacy/stats`
Return redaction statistics.

---

## Reasoning

### `POST /reasoning/analyze`
Run multi-step reasoning chain on a query.

**Body:**
```json
{ "query": "string", "depth": 3, "strategy": "chain_of_thought" }
```

---

## Intelligence

### `POST /intelligence/search`
Semantic search across indexed knowledge.

**Body:**
```json
{ "query": "string", "top_k": 10, "filters": {} }
```

---

## Billing & Payments

### `GET /billing/usage`
Current billing period usage.

### `POST /payment/create-checkout`
Create Stripe checkout session.

### `GET /payment/status/{session_id}`
Check payment status.

---

## API Keys

### `POST /api-keys/`
Create a new API key.

### `GET /api-keys/`
List active API keys.

### `DELETE /api-keys/{key_id}`
Revoke an API key.

---

## Navigation

### `POST /navigation/query`
Natural language navigation — routes user intent to appropriate service.

---

## Resonance

### `POST /resonance/analyze`
Run resonance analytics on a dataset.

### `GET /resonance/patterns`
Retrieve detected resonance patterns.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "status_code": 400
}
```

| Code | HTTP | Meaning |
|------|------|---------|
| `SESSION_EXPIRED` | 401 | Session TTL elapsed without activity |
| `MAX_SESSIONS_EXCEEDED` | 429 | Too many concurrent sessions |
| `RESOURCE_NOT_FOUND` | 404 | Entity not found |
| `STATE_TRANSITION_ERROR` | 409 | Invalid state change |
| `OPERATION_IN_PROGRESS` | 409 | Conflicting operation running |

---

## Rate Limits

- **Default:** 100 requests/minute per API key
- **Inference:** 20 requests/minute per API key
- **Health checks:** Unlimited

---

*Generated 2026-03-14 — GRID Framework v2.6.1*
