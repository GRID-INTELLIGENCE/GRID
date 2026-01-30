import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from grid.security.codebase_tracker import ActivityEvent, CodebaseTracker
from grid.security.database_streamer import DatabaseStreamer


def verify_tracking():
    print("🚀 Verifying Codebase Tracking System...")

    # Initialize with local-only fallback for test
    streamer = DatabaseStreamer(use_databricks=False)
    tracker = CodebaseTracker(os.getcwd())

    print("\n🔍 1. Generating Dummy Activity:")
    dummy_event = ActivityEvent(
        event_type="verification_test",
        path="e:/grid/verify_tracking.py",
        details={"reason": "system_verification"}
    )

    print(f"  - Event: {dummy_event.event_type} at {dummy_event.path}")
    streamer.stream_events([dummy_event])

    print("\n📊 2. Verifying Persistence in SQLite:")
    # Query the local database to see if it was stored
    from grid.skills.intelligence_inventory import IntelligenceInventory
    inventory = IntelligenceInventory.get_instance()

    conn = inventory._get_connection()
    cursor = conn.execute(
        "SELECT timestamp, decision_type, rationale FROM intelligence_records "
        "WHERE skill_id = 'codebase_tracker' ORDER BY timestamp DESC LIMIT 1"
    )
    row = cursor.fetchone()

    if row:
        print("  ✅ Found record in local SQLite!")
        print(f"  - Timestamp: {row['timestamp']}")
        print(f"  - Event Type: {row['decision_type']}")
        print(f"  - Data: {row['rationale'][:100]}...")
    else:
        print("  ❌ Record not found in local SQLite.")
        return False

    print("\n✅ Verification Successful!")
    return True

if __name__ == "__main__":
    verify_tracking()
