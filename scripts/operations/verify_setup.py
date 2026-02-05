"""
Environment Verification Script
===============================
Validates that all environment setup steps completed successfully.
"""

import sys
import importlib


def verify_environment():
    """Verify environment setup is complete."""
    checks = {
        "Python Version": sys.version_info >= (3, 7),
        "Wheel Installed": importlib.util.find_spec("wheel") is not None,
        "No Duplicate Paths": len(sys.path) == len(set(sys.path)),
        "Parasite Guard Available": importlib.util.find_spec("grid.security.parasite_guard") is not None,
    }

    print("Environment Verification Results:")
    print("-" * 40)

    passed = 0
    failed = 0

    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {check}: {status}")

        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 40)
    print(f"Total: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n✅ All checks passed!")
        return 0
    else:
        print(f"\n❌ {failed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(verify_environment())
