# Security Module Boundary Contract

## `src/grid/security/` — Infrastructure-Layer Security

**Owner:** Core platform team
**Layer:** Infrastructure (imported by all layers)

### Responsibilities
- Environment configuration & secrets management
- Path validation & secure file access
- Encryption (AES-GCM, PBKDF2)
- Threat detection & threat profiles (broad categories)
- Parasitic code detection (parasite guard)
- Hardened middleware (rate limiting, request validation)
- General input sanitization (`InputSanitizer`, `ThreatType` enum)
- PII redaction
- Audit logging
- Security runner & compliance checking
- Codebase tracking

### Import Rules
- **MAY** import from: `grid.auth`, stdlib, third-party libs
- **MUST NOT** import from: `application.*` (app layer)

---

## `src/application/mothership/security/` — Application-Layer Security

**Owner:** Mothership application team
**Layer:** Application (imports from infra, never imported by infra)

### Responsibilities
- JWT authentication & token revocation
- RBAC roles & permissions (re-exports `grid.auth.rbac`)
- Secret strength validation
- CORS configuration
- API-specific threat patterns (`ThreatCategory` with HTTP-specific attack types)
- API sentinel defaults & security auditing
- Credential validation
- AI safety (application-level)

### Import Rules
- **MAY** import from: `grid.security`, `grid.auth`, stdlib, third-party libs
- **MUST NOT** be imported by: `grid.*` (infra layer)

---

## `src/grid/auth/` — Shared Auth Types

**Owner:** Core platform team
**Layer:** Infrastructure (shared types for both layers)

### Responsibilities
- RBAC types: `Role`, `Permission`, `ROLE_PERMISSIONS`
- Auth middleware, service, token management

### Import Rules
- **MAY** import from: stdlib, third-party libs
- **MAY** be imported by: both `grid.*` and `application.*`

---

## Overlap Notes

| Concept | `grid/security/` | `mothership/security/` | Resolution |
|---|---|---|---|
| Threat categories | `ThreatCategory` (broad: INJECTION, XSS, etc.) | `ThreatCategory` (specific: SQLI, COMMAND_INJECTION, etc.) | Intentionally different granularity. API-level is HTTP-specific. |
| Input sanitization | `InputSanitizer` + `ThreatType` | `InputSanitizer` + `SQLiFilter` + `XSSDetector` | API layer may delegate to infra for core logic. |
| RBAC | `grid.auth.rbac` (canonical) | Re-exports from `grid.auth.rbac` | Single source of truth in `grid/auth/`. |
