import sqlite3
import json
import uuid
from datetime import datetime


def run_db_demo():
    # 1. Initialization: Create a Relational Database in memory for speed & portability
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    print("🚀 Initializing RDBMS: Relational Resonance Store")

    # 2. Schema Definition (DDL)
    print("\n--- [1] Schema Definition (DDL) ---")
    cursor.executescript(
        """
        CREATE TABLE activities (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            type TEXT,
            query TEXT,
            state TEXT,
            created_at TIMESTAMP
        );

        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            activity_id TEXT,
            type TEXT,
            payload JSON,
            impact REAL,
            created_at TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        );

        CREATE TABLE feedback (
            id TEXT PRIMARY KEY,
            activity_id TEXT,
            tuning_params JSON,
            applied BOOLEAN,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        );
    """
    )
    print("✅ Tables Created: activities, events, feedback")

    # 3. Data Insertion (DML - CREATE)
    print("\n--- [2] Data Population (DML) ---")
    act_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO activities VALUES (?, ?, ?, ?, ?, ?)",
        (act_id, "user_irfan", "arena_chase", "Capture the Photon", "ACTIVE", datetime.utcnow()),
    )

    events = [
        (str(uuid.uuid4()), act_id, "POSITION_UPDATE", json.dumps({"x": 10, "y": 20}), 0.2, datetime.utcnow()),
        (str(uuid.uuid4()), act_id, "CAPTURE_GOAL", json.dumps({"target": "photon"}), 0.9, datetime.utcnow()),
        (str(uuid.uuid4()), act_id, "REWARD_EARNED", json.dumps({"points": 50}), 0.8, datetime.utcnow()),
    ]
    cursor.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", events)

    cursor.execute(
        "INSERT INTO feedback VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), act_id, json.dumps({"attack": 0.5, "friction": 0.1}), False),
    )

    conn.commit()
    print(f"✅ Data Seeded: Activity {act_id} with 3 events.")

    # 4. Complex Query (DQL - READ via JOINS)
    print("\n--- [3] Complex Analytics (JOINS & AGGREGATIONS) ---")
    query = """
        SELECT 
            a.user_id,
            a.type as activity_name,
            COUNT(e.id) as event_count,
            AVG(e.impact) as avg_impact,
            f.tuning_params
        FROM activities a
        LEFT JOIN events e ON a.id = e.activity_id
        LEFT JOIN feedback f ON a.id = f.activity_id
        GROUP BY a.id
    """
    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        print(f"📊 User: {row[0]} | Activity: {row[1]} | Events: {row[2]} | Impact Score: {row[3]:.2f}")
        print(f"   🔧 Pending Tuning: {row[4]}")

    # 5. Data Modification (DML - UPDATE)
    print("\n--- [4] Status Transformation (UPDATE) ---")
    cursor.execute("UPDATE activities SET state = 'COMPLETED' WHERE id = ?", (act_id,))
    print(f"✅ Activity {act_id} marked as COMPLETED.")

    # 6. Data Integrity Check (Filter)
    print("\n--- [5] Data Integrity (High-Impact Filter) ---")
    cursor.execute("SELECT type, impact FROM events WHERE impact > 0.5")
    high_impact = cursor.fetchall()
    for e_type, impact in high_impact:
        print(f"🔥 Critical Event: {e_type} (Impact: {impact})")

    conn.close()
    print("\n🏁 RDBMS Demo Complete.")


if __name__ == "__main__":
    run_db_demo()
