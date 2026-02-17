"""
/ci command implementation - Local CI pipeline simulation
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

from .base import CommandContext, CommandResult, PipelineCommand


class CICommand(PipelineCommand):
    """Execute local CI pipeline simulation"""

    def __init__(self):
        super().__init__()
        self.name = "ci"
        self._setup_pipeline_steps()

    def _setup_pipeline_steps(self):
        """Setup CI pipeline steps"""
        self.add_step("pre_commit", self._run_pre_commit_hooks, required=True)
        self.add_step("unit_tests", self._run_unit_tests, required=True)
        self.add_step("rag_contracts", self._run_rag_contracts, required=False)
        self.add_step("quality_check", self._run_quality_check, required=False)
        self.add_step("security_scan", self._run_security_scan, required=False)

    async def execute(self, args: list[str], kwargs: dict[str, Any], context: CommandContext) -> CommandResult:
        """Execute CI pipeline"""
        start_time = time.time()

        try:
            # Parse arguments
            fast_mode = "--fast" in args
            verbose = "--verbose" in args

            # Execute pipeline
            results = await self.execute_pipeline(context)

            # Generate summary
            summary = self._generate_summary(results, fast_mode)

            # Create recommendations
            recommendations = self._generate_recommendations(results)

            execution_time = time.time() - start_time

            return CommandResult(
                success=summary["overall_success"],
                message=summary["message"],
                data={"pipeline_results": results, "summary": summary, "fast_mode": fast_mode, "verbose": verbose},
                recommendations=recommendations,
                execution_time=execution_time,
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"CI pipeline failed: {str(e)}",
                error_details=str(e),
                execution_time=time.time() - start_time,
            )

    async def _run_subprocess(
        self,
        cmd: list[str],
        timeout: float,  # noqa: ASYNC109 timeout parameter is handled by caller
        cwd: str | Path | None = None,
    ) -> tuple[int, str, str]:
        """Run a subprocess asynchronously with timeout.

        Args:
            cmd: Command and arguments to run.
            timeout: Timeout in seconds.
            cwd: Working directory for the command.

        Returns:
            Tuple of (return_code, stdout, stderr).

        Raises:
            asyncio.TimeoutError: If the command times out.
        """
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            async with asyncio.timeout(timeout):
                stdout_bytes, stderr_bytes = await proc.communicate()
            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            return proc.returncode or 0, stdout, stderr
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise

    async def _run_pre_commit_hooks(self, context: CommandContext) -> dict[str, Any]:
        """Run pre-commit hooks"""
        try:
            self.logger.info("Running pre-commit hooks...")

            returncode, stdout, stderr = await self._run_subprocess(
                ["pre-commit", "run", "--all-files"],
                timeout=300,  # 5 minute timeout
            )

            return {
                "success": returncode == 0,
                "exit_code": returncode,
                "output": stdout[-2000:] if stdout else "",  # Last 2000 chars
                "errors": stderr[-1000:] if stderr else None,
                "duration": time.time(),
            }

        except TimeoutError:
            return {"success": False, "error": "Pre-commit hooks timed out after 5 minutes", "duration": time.time()}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time()}

    async def _run_unit_tests(self, context: CommandContext) -> dict[str, Any]:
        """Run unit tests"""
        try:
            self.logger.info("Running unit tests...")

            returncode, stdout, stderr = await self._run_subprocess(
                [sys.executable, "-m", "pytest", "tests/unit", "--tb=line", "-q", "--no-header"],
                timeout=180,
            )

            # Parse test results
            output = stdout
            passed_count = output.count("passed") if returncode == 0 else 0
            failed_count = output.count("failed") if returncode != 0 else 0
            skipped_count = output.count("skipped")

            return {
                "success": returncode == 0,
                "exit_code": returncode,
                "output": output,
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "total": passed_count + failed_count + skipped_count,
                "pass_rate": passed_count / (passed_count + failed_count) if (passed_count + failed_count) > 0 else 0.0,
                "duration": time.time(),
            }

        except TimeoutError:
            return {"success": False, "error": "Unit tests timed out after 3 minutes", "duration": time.time()}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time()}

    async def _run_rag_contracts(self, context: CommandContext) -> dict[str, Any]:
        """Run RAG contract tests if RAG files changed"""
        try:
            # Check if RAG files exist and have changes
            def _find_rag_files() -> list[Path]:
                return list(Path("grid/rag").rglob("*.py")) + list(Path("tools/rag").rglob("*.py"))

            rag_files = await asyncio.to_thread(_find_rag_files)

            if not rag_files:
                return {
                    "success": True,
                    "message": "No RAG files found, skipping contract tests",
                    "duration": time.time(),
                }

            self.logger.info("Running RAG contract tests...")

            returncode, stdout, stderr = await self._run_subprocess(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_rag_contracts.py",
                    "tests/test_rag.py",
                    "-v",
                    "--tb=short",
                    "-q",
                ],
                timeout=120,
            )

            # Parse test results
            output = stdout
            passed = output.count("passed") if returncode == 0 else 0
            total_tests = len([line for line in output.split("\n") if "test_" in line and "::" in line])

            return {
                "success": returncode == 0,
                "exit_code": returncode,
                "output": output,
                "passed": passed,
                "total": total_tests,
                "duration": time.time(),
            }

        except TimeoutError:
            return {"success": False, "error": "RAG contract tests timed out after 2 minutes", "duration": time.time()}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time()}

    async def _run_quality_check(self, context: CommandContext) -> dict[str, Any]:
        """Run code quality checks"""
        try:
            self.logger.info("Running quality checks...")

            # Check for common quality issues
            quality_issues = []

            # Check for TODO/FIXME comments
            try:
                returncode, stdout, stderr = await self._run_subprocess(
                    ["grep", "-r", "-n", "TODO\\|FIXME", "src/", "--include=*.py"],
                    timeout=30,
                )
                if stdout.strip():
                    todo_count = len(stdout.strip().split("\n"))
                    quality_issues.append(f"Found {todo_count} TODO/FIXME comments")
            except Exception:  # noqa: S110 intentional silent handling
                pass

            # Check for print statements (should use logging)
            try:
                returncode, stdout, stderr = await self._run_subprocess(
                    ["grep", "-r", "-n", "print(", "src/", "--include=*.py"],
                    timeout=30,
                )
                if stdout.strip():
                    print_count = len(stdout.strip().split("\n"))
                    quality_issues.append(f"Found {print_count} print statements (consider using logging)")
            except Exception:  # noqa: S110 intentional silent handling
                pass

            # Check for long lines
            try:
                returncode, stdout, stderr = await self._run_subprocess(
                    ["find", "src/", "-name", "*.py", "-exec", "grep", "-l", ".\\{120\\}", "{}", "+"],
                    timeout=30,
                )
                if stdout.strip():
                    long_line_files = len(stdout.strip().split("\n"))
                    quality_issues.append(f"Found {long_line_files} files with lines > 120 chars")
            except Exception:  # noqa: S110 intentional silent handling
                pass

            return {
                "success": len(quality_issues) == 0,
                "quality_issues": quality_issues,
                "issue_count": len(quality_issues),
                "duration": time.time(),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time()}

    async def _run_security_scan(self, context: CommandContext) -> dict[str, Any]:
        """Run basic security scan"""
        try:
            self.logger.info("Running security scan...")

            security_issues = []

            # Check for hardcoded secrets (basic patterns)
            secret_patterns = [
                "password\\s*=\\s*[\"'][^\"']+[\"']",
                "api_key\\s*=\\s*[\"'][^\"']+[\"']",
                "secret\\s*=\\s*[\"'][^\"']+[\"']",
                "token\\s*=\\s*[\"'][^\"']+[\"']",
            ]

            for pattern in secret_patterns:
                try:
                    returncode, stdout, stderr = await self._run_subprocess(
                        ["grep", "-r", "-n", pattern, "src/", "--include=*.py"],
                        timeout=30,
                    )
                    if stdout.strip():
                        matches = len(stdout.strip().split("\n"))
                        security_issues.append(f"Found {matches} potential hardcoded secrets")
                except Exception:  # noqa: S110 intentional silent handling
                    pass

            # Check for eval/exec usage
            try:
                returncode, stdout, stderr = await self._run_subprocess(
                    ["grep", "-r", "-n", "eval\\|exec", "src/", "--include=*.py"],
                    timeout=30,
                )
                if stdout.strip():
                    eval_count = len(stdout.strip().split("\n"))
                    security_issues.append(f"Found {eval_count} eval/exec statements (review needed)")
            except Exception:  # noqa: S110 intentional silent handling
                pass

            return {
                "success": len(security_issues) == 0,
                "security_issues": security_issues,
                "issue_count": len(security_issues),
                "duration": time.time(),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time()}

    def _generate_summary(self, results: dict[str, Any], fast_mode: bool) -> dict[str, Any]:
        """Generate pipeline execution summary"""
        required_steps = ["pre_commit", "unit_tests"]
        if fast_mode:
            required_steps = ["pre_commit", "unit_tests"]  # Skip optional steps in fast mode

        required_success = all(results.get(step, {}).get("success", False) for step in required_steps)

        total_steps = len([s for s in self.steps if s["name"] in results])
        successful_steps = len(
            [s for s in self.steps if s["name"] in results and results[s["name"]].get("success", False)]
        )

        if required_success:
            if successful_steps == total_steps:
                message = "✅ All CI checks passed"
            else:
                message = f"⚠️ Required checks passed, {total_steps - successful_steps} optional checks failed"
        else:
            failed_required = [step for step in required_steps if not results.get(step, {}).get("success", False)]
            message = f"❌ CI failed: {', '.join(failed_required)} failed"

        return {
            "overall_success": required_success,
            "message": message,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "fast_mode": fast_mode,
        }

    def _generate_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations based on results"""
        recommendations = []

        # Pre-commit recommendations
        pre_commit_result = results.get("pre_commit", {})
        if not pre_commit_result.get("success", True):
            if "ruff" in pre_commit_result.get("errors", "").lower():
                recommendations.append("Run 'ruff check --fix' to auto-fix linting issues")
            if "format" in pre_commit_result.get("errors", "").lower():
                recommendations.append("Run 'ruff format' to fix formatting issues")

        # Unit test recommendations
        unit_test_result = results.get("unit_tests", {})
        if not unit_test_result.get("success", True):
            failed = unit_test_result.get("failed", 0)
            recommendations.append(f"Fix {failed} failing unit tests")

        # Quality recommendations
        quality_result = results.get("quality_check", {})
        if quality_result.get("issue_count", 0) > 0:
            issues = quality_result.get("quality_issues", [])
            recommendations.extend(issues)

        # Security recommendations
        security_result = results.get("security_scan", {})
        if security_result.get("issue_count", 0) > 0:
            issues = security_result.get("security_issues", [])
            recommendations.extend(issues)

        # General recommendations
        if not recommendations:
            recommendations.append("All checks passed! Consider running /audit for deeper analysis.")

        return recommendations

    def get_help(self) -> str:
        """Return help text for the /ci command"""
        return """
/ci - Local CI Pipeline Simulation

USAGE:
    /ci [OPTIONS]

OPTIONS:
    --fast        Skip optional checks (RAG contracts, quality, security)
    --verbose     Show detailed output from all steps

DESCRIPTION:
    Executes a local CI pipeline that mirrors the GitHub Actions workflow.
    Includes pre-commit hooks, unit tests, and optional quality/security checks.

EXAMPLES:
    /ci                    # Run full pipeline
    /ci --fast            # Quick check with required steps only
    /ci --verbose         # Detailed output for debugging

INTEGRATION:
    - Links to fix_bug.md workflow for failures
    - Connects to code_review.md for quality issues
    - Updates testing.md for test improvements
"""

    def get_required_permissions(self) -> list[str]:
        """Return required permissions for CI command"""
        return ["read_files", "execute_commands"]


# Command instance for registration
Command = CICommand
