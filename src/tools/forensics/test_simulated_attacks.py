#!/usr/bin/env python3
"""
Forensic Attack Simulation Tests
================================
Tests simulated attacks on hardened systems to verify detection and logging.
"""

import json
import sys
from pathlib import Path

import pytest

# Add paths for imports (relative to project root)
_project_root = Path(__file__).parent.parent.parent.parent
_work_src = _project_root / "work" / "GRID" / "src"
_mcp_filesystem = _project_root / "work" / "GRID" / "workspace" / "mcp" / "servers" / "filesystem"
_mcp_playwright = _project_root / "work" / "GRID" / "workspace" / "mcp" / "servers" / "playwright"

if _work_src.exists():
    sys.path.insert(0, str(_work_src))
if _mcp_filesystem.exists():
    sys.path.insert(0, str(_mcp_filesystem))
if _mcp_playwright.exists():
    sys.path.insert(0, str(_mcp_playwright))


class TestFilesystemAttacks:
    """Test filesystem access controls."""

    @pytest.fixture
    def server(self):
        from production_server import ProductionFilesystemMCPServer  # type: ignore[import-untyped]

        return ProductionFilesystemMCPServer()

    @pytest.mark.asyncio
    async def test_blocked_drive_access(self, server):
        """Test that access to C: drive is blocked."""
        result = await server._read_file({"path": "C:/windows/system32/drivers/etc/hosts"})
        assert result.isError
        assert "Access denied" in result.content[0].text

        # Verify audit logging
        audit_log_path = _mcp_filesystem / "audit.log"
        if audit_log_path.exists():
            import aiofiles

            async with aiofiles.open(audit_log_path, encoding="utf-8") as f:
                content = await f.read()
                logs = [json.loads(line.strip()) for line in content.splitlines() if line.strip()]

            # Find the access denied event
            denied_events = [
                log
                for log in logs
                if log.get("event_type") == "AUTHZ_ACCESS_DENIED" and "windows" in log.get("resource", "")
            ]
            assert len(denied_events) > 0, "Access denied event not found in audit log"

    @pytest.mark.asyncio
    async def test_allowed_path_access(self, server):
        """Test that allowed paths work and are logged."""
        # Create a test file in allowed path
        test_file = _project_root / ".env"
        if not test_file.exists():
            test_file.write_text("TEST=1")

        result = await server._read_file({"path": str(test_file)})
        assert not result.isError

        # Verify audit logging
        audit_log_path = _mcp_filesystem / "audit.log"
        if audit_log_path.exists():
            import aiofiles

            async with aiofiles.open(audit_log_path, encoding="utf-8") as f:
                content = await f.read()
                logs = [json.loads(line.strip()) for line in content.splitlines() if line.strip()]

            # Find the access granted event
            access_events = [
                log
                for log in logs
                if log.get("event_type") == "DATA_ACCESS_PERSONAL" and ".env" in log.get("resource", "")
            ]
            assert len(access_events) > 0, "Data access event not found in audit log"


class TestPlaywrightAttacks:
    """Test Playwright SSRF protection."""

    @pytest.fixture
    def server(self):
        from server import PlaywrightMCPServer  # type: ignore[import-untyped]

        return PlaywrightMCPServer()

    @pytest.mark.asyncio
    async def test_blocked_localhost_navigation(self, server):
        """Test that localhost navigation is blocked."""
        result = await server._navigate({"url": "http://localhost:8080/test"})
        assert result.isError
        assert "Blocked unsafe URL" in result.content[0].text

        # Verify audit logging
        audit_log_path = _mcp_playwright / "audit.log"
        if audit_log_path.exists():
            import aiofiles

            async with aiofiles.open(audit_log_path, encoding="utf-8") as f:
                content = await f.read()
                logs = [json.loads(line.strip()) for line in content.splitlines() if line.strip()]

            # Find the access denied event
            denied_events = [
                log
                for log in logs
                if log.get("event_type") == "AUTHZ_ACCESS_DENIED" and "localhost" in log.get("resource", "")
            ]
            assert len(denied_events) > 0, "SSRF blocked event not found in audit log"

    @pytest.mark.asyncio
    async def test_blocked_private_ip_navigation(self, server):
        """Test that private IP navigation is blocked."""
        result = await server._navigate({"url": "http://192.168.1.1/test"})
        assert result.isError
        assert "Blocked unsafe URL" in result.content[0].text

        # Verify audit logging
        audit_log_path = _mcp_playwright / "audit.log"
        if audit_log_path.exists():
            import aiofiles

            async with aiofiles.open(audit_log_path, encoding="utf-8") as f:
                content = await f.read()
                logs = [json.loads(line.strip()) for line in content.splitlines() if line.strip()]

            # Find the access denied event
            denied_events = [
                log
                for log in logs
                if log.get("event_type") == "AUTHZ_ACCESS_DENIED" and "192.168" in log.get("resource", "")
            ]
            assert len(denied_events) > 0, "Private IP blocked event not found in audit log"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
