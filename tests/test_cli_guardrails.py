import os
import subprocess
import sys


def run_grid(args, env=None, timeout=10):
    cmd = [sys.executable, "-m", "grid"] + args
    new_env = os.environ.copy()
    if env:
        new_env.update(env)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=new_env, timeout=timeout)
    except subprocess.TimeoutExpired:
        # Commands like 'serve' may start a long-running process;
        # treat timeout as normal completion for guardrail tests.
        result = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="TIMEOUT: process did not exit")
    return result


def test_denylist():
    print("Testing denylist (command 'analyze')...")
    result = run_grid(["analyze", "some text"])
    if "ERROR: Command 'analyze' is currently on the denylist." not in result.stderr:
        print("✅ Denylist allowance working (analyze is unblocked).")
    else:
        print("❌ Denylist still blocking 'analyze'.")
        print("STDERR:", result.stderr)


def test_environment_blocker():
    print("\nTesting environment blocker (GRID_LOCKDOWN=1)...")
    # GRID_LOCKDOWN should no longer block by default
    result = run_grid(["skills", "list"], env={"GRID_LOCKDOWN": "1"})
    if "ERROR: Execution blocked by environment variable: GRID_LOCKDOWN" not in result.stderr:
        print("✅ Environment blocker disabled correctly (GRID_LOCKDOWN=1 allowed).")
    else:
        print("❌ Environment blocker still active for GRID_LOCKDOWN.")
        print("STDERR:", result.stderr)


def test_allowed_command():
    print("\nTesting allowed command ('skills list')...")
    # Note: this might fail if the registry isn't initialized or has errors,
    # but we just want to see it NOT blocked by guardrails.
    result = run_grid(["skills", "list"])
    if (
        "ERROR: Command 'skills' is currently on the denylist." not in result.stderr
        and "ERROR: Execution blocked" not in result.stderr
    ):
        print("✅ Allowed command passed guardrails.")
    else:
        print("❌ Allowed command BLOCKED unexpectedly.")
        print("STDERR:", result.stderr)


def test_contribution_blocker():
    print("\nTesting contribution blocker (Threshold=0.95)...")
    # Use a short-lived command path to avoid long-running server startup in tests.
    # 'skills' has score 0.91, so it should be blocked by 0.95.
    result = run_grid(["skills", "list"], env={"GRID_MIN_CONTRIBUTION": "0.95"})
    if "ERROR: Command 'skills' blocked. Contribution score 0.91 is below threshold 0.95" in result.stderr:
        print("✅ Contribution blocker working correctly.")
    else:
        print("❌ Contribution blocker FAILED.")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)


def test_contribution_allowed():
    print("\nTesting contribution allowed (Threshold=0.80)...")
    # 'skills' has score 0.91, so it should be allowed by 0.80.
    result = run_grid(["skills", "list"], env={"GRID_MIN_CONTRIBUTION": "0.80"})
    if "ERROR: Command 'skills' blocked" not in result.stderr:
        print("✅ Contribution allowance working correctly.")
    else:
        print("❌ Contribution allowance FAILED.")
        print("STDERR:", result.stderr)


if __name__ == "__main__":
    test_denylist()
    test_environment_blocker()
    test_contribution_blocker()
    test_contribution_allowed()
    test_allowed_command()
