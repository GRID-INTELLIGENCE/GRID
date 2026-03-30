#!/usr/bin/env python3
"""
Regression tests for standalone MCP tool servers in mcp-setup/server.

Covers path containment and endpoint helper behavior for:
- code_analysis_mcp_server.py
- test_runner_mcp_server.py
"""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path
from types import ModuleType

import pytest


def _load_module(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def code_analysis_module() -> ModuleType:
    root = Path(__file__).resolve().parents[2]
    module_path = root / "mcp-setup" / "server" / "code_analysis_mcp_server.py"
    return _load_module("code_analysis_mcp_server_under_test", module_path)


@pytest.fixture(scope="module")
def test_runner_module() -> ModuleType:
    root = Path(__file__).resolve().parents[2]
    module_path = root / "mcp-setup" / "server" / "test_runner_mcp_server.py"
    return _load_module("test_runner_mcp_server_under_test", module_path)


def _create_workspace_temp_file(grid_root: Path, content: str, suffix: str = ".py") -> Path:
    target_dir = grid_root / "tmp" / "mcp-test-artifacts"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{uuid.uuid4().hex}{suffix}"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_code_analysis_validate_path_blocks_escape(code_analysis_module: ModuleType) -> None:
    outside = code_analysis_module.GRID_ROOT.parent / f"outside-{uuid.uuid4().hex}.py"
    outside.write_text("print('outside')", encoding="utf-8")

    try:
        with pytest.raises(ValueError, match="outside GRID workspace root"):
            code_analysis_module._validate_path(str(outside))
    finally:
        outside.unlink(missing_ok=True)


def test_code_analysis_analyze_code_missing_file_returns_error(code_analysis_module: ModuleType) -> None:
    missing = code_analysis_module.GRID_ROOT / "tmp" / f"{uuid.uuid4().hex}.py"
    result = code_analysis_module.analyze_code(str(missing))

    assert "error" in result
    assert result["error"] == "File not found"


def test_code_analysis_check_security_detects_issues(code_analysis_module: ModuleType) -> None:
    sample = _create_workspace_temp_file(
        code_analysis_module.GRID_ROOT,
        "api_key = 'abc123'\ndef bad():\n    eval('1+1')\n",
    )
    result = code_analysis_module.check_security(str(sample))

    assert result["file"] == str(sample)
    assert result["total_issues"] >= 2
    issue_types = {issue["type"] for issue in result["issues"]}
    assert "potential_secret" in issue_types
    assert "dangerous_function" in issue_types


def test_test_runner_run_tests_blocks_escape(test_runner_module: ModuleType) -> None:
    outside = test_runner_module.GRID_ROOT.parent / f"outside-tests-{uuid.uuid4().hex}.py"
    outside.write_text("def test_x():\n    assert True\n", encoding="utf-8")

    try:
        result = test_runner_module.run_tests(str(outside), verbose=False)

        assert result["success"] is False
        assert "outside GRID workspace root" in result["error"]
    finally:
        outside.unlink(missing_ok=True)


def test_test_runner_run_coverage_passes_expected_args(
    monkeypatch: pytest.MonkeyPatch, test_runner_module: ModuleType
) -> None:
    captured: dict[str, object] = {}

    def fake_run_pytest(args: list[str], cwd: str = None) -> dict[str, object]:
        captured["args"] = args
        captured["cwd"] = cwd
        return {"success": True, "stdout": "", "stderr": "", "returncode": 0}

    monkeypatch.setattr(test_runner_module, "run_pytest", fake_run_pytest)
    result = test_runner_module.run_coverage(output_format="json")

    assert result["success"] is True
    assert "--cov=src" in captured["args"]
    assert "--cov-report=json" in captured["args"]


def test_test_runner_get_test_summary_parses_collect_count(
    monkeypatch: pytest.MonkeyPatch,
    test_runner_module: ModuleType,
) -> None:
    def fake_run_pytest(args: list[str], cwd: str = None) -> dict[str, object]:
        return {"success": True, "stdout": "12 collected items\n", "stderr": "", "returncode": 0}

    monkeypatch.setattr(test_runner_module, "run_pytest", fake_run_pytest)
    result = test_runner_module.get_test_summary()

    assert result["test_count"] == 12
    assert "collected" in result["output"]


def test_test_runner_discover_tests_lists_workspace_tests(test_runner_module: ModuleType) -> None:
    result = test_runner_module.discover_tests("tests")

    assert "error" not in result
    assert result["total_test_files"] > 0
    assert isinstance(result["test_files"], list)
