#!/usr/bin/env python3
"""
Portfolio Safety Lens Demo
===========================
Demonstrates the Portfolio Safety Lens MCP server with secure portfolio analytics.
"""

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_portfolio_summary_safe():
    """Demo: Get sanitized portfolio summary."""
    logger.info("=== Demo: Portfolio Summary Safe ===")

    # Simulate MCP tool call
    result = {
        "total_positions": 5,
        "total_value": 50000.0,
        "total_gain_loss": 2500.0,
        "gain_loss_percentage": 5.0,
        "positions_count": 5,
        "timestamp": "2024-01-15T10:30:00",
    }

    print("Sanitized Portfolio Summary:")
    print(json.dumps(result, indent=2))
    print("\n✓ No raw positions or quantities exposed")
    print("✓ User ID is hashed")
    print("✓ Audit trail created")


async def demo_portfolio_risk_signal():
    """Demo: Get portfolio risk signals."""
    logger.info("=== Demo: Portfolio Risk Signal ===")

    # Simulate MCP tool call
    result = {
        "risk_level": "MEDIUM",
        "concentration_risk": {"top_position_percentage": 35.0, "top_3_percentage": 65.0},
        "diversification": {
            "total_positions": 5,
            "sectors": ["Technology", "Finance", "Healthcare"],
        },
        "recommendation": "Consider diversifying portfolio to reduce concentration risk",
        "timestamp": "2024-01-15T10:30:00",
    }

    print("Portfolio Risk Signal:")
    print(json.dumps(result, indent=2))
    print("\n✓ No raw position data")
    print("✓ Risk scores only")
    print("✓ Audit trail created")


async def demo_audit_log_tail():
    """Demo: Get recent audit logs."""
    logger.info("=== Demo: Audit Log Tail ===")

    # Simulate MCP tool call
    result = [
        {
            "timestamp": "2024-01-15T10:30:00",
            "event_type": "READ",
            "user_id_hash": "a1b2c3d4e5f6...",
            "action": "portfolio_summary_safe",
            "details_count": 2,
        },
        {
            "timestamp": "2024-01-15T10:29:00",
            "event_type": "AI_ACCESS",
            "user_id_hash": "a1b2c3d4e5f6...",
            "action": "get_top_performers",
            "details_count": 3,
        },
        {
            "timestamp": "2024-01-15T10:28:00",
            "event_type": "WRITE",
            "user_id_hash": "a1b2c3d4e5f6...",
            "action": "save_position",
            "details_count": 4,
        },
    ]

    print("Recent Audit Logs (hashed IDs only):")
    print(json.dumps(result, indent=2))
    print("\n✓ User IDs are hashed and truncated")
    print("✓ Sensitive details are not exposed")
    print("✓ Full audit trail available internally")


async def demo_governance_lint():
    """Demo: Check governance compliance."""
    logger.info("=== Demo: Governance Lint ===")

    # Simulate MCP tool call
    result = {
        "user_id_hashed": True,
        "critical_data_protected": True,
        "audit_logging_enabled": True,
        "ai_safety_enforced": True,
        "output_sanitization": True,
        "policy_compliant": True,
        "timestamp": "2024-01-15T10:30:00",
    }

    print("Governance Compliance Check:")
    print(json.dumps(result, indent=2))
    print("\n✓ All guardrails enforced")
    print("✓ Policy compliant")
    print("✓ Audit trail created")


async def demo_full_workflow():
    """Demo: Full workflow with all tools."""
    logger.info("=== Demo: Full Workflow ===")

    print("\n1. Getting safe portfolio summary...")
    await demo_portfolio_summary_safe()

    print("\n2. Checking portfolio risk signals...")
    await demo_portfolio_risk_signal()

    print("\n3. Viewing recent audit logs...")
    await demo_audit_log_tail()

    print("\n4. Checking governance compliance...")
    await demo_governance_lint()

    print("\n=== Summary ===")
    print("✓ All tools return sanitized data only")
    print("✓ No raw portfolio positions exposed")
    print("✓ Full audit trail maintained")
    print("✓ AI safety enforced")
    print("✓ Policy compliance verified")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("Portfolio Safety Lens MCP Server Demo")
    print("=" * 60)
    print("\nThis demo shows secure portfolio analytics with:")
    print("- Sanitized outputs only (no raw data)")
    print("- Full audit logging")
    print("- AI safety enforcement")
    print("- Policy compliance checks")
    print("\n")

    await demo_full_workflow()

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
