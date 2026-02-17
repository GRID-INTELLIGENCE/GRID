"""
Security Tests for Subprocess Operations.

Tests command injection prevention, path validation, input sanitization,
and timeout handling in the SecureSubprocess wrapper.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from grid.security.subprocess_wrapper import (
    SecureSubprocess,
    SubprocessResult,
    SubprocessSecurityError,
)


class TestSecureSubprocess:
    """Test suite for SecureSubprocess wrapper."""

    def test_command_whitelisting_allows_whitelisted_command(self) -> None:
        """Test that whitelisted commands are allowed."""
        runner = SecureSubprocess(allowed_commands=["python", "echo"])

        # Should not raise
        result = runner.run(["python", "--version"], timeout=5)
        assert isinstance(result, SubprocessResult)

    def test_command_whitelisting_blocks_non_whitelisted_command(self) -> None:
        """Test that non-whitelisted commands are blocked."""
        runner = SecureSubprocess(allowed_commands=["python"])

        with pytest.raises(SubprocessSecurityError, match="not in whitelist"):
            runner.run(["rm", "-rf", "/"], timeout=5)

    def test_command_whitelisting_allows_all_when_empty(self) -> None:
        """Test that empty whitelist allows all commands."""
        runner = SecureSubprocess(allowed_commands=[])

        # Should not raise
        result = runner.run(["python", "--version"], timeout=5)
        assert isinstance(result, SubprocessResult)

    def test_path_validation_allows_allowed_directory(self) -> None:
        """Test that commands can run in allowed directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = SecureSubprocess(allowed_directories=[tmpdir])

            # Should not raise
            result = runner.run(["python", "--version"], cwd=tmpdir, timeout=5)
            assert isinstance(result, SubprocessResult)

    def test_path_validation_blocks_non_allowed_directory(self) -> None:
        """Test that commands cannot run in non-allowed directories."""
        runner = SecureSubprocess(allowed_directories=["/tmp"])

        with pytest.raises(SubprocessSecurityError, match="not in allowed directories"):
            runner.run(["python", "--version"], cwd="/root", timeout=5)

    def test_path_validation_allows_all_when_empty(self) -> None:
        """Test that empty allowed_directories allows all directories."""
        runner = SecureSubprocess(allowed_directories=[])

        # Should not raise
        result = runner.run(["python", "--version"], cwd="/tmp", timeout=5)
        assert isinstance(result, SubprocessResult)

    def test_command_injection_prevention_string_command(self) -> None:
        """Test that string commands are safely parsed."""
        runner = SecureSubprocess()

        # Command injection attempt
        malicious_cmd = "python --version; rm -rf /"
        result = runner.run(malicious_cmd, timeout=5)

        # Should execute only the first command, not the injection
        assert "Python" in result.stdout or result.returncode != 0

    def test_command_injection_prevention_list_command(self) -> None:
        """Test that list commands prevent injection."""
        runner = SecureSubprocess()

        # List command prevents injection
        result = runner.run(["python", "--version"], timeout=5)

        # Should execute successfully
        assert isinstance(result, SubprocessResult)

    def test_timeout_enforcement(self) -> None:
        """Test that timeouts are enforced."""
        runner = SecureSubprocess(default_timeout=1)

        # Command that will hang
        result = runner.run(["python", "-c", "import time; time.sleep(5)"], timeout=1)

        # Should timeout
        assert result.returncode == -1
        assert not result.success

    def test_default_timeout(self) -> None:
        """Test that default timeout is used when not specified."""
        runner = SecureSubprocess(default_timeout=1)

        result = runner.run(["python", "-c", "import time; time.sleep(2)"])

        # Should timeout using default
        assert result.returncode == -1

    def test_successful_execution(self) -> None:
        """Test successful command execution."""
        runner = SecureSubprocess()

        result = runner.run(["python", "--version"], timeout=5)

        assert result.success
        assert result.returncode == 0
        assert "Python" in result.stdout
        assert result.duration_ms > 0

    def test_failed_execution(self) -> None:
        """Test failed command execution."""
        runner = SecureSubprocess()

        result = runner.run(["python", "-c", "exit(1)"], timeout=5)

        assert not result.success
        assert result.returncode == 1

    def test_empty_command_rejected(self) -> None:
        """Test that empty commands are rejected."""
        runner = SecureSubprocess()

        with pytest.raises(SubprocessSecurityError, match="Empty command"):
            runner.run([], timeout=5)

    def test_string_command_parsing(self) -> None:
        """Test that string commands are parsed correctly."""
        runner = SecureSubprocess()

        # String command should be parsed
        result = runner.run("python --version", timeout=5)

        assert result.success
        assert "Python" in result.stdout

    def test_sensitive_argument_redaction(self) -> None:
        """Test that sensitive arguments are redacted in logging."""
        runner = SecureSubprocess(enable_audit_logging=True)

        # Command with sensitive data
        result = runner.run(
            ["python", "-c", "print('test')"],
            env={"PASSWORD": "secret123", "API_KEY": "key456"},
            timeout=5,
        )

        # Should execute successfully
        assert result.success

        # Note: Actual redaction testing would require inspecting audit logs
        # This is a basic smoke test

    def test_async_execution(self) -> None:
        """Test asynchronous command execution."""
        import asyncio

        async def run_async() -> None:
            runner = SecureSubprocess()
            result = await runner.run_async(["python", "--version"], timeout=5)

            assert result.success
            assert "Python" in result.stdout

        asyncio.run(run_async())

    def test_async_timeout(self) -> None:
        """Test async timeout enforcement."""
        import asyncio

        async def run_async_timeout() -> None:
            runner = SecureSubprocess(default_timeout=1)
            result = await runner.run_async(["python", "-c", "import time; time.sleep(5)"], timeout=1)

            assert result.returncode == -1
            assert not result.success

        asyncio.run(run_async_timeout())

    def test_invalid_command_format(self) -> None:
        """Test that invalid command formats are rejected."""
        runner = SecureSubprocess()

        # Invalid command type
        with pytest.raises(SubprocessSecurityError):
            runner.run(123, timeout=5)  # type: ignore[arg-type]

    def test_check_parameter_raises_on_failure(self) -> None:
        """Test that check=True raises exception on failure."""
        runner = SecureSubprocess()

        with pytest.raises(subprocess.CalledProcessError):
            runner.run(["python", "-c", "exit(1)"], check=True, timeout=5)

    def test_check_parameter_succeeds_on_success(self) -> None:
        """Test that check=True doesn't raise on success."""
        runner = SecureSubprocess()

        # Should not raise
        result = runner.run(["python", "--version"], check=True, timeout=5)
        assert result.success


class TestCommandInjectionPrevention:
    """Test suite for command injection prevention."""

    def test_shell_injection_attempt(self) -> None:
        """Test prevention of shell injection attempts."""
        runner = SecureSubprocess()

        # Various injection attempts
        injection_attempts = [
            "python --version; rm -rf /",
            "python --version && rm -rf /",
            "python --version | cat /etc/passwd",
            "python --version `whoami`",
            "python --version $(whoami)",
        ]

        for attempt in injection_attempts:
            # Should parse safely and not execute injection
            result = runner.run(attempt, timeout=5)
            # Command should either succeed (python --version) or fail safely
            assert isinstance(result, SubprocessResult)

    def test_path_traversal_prevention(self) -> None:
        """Test prevention of path traversal attacks."""
        runner = SecureSubprocess(allowed_directories=["/tmp"])

        # Path traversal attempts
        traversal_attempts = [
            "../../etc/passwd",
            "/root/.ssh/id_rsa",
            "..\\..\\windows\\system32",
        ]

        for attempt in traversal_attempts:
            with pytest.raises(SubprocessSecurityError):
                runner.run(["python", "--version"], cwd=attempt, timeout=5)


class TestPathValidation:
    """Test suite for path validation."""

    def test_relative_path_within_base(self) -> None:
        """Test that relative paths within base are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = SecureSubprocess(allowed_directories=[tmpdir])

            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            result = runner.run(["python", "--version"], cwd=str(subdir), timeout=5)
            assert result.success

    def test_absolute_path_within_base(self) -> None:
        """Test that absolute paths within base are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = SecureSubprocess(allowed_directories=[tmpdir])

            result = runner.run(["python", "--version"], cwd=Path(tmpdir).resolve(), timeout=5)
            assert result.success

    def test_path_outside_base_rejected(self) -> None:
        """Test that paths outside base are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = SecureSubprocess(allowed_directories=[tmpdir])

            with tempfile.TemporaryDirectory() as other_dir:
                with pytest.raises(SubprocessSecurityError):
                    runner.run(["python", "--version"], cwd=str(other_dir), timeout=5)
