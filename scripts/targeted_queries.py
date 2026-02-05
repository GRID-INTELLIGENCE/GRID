import os
import sys
from datetime import datetime, timedelta

# Add src to path
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_PATH)

from application.resonance.query_engine import ResonanceQueryEngine  # noqa: E402


def run_targeted_investigation():
    print("--- [Resonance Targeted Database Investigation] ---")
    db_name = "strategic_resonance.db"
    engine = ResonanceQueryEngine(db_name)

    # 1. Seed Complex Data: Multiple activities, Interleaved times
    print("\n[Step 1] Seeding Strategic Telemetry Dataset...")
    # activities = [
    #     ("act_1", "chase_high_intensity"),
    #     ("act_2", "stealth_low_intensity")
    # ]

    events = []
    start_time = datetime.now()

    # Activity 1: Intense, many events
    for i in range(50):
        impact = 0.4 + (0.1 * (i % 5))  # Base rising impact
        if i % 10 == 0:
            impact = 0.95  # Spikes
        events.append(
            {
                "id": f"e_a1_{i}",
                "activity_id": "act_1",
                "type": "CHASE_TICK",
                "impact": impact,
                "data": {"v": i},
                "timestamp": (start_time + timedelta(milliseconds=200 * i)).isoformat(),
            }
        )

    # Activity 2: Slow, few events
    for i in range(10):
        events.append(
            {
                "id": f"e_a2_{i}",
                "activity_id": "act_2",
                "type": "SNEAK_TICK",
                "impact": 0.1,
                "data": {"v": i},
                "timestamp": (start_time + timedelta(seconds=2 * i)).isoformat(),
            }
        )

    engine.ingest_batch(events)
    print(f"Ingested {len(events)} events across 2 activities.")

    # 2. TARGETED QUERY A: Session Duration Analysis
    print("\n[Targeted Query A] Session Duration Analysis")
    sql_a = """
        SELECT
            activity_id,
            MIN(created_at) as start_time,
            MAX(created_at) as end_time,
            (strftime('%s', MAX(created_at)) - strftime('%s', MIN(created_at))) as duration_seconds,
            COUNT(*) as event_count
        FROM telemetry_events
        GROUP BY activity_id
    """
    print(engine.execute_query(sql_a).to_string(index=False))

    # 3. TARGETED QUERY B: Impact Hotspots (1-Second Windows)
    # Finding the most intense seconds of simulation
    print("\n[Targeted Query B] Intensity Hotspots (Top 5 Active Seconds)")
    sql_b = """
        SELECT
            activity_id,
            substr(created_at, 1, 19) as second_slice,
            SUM(impact) as combined_intensity,
            COUNT(*) as events_in_sec
        FROM telemetry_events
        GROUP BY activity_id, second_slice
        ORDER BY combined_intensity DESC
        LIMIT 5
    """
    print(engine.execute_query(sql_b).to_string(index=False))

    # 4. TARGETED QUERY C: Statistical Anomaly Detection
    # Finding events where impact is > AVG + 1.5*STDEV (approx)
    print("\n[Targeted Query C] Anomaly Detection (High-Impact Deviations)")
    sql_c = """
        WITH Metrics AS (
            SELECT AVG(impact) as mu, 0.2 as threshold FROM telemetry_events -- SQLite lacks built-in STDEV, using fixed variance approx
        )
        SELECT
            id, event_type, impact,
            ROUND(impact - (SELECT mu FROM Metrics), 3) as deviation
        FROM telemetry_events
        WHERE impact > (SELECT mu FROM Metrics) + (SELECT threshold FROM Metrics)
        ORDER BY impact DESC
    """
    print(engine.execute_query(sql_c).to_string(index=False))

    # Cleanup
    try:
        engine = None  # Close connections
        import gc

        gc.collect()
        # os.remove(db_name)  # Keep for record if preferred, but user usually wants clean workspace
    except Exception:
        pass


if __name__ == "__main__":
    run_targeted_investigation()
