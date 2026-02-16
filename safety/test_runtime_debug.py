"""Direct runtime test to generate debug logs."""

import os
import sys

# Add safety to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from safety.ai_workflow_safety import TemporalSafetyConfig
from safety.context_safe_engine_manager import ContextSafeEngineManager


async def main():
    """Run direct test."""
    manager = ContextSafeEngineManager(max_cache_size=5, cleanup_interval_seconds=1)

    # Test 1: Timestamp inconsistency
    print("Test 1: Timestamp inconsistency")
    engine1 = await manager.get_engine("user1")
    await asyncio.sleep(0.01)
    engine2 = await manager.get_engine("user1")  # Should trigger timestamp update

    # Test 2: Invalid user_id
    print("\nTest 2: Invalid user_id")
    try:
        await manager.get_engine("")  # Empty
    except Exception as e:
        print(f"  Empty rejected: {e}")

    try:
        await manager.get_engine("a" * 300)  # Too long
    except Exception as e:
        print(f"  Long rejected: {e}")

    # Test 3: Config bounds
    print("\nTest 3: Config bounds")
    try:
        config = TemporalSafetyConfig(stamina_cost_per_char=15.0)
        await manager.get_engine("test", config)
        print("  Config with stamina_cost_per_char=15.0 accepted (should validate)")
    except Exception as e:
        print(f"  Config rejected: {e}")

    print("\nCheck e:\\grid\\.cursor\\debug.log for detailed logs")


if __name__ == "__main__":
    asyncio.run(main())
