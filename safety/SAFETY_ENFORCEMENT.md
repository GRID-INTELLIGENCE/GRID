# Safety Enforcement Specification

## Goal

Integrate a realtime safety enforcement pipeline that **deterministically
refuses unsafe inputs**, **detects and blocks systematic misuse**,
**escalates uncertain/high-risk cases to humans**, and **fails closed**
if safety infrastructure is degraded.

**See also:** [Safety Layer & Cognitive Privacy Shield — Architecture](../docs/SAFETY_ARCHITECTURE.md) for pipeline details, Privacy Shield integration, and key files.

---

## Architecture

```
API (FastAPI + middleware)
  -> Pre-check detector (sync, <50ms)
  -> Rate limiter (Redis token-bucket)
  -> Enqueue to Redis Stream (inference-stream)
  -> Worker(s) (consumer group) {
       call model via model client (sandboxed);
       run post-check detector (ML + heuristics);
       if PASS -> response-stream;
       if FLAG -> escalation-handler (audit DB + notify) -> block/suspend
     }

Observability: Prometheus metrics, structlog JSON, Sentry
Red-team harness: CI-blocking test suite
```

---

## Mandatory Request Flow

1. **Authenticate** every request; assign trust tier (anon/user/verified/privileged).
2. **Rate limit** per user, per tier, before any model invocation.
3. **Run synchronous pre-check** (<50ms). If flagged: refuse immediately.
4. **Enqueue** to Redis Streams. Direct model calls from API prohibited.
5. **Worker** consumes, calls model in sandbox, runs post-check.
6. **Release** or **escalate** based on post-check result.

---

## Refusal Behavior

All refusals are:
- **Deterministic** (no negotiation, no partial answers)
- **Non-informative** (no bypass hints)
- **Logged** with reason codes

Format:
```json
{
  "refused": true,
  "reason_code": "HIGH_RISK_BIO",
  "explanation": "request denied",
  "support_ticket_id": "audit-<uuid>"
}
```

---

## Redis Streams Contract

| Stream             | Purpose                    | Fields                                           |
|--------------------|----------------------------|--------------------------------------------------|
| `inference-stream` | Incoming requests          | request_id, user_id, input, trust_tier, trace_id |
| `response-stream`  | Approved outputs           | request_id, response, status                     |
| `audit-stream`     | Events (refusals, etc.)    | event, request_id, user_id, reason, payload      |

---

## Escalation Workflow

1. Worker flags output -> `escalation.handler.escalate()`.
2. Creates audit DB record with status `escalated`.
3. Notifies Slack channel with preformatted message.
4. Critical/high severity triggers PagerDuty.
5. Human reviewer calls `/review` endpoint: `approve` or `block`.
6. `approve` releases stored output; `block` adds to blocklist.

---

## Systematic Misuse Handling

If repeated escalations for a user within a configurable window:
- Automatically tighten rate limits (50-75% reduction).
- Suspend the user token.
- Log systematic misuse event to audit stream.

---

## Fail-Closed Rules

If any of these are unavailable: Redis, audit DB, detectors —
the system **refuses all requests** with `SAFETY_UNAVAILABLE`.
No silent fallback to direct model calls.

---

## Acceptance Criteria

1. Pre-check detects and refuses canonical red-team vectors.
2. Worker post-check flags and escalates the same vectors end-to-end.
3. Red-team tests run in CI and pass at >= 99% detection threshold.
4. Metrics and structured logs show trace IDs for 100% of requests.
5. Human review flow exists and can approve/reject escalations.
6. System fails closed when safety infra is down.

---

## File Layout

```
safety/
├─ api/main.py, middleware.py, auth.py, rate_limiter.py
├─ detectors/pre_check.py, ml_detector.py, post_check.py
├─ workers/consumer.py, worker_utils.py
├─ model/client.py, sandbox.py
├─ audit/db.py, models.py
├─ escalation/handler.py, notifier.py
├─ observability/metrics.py, logging_setup.py
├─ tests/unit/, tests/redteam/
├─ scripts/load_blocklist.py
├─ .env.example
└─ SAFETY_ENFORCEMENT.md
```
