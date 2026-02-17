import os
import sys

# Path setup
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_PATH)

from application.resonance.query_engine import ResonanceQueryEngine  # noqa: E402


def run_investigative_suite():
    print("--- [Databricks Investigative SQL Suite] ---")
    print("Scenario: Mirroring Cloud SQL Analytics in Local Relational Store")

    db_name = "strategic_resonance.db"
    if not os.path.exists(db_name):
        print(f"Error: {db_name} not found. Running seed...")
        # (Internal seeding would happen here if needed)

    engine = ResonanceQueryEngine(db_name)

    # QUERY 1: The "Spike" Investigation (Anomaly Detection)
    # Goal: Identify high-urgency pulses that may require HITL intervention.
    print("\n[Query 1] High-Intensity Pulse Detection (Impact > 0.9)")
    q1 = """
        SELECT
            activity_id, event_type, impact, created_at
        FROM telemetry_events
        WHERE impact > 0.9
        ORDER BY created_at ASC
    """
    print(engine.execute_query(q1).to_string(index=False))

    # QUERY 2: Cross-Modality Frequency Breakdown
    # Goal: Statistical breakdown for a "Pie Chart" visualization in Databricks.
    print("\n[Query 2] Modality Frequency Breakdown (Global)")
    q2 = """
        SELECT
            event_type,
            COUNT(*) as occurrences,
            ROUND(AVG(impact), 3) as avg_impact,
            ROUND(MAX(impact), 3) as max_impact
        FROM telemetry_events
        GROUP BY event_type
        ORDER BY occurrences DESC
    """
    print(engine.execute_query(q2).to_string(index=False))

    # QUERY 3: The "Resonance Envelope" Duration Join
    # Goal: Mapping simulated time-span to event density (Efficiency Metrics).
    print("\n[Query 3] Efficiency Metrics (Events per Active Second)")
    q3 = """
        WITH ActivityBounds AS (
            SELECT
                activity_id,
                (strftime('%s', MAX(created_at)) - strftime('%s', MIN(created_at))) as duration
            FROM telemetry_events
            GROUP BY activity_id
        )
        SELECT
            t.activity_id,
            COUNT(t.id) as total_events,
            ab.duration as duration_sec,
            ROUND(CAST(COUNT(t.id) AS REAL) / MAX(1, ab.duration), 2) as events_per_sec
        FROM telemetry_events t
        JOIN ActivityBounds ab ON t.activity_id = ab.activity_id
        GROUP BY t.activity_id
    """
    print(engine.execute_query(q3).to_string(index=False))


if __name__ == "__main__":
    run_investigative_suite()
