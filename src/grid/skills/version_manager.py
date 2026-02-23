"""
Version manager for skills with rollback capabilities and performance tracking.

Audio engineering-inspired approach:
- Code snapshots for each version (Lossless capture)
- Version history with git SHA integration
- Performance baselines tethered to versions
- Rollback with zero-latency swap
"""

import asyncio
import hashlib
import json
import logging
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .intelligence_inventory import IntelligenceInventory


@dataclass
class SkillVersion:
    """Skill version metadata."""

    version_id: str
    skill_id: str
    created_at: float
    git_sha: str | None
    code_hash: str
    code_snapshot: str
    performance_baseline: dict[str, float] | None
    metadata: dict[str, Any]
    skill_file_path: str | None = None  # Path to the original skill file

    @property
    def id(self) -> str:
        """Alias for version_id for convenience."""
        return self.version_id


class SkillVersionManager:
    """
    Manages skill versions with snapshotting and rollback support.
    """

    STORAGE_DIR = Path("./data/skill_versions")

    def __init__(self, storage_dir: Path | str | None = None):
        self._logger = logging.getLogger(__name__)
        if storage_dir is None:
            self._storage_dir = self.STORAGE_DIR
        elif isinstance(storage_dir, str):
            self._storage_dir = Path(storage_dir)
        else:
            self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._inventory = IntelligenceInventory()

    def _get_skill_dir(self, skill_id: str) -> Path:
        skill_dir = self._storage_dir / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)
        return skill_dir

    def _calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_git_sha(self, file_path: Path) -> str | None:
        """Get git SHA for a file (sync version)."""
        try:
            result = subprocess.run(  # noqa: S603 subprocess call is intentional
                ["git", "log", "-1", "--format=%H", str(file_path)],  # noqa: S607 partial path is intentional
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self._logger.warning(f"Git SHA lookup timed out for {file_path}")
        except Exception:  # noqa: S110 intentional silent handling
            pass
        return None

    async def _get_git_sha_async(self, file_path: Path) -> str | None:
        """Get git SHA for a file (async version).

        Uses asyncio subprocess to avoid blocking the event loop.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "log",
                "-1",
                "--format=%H",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            async with asyncio.timeout(10):
                stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return stdout.decode("utf-8", errors="replace").strip()
        except TimeoutError:
            self._logger.warning(f"Async git SHA lookup timed out for {file_path}")
        except Exception as e:
            self._logger.debug(f"Async git SHA lookup failed: {e}")
        return None

    def capture_version(
        self, skill_id: str, skill_file: Path | str | None = None, version_label: str | None = None
    ) -> SkillVersion:
        """Capture current state of a skill as a new version.

        Args:
            skill_id: The skill identifier
            skill_file: Optional path to the skill file. If not provided, defaults to
                       src/grid/skills/{skill_id}.py
            version_label: Optional version label. If not provided, auto-generated.

        Returns:
            SkillVersion object with captured state
        """
        # 1. Locate file
        if skill_file is None:
            skill_file_path = Path("src/grid/skills") / f"{skill_id}.py"
        elif isinstance(skill_file, str):
            skill_file_path = Path(skill_file)
        else:
            skill_file_path = skill_file

        if not skill_file_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_file_path}")

        # 2. Capture code
        code_snapshot = skill_file_path.read_text()
        code_hash = self._calculate_hash(code_snapshot)
        git_sha = self._get_git_sha(skill_file_path)

        # 3. Fetch summary for baseline
        summary = self._inventory.get_skill_summary(skill_id)
        baseline = None
        if summary:
            baseline = {
                "success_rate": summary.success_rate,
                "p50_ms": summary.p50_latency_ms,
                "p95_ms": summary.p95_latency_ms,
                "p99_ms": summary.p99_latency_ms,
            }

        # 4. Generate version ID
        version_id = version_label or f"v_{int(time.time())}_{code_hash[:8]}"

        version = SkillVersion(
            version_id=version_id,
            skill_id=skill_id,
            created_at=time.time(),
            git_sha=git_sha,
            code_hash=code_hash,
            code_snapshot=code_snapshot,
            performance_baseline=baseline,
            metadata={},
            skill_file_path=str(skill_file_path),
        )

        # 5. Save to disk (sync for backward compatibility with sync callers)
        self._save_version_sync(version)

        self._logger.info(f"Captured version {version_id} for skill {skill_id}")
        return version

    def _save_version_sync(self, version: SkillVersion) -> None:
        """Save version to disk (sync)."""
        skill_dir = self._get_skill_dir(version.skill_id)
        version_file = skill_dir / f"{version.version_id}.json"
        version_file.write_text(json.dumps(asdict(version), indent=2))

    async def _save_version(self, version: SkillVersion) -> None:
        import aiofiles

        skill_dir = self._get_skill_dir(version.skill_id)
        version_file = skill_dir / f"{version.version_id}.json"
        async with aiofiles.open(version_file, "w") as f:
            await f.write(json.dumps(asdict(version), indent=2))

    def list_versions(self, skill_id: str) -> list[dict[str, Any]]:
        """List available versions for a skill (sync)."""
        skill_dir = self._get_skill_dir(skill_id)
        versions = []
        for v_file in skill_dir.glob("*.json"):
            content = v_file.read_text()
            data = json.loads(content)
            data.pop("code_snapshot", None)
            versions.append(data)
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)

    async def list_versions_async(self, skill_id: str) -> list[dict[str, Any]]:
        """List available versions for a skill."""
        import aiofiles

        skill_dir = self._get_skill_dir(skill_id)
        versions = []
        v_files = await asyncio.to_thread(lambda: list(skill_dir.glob("*.json")))
        for v_file in v_files:
            async with aiofiles.open(v_file) as f:
                content = await f.read()
                data = json.loads(content)
                # Don't return full snapshot in list
                data.pop("code_snapshot", None)
                versions.append(data)
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)

    async def get_version(self, skill_id: str, version_id: str) -> SkillVersion | None:
        """Fetch a specific version."""
        import aiofiles

        skill_dir = self._get_skill_dir(skill_id)
        version_file = skill_dir / f"{version_id}.json"

        if not await asyncio.to_thread(version_file.exists):
            return None

        async with aiofiles.open(version_file) as f:
            content = await f.read()
            data = json.loads(content)
            return SkillVersion(**data)

    def get_version_sync(self, skill_id: str, version_id: str) -> SkillVersion | None:
        """Fetch a specific version (sync)."""
        skill_dir = self._get_skill_dir(skill_id)
        version_file = skill_dir / f"{version_id}.json"
        if not version_file.exists():
            return None
        content = version_file.read_text()
        data = json.loads(content)
        return SkillVersion(**data)

    def rollback(self, skill_id: str, version_id: str) -> bool:
        """Rollback skill to a previous version."""
        version = self.get_version_sync(skill_id, version_id)
        if not version:
            self._logger.error(f"Version {version_id} not found for skill {skill_id}")
            return False

        try:
            # Use stored path if available, otherwise fall back to default
            if version.skill_file_path:
                skill_file = Path(version.skill_file_path)
            else:
                skill_file = Path("src/grid/skills") / f"{skill_id}.py"

            # Backup current to temp before overwrite
            backup_path = skill_file.with_suffix(".py.bak")
            if skill_file.exists():
                shutil.copy2(skill_file, backup_path)

            # Overwrite with snapshot
            skill_file.write_text(version.code_snapshot)

            # Trigger hot reload if available
            from .hot_reload_manager import HotReloadManager

            HotReloadManager.get_instance()._reload_skill(skill_id)

            self._logger.info(f"Successfully rolled back {skill_id} to {version_id}")
            return True

        except Exception as e:
            self._logger.error(f"Rollback failed: {e}")
            return False

    def compare(self, skill_id: str, v1_id: str, v2_id: str) -> dict[str, Any]:
        """Compare two versions (performance + code diff placeholder)."""
        v1 = self.get_version_sync(skill_id, v1_id)
        v2 = self.get_version_sync(skill_id, v2_id)

        if not v1 or not v2:
            return {"error": "One or both versions not found"}

        comparison = {"skill_id": skill_id, "v1": v1.version_id, "v2": v2.version_id, "performance_delta": {}}

        if v1.performance_baseline and v2.performance_baseline:
            for metric in v1.performance_baseline:
                m1 = v1.performance_baseline[metric]
                m2 = v2.performance_baseline[metric]
                if m1 and m2:
                    delta_pct = ((m2 / m1) - 1) * 100
                    comparison["performance_delta"][metric] = delta_pct

        return comparison


# Backward compatibility alias
VersionManager = SkillVersionManager
