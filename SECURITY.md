# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.7.x   | ✅ Current release  |
| 2.6.x   | ✅ Security fixes   |
| < 2.6   | ❌ End of life      |

## Reporting a Vulnerability

If you discover a security vulnerability in GRID, **please do not open a public issue.**

Instead, report it privately using one of the following methods:

1. **GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/GRID-INTELLIGENCE/GRID/security/advisories/new)
2. **Email**: Send details to **irfankabir02@gmail.com** with the subject line `[GRID SECURITY]`

### What to Include

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Affected versions (if known)
- Any suggested fix or mitigation (optional)

### What to Expect

- **Acknowledgement** within 48 hours of your report
- **Assessment** within 7 days — we will confirm whether the issue is accepted, provide a severity rating, and share a remediation timeline
- **Fix and disclosure** — accepted vulnerabilities are patched in a security release. You will be credited in the release notes unless you prefer to remain anonymous

### Scope

The following are in scope for security reports:

- `grid-intelligence` Python package (`src/`, `safety/`, `security/`, `boundaries/`)
- `grid-safety` Python package (`safety/`)
- CI/CD pipeline configuration (`.github/workflows/`)
- Transition Gate sealed-envelope handshake (`boundaries/transition_gate/`)
- Authentication, authorization, and token management
- Path traversal, injection, or input validation bypasses
- Dependency vulnerabilities in direct dependencies

The following are **out of scope**:

- The landing page (`landing/`) — static HTML/CSS/JS with no server-side processing
- Demo or example scripts (`examples/`, `demos/`)
- Development tooling (`dev/`, `scripts/`)

## Security Architecture

GRID implements defense-in-depth with multiple layers:

- **Zero-trust transfer boundary** — Sealed-envelope handshake with HMAC-SHA256 fingerprinting, single-use nonces, and timing-safe comparison
- **Fail-closed verification** — Any verification step failure rejects the entire envelope
- **JWT token management** — Access/refresh tokens with revocation list and automatic expiration
- **Rate limiting and input sanitization** — API-level guardrails with configurable thresholds
- **Append-only audit logging** — All verification events logged to NDJSON for forensic review

For full details, see [`docs/security/SECURITY_ARCHITECTURE.md`](docs/security/SECURITY_ARCHITECTURE.md).