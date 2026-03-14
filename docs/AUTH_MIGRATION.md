# Auth Provider Migration Guide

> **TDC-0002** | Status: Complete | Date: 2026-03-14

## Overview

GRID Mothership now supports pluggable authentication providers. The system can switch between the **internal JWT provider** (default, backward-compatible) and **external OAuth2/OIDC providers** (Auth0, Keycloak, Okta, etc.) via a single environment variable.

## Architecture

```
┌─────────────────────────────────────┐
│         routers/auth.py             │  ← login, refresh, validate, logout
│    (uses get_auth_provider())       │
└──────────────┬──────────────────────┘
               │
     ┌─────────▼─────────┐
     │   AuthProvider     │  ← abstract interface
     │   (auth_provider.py)│
     └─────┬─────────┬───┘
           │         │
    ┌──────▼──┐  ┌───▼──────────┐
    │Internal │  │  OAuth2       │
    │JWT      │  │  Provider     │
    │Provider │  │  (OIDC/JWKS) │
    └─────────┘  └──────────────┘
```

### Key files

| File | Purpose |
|------|---------|
| `security/auth_provider.py` | Provider abstraction, factory, both implementations |
| `security/auth.py` | `verify_jwt_token()` now routes through provider |
| `routers/auth.py` | Login/refresh endpoints use provider |
| `config/__init__.py` | `SecuritySettings` includes provider config |

## Configuration

### Internal JWT (default — no changes needed)

```bash
# This is the default. No env vars required for backward compatibility.
MOTHERSHIP_AUTH_PROVIDER=internal
```

### External OAuth2/OIDC

```bash
MOTHERSHIP_AUTH_PROVIDER=oauth2
MOTHERSHIP_OAUTH2_ISSUER_URL=https://auth.example.com/realms/grid
MOTHERSHIP_OAUTH2_CLIENT_ID=grid-api
MOTHERSHIP_OAUTH2_CLIENT_SECRET=your-client-secret
MOTHERSHIP_OAUTH2_AUDIENCE=grid-api           # optional
MOTHERSHIP_OAUTH2_JWKS_URI=                   # auto-derived from issuer if empty
MOTHERSHIP_OAUTH2_TOKEN_ENDPOINT=             # auto-derived from issuer if empty
MOTHERSHIP_OAUTH2_USERINFO_ENDPOINT=          # optional
```

### Keycloak example

```bash
MOTHERSHIP_AUTH_PROVIDER=oauth2
MOTHERSHIP_OAUTH2_ISSUER_URL=https://keycloak.company.com/realms/grid
MOTHERSHIP_OAUTH2_CLIENT_ID=grid-mothership
MOTHERSHIP_OAUTH2_CLIENT_SECRET=abc123
```

### Auth0 example

```bash
MOTHERSHIP_AUTH_PROVIDER=oauth2
MOTHERSHIP_OAUTH2_ISSUER_URL=https://grid-dev.us.auth0.com/
MOTHERSHIP_OAUTH2_CLIENT_ID=abc123
MOTHERSHIP_OAUTH2_CLIENT_SECRET=xyz789
MOTHERSHIP_OAUTH2_AUDIENCE=https://api.grid.example.com
```

## Rollback Procedure

To rollback to internal JWT at any time:

```bash
# Option 1: Remove the env var (defaults to internal)
unset MOTHERSHIP_AUTH_PROVIDER

# Option 2: Explicitly set to internal
MOTHERSHIP_AUTH_PROVIDER=internal
```

No code changes or redeployment of code required — just restart the service.

## Claim Mapping

External providers map claims to internal user fields. Default mapping:

| External Claim | Internal Field |
|----------------|----------------|
| `sub` | `user_id` |
| `email` | `email` |
| `preferred_username` | `username` |
| `realm_access.roles` | `roles` |

Custom mappings can be configured in `OAuth2ProviderConfig.claim_map`.

## Token Verification Flow

1. Request arrives with `Authorization: Bearer <token>`
2. `security/auth.py:verify_jwt_token()` calls `get_auth_provider().verify_token(token)`
3. **Internal provider**: Verifies with local secret + checks revocation list
4. **OAuth2 provider**: Fetches JWKS from issuer, verifies RS256 signature + audience + issuer
5. Returns normalized `AuthUser` with mapped claims → RBAC role resolution

## API Compatibility

All existing API contracts are preserved:

- `POST /auth/login` — works with both providers
- `POST /auth/refresh` — works with both providers  
- `GET /auth/validate` — works with both providers
- `GET /auth/me` — works with both providers
- `POST /auth/logout` — internal: revokes via JTI; oauth2: calls provider revocation endpoint

## Testing

```bash
# Run auth-related tests
uv run pytest tests/unit/ -q -k "auth or jwt or session or token or security"

# Full unit suite
uv run pytest tests/unit/ -q --tb=short
```

## Dependencies

The OAuth2 provider requires `httpx` for token endpoint calls (already in project dependencies via FastAPI). JWKS verification uses `PyJWT`'s built-in `PyJWKClient` (already a dependency).

No new packages required.
