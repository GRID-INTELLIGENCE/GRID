import logging
import os
import sys

# Add src to path
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_PATH)

from integration.databricks.client import DatabricksClient  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_real_databricks_queries():
    print("Connecting to Databricks Cloud...")
    try:
        db = DatabricksClient()
        client = db.workspace

        # 1. Investigate Compute Resources
        print("\n--- [1] Compute Resource Audit ---")

        # List Clusters
        clusters = list(client.clusters.list())
        print(f"Found {len(clusters)} Clusters:")
        for c in clusters[:3]:  # Limit to first 3
            print(f" - {c.cluster_name} ({c.state.value})")

        # List SQL Warehouses
        warehouses = list(client.warehouses.list())
        print(f"\nFound {len(warehouses)} SQL Warehouses:")
        active_warehouse = None
        for w in warehouses:
            print(f" - {w.name} (ID: {w.id}, State: {w.state.value})")
            if w.state.value == "RUNNING" or w.state.value == "STARTING":
                active_warehouse = w.id

        # 2. Execute Real SQL Queries if warehouse found
        if active_warehouse:
            print(f"\n--- [2] Executing Cloud SQL on Warehouse: {active_warehouse} ---")

            queries = [
                "SELECT current_user() as user, current_catalog() as cat, current_schema() as schema",
                "SHOW TABLES IN main.default",  # Common default path
            ]

            for sql in queries:
                print(f"Running: {sql}")
                try:
                    # In DB SDK v1+, statement_execution is a separate client or accessed via workspace
                    # Using the SDK pattern for statement execution
                    res = client.statement_execution.execute_statement(warehouse_id=active_warehouse, statement=sql)

                    # Log the structure of the response
                    if res.result and res.result.data_array:
                        print(f"Result: {res.result.data_array}")
                    else:
                        print(f"Query executed successfully (Status: {res.status.state.value})")
                except Exception as e:
                    print(f"Query Failed: {e}")
        else:
            print("\nWarning: No active SQL Warehouse found. Skipping Cloud SQL execution.")
            print("Try checking 'main.default' via DBFS or listing catalogs instead.")

            # Fallback: List Catalogs (Metadata only, usually works if compute is down)
            try:
                print("\n--- [Fallback] Listing Unity Catalog Catalogs ---")
                catalogs = list(client.catalogs.list())
                print(f"Available Catalogs: {[c.name for c in catalogs]}")
            except Exception as e:
                print(f"Catalog listing failed: {e}")

        # 3. Check for Resonance Artifacts
        print("\n--- [3] Resonance Artifact Search ---")
        try:
            # Check for a specific path in DBFS
            path = "/resonance/telemetry"
            objs = list(client.dbfs.list(path))
            print(f"Found {len(objs)} items in {path}")
        except Exception:
            print("Path '/resonance/telemetry' not found or inaccessible.")

    except Exception as e:
        print(f"Connection/SDK Error: {e}")


if __name__ == "__main__":
    run_real_databricks_queries()
