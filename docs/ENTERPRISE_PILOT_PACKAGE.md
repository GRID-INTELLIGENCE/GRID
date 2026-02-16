# GRID Enterprise Pilot Package

> **Version:** 2.2.2  
> **Target:** Enterprise clients in Bangladesh (Grameenphone, bKash, banks, telcos)  
> **Positioning:** GRID is the trust infrastructure platform that giants *use*.

---

## What GRID Delivers

GRID is a **trust layer** for AI-powered applications. It sits between your users and your AI systems, ensuring every interaction is safe, auditable, and compliant.

### Core Capabilities

| Capability | Endpoint | What It Does |
|---|---|---|
| **Safety Pipeline** | `POST /api/v1/resonance/process` | Processes queries through multi-layer safety checks before AI response |
| **Definitive Checkpoint** | `POST /api/v1/resonance/definitive` | Canvas-flip: turns chaotic context into structured, audience-aligned explanations |
| **PII Detection** | `POST /api/v1/privacy/detect` | Detects emails, phone numbers, NID numbers, and other PII in text |
| **PII Masking** | `POST /api/v1/privacy/mask` | Masks detected PII with configurable privacy levels (strict/balanced/minimal) |
| **Content Moderation** | Internal (AISafetyFramework) | Multi-layer analysis: harmful content, cultural sensitivity, safety patterns |
| **Inference Gateway** | `POST /api/v1/inference/` | Proxied model inference with audit logging and rate limiting |

### Bangladesh Market Differentiators

- **Curated safety detection seed set** — 15 high-confidence tokens across 6 categories, expanding via field research:
  - Non-consensual media (sextortion, revenge/deepfake explicit content)
  - Financial fraud (phishing, forgery, deception)
  - Violence and gendered violence (trafficking, sexual abuse)
  - Platform exploitation (doxxing, cyberbullying)
  - Distress signals (routed to care pathways, not punitive action)
- **Bangla + Banglish support** — native and transliterated detection tokens
- **Cultural context** — SE Asia sensitivity patterns for religious, cultural, political content

### Security Infrastructure

- **Parasite Guard** — 3 real-time detectors (C1: WebSocket No-Ack, C2: Event Subscription Leak, C3: DB Connection Orphan)
- **Secret Validation** — OWASP-compliant, STRONG classification enforced in production
- **JWT Authentication** — Token-based auth with refresh flow
- **Rate Limiting** — Configurable per-endpoint rate limits
- **Audit Logging** — Every inference request logged with user ID, model, token count

---

## Deployment Options

### Option A: Render (Recommended for pilot)

```bash
# render.yaml included — one-click deploy
# Region: Singapore (lowest latency to Bangladesh)
# Auto-generates MOTHERSHIP_SECRET_KEY
```

### Option B: Railway

```bash
# railway.json included — Nixpacks builder
# Healthcheck at /ping
# Auto-restart on failure
```

### Option C: Self-hosted (Docker)

```bash
docker build -t grid-mothership .
docker run -p 8080:8080 \
  -e MOTHERSHIP_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))") \
  -e MOTHERSHIP_ENVIRONMENT=production \
  grid-mothership
```

---

## Pilot Integration Guide

### 1. Authentication

```bash
# Login
curl -X POST https://your-grid.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "operator", "password": "your-password"}'

# Use the returned access_token in subsequent requests
```

### 2. Process a Query Through the Trust Layer

```bash
curl -X POST https://your-grid.onrender.com/api/v1/resonance/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I transfer money to another account?",
    "activity_type": "general",
    "context": {}
  }'
```

**Response includes:**
- `activity_id` — unique tracking ID
- `state` — safety state assessment
- `message` — processed response
- `context` — fast context snapshot
- `paths` — decision path options

### 3. Check Content for PII

```bash
curl -X POST https://your-grid.onrender.com/api/v1/privacy/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact me at user@example.com or 017-1234-5678"}'
```

### 4. Content Safety Check

The safety pipeline checks all text against a curated seed set of high-confidence detection tokens. Matches are flagged with severity by category:

- **CRITICAL** — nonconsensual media, violence, gendered violence
- **HIGH** — distress signals (→ care pathway), platform exploitation
- **MEDIUM** — financial fraud (and future field-research-validated categories)

---

## Compliance & Audit

| Requirement | GRID Coverage |
|---|---|
| Data residency | Self-hosted option; Render Singapore region |
| PII handling | Detection + masking before any AI processing |
| Audit trail | Every request logged with user ID, timestamp, model |
| Content moderation | Multi-layer: keyword detection + cultural context |
| Rate limiting | Per-user, per-endpoint, configurable thresholds |
| Secret management | OWASP-compliant, no hardcoded secrets, env-var based |

---

## SLA Targets (Pilot)

| Metric | Target |
|---|---|
| API Availability | 99.5% |
| Safety check latency (p95) | < 200ms |
| PII detection accuracy | > 95% |
| Safety pattern coverage | 15 seed tokens, 6 categories (expanding via field research) |
| Incident response | < 4 hours during business hours |

---

## Next Steps for Pilot Client

1. **Schedule demo** — 30-min live walkthrough of the trust layer with your team
2. **API key provisioning** — We set up dedicated credentials for your pilot
3. **Integration support** — 2 weeks of hands-on engineering support
4. **Custom patterns** — Add your domain-specific harmful content patterns
5. **Compliance review** — Joint review against your regulatory requirements

---

*GRID — The trust infrastructure that enterprise giants use.*
