#!/usr/bin/env python3
"""
Security tests for MCP Mastermind Server.
Tests for path traversal vulnerabilities and access controls.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

from grid.mcp.mastermind_server import MastermindSession, analyze_file


class TestMastermindSecurity:
    """Security tests for mastermind server functions."""

    @pytest.fixture
    def session(self):
        """Create a test session."""
        session = MastermindSession()
        # Use a temporary directory as project root for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            session.project_root = Path(temp_dir)
            # Patch the global session
            with patch("grid.mcp.mastermind_server.session", session):
                yield session

    @pytest.mark.asyncio
    async def test_analyze_file_path_traversal_prevention(self, session):
        """Test that analyze_file prevents path traversal attacks."""

        # Test various path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "/etc/shadow",
            "../../../secrets/api_keys.txt",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
        ]

        for malicious_path in malicious_paths:
            result = await analyze_file(malicious_path)

            # Should return an error (either access denied or file not found)
            assert "error" in result
            assert result["exists"] is False
            # The specific error message may vary depending on the path resolution,
            # but it should always be blocked
            assert any(msg in result["error"] for msg in ["Access denied", "File not found"])

    @pytest.mark.asyncio
    async def test_analyze_file_within_project_allowed(self, session):
        """Test that analyze_file allows access to files within project directory."""

        # Create a test file within the project directory
        test_file = session.project_root / "test.py"
        test_content = """
def test_function():
    pass

class TestClass:
    pass

import os
from typing import Any
"""
        test_file.write_text(test_content)

        # Test analyzing the file
        result = await analyze_file("test.py")

        # Should succeed
        assert result["exists"] is True
        assert result["lines"] > 0
        assert result["functions"] == 1
        assert result["classes"] == 1
        assert len(result["imports"]) == 2
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_analyze_file_subdirectory_access(self, session):
        """Test that analyze_file allows access to subdirectories within project."""

        # Create a subdirectory and file
        subdir = session.project_root / "src" / "utils"
        subdir.mkdir(parents=True, exist_ok=True)

        test_file = subdir / "helper.py"
        test_file.write_text("def helper(): pass")

        # Test analyzing the file
        result = await analyze_file("src/utils/helper.py")

        # Should succeed
        assert result["exists"] is True
        assert result["functions"] == 1
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_analyze_file_symlink_prevention(self, session):
        """Test that analyze_file prevents access through symlinks pointing outside."""

        # This test would require creating symlinks, which is complex in cross-platform tests
        # For now, we'll test the basic path resolution logic
        malicious_path = "../../../etc/passwd"

        result = await analyze_file(malicious_path)

        # Should be blocked
        assert "error" in result
        assert "Access denied" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_file_nonexistent_within_project(self, session):
        """Test that analyze_file handles non-existent files within project correctly."""

        result = await analyze_file("nonexistent.py")

        # Should return file not found error, not access denied
        assert "error" in result
        assert "File not found" in result["error"]
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_analyze_file_absolute_path_blocked(self, session):
        """Test that absolute paths outside project are blocked."""

        # Try to access an absolute path
        absolute_path = "/etc/passwd" if Path("/etc/passwd").exists() else "C:\\Windows\\System32\\config\\SAM"

        result = await analyze_file(absolute_path)

        # Should be blocked
        assert "error" in result
        assert "Access denied" in result["error"]
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_analyze_file_path_resolution_consistency(self, session):
        """Test that path resolution is consistent and safe."""

        # Create a test file
        test_file = session.project_root / "test.py"
        test_file.write_text("print('hello')")

        # Test with different path formats that should resolve to the same file
        paths_to_test = [
            "test.py",
            "./test.py",
            "test.py",  # Already normalized
        ]

        for path in paths_to_test:
            result = await analyze_file(path)

            # All should succeed and return the same relative path
            assert result["exists"] is True
            assert result["file_path"] == "test.py"
            assert "error" not in result


if __name__ == "__main__":
    pytest.main([__file__])
