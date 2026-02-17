"""
Network Security System
=======================
Centralized network access control and monitoring for the entire codebase.

This module enforces strict network access policies, monitors all outbound
connections, and provides tools for security analysis and whitelisting.

Usage:
    # Import to automatically apply security patches
    import security

    # Or manually control initialization
    from security.network_interceptor import apply_all_patches, nac
    apply_all_patches()

    # Check metrics
    metrics = nac.get_metrics()
    print(f"Blocked: {metrics['blocked_requests']}")

    # Temporarily disable for testing (NOT recommended in production)
    import os
    os.environ['DISABLE_NETWORK_SECURITY'] = 'true'
"""

import logging
import os
import sys
from pathlib import Path

__version__ = "1.0.0"
__author__ = "Security Team"

logger = logging.getLogger(__name__)

# Ensure logs directory exists
SECURITY_DIR = Path(__file__).parent
LOGS_DIR = SECURITY_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Initialize network access control
try:
    from .network_interceptor import (
        DataLeakDetected,
        NetworkAccessControl,
        NetworkAccessDenied,
        apply_all_patches,
        enforce_network_policy,
        nac,
    )

    # Check if security should be disabled
    if os.environ.get("DISABLE_NETWORK_SECURITY") == "true":
        logger.warning("⚠️  NETWORK SECURITY DISABLED - Set DISABLE_NETWORK_SECURITY=false to enable")
    else:
        logger.info("🔒 Network security system initialized")
        logger.info(f"📁 Config: {SECURITY_DIR / 'network_access_control.yaml'}")
        logger.info(f"📋 Logs: {LOGS_DIR}")
        logger.info("⚠️  ALL network access is DENIED by default")
        logger.info("💡 Use security/monitor_network.py to manage whitelist")

except ImportError as e:
    logger.error(f"Failed to initialize network security: {e}")
    logger.error("Install required dependencies: pip install pyyaml rich")
    NetworkAccessControl = None
    NetworkAccessDenied = Exception
    DataLeakDetected = Exception
    nac = None
    enforce_network_policy = None
    apply_all_patches = None


def get_status() -> dict:
    """Get current security system status."""
    if nac is None:
        return {
            "status": "error",
            "message": "Security system not initialized",
            "network_enabled": False,
        }

    config = nac.config
    metrics = nac.get_metrics()

    return {
        "status": "active",
        "mode": config.get("mode", "unknown"),
        "default_policy": config.get("default_policy", "deny"),
        "network_enabled": config.get("global", {}).get("network_enabled", False),
        "kill_switch": config.get("emergency", {}).get("kill_switch", False),
        "localhost_only": config.get("emergency", {}).get("localhost_only", True),
        "metrics": metrics,
    }


def print_status():
    """Print security system status to console."""
    status = get_status()

    print("=" * 80)
    print("🔒 NETWORK SECURITY SYSTEM STATUS")
    print("=" * 80)

    if status["status"] == "error":
        print(f"❌ ERROR: {status['message']}")
        return

    print(f"Status: {status['status'].upper()}")
    print(f"Mode: {status['mode'].upper()}")
    print(f"Default Policy: {status['default_policy'].upper()}")
    print()

    print("Configuration:")
    print(f"  Network Enabled: {status['network_enabled']}")
    print(f"  Kill Switch: {status['kill_switch']}")
    print(f"  Localhost Only: {status['localhost_only']}")
    print()

    if "metrics" in status:
        metrics = status["metrics"]
        print("Metrics:")
        print(f"  Total Requests: {metrics['total_requests']}")
        print(f"  ✅ Allowed: {metrics['allowed_requests']}")
        print(f"  🚫 Blocked: {metrics['blocked_requests']}")
        print(f"  🚨 Data Leaks: {metrics['data_leaks_detected']}")
        print(f"  Uptime: {metrics.get('uptime_seconds', 0):.1f}s")

    print("=" * 80)


def enable_network():
    """Enable global network access."""
    if nac is None:
        print("❌ Security system not initialized")
        return False

    config = nac.config
    if "global" not in config:
        config["global"] = {}
    config["global"]["network_enabled"] = True

    # Reload config
    nac.config = config
    print("✅ Global network access ENABLED")
    return True


def disable_network():
    """Disable global network access."""
    if nac is None:
        print("❌ Security system not initialized")
        return False

    config = nac.config
    if "global" not in config:
        config["global"] = {}
    config["global"]["network_enabled"] = False

    # Reload config
    nac.config = config
    print("🚫 Global network access DISABLED")
    return True


def activate_kill_switch():
    """Activate emergency kill switch - blocks ALL network access."""
    if nac is None:
        print("❌ Security system not initialized")
        return False

    config = nac.config
    if "emergency" not in config:
        config["emergency"] = {}
    config["emergency"]["kill_switch"] = True

    # Reload config
    nac.config = config
    print("🚨 EMERGENCY KILL SWITCH ACTIVATED - ALL NETWORK ACCESS BLOCKED")
    return True


def deactivate_kill_switch():
    """Deactivate emergency kill switch."""
    if nac is None:
        print("❌ Security system not initialized")
        return False

    config = nac.config
    if "emergency" not in config:
        config["emergency"] = {}
    config["emergency"]["kill_switch"] = False

    # Reload config
    nac.config = config
    print("✅ Emergency kill switch deactivated")
    return True


def whitelist_domain(domain: str, description: str = ""):
    """Add domain to whitelist."""
    if nac is None:
        print("❌ Security system not initialized")
        return False

    config = nac.config
    if "whitelist" not in config:
        config["whitelist"] = {"rules": []}

    # Check if already whitelisted
    for rule in config["whitelist"]["rules"]:
        if rule.get("domain") == domain:
            print(f"⚠️  Domain {domain} is already whitelisted")
            return False

    # Add to whitelist
    from datetime import datetime, timezone

    rule = {
        "domain": domain,
        "protocol": "https",
        "description": description or "Added programmatically",
        "added_by": "api",
        "added_date": datetime.now(pytz.utc).isoformat(),
    }

    config["whitelist"]["rules"].append(rule)
    nac.config = config
    print(f"✅ Added {domain} to whitelist")
    return True


def get_blocked_requests(limit: int = 100):
    """Get list of blocked requests."""
    if nac is None:
        return []
    return nac.get_blocked_requests(limit=limit)


def get_allowed_requests(limit: int = 100):
    """Get list of allowed requests."""
    if nac is None:
        return []
    return nac.get_allowed_requests(limit=limit)


def generate_security_report():
    """Generate and save security report."""
    if nac is None:
        print("❌ Security system not initialized")
        return None

    filepath = nac.save_report()
    print(f"📄 Security report saved to: {filepath}")
    return filepath


# Export public API
__all__ = [
    "NetworkAccessControl",
    "NetworkAccessDenied",
    "DataLeakDetected",
    "nac",
    "enforce_network_policy",
    "apply_all_patches",
    "get_status",
    "print_status",
    "enable_network",
    "disable_network",
    "activate_kill_switch",
    "deactivate_kill_switch",
    "whitelist_domain",
    "get_blocked_requests",
    "get_allowed_requests",
    "generate_security_report",
]


# Print banner on import (only if interactive)
if hasattr(sys, "ps1") or os.environ.get("PYTHON_INTERACTIVE"):
    if os.environ.get("DISABLE_NETWORK_SECURITY") != "true":
        print()
        print("=" * 80)
        print("🔒 NETWORK SECURITY SYSTEM ACTIVE")
        print("=" * 80)
        print("⚠️  ALL network access is DENIED by default")
        print("💡 Use: python security/monitor_network.py dashboard")
        print("📖 Documentation: security/README.md")
        print("=" * 80)
        print()
