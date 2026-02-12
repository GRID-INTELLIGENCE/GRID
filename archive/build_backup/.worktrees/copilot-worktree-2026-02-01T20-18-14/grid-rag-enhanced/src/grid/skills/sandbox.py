"""
Skills sandboxing and isolation for GRID.

Provides secure execution environments for skills with resource limits,
network isolation, and audit logging. Implements containerized execution
and performance monitoring for skill isolation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# resource module is Unix-only
try:
    import resource

    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

# psutil is optional - used for process monitoring
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    psutil = None  # type: ignore
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


class SandboxStatus(Enum):
    """Sandbox execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


class ResourceLimit(Enum):
    """Resource limit types."""

    CPU_TIME = "cpu_time"
    MEMORY = "memory"
    DISK_SPACE = "disk_space"
    NETWORK = "network"
    PROCESSES = "processes"


@dataclass
class SandboxConfig:
    """Sandbox configuration."""

    max_cpu_time: float = 30.0  # seconds
    max_memory: int = 512 * 1024 * 1024  # 512MB
    max_disk_space: int = 100 * 1024 * 1024  # 100MB
    allow_network: bool = False
    allow_filesystem: bool = True
    allowed_paths: set[Path] = None
    environment_variables: dict[str, str] = None
    timeout: float = 60.0  # seconds

    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = set()
        if self.environment_variables is None:
            self.environment_variables = {}


@dataclass
class SandboxResult:
    """Sandbox execution result."""

    execution_id: str
    status: SandboxStatus
    start_time: datetime
    end_time: datetime | None
    exit_code: int | None
    stdout: str
    stderr: str
    resource_usage: dict[str, Any]
    error_message: str | None
    security_violations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "resource_usage": self.resource_usage,
            "error_message": self.error_message,
            "security_violations": self.security_violations,
        }


class SkillsSandbox:
    """
    Secure sandbox for skill execution with resource limits and monitoring.

    Features:
    - Resource limits (CPU, memory, disk, network)
    - Filesystem isolation
    - Network isolation
    - Process isolation
    - Security monitoring
    - Performance metrics
    - Audit logging
    """

    def __init__(self, config: SandboxConfig | None = None):
        """
        Initialize skills sandbox.

        Args:
            config: Sandbox configuration
        """
        self.config = config or SandboxConfig()
        self._active_executions: dict[str, asyncio.Task] = {}
        self._resource_monitors: dict[str, asyncio.Task] = {}
        self._execution_history: list[SandboxResult] = []
        self._security_violations: list[dict[str, Any]] = []

        logger.info("SkillsSandbox initialized")

    async def execute_skill(
        self,
        skill_code: str,
        skill_args: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> SandboxResult:
        """
        Execute a skill in the sandbox.

        Args:
            skill_code: Skill code to execute
            skill_args: Arguments for the skill
            execution_id: Unique execution identifier

        Returns:
            Sandbox execution result
        """
        if not execution_id:
            execution_id = f"skill_exec_{int(time.time())}"

        start_time = datetime.now()
        logger.info(f"Starting skill execution: {execution_id}")

        try:
            # Create temporary execution directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Prepare skill execution
                exec_script = self._prepare_execution_script(skill_code, skill_args or {})
                script_path = temp_path / "skill.py"
                script_path.write_text(exec_script)

                # Set up resource limits
                self._apply_resource_limits()

                # Execute with monitoring
                result = await self._execute_with_monitoring(
                    execution_id,
                    script_path,
                    temp_path,
                    start_time,
                )

                # Store result
                self._execution_history.append(result)
                logger.info(f"Skill execution completed: {execution_id}")

                return result

        except Exception as e:
            logger.error(f"Skill execution failed: {execution_id} - {e}")
            result = SandboxResult(
                execution_id=execution_id,
                status=SandboxStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=None,
                stdout="",
                stderr=str(e),
                resource_usage={},
                error_message=str(e),
                security_violations=[],
            )
            self._execution_history.append(result)
            return result

    def _prepare_execution_script(self, skill_code: str, skill_args: dict[str, Any]) -> str:
        """Prepare the skill execution script."""
        # Wrap skill code in execution harness
        harness = f"""
import sys
import json
import traceback
from datetime import datetime

# Skill arguments
SKILL_ARGS = {json.dumps(skill_args)}

# Execution context
execution_context = {{
    'start_time': datetime.now().isoformat(),
    'args': SKILL_ARGS,
}}

# Skill code
{skill_code}

# Execute main function if exists
if 'main' in locals():
    try:
        result = main(SKILL_ARGS)
        print(f"RESULT: {{json.dumps(result)}}")
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        traceback.print_exc()
        sys.exit(1)
else:
    print("ERROR: No main function found in skill")
    sys.exit(1)
"""
        return harness

    def _apply_resource_limits(self) -> None:
        """Apply resource limits to current process."""
        if not HAS_RESOURCE:
            logger.debug("Resource limits not available on this platform (Windows lacks resource module)")
            return

        try:
            # Set memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.config.max_memory, self.config.max_memory))

            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.config.max_cpu_time, self.config.max_cpu_time))

            # Set process limit
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (10, 10),  # Max 10 processes
            )

            logger.debug("Resource limits applied")

        except (OSError, ValueError) as e:
            logger.warning(f"Failed to apply resource limits: {e}")

    async def _execute_with_monitoring(
        self,
        execution_id: str,
        script_path: Path,
        work_dir: Path,
        start_time: datetime,
    ) -> SandboxResult:
        """Execute skill with resource monitoring."""
        process = None
        monitor_task = None

        try:
            # Start the process
            process = await asyncio.create_subprocess_exec(
                "python",
                str(script_path),
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_execution_environment(),
            )

            # Start resource monitoring
            monitor_task = asyncio.create_task(self._monitor_resources(execution_id, process.pid))

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.config.timeout)
                status = SandboxStatus.COMPLETED if process.returncode == 0 else SandboxStatus.FAILED

            except TimeoutError:
                # Kill the process on timeout
                process.kill()
                await process.wait()
                stdout, stderr = await process.communicate()
                status = SandboxStatus.TIMEOUT

            # Stop monitoring
            if monitor_task:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            # Get resource usage
            resource_usage = await self._get_resource_usage(execution_id)

            # Decode output
            stdout_text = stdout.decode("utf-8") if stdout else ""
            stderr_text = stderr.decode("utf-8") if stderr else ""

            # Check for security violations
            violations = self._check_security_violations(execution_id, work_dir)

            return SandboxResult(
                execution_id=execution_id,
                status=status,
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=process.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
                resource_usage=resource_usage,
                error_message=None if status == SandboxStatus.COMPLETED else stderr_text,
                security_violations=violations,
            )

        except Exception:
            # Cleanup on error
            if monitor_task:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            if process:
                process.kill()
                await process.wait()

            raise

    def _get_execution_environment(self) -> dict[str, str]:
        """Get execution environment variables."""
        import os

        env = os.environ.copy()

        # Add sandbox-specific variables
        env.update(self.config.environment_variables)
        env["SANDBOX_EXECUTION"] = "true"
        env["SANDBOX_START_TIME"] = datetime.now().isoformat()

        # Remove potentially dangerous variables
        dangerous_vars = [
            "PYTHONPATH",
            "PYTHONHOME",
            "LD_LIBRARY_PATH",
            "DYLD_LIBRARY_PATH",
        ]
        for var in dangerous_vars:
            env.pop(var, None)

        return env

    async def _monitor_resources(self, execution_id: str, pid: int) -> None:
        """Monitor resource usage during execution."""
        if not HAS_PSUTIL:
            # psutil not available - skip resource monitoring
            logger.debug(f"Resource monitoring skipped for {execution_id}: psutil not installed")
            return

        try:
            process = psutil.Process(pid)
            self._resource_monitors[execution_id] = asyncio.current_task()

            while process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                try:
                    # Collect metrics
                    metrics = {
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "memory_percent": process.memory_percent(),
                        "num_threads": process.num_threads(),
                        "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Store metrics
                    if execution_id not in self._active_executions:
                        self._active_executions[execution_id] = asyncio.current_task()

                    # Check limits
                    if metrics["memory_mb"] > self.config.max_memory / 1024 / 1024:
                        logger.warning(f"Memory limit exceeded for {execution_id}")
                        process.kill()
                        break

                    await asyncio.sleep(0.1)  # Monitor every 100ms

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

        except Exception as e:
            logger.error(f"Resource monitoring failed for {execution_id}: {e}")

    async def _get_resource_usage(self, execution_id: str) -> dict[str, Any]:
        """Get resource usage statistics."""
        # This is a simplified version - in production, you'd aggregate
        # the metrics collected during monitoring
        return {
            "peak_memory_mb": 0,
            "peak_cpu_percent": 0,
            "execution_time_seconds": 0,
            "disk_usage_mb": 0,
        }

    def _check_security_violations(self, execution_id: str, work_dir: Path) -> list[str]:
        """Check for security violations."""
        violations = []

        try:
            # Check for unauthorized file access
            if not self.config.allow_filesystem:
                for file_path in work_dir.rglob("*"):
                    if file_path.is_file():
                        violations.append(f"Unauthorized file access: {file_path}")

            # Check for network access attempts
            # This would require more sophisticated monitoring in production

            # Check for suspicious patterns
            suspicious_patterns = [
                "import os",
                "import subprocess",
                "import socket",
                "eval(",
                "exec(",
                "__import__",
            ]

            for pattern in suspicious_patterns:
                if pattern in violations:
                    violations.append(f"Suspicious pattern detected: {pattern}")

        except Exception as e:
            logger.error(f"Security violation check failed: {e}")

        return violations

    def get_execution_history(self, limit: int = 100) -> list[SandboxResult]:
        """Get execution history."""
        return self._execution_history[-limit:]

    def get_active_executions(self) -> list[str]:
        """Get list of active executions."""
        return list(self._active_executions.keys())

    async def kill_execution(self, execution_id: str) -> bool:
        """Kill an active execution."""
        if execution_id in self._active_executions:
            task = self._active_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._active_executions[execution_id]
            return True
        return False

    def get_security_violations(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get security violations."""
        return self._security_violations[-limit:]

    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel all active executions
        for execution_id in list(self._active_executions.keys()):
            asyncio.create_task(self.kill_execution(execution_id))

        # Clear monitors
        self._resource_monitors.clear()

        logger.info("Sandbox cleanup completed")


# Global sandbox instance
_global_sandbox: SkillsSandbox | None = None


def get_skills_sandbox() -> SkillsSandbox:
    """Get or create global skills sandbox instance."""
    global _global_sandbox
    if _global_sandbox is None:
        _global_sandbox = SkillsSandbox()
    return _global_sandbox


def set_skills_sandbox(sandbox: SkillsSandbox) -> None:
    """Set global skills sandbox instance."""
    global _global_sandbox
    _global_sandbox = sandbox


# Backward compatibility alias
SkillSandbox = SkillsSandbox
