"""
Comprehensive Security Demo
=============================
Demonstrate full security guardrails for portfolio data.

Security Level: CRITICAL
Privacy: Personal Sensitive Information
AI Safety: Full privileges
"""

from coinbase.security.ai_safety import (
    get_ai_safety,
)
from coinbase.security.audit_logger import AuditEventType, get_audit_logger
from coinbase.security.portfolio_security import (
    AccessLevel,
    get_portfolio_security,
)


def comprehensive_security_demo():
    """
    Demonstrate comprehensive security for portfolio data.

    Shows: Full security guardrails, privacy, AI safety, audit logging
    """
    print("=" * 70)
    print("Comprehensive Security Demo - Portfolio Data")
    print("=" * 70)
    print()

    # Initialize security components
    print("Step 1: Initialize Security Components")
    print("-" * 70)

    portfolio_security = get_portfolio_security()
    ai_safety = get_ai_safety()
    audit_logger = get_audit_logger()

    print("✓ PortfolioDataSecurity initialized")
    print("✓ PortfolioAISafety initialized")
    print("✓ PortfolioAuditLogger initialized")
    print()

    # Step 2: User authentication and security context
    print("Step 2: User Authentication & Security Context")
    print("-" * 70)

    user_id = "user123"
    hashed_id = portfolio_security.hash_user_id(user_id)

    print(f"User ID: {user_id}")
    print(f"Hashed ID: {hashed_id[:16]}...")

    # Create security context
    security_context = portfolio_security.create_security_context(
        user_id=user_id,
        access_level=AccessLevel.READ_WRITE,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
    )

    print("Security Context Created")
    print(f"  Access Level: {security_context.access_level.value}")
    print(f"  Session ID: {security_context.session_id[:16]}...")
    print()

    # Step 3: Validate access
    print("Step 3: Access Validation")
    print("-" * 70)

    access_granted = portfolio_security.validate_access(
        user_id=user_id, access_level=AccessLevel.READ_WRITE, context=security_context
    )

    print(f"Access Granted: {access_granted}")

    if access_granted:
        audit_logger.log_event(
            event_type=AuditEventType.ACCESS_GRANTED,
            user_id_hash=hashed_id,
            details="Portfolio data access granted",
            ip_address="192.168.1.100",
        )
    print()

    # Step 4: Data encryption
    print("Step 4: Data Encryption")
    print("-" * 70)

    sensitive_data = "Portfolio value: $50,000 | Total positions: 5"
    encrypted = portfolio_security.encrypt_data(sensitive_data)
    decrypted = portfolio_security.decrypt_data(encrypted)

    print(f"Original: {sensitive_data}")
    print(f"Encrypted: {encrypted[:32]}...")
    print(f"Decrypted: {decrypted}")
    print()

    # Step 5: AI safety validation
    print("Step 5: AI Safety Validation")
    print("-" * 70)

    ai_context = ai_safety.create_safety_context(purpose="portfolio_analysis", approved=True)

    ai_access = ai_safety.validate_ai_access(
        user_id=user_id, purpose="portfolio_analysis", context=ai_context
    )

    print(f"AI Access Granted: {ai_access}")
    print(f"  Safety Level: {ai_context.safety_level.value}")
    print(f"  Sensitivity: {ai_context.sensitivity.value}")
    print(f"  Purpose: {ai_context.purpose}")
    print()

    # Step 6: Data sanitization
    print("Step 6: Data Sanitization")
    print("-" * 70)

    portfolio_data = {
        "total_positions": 5,
        "total_value": 50000.0,
        "total_gain_loss": 5000.0,
        "gain_loss_percentage": 10.0,
        "positions": [
            {"symbol": "AAPL", "quantity": 50, "value": 10000.0},
            {"symbol": "MSFT", "quantity": 30, "value": 15000.0},
        ],
    }

    sanitized = portfolio_security.sanitize_portfolio_data(portfolio_data)
    ai_sanitized = ai_safety.sanitize_for_ai_output(portfolio_data)

    print("Sanitized for Output:")
    print(f"  Total Positions: {sanitized['total_positions']}")
    print(f"  Total Value: ${sanitized['total_value']:,.2f}")
    print(f"  Positions Count: {sanitized['positions_count']}")
    print("  (Individual positions removed)")

    print("\nSanitized for AI:")
    print(f"  Total Positions: {ai_sanitized['total_positions']}")
    print(f"  Total Value: ${ai_sanitized['total_value']:,.2f}")
    print(f"  Positions Count: {ai_sanitized['positions_count']}")
    print("  (Individual positions removed)")
    print()

    # Step 7: Audit logging
    print("Step 7: Audit Logging")
    print("-" * 70)

    # Log data read
    audit_logger.log_event(
        event_type=AuditEventType.DATA_READ,
        user_id_hash=hashed_id,
        details="Portfolio positions read from database",
        metadata={"positions_count": 5},
    )

    # Log query executed
    audit_logger.log_event(
        event_type=AuditEventType.QUERY_EXECUTED,
        user_id_hash=hashed_id,
        details="Portfolio analysis query executed",
        metadata={"query_type": "portfolio_summary"},
    )

    # Get audit log
    audit_log = audit_logger.get_audit_log(limit=10)
    print(f"Audit Log Entries: {len(audit_log)}")
    for event in audit_log[-5:]:
        print(f"  {event.event_type.value}: {event.details}")
    print()

    # Step 8: Security events
    print("Step 8: Security Events")
    print("-" * 70)

    security_events = audit_logger.get_security_events(limit=5)
    print(f"Security Events: {len(security_events)}")
    for event in security_events:
        print(f"  {event.event_type.value}: {event.details}")
    print()

    # Summary
    print("=" * 70)
    print("Security Implementation Complete")
    print("=" * 70)
    print("\nSecurity Features Implemented:")
    print("• User ID hashing (SHA-256 double hashing)")
    print("• Data encryption/decryption")
    print("• Access control validation")
    print("• AI safety privilege checks")
    print("• Data sanitization for output")
    print("• Comprehensive audit logging")
    print("• Security event tracking")
    print()
    print("Portfolio Data Treated As:")
    print("• Personal Sensitive Information")
    print("• Security Level: CRITICAL")
    print("• AI Safety: Full privileges required")
    print()
    print("Guardrails:")
    print("• Encryption at rest and in transit")
    print("• Access controls and validation")
    print("• AI safety privilege checks")
    print("• Audit logging for all operations")
    print("• Data sanitization for output")
    print()


if __name__ == "__main__":
    comprehensive_security_demo()
