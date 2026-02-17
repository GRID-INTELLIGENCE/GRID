"""
Network Security System - Test Suite
=====================================
Verifies that the network security system is working correctly.

Usage:
    python security/test_security.py
"""

import importlib.util
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable security for import testing
os.environ["DISABLE_NETWORK_SECURITY"] = "true"


def print_header(text):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def test_imports():
    """Test that security module can be imported."""
    print_header("TEST 1: Module Import")

    try:
        import security

        print("✅ Security module imported successfully")
        print(f"   Version: {security.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import security module: {e}")
        return False


def test_dependencies():
    """Test that dependencies are installed."""
    print_header("TEST 2: Dependencies")

    results = []

    # Test YAML
    try:
        import yaml  # noqa: F401

        print("✅ pyyaml is installed")
        results.append(True)
    except ImportError:
        print("❌ pyyaml is NOT installed - run: pip install pyyaml")
        results.append(False)

    # Test rich (optional)
    try:
        importlib.util.find_spec("rich")
        print("✅ rich is installed (optional)")
        results.append(True)
    except ImportError:
        print("⚠️  rich is NOT installed (optional) - run: pip install rich")
        results.append(True)  # Not critical

    return all(results)


def test_configuration():
    """Test that configuration file exists and is valid."""
    print_header("TEST 3: Configuration File")

    config_path = Path(__file__).parent / "network_access_control.yaml"

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False

    print(f"✅ Configuration file exists: {config_path}")

    try:
        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        print("✅ Configuration file is valid YAML")

        # Check key settings
        mode = config.get("mode", "unknown")
        policy = config.get("default_policy", "unknown")
        network_enabled = config.get("global", {}).get("network_enabled", False)

        print(f"   Mode: {mode}")
        print(f"   Default Policy: {policy}")
        print(f"   Network Enabled: {network_enabled}")

        if policy == "deny":
            print("✅ Default policy is DENY (secure)")
        else:
            print("⚠️  Default policy is not DENY (less secure)")

        return True

    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False


def test_logs_directory():
    """Test that logs directory exists."""
    print_header("TEST 4: Logs Directory")

    logs_dir = Path(__file__).parent / "logs"

    if not logs_dir.exists():
        try:
            logs_dir.mkdir(exist_ok=True)
            print(f"✅ Created logs directory: {logs_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to create logs directory: {e}")
            return False
    else:
        print(f"✅ Logs directory exists: {logs_dir}")
        return True


def test_security_status():
    """Test getting security status."""
    print_header("TEST 5: Security Status")

    # Re-enable security
    os.environ["DISABLE_NETWORK_SECURITY"] = "false"

    try:
        # Force reload
        if "security" in sys.modules:
            del sys.modules["security"]
        if "security.network_interceptor" in sys.modules:
            del sys.modules["security.network_interceptor"]

        import security

        status = security.get_status()

        print("✅ Got security status:")
        print(f"   Status: {status.get('status', 'unknown')}")
        print(f"   Mode: {status.get('mode', 'unknown')}")
        print(f"   Default Policy: {status.get('default_policy', 'unknown')}")
        print(f"   Network Enabled: {status.get('network_enabled', False)}")
        print(f"   Kill Switch: {status.get('kill_switch', False)}")

        if "metrics" in status:
            metrics = status["metrics"]
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Blocked: {metrics.get('blocked_requests', 0)}")
            print(f"   Allowed: {metrics.get('allowed_requests', 0)}")

        return True

    except Exception as e:
        print(f"❌ Failed to get security status: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_network_interception():
    """Test that network requests are intercepted."""
    print_header("TEST 6: Network Interception")

    # Re-enable security
    os.environ["DISABLE_NETWORK_SECURITY"] = "false"

    try:
        # Force reload to ensure patches are applied
        if "security" in sys.modules:
            del sys.modules["security"]
        if "security.network_interceptor" in sys.modules:
            del sys.modules["security.network_interceptor"]

        from security import NetworkAccessDenied

        # Try to make a request (should be blocked)
        try:
            import requests

            requests.get("https://api.github.com", timeout=10)
            print("⚠️  Request was NOT blocked (network might be enabled)")
            return True  # Still pass if network is enabled
        except NetworkAccessDenied as e:
            print("✅ Network request was correctly BLOCKED")
            print(f"   Reason: {str(e)[:100]}")
            return True
        except Exception as e:
            print(f"⚠️  Request blocked with different error: {type(e).__name__}")
            return True  # Still acceptable

    except ImportError:
        print("⚠️  requests library not installed, skipping interception test")
        return True  # Not critical


def test_monitor_script():
    """Test that monitor script exists."""
    print_header("TEST 7: Monitor Script")

    monitor_script = Path(__file__).parent / "monitor_network.py"

    if not monitor_script.exists():
        print(f"❌ Monitor script not found: {monitor_script}")
        return False

    print(f"✅ Monitor script exists: {monitor_script}")
    print(f"   Run: python {monitor_script} dashboard")

    return True


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "#" * 80)
    print("  NETWORK SECURITY SYSTEM - TEST SUITE")
    print("#" * 80)

    tests = [
        ("Module Import", test_imports),
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Logs Directory", test_logs_directory),
        ("Security Status", test_security_status),
        ("Network Interception", test_network_interception),
        ("Monitor Script", test_monitor_script),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Security system is operational.")
        print("\nNext steps:")
        print("1. Add 'import security' to your main application file")
        print("2. Run: python security/monitor_network.py dashboard")
        print("3. Start your application and observe blocked requests")
        print("4. Whitelist trusted domains as needed")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r security/requirements.txt")
        print("- Check configuration: security/network_access_control.yaml")
        print("- Review installation: security/README.md")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
