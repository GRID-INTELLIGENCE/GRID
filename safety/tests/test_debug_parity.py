"""Test script to reproduce timestamp inconsistency and validation issues."""

import asyncio

from safety.ai_workflow_safety import TemporalSafetyConfig
from safety.context_safe_engine_manager import get_safe_engine


async def test_timestamp_inconsistency():
    """Test timestamp inconsistency by triggering cleanup and access in quick succession."""
    print("Testing timestamp inconsistency...")

    # Create engine for user1
    engine1 = await get_safe_engine("user1")
    print("Created engine for user1")

    # Wait a bit
    await asyncio.sleep(0.1)

    # Access again to trigger timestamp update
    engine2 = await get_safe_engine("user1")
    print("Accessed engine for user1 again")

    # Create multiple engines to potentially trigger cleanup
    for i in range(5):
        await get_safe_engine(f"user{i + 2}")

    print("Created multiple engines")


async def test_invalid_user_id():
    """Test with invalid user_ids."""
    print("\nTesting invalid user_id validation...")

    # Test cases
    test_cases = [
        ("", "empty string"),
        ("a" * 300, "too long"),
        ("user@invalid", "invalid characters"),
        ("user with spaces", "spaces"),
        ("user\nnewline", "newline"),
        ("user<script>alert('xss')</script>", "xss attempt"),
    ]

    for user_id, description in test_cases:
        try:
            print(f"Testing {description}: {user_id[:50]}...")
            engine = await get_safe_engine(user_id)
            print("  ✓ Accepted (should validate)")
        except Exception as e:
            print(f"  ✗ Rejected: {e}")


async def test_config_bounds():
    """Test configuration bounds validation."""
    print("\nTesting config bounds validation...")

    # Test invalid configs — each is a (callable, description) pair so that
    # the config is only constructed inside the try/except block.
    test_configs = [
        (lambda: TemporalSafetyConfig(stamina_cost_per_char=15.0), "stamina_cost_per_char > 10"),
        (lambda: TemporalSafetyConfig(heat_threshold=150.0), "heat_threshold > 100"),
        (lambda: TemporalSafetyConfig(stamina_cost_per_char=-1.0), "stamina_cost_per_char < 0"),
    ]

    for make_config, description in test_configs:
        try:
            print(f"Testing {description}...")
            config = make_config()
            engine = await get_safe_engine("test_user", config)
            print("  ✓ Accepted (should validate bounds)")
        except Exception as e:
            print(f"  ✗ Rejected: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("DEBUG: Testing Safety Engine Issues")
    print("=" * 60)

    await test_timestamp_inconsistency()
    await test_invalid_user_id()
    await test_config_bounds()

    print("\n" + "=" * 60)
    print("Tests completed. Check debug.log for detailed timestamps.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
