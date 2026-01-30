import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from grid.security.codebase_tracker import CodebaseTracker
from grid.security.database_streamer import DatabaseStreamer


def real_activity_test():
    print("🚀 Testing real-time activity capture...")

    tracker = CodebaseTracker(os.getcwd())
    streamer = DatabaseStreamer(use_databricks=False)

    # 1. Clear status
    tracker.poll_activity()
    print("  - Initial status cleared.")

    # 2. Simulate activity (modify a temporary file)
    temp_file = Path("activity_test.txt")
    with open(temp_file, "w") as f:
        f.write(f"Activity at {time.time()}")
    print(f"  - Modified {temp_file}")

    # 3. Poll and Verify
    time.sleep(1) # Give it a second
    events = tracker.poll_activity()

    if any(e.event_type == "file_modified" and "activity_test.txt" in e.path for e in events):
        print("  ✅ Tracker detected the file modification!")
        streamer.stream_events(events)
    else:
        print("  ❌ Tracker failed to detect file modification.")
        # Cleanup
        if temp_file.exists(): temp_file.unlink()
        return False

    # 4. Cleanup
    if temp_file.exists(): temp_file.unlink()
    print("\n✅ Real-time Activity Test Successful!")
    return True

if __name__ == "__main__":
    real_activity_test()
