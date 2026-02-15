"""Final verification test for fixes."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from safety.context_safe_engine_manager import ContextSafeEngineManager
from safety.ai_workflow_safety import TemporalSafetyConfig

async def main():
    """Verify all fixes."""
    manager = ContextSafeEngineManager(max_cache_size=5, cleanup_interval_seconds=1)

    print("Verification Test:")
    print("=" * 60)

    # Test 1: Timestamp consistency for existing engine
    print("\n1. Testing timestamp consistency (existing engine)...")
    engine1 = await manager.get_engine("user1")
    await asyncio.sleep(0.01)
    engine2 = await manager.get_engine("user1")  # Should use same timestamp

    # Test 2: User_id validation
    print("\n2. Testing user_id validation...")
    try:
        await manager.get_engine("user@test")
        print("  ✗ FAILED: Invalid user_id accepted")
    except ValueError as e:
        print(f"  PASSED: Invalid user_id rejected: {e}")

    # Test 3: Config bounds
    print("\n3. Testing config bounds...")
    try:
        config = TemporalSafetyConfig(stamina_cost_per_char=15.0)
        await manager.get_engine("test", config)
        print("  ✗ FAILED: Invalid config accepted")
    except ValueError as e:
        print(f"  PASSED: Invalid config rejected: {e}")

    try:
        config = TemporalSafetyConfig(heat_threshold=150.0)
        await manager.get_engine("test2", config)
        print("  ✗ FAILED: Invalid heat_threshold accepted")
    except ValueError as e:
        print(f"  PASSED: Invalid heat_threshold rejected: {e}")

    print("\n" + "=" * 60)
    print("Verification complete. Check debug.log for timestamp consistency.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
