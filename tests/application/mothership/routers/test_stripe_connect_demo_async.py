"""
Tests for async patterns in stripe_connect_demo router.

Ensures no blocking calls in async endpoints and proper async/await usage.
"""

import asyncio
import inspect
import re
from pathlib import Path

import pytest

# Import the router module to inspect
from application.mothership.routers import stripe_connect_demo


class TestAsyncPatterns:
    """Test that async patterns are correctly implemented."""

    def test_no_blocking_stripe_calls(self):
        """Verify all Stripe SDK calls are wrapped with asyncio.to_thread."""
        router_file = Path(stripe_connect_demo.__file__)
        content = router_file.read_text()

        # Find all async functions
        async_func_pattern = r"async def (\w+)\([^)]*\):"
        async_functions = re.finditer(async_func_pattern, content)

        violations = []
        for match in async_functions:
            func_name = match.group(1)
            start_pos = match.end()
            # Find the function body (next def/class/EOF)
            next_def = content.find("\n    def ", start_pos)
            next_class = content.find("\nclass ", start_pos)
            next_async = content.find("\nasync def ", start_pos + 1)
            end_pos = min(
                pos for pos in [next_def, next_class, next_async, len(content)] if pos > 0
            )

            func_body = content[start_pos:end_pos]

            # Check for unwrapped Stripe calls
            # Pattern: stripe_client.*.retrieve( or stripe_client.*.create( or stripe_client.parse_*
            stripe_call_patterns = [
                r"stripe_client\.v\d+\.core\.accounts\.retrieve\(",
                r"stripe_client\.v\d+\.core\.events\.retrieve\(",
                r"stripe_client\.v\d+\.core\.account_links\.create\(",
                r"stripe_client\.v\d+\.core\.accounts\.create\(",
                r"stripe_client\.v\d+\.products\.(create|list)\(",
                r"stripe_client\.v\d+\.prices\.list\(",
                r"stripe_client\.v\d+\.checkout\.sessions\.create\(",
                r"stripe_client\.v\d+\.billing_portal\.sessions\.create\(",
                r"stripe_client\.parse_thin_event\(",
                r"stripe_client\.parse_event_notification\(",
            ]

            for pattern in stripe_call_patterns:
                if re.search(pattern, func_body):
                    # Check if it's wrapped with asyncio.to_thread
                    if "asyncio.to_thread" not in func_body[: func_body.find(pattern)]:
                        violations.append(f"{func_name}: Unwrapped Stripe call: {pattern}")

        assert not violations, f"Found blocking Stripe calls:\n" + "\n".join(violations)

    def test_csrf_secret_fail_fast(self):
        """Verify CSRF secret validation fails fast in production."""
        import os

        # Save original env
        original_env = os.getenv("ENVIRONMENT")
        original_secret = os.getenv("CSRF_SECRET")

        try:
            # Test production mode without secret
            os.environ["ENVIRONMENT"] = "production"
            if "CSRF_SECRET" in os.environ:
                del os.environ["CSRF_SECRET"]

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="CSRF_SECRET must be configured"):
                stripe_connect_demo._get_csrf_secret()

        finally:
            # Restore original env
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]
            if original_secret:
                os.environ["CSRF_SECRET"] = original_secret
            elif "CSRF_SECRET" in os.environ:
                del os.environ["CSRF_SECRET"]

    def test_fee_validation_bounds(self):
        """Verify fee amount validation has both lower and upper bounds."""
        router_file = Path(stripe_connect_demo.__file__)
        content = router_file.read_text()

        # Find fee validation code
        fee_validation = re.search(
            r"fee_amount\s*=\s*int\(fee_amount_str\)\s*if\s*fee_amount\s*<\s*0\s*or\s*fee_amount\s*>\s*100000",
            content,
        )

        assert fee_validation is not None, "Fee validation missing upper bound check (must be <= 100000)"

    def test_memory_mode_production_check(self):
        """Verify memory mode is prevented in production."""
        import os

        original_env = os.getenv("ENVIRONMENT")
        original_mode = os.getenv("MOTHERSHIP_PERSISTENCE_MODE")

        try:
            # Test production mode with memory persistence
            os.environ["ENVIRONMENT"] = "production"
            os.environ["MOTHERSHIP_PERSISTENCE_MODE"] = "memory"

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Memory persistence mode is not allowed"):
                stripe_connect_demo._check_persistence_mode()

        finally:
            # Restore original env
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]
            if original_mode:
                os.environ["MOTHERSHIP_PERSISTENCE_MODE"] = original_mode
            elif "MOTHERSHIP_PERSISTENCE_MODE" in os.environ:
                del os.environ["MOTHERSHIP_PERSISTENCE_MODE"]

    def test_all_async_functions_use_await(self):
        """Verify async functions properly use await for async operations."""
        router_file = Path(stripe_connect_demo.__file__)
        content = router_file.read_text()

        # Find async functions that call async operations without await
        # This is a basic check - more sophisticated analysis would use AST
        async_funcs = re.finditer(r"async def (\w+)\([^)]*\):", content)
        violations = []

        for match in async_funcs:
            func_name = match.group(1)
            # Skip test/demo functions
            if func_name.startswith("test_") or func_name.startswith("demo_"):
                continue

            # Check for common async patterns without await
            # This is a simplified check - full AST analysis would be better
            start = match.end()
            end = content.find("\n    def ", start)
            if end == -1:
                end = content.find("\nclass ", start)
            if end == -1:
                end = len(content)

            func_body = content[start:end]

            # Check for async calls without await (simplified)
            if "_is_event_processed(" in func_body and "await _is_event_processed" not in func_body:
                violations.append(f"{func_name}: Missing await on _is_event_processed")
            if "_record_webhook_event(" in func_body and "await _record_webhook_event" not in func_body:
                violations.append(f"{func_name}: Missing await on _record_webhook_event")

        # Note: This is a basic check. Full AST analysis would catch more cases.
        # For now, we rely on type checking (mypy) to catch missing awaits.
        assert not violations, f"Found missing await:\n" + "\n".join(violations)
