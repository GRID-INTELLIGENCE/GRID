import os
import sys
import time
import subprocess
import json
from typing import Optional, Dict, Any

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    print(f"Running: {command}")
    return subprocess.run(command, shell=True, capture_output=True, text=True, check=check)

def get_latest_run(workflow_name: str) -> Optional[Dict[str, Any]]:
    cmd = f'gh run list --workflow "{workflow_name}" --limit 1 --json databaseId,status,conclusion,url'
    result = run_command(cmd)
    runs = json.loads(result.stdout)
    return runs[0] if runs else None

def trigger_workflow(event_type: str = "feedback-loop"):
    print(f"Triggering workflow with event type: {event_type}")
    # Using gh api to dispatch repository event
    cmd = f'gh api repos/:owner/:repo/dispatches -f event_type="{event_type}"'
    run_command(cmd)

def monitor_run(workflow_name: str, skip_trigger: bool = False):
    if not skip_trigger:
        # Get latest run ID before triggering to distinguish the new one
        last_run = get_latest_run(workflow_name)
        last_id = last_run['databaseId'] if last_run else None

        trigger_workflow()

        # Wait for new run to start
        print("Waiting for new run to start...")
        new_run = None
        for _ in range(30): # 30 seconds timeout to start
            time.sleep(2)
            current_run = get_latest_run(workflow_name)
            if current_run and current_run['databaseId'] != last_id:
                new_run = current_run
                break
    else:
        new_run = get_latest_run(workflow_name)

    if not new_run:
        print("No run found.")
        return

    run_id = new_run['databaseId']
    print(f"Monitoring run {run_id}: {new_run['url']}")

    # Wait for completion
    while True:
        run = get_latest_run(workflow_name)
        if not run or run['databaseId'] != run_id:
            print("Run lost or changed.")
            break

        status = run['status']
        conclusion = run['conclusion']
        print(f"Current status: {status} (Conclusion: {conclusion})")

        if status == "completed":
            if conclusion == "success":
                print("✅ GitHub Action passed!")
                return True
            else:
                print(f"❌ GitHub Action failed with conclusion: {conclusion}")
                fetch_failure_logs(run_id)
                return False

        time.sleep(10)

def fetch_failure_logs(run_id: int):
    print(f"Fetching logs for failed run {run_id}...")
    try:
        # Get failed logs
        result = run_command(f"gh run view {run_id} --log-failed", check=False)
        print("\n--- FAILED LOGS ---")
        print(result.stdout)
        print("-------------------\n")

        # Also check annotations
        result = run_command(f"gh run view {run_id}", check=False)
        print("\n--- RUN SUMMARY ---")
        print(result.stdout)
        print("-------------------\n")
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    workflow = "GRID CI/CD Pipeline"

    # Check if gh is authenticated
    try:
        run_command("gh auth status")
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI is not authenticated. Please run 'gh auth login'.")
        sys.exit(1)

    print("--- Starting Feedback Loop ---")
    monitor_run(workflow)
