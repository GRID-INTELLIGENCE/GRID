import sys
import os
from datetime import datetime, timedelta

# Add src to path
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_PATH)

from application.resonance.query_engine import ResonanceQueryEngine  # noqa: E402

def run_query_demo():
    print("Initializing Resonance SQL Query Engine...")
    engine = ResonanceQueryEngine("demo_resonance.db")

    # 1. Seed simulated data
    print("\nSeeding Simulated Telemetry Data...")
    act_id = "activity_alpha_1"
    events = []
    base_time = datetime.utcnow()

    # Generate 20 events with varying impact
    for i in range(20):
        impact = 0.2 if i % 3 == 0 else (0.8 if i % 5 == 0 else 0.5)
        events.append({
            "id": f"event_{i}",
            "activity_id": act_id,
            "type": "SIM_TICK" if impact < 0.5 else "CRITICAL_HIT",
            "impact": impact,
            "data": {"value": i * 10},
            "timestamp": (base_time + timedelta(seconds=i)).isoformat()
        })

    engine.ingest_batch(events)
    print(f"Ingested {len(events)} events for activity {act_id}.")

    # 2. Run Investigative SQL 1: Impact Distribution
    print("\nQuery 1: Impact Distribution by Event Type")
    sql1 = """
        SELECT event_type, AVG(impact) as mean_impact, COUNT(*) as count
        FROM telemetry_events
        GROUP BY event_type
    """
    df1 = engine.execute_query(sql1)
    print(df1.to_string(index=False))

    # 3. Run Investigative SQL 2: Temporal Rolling Impact
    # This demonstrates Window Functions in SQLite
    print("\nQuery 2: Rolling Average Impact (Window Function)")
    sql2 = f"""
        SELECT
            event_type,
            substr(created_at, 12, 8) as time,
            impact,
            ROUND(AVG(impact) OVER (ORDER BY created_at ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 3) as moving_avg
        FROM telemetry_events
        WHERE activity_id = '{act_id}'
        LIMIT 10
    """
    df2 = engine.execute_query(sql2)
    print(df2.to_string(index=False))

    # 4. Filter High Impact
    print("\nQuery 3: Filtering High-Impact Activity Peaks")
    sql3 = "SELECT * FROM telemetry_events WHERE impact >= 0.8"
    df3 = engine.execute_query(sql3)
    print(f"Found {len(df3)} high-impact peaks.")
    print(df3[['id', 'event_type', 'impact']].to_string(index=False))

    # Cleanup
    if os.path.exists("demo_resonance.db"):
        os.remove("demo_resonance.db")

if __name__ == "__main__":
    run_query_demo()
