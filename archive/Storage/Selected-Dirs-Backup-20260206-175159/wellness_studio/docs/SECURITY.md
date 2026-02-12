# Security & Privacy Documentation

## Wellness Studio Security Architecture

This document outlines the comprehensive security and privacy safeguards implemented in Wellness Studio.

## Table of Contents

1. [Overview](#overview)
2. [PII/PHI Protection](#piiphi-protection)
3. [AI Safety Guardrails](#ai-safety-guardrails)
4. [Audit & Compliance](#audit--compliance)
5. [Rate Limiting & Abuse Prevention](#rate-limiting--abuse-prevention)
6. [HIPAA Compliance](#hipaa-compliance)
7. [Testing](#testing)

## Overview

Wellness Studio implements defense-in-depth security with multiple layers of protection:

- **Input Validation**: Sanitization and validation of all inputs
- **PII/PHI Detection**: Automatic detection and protection of sensitive data
- **AI Safety**: Content filtering and ethical guidelines
- **Audit Logging**: Comprehensive audit trails
- **Rate Limiting**: Prevention of abuse and DoS attacks
- **Data Retention**: Automated data lifecycle management

## PII/PHI Protection

### PIIDetector

The `PIIDetector` class automatically identifies and protects:

- **Government IDs**: SSN, Medicare ID, Passport numbers
- **Contact Information**: Phone, Email, Addresses
- **Financial Data**: Credit cards, Bank accounts
- **Health Information**: MRN, Insurance ID, DOB

### Usage Example

```python
from wellness_studio.security import PIIDetector

detector = PIIDetector()

# Detect PII in text
text = "Patient John Smith, SSN: 123-45-6789"
entities = detector.detect_pii(text)

# Assess risk
assessment = detector.assess_risk_level(text)
print(f"Risk Level: {assessment['risk_level']}")

# Sanitize
sanitized, mapping = detector.sanitize_text(text, replacement_mode='hash')
```

### Risk Levels

- **CRITICAL**: Multiple PHI elements detected - Immediate sanitization required
- **HIGH**: PHI or multiple PII elements present
- **MEDIUM**: Some PII elements detected
- **LOW**: No PII detected

### Sanitization Modes

1. **hash**: Replace with hash-based identifier (default)
2. **mask**: Partial masking (e.g., XXX-XX-6789)
3. **remove**: Full redaction with tags

## AI Safety Guardrails

### ContentSafetyFilter

Prevents:
- **Prompt Injection**: "Ignore previous instructions", "DAN mode"
- **Harmful Content**: Self-harm, overdose instructions
- **Inappropriate Requests**: Fake prescriptions, third-party data access
- **Medical Misinformation**: Unverified cure claims

### Usage Example

```python
from wellness_studio.security import ContentSafetyFilter

safety = ContentSafetyFilter()

# Check input
is_safe, violations = safety.validate_input(user_input)

if not is_safe:
    for violation in violations:
        print(f"Blocked: {violation.description}")

# Check AI output
is_safe, violations = safety.validate_output(ai_response)
```

### EthicalGuidelines

Ensures recommendations follow ethical principles:
- Autonomy: Respect patient decision-making
- Beneficence: Act in best interest
- Non-maleficence: Do no harm
- Justice: Fair recommendations
- Transparency: Clear evidence levels

## Audit & Compliance

### AuditLogger

Comprehensive audit trail for:
- All data access
- PII detection/sanitization
- Model inference
- Safety violations
- System errors

### Usage Example

```python
from wellness_studio.security import AuditLogger, AuditEventType

logger = AuditLogger()

# Log data input
logger.log_data_input(
    source_type="pdf",
    content_hash="abc123...",
    size_bytes=2048,
    pii_detected=True
)

# Log PII sanitization
logger.log_pii_sanitization(
    content_hash="abc123...",
    entities_removed=3,
    sanitization_method="hash"
)

# Query audit trail
events = logger.get_audit_trail(
    start_date=datetime.now() - timedelta(days=7)
)
```

### Audit Event Types

- `DATA_INPUT`: File/text/audio input received
- `DATA_PROCESSING`: Processing operations
- `DATA_ACCESS`: Data access events
- `PII_DETECTED`: PII detection events
- `PII_SANITIZED`: Sanitization operations
- `MODEL_INFERENCE`: AI model usage
- `SAFETY_VIOLATION`: Blocked/flagged content
- `REPORT_GENERATED`: Report creation
- `ERROR_OCCURRED`: System errors

## Rate Limiting & Abuse Prevention

### RateLimiter

Multiple strategies:
- **Sliding Window**: Smooth rate limiting
- **Fixed Window**: Simple burst control
- **Token Bucket**: Burst allowance with rate limiting

Multiple scopes:
- **USER**: Per-user limits
- **IP**: Per-IP address limits
- **GLOBAL**: System-wide limits
- **SESSION**: Per-session limits

### Usage Example

```python
from wellness_studio.security import RateLimiter, RateLimitConfig

config = RateLimitConfig(
    requests_per_window=100,
    window_seconds=60,
    block_duration_seconds=300
)

limiter = RateLimiter(config)

# Check and record request
status = limiter.record_request("user_001")

if status.allowed:
    print(f"Remaining: {status.remaining}")
else:
    print(f"Retry after: {status.retry_after} seconds")
```

### AbusePrevention

Detects suspicious patterns:
- Rapid-fire requests (>60/hour)
- Burst attacks (>10 in 10 seconds)
- Repetitive content submission

### CircuitBreaker

Fault tolerance for external services:
- Opens after threshold failures
- Enters half-open state for recovery
- Prevents cascade failures

## HIPAA Compliance

### Technical Safeguards (164.312)

#### Access Control (a)
- Unique user identification
- Session management
- Access logging

#### Audit Controls (b)
- Comprehensive audit trails
- Immutable logs
- Retention policies

#### Integrity (c)
- Data integrity validation
- Tamper detection
- Hash verification

#### Transmission Security (e)
- Content hashing
- Encryption at rest
- Secure key management

### Administrative Safeguards (164.308)

- Security management
- Information access management
- Workforce training logging
- Evaluation logging

### Usage Example

```python
# HIPAA-compliant data handling
from wellness_studio.security import (
    PIIDetector,
    AuditLogger,
    DataRetentionPolicy,
    SensitivityLevel
)

# 1. Detect and sanitize PHI
detector = PIIDetector()
entities = detector.detect_pii(text)
sanitized, mapping = detector.sanitize_text(text)

# 2. Log all access
logger = AuditLogger()
logger.log_data_input("text", content_hash, len(text), pii_detected=True)
logger.log_pii_sanitization(content_hash, len(entities), "hash")

# 3. Enforce retention policy
policy = DataRetentionPolicy(retention_days=30)
policy.register_data(content_hash, SensitivityLevel.PHI)

# Check if should dispose
if policy.should_dispose(content_hash):
    secure_delete(data)
```

## Testing

### Running Security Tests

```bash
# Run all security tests
pytest tests/test_security_*.py -v

# Run specific test categories
pytest tests/test_security_pii.py -v          # PII tests
pytest tests/test_security_ai_safety.py -v    # AI safety tests
pytest tests/test_security_audit.py -v        # Audit tests
pytest tests/test_hipaa_compliance.py -v      # HIPAA tests
pytest tests/test_rate_limiting.py -v         # Rate limiting tests

# Run with coverage
pytest tests/test_security_*.py --cov=wellness_studio.security --cov-report=html
```

### Test Coverage

- **PII Detection**: 20+ test cases
- **Sanitization**: 15+ test cases
- **AI Safety**: 25+ test cases
- **Audit Logging**: 20+ test cases
- **Rate Limiting**: 15+ test cases
- **HIPAA Compliance**: 20+ test cases
- **Integration**: 10+ test cases

### Security Test Files

1. `test_security_pii.py` - PII/PHI detection and sanitization
2. `test_security_ai_safety.py` - Content filtering and ethics
3. `test_security_audit.py` - Audit logging and trails
4. `test_security_integration.py` - End-to-end security
5. `test_hipaa_compliance.py` - HIPAA technical safeguards
6. `test_rate_limiting.py` - Rate limiting and abuse prevention

## Security Checklist

### Before Deployment

- [ ] All PII detection patterns tested
- [ ] Sanitization methods verified
- [ ] AI safety filters active
- [ ] Audit logging enabled
- [ ] Rate limits configured
- [ ] Data retention policies set
- [ ] HIPAA compliance verified
- [ ] Security tests passing (>90% coverage)

### Configuration Recommendations

```python
# Recommended production settings
PII_SANITIZATION_MODE = "hash"  # or "mask" for debugging
RATE_LIMIT_REQUESTS = 100       # per minute
RATE_LIMIT_WINDOW = 60          # seconds
DATA_RETENTION_DAYS = 30        # for non-PHI
PHI_RETENTION_DAYS = 7          # immediate disposal preferred
AUDIT_LOG_RETENTION = 2555      # days (7 years for HIPAA)
```

## Incident Response

### Detected PII in Output

1. Immediately sanitize
2. Log incident
3. Notify administrator
4. Review sanitization pipeline

### Safety Violation Detected

1. Block request/response
2. Log violation details
3. Flag user if repeated
4. Alert security team

### Suspicious Activity

1. Analyze access patterns
2. Check for abuse indicators
3. Apply stricter rate limits
4. Consider temporary block

## Compliance Certifications

Wellness Studio security features support:
- **HIPAA**: Technical safeguards implemented
- **GDPR**: Data minimization and retention
- **SOC 2**: Audit trails and access controls
- **ISO 27001**: Security management framework

## Contact & Support

For security issues:
1. Review this documentation
2. Check test suite for examples
3. Examine audit logs
4. Contact security team

---

**Note**: This system is designed for educational wellness purposes. Always consult healthcare professionals for medical decisions.
