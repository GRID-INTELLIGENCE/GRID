#!/usr/bin/env python3
"""Detect parasitic leaks in EventBus and DB engine."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


async def detect_eventbus_leaks() -> dict[str, int]:
    """Detect EventBus subscription leaks."""
    try:
        from infrastructure.event_bus.event_system import get_eventbus

        bus = await get_eventbus()

        # Get subscriber counts
        total_subscriptions = sum(len(subs) for subs in bus._subscribers.values())
        active_subscriptions = len(bus._index)

        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "stale_subscriptions": total_subscriptions - active_subscriptions,
        }
    except Exception as e:
        print(f"Error detecting EventBus leaks: {e}")
        return {}


async def detect_db_leaks() -> dict[str, int]:
    """Detect DB engine connection leaks."""
    try:
        from application.mothership.db.engine import get_async_engine

        engine = get_async_engine()

        if engine and engine.pool:
            pool_size = engine.pool.size()
            checked_out = engine.pool.checkedout()

            return {
                "pool_size": pool_size,
                "checked_out": checked_out,
                "available": pool_size - checked_out,
            }
    except Exception as e:
        print(f"Error detecting DB leaks: {e}")
        return {}


async def main() -> None:
    """Run leak detection."""
    print("=== Parasitic Leak Detection ===\n")

    # Detect EventBus leaks
    print("EventBus Leaks:")
    eventbus_stats = await detect_eventbus_leaks()
    if eventbus_stats:
        for key, value in eventbus_stats.items():
            print(f"  {key}: {value}")

        if eventbus_stats.get("stale_subscriptions", 0) > 0:
            print(f"  ⚠️  WARNING: {eventbus_stats['stale_subscriptions']} stale subscriptions detected!")
    else:
        print("  Unable to detect EventBus leaks")

    print()

    # Detect DB leaks
    print("DB Engine Leaks:")
    db_stats = await detect_db_leaks()
    if db_stats:
        for key, value in db_stats.items():
            print(f"  {key}: {value}")

        if db_stats.get("checked_out", 0) > db_stats.get("pool_size", 0) * 0.8:
            print("  ⚠️  WARNING: High connection pool utilization!")
    else:
        print("  Unable to detect DB leaks")

    print("\n=== Detection Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
