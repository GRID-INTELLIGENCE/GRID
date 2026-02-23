import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
except ImportError:
    print("MCP library not found. Please install: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolSession:
    """Manages tool execution session state."""

    execution_count: int = 0
    last_execution: str | None = None
    workspace_root: Path | None = None

    def __post_init__(self):
        if self.workspace_root is None:
            self.workspace_root = Path.cwd()


# Global session state
session = ToolSession()

# Initialize MCP server
server = Server("grid-enhanced-tools")


def format_tool_output(tool_name: str, result: dict[str, Any], execution_time: float) -> str:
    """Format tool execution output."""
    return f"""
🔧 **{tool_name.replace("_", " ").title()} Results:**
✅ Execution completed in {execution_time:.2f}s
📊 {json.dumps(result, indent=2)[:500]}{"..." if len(json.dumps(result)) > 500 else ""}
"""


# region agent log
def _debug_log(message: str, data: dict[str, Any] | None = None, hypothesis_id: str = "H1") -> None:
    try:
        import os as _os
        _path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "debug-14d2f0.log")
        _payload = {
            "sessionId": "14d2f0",
            "runId": data.get("runId", "run1") if data else "run1",
            "hypothesisId": hypothesis_id,
            "location": "enhanced_tools_mcp_server.py:run_command",
            "message": message,
            "data": data or {},
            "timestamp": __import__("time", fromlist=["time"]).time() * 1000,
        }
        with open(_path, "a", encoding="utf-8") as _f:
            _f.write(__import__("json", fromlist=["json"]).json.dumps(_payload) + "\n")
    except Exception:
        pass
# endregion


async def _run_process_and_communicate(
    cmd: list[str], cwd: Path | None, timeout: int
) -> tuple[asyncio.subprocess.Process, bytes, bytes]:
    """Run subprocess and communicate; entire operation must complete within timeout (unblocks stuck communicate)."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd or session.workspace_root,
    )
    # region agent log
    _debug_log("run_command process_created", {"pid": process.pid}, "H1")
    _debug_log("run_command before_communicate", {}, "H1")
    # endregion
    try:
        async with asyncio.timeout(timeout):
            stdout, stderr = await process.communicate()
    except TimeoutError:
        process.kill()
        await process.wait()
        raise
    # region agent log
    _debug_log("run_command after_communicate", {"returncode": process.returncode}, "H1")
    # endregion
    return process, stdout or b"", stderr or b""


async def run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 30) -> dict[str, Any]:
    """Run command with timeout and error handling. Timeout covers both process start and communicate (avoids stuck thread)."""
    # region agent log
    _debug_log("run_command entry", {"cmd": cmd, "timeout": timeout}, "H1")
    # endregion
    try:
        process, stdout, stderr = await asyncio.wait_for(
            _run_process_and_communicate(cmd, cwd, timeout),
            timeout=timeout,
        )
        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="ignore"),
            "stderr": stderr.decode("utf-8", errors="ignore"),
        }
    except TimeoutError:
        # region agent log
        _debug_log("run_command timeout (full)", {"timeout": timeout}, "H3")
        # endregion
        return {"success": False, "error": f"Command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "error": str(e), "returncode": -1}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available enhanced tools."""
    return [
        Tool(
            name="performance_profiler",
            description="Profile code execution performance and identify bottlenecks",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Python file or function to profile"},
                    "profiler_type": {
                        "type": "string",
                        "enum": ["cpu", "memory", "line_profiler"],
                        "default": "cpu",
                        "description": "Type of profiling to perform",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json"],
                        "default": "json",
                        "description": "Output format for results",
                    },
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="security_auditor",
            description="Audit code for security vulnerabilities and compliance issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "File or directory to audit"},
                    "audit_type": {
                        "type": "string",
                        "enum": ["vulnerabilities", "secrets", "dependencies", "all"],
                        "default": "all",
                        "description": "Type of security audit to perform",
                    },
                    "severity_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium",
                        "description": "Minimum severity level to report",
                    },
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="test_coverage_analyzer",
            description="Analyze test coverage and identify gaps",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Test directory or specific test file"},
                    "coverage_type": {
                        "type": "string",
                        "enum": ["line", "branch", "function", "statement"],
                        "default": "line",
                        "description": "Type of coverage analysis",
                    },
                    "threshold": {"type": "number", "default": 80.0, "description": "Coverage threshold percentage"},
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="documentation_generator",
            description="Generate documentation from code and docstrings",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Source code directory or file"},
                    "doc_type": {
                        "type": "string",
                        "enum": ["api", "readme", "inline", "sphinx"],
                        "default": "api",
                        "description": "Type of documentation to generate",
                    },
                    "output_dir": {"type": "string", "description": "Output directory for generated docs"},
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="dependency_health_monitor",
            description="Monitor and analyze project dependency health",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Requirements file or project directory"},
                    "check_type": {
                        "type": "string",
                        "enum": ["outdated", "vulnerabilities", "licenses", "health"],
                        "default": "health",
                        "description": "Type of dependency check",
                    },
                    "include_dev": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include development dependencies",
                    },
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="code_quality_gate",
            description="Enforce code quality standards and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "File or directory to analyze"},
                    "quality_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["lint", "complexity", "style", "type_check"],
                        "description": "Quality metrics to check",
                    },
                    "fail_threshold": {
                        "type": "number",
                        "default": 8.0,
                        "description": "Quality score threshold (0-10)",
                    },
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="workflow_orchestrator",
            description="Automate and orchestrate development workflows",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_type": {
                        "type": "string",
                        "enum": ["ci_cd", "testing", "deployment", "custom"],
                        "description": "Type of workflow to orchestrate",
                    },
                    "config": {"type": "object", "description": "Workflow configuration parameters"},
                    "dry_run": {
                        "type": "boolean",
                        "default": True,
                        "description": "Preview workflow without executing",
                    },
                },
                "required": ["workflow_type"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Execute enhanced tools."""
    start_time = asyncio.get_event_loop().time()
    session.execution_count += 1
    session.last_execution = name

    try:
        if name == "performance_profiler":
            result = await handle_performance_profiler(arguments)
        elif name == "security_auditor":
            result = await handle_security_auditor(arguments)
        elif name == "test_coverage_analyzer":
            result = await handle_test_coverage_analyzer(arguments)
        elif name == "documentation_generator":
            result = await handle_documentation_generator(arguments)
        elif name == "dependency_health_monitor":
            result = await handle_dependency_health_monitor(arguments)
        elif name == "code_quality_gate":
            result = await handle_code_quality_gate(arguments)
        elif name == "workflow_orchestrator":
            result = await handle_workflow_orchestrator(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        execution_time = asyncio.get_event_loop().time() - start_time
        formatted_output = format_tool_output(name, result, execution_time)

        return CallToolResult(content=[TextContent(type="text", text=formatted_output)])

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        execution_time = asyncio.get_event_loop().time() - start_time
        error_result = {"success": False, "error": str(e), "execution_time": execution_time}
        formatted_output = format_tool_output(name, error_result, execution_time)

        return CallToolResult(content=[TextContent(type="text", text=formatted_output)])


async def handle_performance_profiler(args: dict[str, Any]) -> dict[str, Any]:
    """Handle performance profiling."""
    target = args["target"]
    profiler_type = args.get("profiler_type", "cpu")
    args.get("output_format", "json")

    if profiler_type == "cpu":
        cmd = ["python", "-m", "cProfile", "-s", "cumulative", target]
    elif profiler_type == "memory":
        cmd = ["python", "-m", "memory_profiler", target]
    else:
        cmd = ["python", "-m", "line_profiler", target]

    result = await run_command(cmd, timeout=60)

    if result["success"]:
        return {
            "success": True,
            "profiler_type": profiler_type,
            "target": target,
            "output": result["stdout"],
            "recommendations": _generate_performance_recommendations(result["stdout"]),
        }
    else:
        return {"success": False, "error": result.get("stderr", "Profiling failed"), "target": target}


async def handle_security_auditor(args: dict[str, Any]) -> dict[str, Any]:
    """Handle security auditing."""
    target = args["target"]
    audit_type = args.get("audit_type", "all")
    severity_level = args.get("severity_level", "medium")

    results = {}

    if audit_type in ["vulnerabilities", "all"]:
        # Use bandit for security vulnerabilities
        cmd = ["python", "-m", "bandit", "-r", target, "-f", "json"]
        bandit_result = await run_command(cmd, timeout=60)
        results["vulnerabilities"] = bandit_result

    if audit_type in ["secrets", "all"]:
        # Use truffleHog or similar for secrets detection
        cmd = ["python", "-m", "detect-secrets", "scan", target]
        secrets_result = await run_command(cmd, timeout=60)
        results["secrets"] = secrets_result

    if audit_type in ["dependencies", "all"]:
        # Check for vulnerable dependencies
        cmd = ["python", "-m", "pip-audit", "--requirement", "requirements.txt"]
        deps_result = await run_command(cmd, timeout=60)
        results["dependencies"] = deps_result

    return {
        "success": True,
        "target": target,
        "audit_type": audit_type,
        "severity_level": severity_level,
        "results": results,
        "summary": _generate_security_summary(results),
    }


async def handle_test_coverage_analyzer(args: dict[str, Any]) -> dict[str, Any]:
    """Handle test coverage analysis."""
    target = args["target"]
    coverage_type = args.get("coverage_type", "line")
    threshold = args.get("threshold", 80.0)

    # Run pytest with coverage
    cmd = ["python", "-m", "pytest", f"--cov={target}", "--cov-report=json", "--cov-report=term"]
    result = await run_command(cmd, timeout=120)

    coverage_data = {}
    if result["success"]:
        try:
            # Try to read coverage.json if it exists
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
        except Exception:
            pass

    return {
        "success": result["success"],
        "target": target,
        "coverage_type": coverage_type,
        "threshold": threshold,
        "coverage_data": coverage_data,
        "meets_threshold": coverage_data.get("totals", {}).get("percent_covered", 0) >= threshold,
        "recommendations": _generate_coverage_recommendations(coverage_data),
    }


async def handle_documentation_generator(args: dict[str, Any]) -> dict[str, Any]:
    """Handle documentation generation."""
    target = args["target"]
    doc_type = args.get("doc_type", "api")
    output_dir = args.get("output_dir", "docs/generated")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if doc_type == "api":
        cmd = ["python", "-m", "sphinx", "-b", "html", target, output_dir]
    elif doc_type == "readme":
        cmd = ["python", "-c", f"import {target}; help({target})"]
    else:
        cmd = ["python", "-m", "pydoc", target]

    result = await run_command(cmd, timeout=120)

    return {
        "success": result["success"],
        "target": target,
        "doc_type": doc_type,
        "output_dir": output_dir,
        "generated_files": _list_generated_files(output_dir),
        "output": result["stdout"],
    }


async def handle_dependency_health_monitor(args: dict[str, Any]) -> dict[str, Any]:
    """Handle dependency health monitoring."""
    target = args["target"]
    check_type = args.get("check_type", "health")
    include_dev = args.get("include_dev", True)

    results = {}

    if check_type in ["outdated", "health"]:
        cmd = ["python", "-m", "pip", "list", "--outdated"]
        outdated_result = await run_command(cmd, timeout=60)
        results["outdated"] = outdated_result

    if check_type in ["vulnerabilities", "health"]:
        cmd = ["python", "-m", "pip-audit"]
        vuln_result = await run_command(cmd, timeout=60)
        results["vulnerabilities"] = vuln_result

    if check_type in ["licenses", "health"]:
        cmd = ["python", "-m", "pip-licenses", "--format=json"]
        license_result = await run_command(cmd, timeout=60)
        results["licenses"] = license_result

    return {
        "success": True,
        "target": target,
        "check_type": check_type,
        "include_dev": include_dev,
        "results": results,
        "health_score": _calculate_dependency_health_score(results),
    }


async def handle_code_quality_gate(args: dict[str, Any]) -> dict[str, Any]:
    """Handle code quality gating."""
    target = args["target"]
    quality_metrics = args.get("quality_metrics", ["lint", "complexity", "style", "type_check"])
    fail_threshold = args.get("fail_threshold", 8.0)

    results = {}

    if "lint" in quality_metrics:
        cmd = ["python", "-m", "ruff", "check", target, "--output-format=json"]
        lint_result = await run_command(cmd, timeout=60)
        results["lint"] = lint_result

    if "complexity" in quality_metrics:
        cmd = ["python", "-m", "radon", "cc", target, "--json"]
        complexity_result = await run_command(cmd, timeout=60)
        results["complexity"] = complexity_result

    if "style" in quality_metrics:
        cmd = ["python", "-m", "black", "--check", target]
        style_result = await run_command(cmd, timeout=60)
        results["style"] = style_result

    if "type_check" in quality_metrics:
        cmd = ["python", "-m", "mypy", target, "--json-report", "/tmp/mypy_report"]
        type_check_result = await run_command(cmd, timeout=60)
        results["type_check"] = type_check_result

    quality_score = _calculate_quality_score(results)
    passes_gate = quality_score >= fail_threshold

    return {
        "success": True,
        "target": target,
        "quality_metrics": quality_metrics,
        "fail_threshold": fail_threshold,
        "results": results,
        "quality_score": quality_score,
        "passes_gate": passes_gate,
        "recommendations": _generate_quality_recommendations(results),
    }


async def handle_workflow_orchestrator(args: dict[str, Any]) -> dict[str, Any]:
    """Handle workflow orchestration."""
    workflow_type = args["workflow_type"]
    config = args.get("config", {})
    dry_run = args.get("dry_run", True)

    workflow_templates = {
        "ci_cd": {
            "steps": ["lint", "test", "build", "security_scan", "deploy"],
            "tools": ["code_quality_gate", "test_coverage_analyzer", "security_auditor"],
        },
        "testing": {
            "steps": ["unit_tests", "integration_tests", "coverage_report"],
            "tools": ["test_coverage_analyzer"],
        },
        "deployment": {
            "steps": ["build", "security_check", "deploy"],
            "tools": ["security_auditor", "dependency_health_monitor"],
        },
    }

    template = workflow_templates.get(workflow_type, {"steps": [], "tools": []})

    if dry_run:
        return {
            "success": True,
            "workflow_type": workflow_type,
            "dry_run": True,
            "planned_steps": template["steps"],
            "required_tools": template["tools"],
            "estimated_duration": _estimate_workflow_duration(template),
            "config": config,
        }
    else:
        # Execute workflow (simplified for demo)
        execution_log = []
        for step in template["steps"]:
            execution_log.append(f"Executing step: {step}")

        return {
            "success": True,
            "workflow_type": workflow_type,
            "dry_run": False,
            "execution_log": execution_log,
            "config": config,
        }


# Helper functions
def _generate_performance_recommendations(output: str) -> list[str]:
    """Generate performance recommendations from profiler output."""
    recommendations = []
    if "ncalls" in output and "tottime" in output:
        recommendations.append("Consider optimizing functions with high total time")
    if "memory" in output.lower():
        recommendations.append("Review memory usage patterns")
    return recommendations


def _generate_security_summary(results: dict[str, Any]) -> dict[str, Any]:
    """Generate security audit summary."""
    summary = {"issues_found": 0, "critical_issues": 0, "recommendations": []}

    for audit_type, result in results.items():
        if result.get("success"):
            summary["issues_found"] += 1
            summary["recommendations"].append(f"Review {audit_type} findings")

    return summary


def _generate_coverage_recommendations(coverage_data: dict[str, Any]) -> list[str]:
    """Generate test coverage recommendations."""
    recommendations = []
    percent_covered = coverage_data.get("totals", {}).get("percent_covered", 0)

    if percent_covered < 80:
        recommendations.append("Increase test coverage to meet 80% threshold")

    return recommendations


def _list_generated_files(output_dir: str) -> list[str]:
    """List files in output directory."""
    try:
        return [str(p) for p in Path(output_dir).rglob("*") if p.is_file()]
    except Exception:
        return []


def _calculate_dependency_health_score(results: dict[str, Any]) -> float:
    """Calculate dependency health score."""
    score = 10.0

    for _check_type, result in results.items():
        if not result.get("success"):
            score -= 2.0

    return max(0.0, score)


def _calculate_quality_score(results: dict[str, Any]) -> float:
    """Calculate code quality score."""
    score = 10.0

    for _metric, result in results.items():
        if not result.get("success"):
            score -= 2.5

    return max(0.0, score)


def _generate_quality_recommendations(results: dict[str, Any]) -> list[str]:
    """Generate quality recommendations."""
    recommendations = []

    for metric, result in results.items():
        if not result.get("success"):
            recommendations.append(f"Fix {metric} issues")

    return recommendations


def _estimate_workflow_duration(template: dict[str, Any]) -> float:
    """Estimate workflow duration in seconds."""
    return len(template["steps"]) * 30  # 30 seconds per step estimate


async def main():
    """Main entry point."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
