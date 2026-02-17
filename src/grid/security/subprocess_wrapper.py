"""
Secure Subprocess Wrapper for GRID.

Provides a secure interface for executing subprocess commands with:
- Command whitelisting
- Input validation
- Path validation
- Automatic argument sanitization
- Timeout enforcement
- Audit logging

Usage:
    from grid.security.subprocess_wrapper import SecureSubprocess

    runner = SecureSubprocess(allowed_commands=["git", "python", "pytest"])
    result = runner.run(["git", "status"], cwd="/app/repo", timeout=30)
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .audit_logger import AuditEventType, AuditLogger
from .path_validator import SecurityError

logger = logging.getLogger(__name__)


@dataclass
class SubprocessResult:
    """Result of a subprocess execution."""

    returncode: int
    stdout: str
    stderr: str
    success: bool
    command: list[str]
    duration_ms: float


class SubprocessSecurityError(SecurityError):
    """Raised when a subprocess security constraint is violated."""

    pass


class SecureSubprocess:
    """
    Secure wrapper for subprocess operations.

    Features:
    - Command whitelisting
    - Path validation
    - Input sanitization
    - Timeout enforcement
    - Audit logging
    """

    def __init__(
        self,
        allowed_commands: list[str] | None = None,
        allowed_directories: list[str | Path] | None = None,
        default_timeout: int = 30,
        enable_audit_logging: bool = True,
        audit_logger: AuditLogger | None = None,
    ):
        """
        Initialize secure subprocess runner.

        Args:
            allowed_commands: Whitelist of allowed command names (e.g., ["git", "python"])
            allowed_directories: Directories where commands can be executed
            default_timeout: Default timeout in seconds
            enable_audit_logging: Whether to log subprocess executions
            audit_logger: Optional audit logger instance
        """
        self.allowed_commands = set(allowed_commands or [])
        self.allowed_directories = [Path(d) for d in (allowed_directories or [])]
        self.default_timeout = default_timeout
        self.enable_audit_logging = enable_audit_logging
        self.audit_logger = audit_logger or AuditLogger() if enable_audit_logging else None

    def _validate_command(self, command: list[str]) -> None:
        """
        Validate that the command is allowed.

        Args:
            command: Command as list of arguments

        Raises:
            SubprocessSecurityError: If command is not whitelisted
        """
        if not command:
            raise SubprocessSecurityError("Empty command not allowed")

        # Extract command name (first argument)
        cmd_name = Path(command[0]).name

        # If whitelist is configured, check it
        if self.allowed_commands and cmd_name not in self.allowed_commands:
            raise SubprocessSecurityError(
                f"Command '{cmd_name}' not in whitelist. Allowed: {sorted(self.allowed_commands)}"
            )

    def _validate_working_directory(self, cwd: str | Path | None) -> None:
        """
        Validate that the working directory is allowed.

        Args:
            cwd: Working directory path

        Raises:
            SubprocessSecurityError: If directory is not allowed
        """
        if cwd is None:
            return

        cwd_path = Path(cwd).resolve()

        # If allowed directories are configured, check them
        if self.allowed_directories:
            allowed = False
            for allowed_dir in self.allowed_directories:
                try:
                    if cwd_path.is_relative_to(allowed_dir.resolve()):
                        allowed = True
                        break
                except ValueError:
                    # Different drives on Windows
                    continue

            if not allowed:
                raise SubprocessSecurityError(f"Working directory '{cwd_path}' not in allowed directories")

    def _sanitize_command(self, command: str | list[str]) -> list[str]:
        """
        Sanitize command input.

        Args:
            command: Command as string or list

        Returns:
            Command as list of arguments

        Raises:
            SubprocessSecurityError: If command cannot be parsed
        """
        if isinstance(command, list):
            # Validate list elements are strings
            if not all(isinstance(arg, str) for arg in command):
                raise SubprocessSecurityError("Command arguments must be strings")
            return command

        if isinstance(command, str):
            # Parse string command using shlex
            try:
                return shlex.split(command)
            except ValueError as e:
                raise SubprocessSecurityError(f"Invalid command format: {e}") from e

        raise SubprocessSecurityError(f"Command must be str or list[str], got {type(command)}")

    def _log_execution(
        self,
        command: list[str],
        cwd: str | Path | None,
        timeout: int | None,
        result: SubprocessResult | None = None,
        error: str | None = None,
    ) -> None:
        """
        Log subprocess execution for audit purposes.

        Args:
            command: Command that was executed
            cwd: Working directory
            timeout: Timeout used
            result: Execution result (if successful)
            error: Error message (if failed)
        """
        if not self.enable_audit_logging or not self.audit_logger:
            return

        try:
            # Sanitize command for logging (remove sensitive data)
            sanitized_cmd = self._sanitize_for_logging(command)

            details = {
                "command": sanitized_cmd,
                "cwd": str(cwd) if cwd else None,
                "timeout": timeout,
            }

            if result:
                details.update(
                    {
                        "returncode": result.returncode,
                        "success": result.success,
                        "duration_ms": result.duration_ms,
                        "stdout_length": len(result.stdout),
                        "stderr_length": len(result.stderr),
                    }
                )

            if error:
                details["error"] = error

            # Log as security event
            self.audit_logger.log_event(
                event_type=AuditEventType.SECRET_ACCESS,  # Using existing event type
                details=details,
            )
        except Exception as e:
            logger.warning(f"Failed to log subprocess execution: {e}")

    def _sanitize_for_logging(self, command: list[str]) -> list[str]:
        """
        Sanitize command for logging (remove sensitive arguments).

        Args:
            command: Command to sanitize

        Returns:
            Sanitized command
        """
        # List of argument patterns that might contain sensitive data
        sensitive_patterns = ["--password", "--token", "--secret", "--key", "--api-key"]

        sanitized = []
        skip_next = False

        for i, arg in enumerate(command):
            if skip_next:
                skip_next = False
                sanitized.append("***REDACTED***")
                continue

            # Check if this argument is sensitive
            is_sensitive = any(pattern in arg.lower() for pattern in sensitive_patterns)

            if is_sensitive:
                # Check if value is in next argument or same argument
                if "=" in arg:
                    # Format: --key=value
                    key, _ = arg.split("=", 1)
                    sanitized.append(f"{key}=***REDACTED***")
                else:
                    # Format: --key value
                    sanitized.append(arg)
                    skip_next = True
            else:
                sanitized.append(arg)

        return sanitized

    def run(
        self,
        command: str | list[str],
        cwd: str | Path | None = None,
        timeout: int | None = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        env: dict[str, str] | None = None,
    ) -> SubprocessResult:
        """
        Execute a subprocess command securely.

        Args:
            command: Command to execute (string or list)
            cwd: Working directory (must be in allowed_directories if configured)
            timeout: Timeout in seconds (uses default_timeout if not specified)
            check: Raise exception if return code is non-zero
            capture_output: Capture stdout and stderr
            text: Return output as text (not bytes)
            env: Environment variables

        Returns:
            SubprocessResult with execution details

        Raises:
            SubprocessSecurityError: If security validation fails
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If check=True and return code is non-zero
        """
        import time

        start_time = time.perf_counter()

        # Sanitize and validate command
        cmd_list = self._sanitize_command(command)
        self._validate_command(cmd_list)

        # Validate working directory
        self._validate_working_directory(cwd)

        # Use default timeout if not specified
        timeout = timeout or self.default_timeout

        # Log execution start
        self._log_execution(cmd_list, cwd, timeout)

        try:
            # Execute command
            result = subprocess.run(
                cmd_list,
                cwd=str(cwd) if cwd else None,
                timeout=timeout,
                check=check,
                capture_output=capture_output,
                text=text,
                shell=False,  # NEVER use shell=True
                env=env,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000

            subprocess_result = SubprocessResult(
                returncode=result.returncode,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                success=result.returncode == 0,
                command=cmd_list,
                duration_ms=duration_ms,
            )

            # Log successful execution
            self._log_execution(cmd_list, cwd, timeout, result=subprocess_result)

            return subprocess_result

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Command timed out after {timeout} seconds"

            # Log timeout
            self._log_execution(cmd_list, cwd, timeout, error=error_msg)

            logger.warning(f"Subprocess timeout: {cmd_list}")

            # Create result for timeout
            subprocess_result = SubprocessResult(
                returncode=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                success=False,
                command=cmd_list,
                duration_ms=duration_ms,
            )

            if check:
                raise
            return subprocess_result

        except subprocess.CalledProcessError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Command failed with return code {e.returncode}"

            # Log failure
            subprocess_result = SubprocessResult(
                returncode=e.returncode,
                stdout=e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else ""),
                stderr=e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else ""),
                success=False,
                command=cmd_list,
                duration_ms=duration_ms,
            )

            self._log_execution(cmd_list, cwd, timeout, result=subprocess_result, error=error_msg)

            if check:
                raise
            return subprocess_result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"

            # Log error
            self._log_execution(cmd_list, cwd, timeout, error=error_msg)

            logger.error(f"Subprocess execution error: {e}", exc_info=True)
            raise SubprocessSecurityError(f"Failed to execute command: {e}") from e

    async def run_async(
        self,
        command: str | list[str],
        cwd: str | Path | None = None,
        timeout: int | None = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        env: dict[str, str] | None = None,
    ) -> SubprocessResult:
        """
        Execute a subprocess command asynchronously.

        Args:
            command: Command to execute (string or list)
            cwd: Working directory
            timeout: Timeout in seconds
            check: Raise exception if return code is non-zero
            capture_output: Capture stdout and stderr
            text: Return output as text
            env: Environment variables

        Returns:
            SubprocessResult with execution details
        """
        import asyncio
        import time

        start_time = time.perf_counter()

        # Sanitize and validate command
        cmd_list = self._sanitize_command(command)
        self._validate_command(cmd_list)
        self._validate_working_directory(cwd)

        timeout = timeout or self.default_timeout

        # Log execution start
        self._log_execution(cmd_list, cwd, timeout)

        try:
            # Execute asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                cwd=str(cwd) if cwd else None,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                env=env,
            )

            try:
                async with asyncio.timeout(timeout):
                    stdout, stderr = await process.communicate()
            except TimeoutError:
                process.kill()
                await process.wait()
                raise subprocess.TimeoutExpired(cmd_list, timeout)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Decode output if needed
            stdout_str = stdout.decode() if stdout and text else (stdout if stdout else "")
            stderr_str = stderr.decode() if stderr and text else (stderr if stderr else "")

            subprocess_result = SubprocessResult(
                returncode=process.returncode,
                stdout=stdout_str if isinstance(stdout_str, str) else "",
                stderr=stderr_str if isinstance(stderr_str, str) else "",
                success=process.returncode == 0,
                command=cmd_list,
                duration_ms=duration_ms,
            )

            if check and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd_list, stdout_str, stderr_str)

            # Log execution
            self._log_execution(cmd_list, cwd, timeout, result=subprocess_result)

            return subprocess_result

        except subprocess.TimeoutExpired:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Command timed out after {timeout} seconds"

            self._log_execution(cmd_list, cwd, timeout, error=error_msg)

            subprocess_result = SubprocessResult(
                returncode=-1,
                stdout="",
                stderr="",
                success=False,
                command=cmd_list,
                duration_ms=duration_ms,
            )

            if check:
                raise
            return subprocess_result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"

            self._log_execution(cmd_list, cwd, timeout, error=error_msg)

            logger.error(f"Async subprocess execution error: {e}", exc_info=True)
            raise SubprocessSecurityError(f"Failed to execute command: {e}") from e
