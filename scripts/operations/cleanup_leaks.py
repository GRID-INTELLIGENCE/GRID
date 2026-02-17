#!/usr/bin/env python3
"""Clean up parasitic leaks in EventBus and DB engine."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


async def cleanup_eventbus() -> int:
    """Clean up stale EventBus subscriptions."""
    try:
        from infrastructure.event_bus.event_system import get_eventbus

        bus = await get_eventbus()

        # Clear all subscriptions
        initial_count = sum(len(subs) for subs in bus._subscribers.values())
        await bus.clear_all()

        final_count = sum(len(subs) for subs in bus._subscribers.values())
        cleaned = initial_count - final_count

        print(f"EventBus cleanup: {cleaned} subscriptions removed")
        return cleaned
    except Exception as e:
        print(f"Error cleaning EventBus: {e}")
        return 0


async def cleanup_db_engine() -> bool:
    """Dispose DB engine connections."""
    try:
        from application.mothership.db.engine import dispose_async_engine

        await dispose_async_engine()
        print("DB engine disposed")
        return True
    except Exception as e:
        print(f"Error disposing DB engine: {e}")
        return False


async def main() -> None:
    """Run cleanup operations."""
    print("=== Parasitic Leak Cleanup ===\n")

    # Cleanup EventBus
    print("Cleaning EventBus...")
    eventbus_cleaned = await cleanup_eventbus()

    # Cleanup DB engine
    print("\nCleaning DB engine...")
    db_cleaned = await cleanup_db_engine()

    print("\n=== Cleanup Complete ===")
    print(f"EventBus subscriptions removed: {eventbus_cleaned}")
    print(f"DB engine disposed: {db_cleaned}")


if __name__ == "__main__":
    asyncio.run(main())
