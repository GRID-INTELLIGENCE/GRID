"""
Tests for skills discovery, sandbox isolation, and versioning.
Covers:
- SkillDiscoveryEngine: discovery of skills in a temporary package
- SkillsSandbox: execution success/timeout handling with resource limits mocked
- VersionManager: version capture/list/rollback safety using temp storage
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from grid.skills.discovery_engine import SkillDiscoveryEngine
from grid.skills.sandbox import SandboxConfig, SandboxStatus, SkillsSandbox
from grid.skills.version_manager import VersionManager


@pytest.fixture()
def temp_skill_package(tmp_path: Path):
    """Create a temporary skills package with a single skill."""
    package_root = tmp_path / "temp_skills_pkg"
    skills_dir = package_root / "skills"
    skills_dir.mkdir(parents=True)

    # Package __init__ files
    (package_root / "__init__.py").write_text("")
    (skills_dir / "__init__.py").write_text("")

    # Skill file with a simple class exposing id/run
    skill_file = skills_dir / "sample_skill.py"
    skill_file.write_text("""
class SampleSkill:
    id = "sample.skill"
    name = "Sample Skill"
    description = "A sample skill for testing."
    version = "1.0.0"

    def run(self, args):
        return {"ok": True, "args": args}

sample_skill = SampleSkill()
""")

    sys.path.insert(0, str(tmp_path))
    yield "temp_skills_pkg.skills", skill_file
    sys.path.remove(str(tmp_path))


class TestSkillDiscoveryEngine:
    def test_discover_skills_in_temp_package(self, temp_skill_package):
        base_package, skill_file = temp_skill_package
        engine = SkillDiscoveryEngine()

        count = engine.discover_skills(base_package=base_package)
        assert count == 1

        skills = engine.list_skills()
        assert len(skills) == 1
        meta = skills[0]
        assert meta.id == "sample.skill"
        assert meta.file_path == str(skill_file)
        assert meta.category in {"high-level", "low-level"}

    def test_registry_registers_discovered_skills(self, temp_skill_package, monkeypatch):
        """Test that discovered skills can be listed after discovery."""
        base_package, _ = temp_skill_package

        # Just test that the discovery engine works and can list skills
        engine = SkillDiscoveryEngine()
        count = engine.discover_skills(base_package=base_package)
        assert count == 1

        # Verify we can list the discovered skills
        skills = engine.list_skills()
        assert len(skills) == 1
        assert skills[0].id == "sample.skill"


class TestSkillsSandbox:
    def test_execute_skill_success(self, monkeypatch):
        """Skill completes successfully and records output."""
        sandbox = SkillsSandbox(config=SandboxConfig(timeout=2.0))
        monkeypatch.setattr(sandbox, "_apply_resource_limits", lambda: None)

        skill_code = """
import json
def main(args):
    return {"result": "ok", "echo": args.get("value")}
"""
        result = asyncio.run(sandbox.execute_skill(skill_code, {"value": 42}))

        assert result.status == SandboxStatus.COMPLETED
        assert "RESULT:" in result.stdout
        assert result.error_message is None

    def test_execute_skill_timeout(self, monkeypatch):
        """Long-running skill should hit timeout and report status."""
        sandbox = SkillsSandbox(config=SandboxConfig(timeout=0.5))
        monkeypatch.setattr(sandbox, "_apply_resource_limits", lambda: None)

        skill_code = """
import time
def main(args):
    time.sleep(2)
    return {"result": "late"}
"""
        result = asyncio.run(sandbox.execute_skill(skill_code))

        assert result.status == SandboxStatus.TIMEOUT
        assert result.exit_code is not None

    def test_security_violations_flagged(self, monkeypatch):
        """Filesystem disallowed should flag violations for created files."""
        sandbox = SkillsSandbox(config=SandboxConfig(allow_filesystem=False, timeout=2.0))
        monkeypatch.setattr(sandbox, "_apply_resource_limits", lambda: None)

        # Skill writes a file, which should be flagged when FS disallowed
        skill_code = """
from pathlib import Path
def main(args):
    Path('data.txt').write_text('secret')
    return {"written": True}
"""
        result = asyncio.run(sandbox.execute_skill(skill_code))

        assert result.security_violations is not None
        assert any("Unauthorized file access" in v for v in result.security_violations)


class TestVersionManager:
    def test_capture_and_list_versions(self, tmp_path: Path, monkeypatch):
        storage_dir = tmp_path / "versions"
        storage_dir.mkdir()

        skill_file = tmp_path / "demo_skill.py"
        skill_file.write_text("def handler():\n    return 'ok'\n")

        manager = VersionManager(storage_dir=str(storage_dir))

        # Mock inventory to avoid external dependencies
        mock_inventory = MagicMock()
        mock_inventory.get_skill_summary.return_value = {}
        manager._inventory = mock_inventory

        version = manager.capture_version(skill_id="demo.skill", skill_file=skill_file)
        assert version.version_id.startswith("v_")  # Format: v_{timestamp}_{hash[:8]}

        versions = manager.list_versions("demo.skill")
        assert len(versions) == 1
        assert versions[0]["skill_id"] == "demo.skill"

    def test_rollback_restores_content(self, tmp_path: Path, monkeypatch):
        storage_dir = tmp_path / "versions"
        storage_dir.mkdir()

        skill_file = tmp_path / "demo_skill.py"
        skill_file.write_text("def handler():\n    return 'v1'\n")

        manager = VersionManager(storage_dir=str(storage_dir))
        mock_inventory = MagicMock()
        mock_inventory.get_skill_summary.return_value = {}
        manager._inventory = mock_inventory

        version = manager.capture_version("demo.skill", skill_file=skill_file)

        # Modify skill file
        skill_file.write_text("def handler():\n    return 'v2'\n")

        # Rollback should restore original snapshot
        assert manager.rollback("demo.skill", version.version_id) is True
        assert "v1" in skill_file.read_text()
