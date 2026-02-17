from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)


def test_workspace_baseline_validator_passes() -> None:
    result = _run([sys.executable, "scripts/validate_workspace_baseline.py"])
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "Workspace baseline validation PASSED" in result.stdout


def test_coldstart_runtime_healthcheck_passes() -> None:
    result = _run([sys.executable, "scripts/coldstart_healthcheck.py"])
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "Coldstart runtime healthcheck PASSED" in result.stdout


def test_coldstart_wrapper_scripts_exist() -> None:
    assert (ROOT / "scripts" / "coldstart.ps1").exists()
    assert (ROOT / "scripts" / "start_api_coldstart.ps1").exists()
    assert (ROOT / "scripts" / "start_worker_coldstart.ps1").exists()


@pytest.mark.skipif(
    shutil.which("powershell") is None and shutil.which("pwsh") is None,
    reason="PowerShell is required for coldstart routine test.",
)
def test_coldstart_script_runs_in_test_mode() -> None:
    powershell_bin = shutil.which("powershell") or shutil.which("pwsh")
    assert powershell_bin is not None

    result = _run(
        [
            powershell_bin,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts/coldstart.ps1",
            "-Mode",
            "test",
            "-SkipValidation",
        ]
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "[OK] Coldstart complete" in result.stdout
