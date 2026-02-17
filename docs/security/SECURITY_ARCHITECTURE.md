# Security Architecture

## Overview

The Mothership Cockpit API implements a **deny-by-default** security posture with explicit configuration required for production deployments.

## Security Principles

1. **Deny by Default**: All security controls default to the most restrictive setting
2. **Explicit Configuration**: Production deployments MUST explicitly configure security settings
3. **Defense in Depth**: Multiple layers of security (authentication, authorization, CORS, rate limiting, request size limits)
4. **Secure Defaults**: Sensible defaults that favor security over convenience

## Security Modules

### Authentication (`application/mothership/security/auth.py`)

- **API Key Authentication**: Header-based API key validation
- **JWT Bearer Token**: Standard OAuth2 Bearer token authentication
- **Development Bypass**: Optional development mode bypass (explicit opt-in required)

### CORS (`application/mothership/security/cors.py`)

- **Default**: Empty origins list (deny all cross-origin requests)
- **Production**: Wildcard (`*`) is rejected; explicit origins required
- **Validation**: Origin format validation and sanitization

### Request Limits (`application/mothership/middleware/request_size.py`)

- **Default**: 10MB maximum request body size
- **Configurable**: Via `MOTHERSHIP_MAX_REQUEST_SIZE_BYTES` environment variable
- **Protection**: Prevents DoS attacks via large request bodies

## Configuration

### Environment Variables

```bash
# CORS (REQUIRED in production)
MOTHERSHIP_CORS_ORIGINS=https://example.com,https://app.example.com

# Security (REQUIRED in production)
MOTHERSHIP_SECRET_KEY=<32+ character secret key>

# Optional
MOTHERSHIP_MAX_REQUEST_SIZE_BYTES=10485760  # 10MB
MOTHERSHIP_CORS_CREDENTIALS=false
```

### Defaults

- **CORS Origins**: Empty list (deny all)
- **CORS Credentials**: `false`
- **Request Size Limit**: 10MB
- **Authentication**: Required in production
- **Rate Limiting**: Enabled by default

## Security Headers

The application automatically adds security headers via `SecurityHeadersMiddleware`:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=()`

## Validation

Security settings are validated at startup:

- Secret key length (minimum 32 characters)
- CORS wildcard rejection in production
- Request size limit warnings (>100MB)
- Configuration warnings logged during startup

## Development Mode

Development mode (`MOTHERSHIP_ENVIRONMENT=development`) allows:

- Unauthenticated access (if explicitly enabled)
- More permissive CORS (but still requires explicit configuration)
- Debug error messages

**Note**: Development mode settings are NOT suitable for production.
