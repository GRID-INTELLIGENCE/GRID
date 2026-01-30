"""Example script demonstrating Databricks SDK integration with GRID."""

from integration.databricks import DatabricksClient, DatabricksJobsManager


def main():
    """Run Databricks SDK example."""
    # Initialize client (uses DATABRICKS_HOST and DATABRICKS_TOKEN env vars)
    # Or use explicit parameters:
    # client = DatabricksClient(host="https://your-workspace.cloud.databricks.com", token="your-token")

    print("Connecting to Databricks...")
    client = DatabricksClient()

    # List clusters
    print("\n=== Clusters ===")
    clusters = client.list_clusters()
    for cluster in clusters:
        print(f"  - {cluster['cluster_name']} (ID: {cluster['cluster_id']}, State: {cluster['state']})")

    # Create jobs manager
    jobs_manager = DatabricksJobsManager(client)

    # List existing jobs
    print("\n=== Jobs ===")
    jobs = jobs_manager.list_jobs()
    for job in jobs:
        print(f"  - {job['settings']} (ID: {job['job_id']})")

    # Example: Create a notebook job (uncomment to use)
    # print("\n=== Creating Notebook Job ===")
    # job_id = jobs_manager.create_notebook_job(
    #     job_name="grid-example-job",
    #     notebook_path="/Repos/your-username/your-repo/notebook.ipynb",
    #     cluster_id=clusters[0]["cluster_id"] if clusters else None,
    #     base_parameters={"param1": "value1"}
    # )
    # print(f"Created job with ID: {job_id}")

    # Example: Run a job (uncomment to use)
    # print("\n=== Running Job ===")
    # run_id = jobs_manager.run_job(job_id, notebook_params={"param1": "new_value"})
    # print(f"Started run with ID: {run_id}")

    print("\nExample completed!")


if __name__ == "__main__":
    main()
