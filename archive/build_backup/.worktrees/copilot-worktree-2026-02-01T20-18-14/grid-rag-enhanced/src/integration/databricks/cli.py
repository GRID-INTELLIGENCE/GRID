"""Databricks CLI for GRID."""

import argparse
import sys


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="GRID Databricks CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List clusters
    subparsers.add_parser("clusters", help="List all clusters")

    # List jobs
    subparsers.add_parser("jobs", help="List all jobs")

    # Create job
    create_job_parser = subparsers.add_parser("create-job", help="Create a notebook job")
    create_job_parser.add_argument("--name", required=True, help="Job name")
    create_job_parser.add_argument("--notebook", required=True, help="Notebook path")
    create_job_parser.add_argument("--cluster", help="Cluster ID")

    # Run job
    run_job_parser = subparsers.add_parser("run-job", help="Run a job")
    run_job_parser.add_argument("--job-id", required=True, help="Job ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        from integration.databricks import DatabricksClient, DatabricksJobsManager

        client = DatabricksClient()

        if args.command == "clusters":
            clusters = client.list_clusters()
            for cluster in clusters:
                print(f"{cluster['cluster_name']} ({cluster['cluster_id']}) - {cluster['state']}")

        elif args.command == "jobs":
            jobs_manager = DatabricksJobsManager(client)
            jobs = jobs_manager.list_jobs()
            for job in jobs:
                print(f"{job['settings']} (ID: {job['job_id']})")

        elif args.command == "create-job":
            jobs_manager = DatabricksJobsManager(client)
            job_id = jobs_manager.create_notebook_job(
                job_name=args.name,
                notebook_path=args.notebook,
                cluster_id=args.cluster,
            )
            print(f"Created job with ID: {job_id}")

        elif args.command == "run-job":
            jobs_manager = DatabricksJobsManager(client)
            run_id = jobs_manager.run_job(job_id=args.job_id)
            print(f"Started run with ID: {run_id}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
