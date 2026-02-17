#!/usr/bin/env python3
"""
GRID Mastermind MCP Server

Provides intelligent code analysis, project navigation, and knowledge management
capabilities for the GRID project.
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

# Ensure MCP is available before proceeding
# Flag to track MCP availability - allows graceful degradation
MCP_AVAILABLE = False

try:
    import mcp  # type: ignore[import-untyped]  # Optional dependency - graceful degradation

    mcp_path = mcp.__file__
    print(f"MCP library found at: {mcp_path}")

    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.server.stdio import stdio_server  # type: ignore[import-untyped]
    from mcp.types import (  # type: ignore[import-untyped]
        AnyUrl,
        CallToolResult,
        ReadResourceResult,
        Resource,
        TextContent,
        Tool,
    )

    MCP_AVAILABLE = True
except ImportError as e:
    print(f"MCP library not found or incomplete: {e}")
    print("Please ensure MCP library is properly installed: pip install mcp")
    print("MCP features will be unavailable.")
    # Don't exit - allow module to load with degraded functionality
    # Define placeholder types for when MCP is not available
    Server = None  # type: ignore[assignment,misc]
    stdio_server = None  # type: ignore[assignment]
    CallToolResult = None  # type: ignore[assignment,misc]
    ReadResourceResult = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]
    TextContent = None  # type: ignore[assignment,misc]
    Tool = None  # type: ignore[assignment,misc]
    AnyUrl = None  # type: ignore[assignment,misc]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MastermindSession:
    """Manages mastermind session state."""

    project_root: Path = grid_root
    last_analysis: dict[str, Any] | None = None
    indexed_files: list[str] = field(default_factory=list)
    query_count: int = 0


# Global session state
session = MastermindSession()

# Initialize MCP server (only if MCP is available)
if MCP_AVAILABLE and Server is not None:
    server = Server("grid-mastermind")
else:
    server = None  # type: ignore[assignment]


def format_project_info(info: dict[str, Any]) -> str:
    """Format project information for display."""
    return f"""
📁 **Project Information:**
- Root: {info.get("root", "N/A")}
- Files: {info.get("file_count", 0)}
- Directories: {info.get("dir_count", 0)}
- Languages: {", ".join(info.get("languages", []))}
- Last Updated: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")}
"""


def format_analysis_results(results: dict[str, Any]) -> str:
    """Format analysis results for display."""
    return f"""
🔍 **Analysis Results:**
- Complexity: {results.get("complexity", "N/A")}
- Quality Score: {results.get("quality_score", "N/A")}
- Test Coverage: {results.get("test_coverage", "N/A")}%
- Dependencies: {results.get("dependencies", 0)}
- Issues Found: {results.get("issues", 0)}
"""


def _list_resources_impl() -> list:
    """List available mastermind resources implementation."""
    if not MCP_AVAILABLE or Resource is None or AnyUrl is None:
        return []
    return [
        Resource(
            uri=AnyUrl("mastermind://project-info"),  # type: ignore[call-arg]
            name="Project Information",
            description="General information about the GRID project",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("mastermind://code-analysis"),  # type: ignore[call-arg]
            name="Code Analysis",
            description="Analysis of code quality and complexity",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("mastermind://dependencies"),  # type: ignore[call-arg]
            name="Dependencies",
            description="Project dependencies and relationships",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("mastermind://test-coverage"),  # type: ignore[call-arg]
            name="Test Coverage",
            description="Test coverage information",
            mimeType="application/json",
        ),
    ]


if MCP_AVAILABLE and server is not None:

    @server.list_resources()  # type: ignore[misc]
    async def list_resources() -> list:
        """List available mastermind resources."""
        return _list_resources_impl()


async def _read_resource_impl(uri: Any) -> Any:
    """Read a specific resource implementation."""
    if not MCP_AVAILABLE or ReadResourceResult is None or TextContent is None:
        return None
    try:
        uri_str = str(uri)
        if uri_str == "mastermind://project-info":
            info = await get_project_info()
            return ReadResourceResult(contents=[TextContent(type="text", text=json.dumps(info, indent=2))])  # type: ignore[call-arg]
        elif uri_str == "mastermind://code-analysis":
            analysis = await analyze_codebase()
            return ReadResourceResult(contents=[TextContent(type="text", text=json.dumps(analysis, indent=2))])  # type: ignore[call-arg]
        elif uri_str == "mastermind://dependencies":
            deps = await analyze_dependencies()
            return ReadResourceResult(contents=[TextContent(type="text", text=json.dumps(deps, indent=2))])  # type: ignore[call-arg]
        elif uri_str == "mastermind://test-coverage":
            coverage = await analyze_test_coverage()
            return ReadResourceResult(contents=[TextContent(type="text", text=json.dumps(coverage, indent=2))])  # type: ignore[call-arg]
        else:
            raise ValueError(f"Unknown resource: {uri_str}")
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return ReadResourceResult(contents=[TextContent(type="text", text=f"Error: {str(e)}")])  # type: ignore[call-arg]


if MCP_AVAILABLE and server is not None:

    @server.read_resource()  # type: ignore[misc]
    async def read_resource(uri: Any) -> Any:
        """Read a specific resource."""
        return await _read_resource_impl(uri)


def _list_tools_impl() -> list:
    """List available mastermind tools implementation."""
    if not MCP_AVAILABLE or Tool is None:
        return []
    return [
        Tool(
            name="analyze_file",
            description="Analyze a specific file for complexity and quality",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the file to analyze"}},
                "required": ["file_path"],
            },
        ),
        Tool(
            name="search_code",
            description="Search for code patterns across the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex supported)"},
                    "file_pattern": {"type": "string", "description": "File pattern to search in (e.g., *.py)"},
                },
                "required": ["pattern"],
            },
        ),
        Tool(
            name="find_dependencies",
            description="Find dependencies for a given file or module",
            inputSchema={
                "type": "object",
                "properties": {"target": {"type": "string", "description": "File or module to analyze"}},
                "required": ["target"],
            },
        ),
        Tool(
            name="get_project_structure",
            description="Get the project structure as a tree",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_depth": {"type": "integer", "description": "Maximum depth to traverse", "default": 3}
                },
            },
        ),
    ]


if MCP_AVAILABLE and server is not None:

    @server.list_tools()  # type: ignore[misc]
    async def list_tools() -> list:
        """List available mastermind tools."""
        return _list_tools_impl()


async def _call_tool_impl(name: str, arguments: dict[str, Any]) -> Any:
    """Call a specific tool implementation."""
    if not MCP_AVAILABLE or CallToolResult is None or TextContent is None:
        return None
    try:
        if name == "analyze_file":
            file_path = arguments.get("file_path")
            if file_path is None:
                raise ValueError("file_path argument is required")
            result = await analyze_file(str(file_path))
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])  # type: ignore[call-arg]
        elif name == "search_code":
            pattern = arguments.get("pattern")
            file_pattern = arguments.get("file_pattern", "*")
            if pattern is None:
                raise ValueError("pattern argument is required")
            result = await search_code(str(pattern), str(file_pattern))
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])  # type: ignore[call-arg]
        elif name == "find_dependencies":
            target = arguments.get("target")
            if target is None:
                raise ValueError("target argument is required")
            result = await find_dependencies(str(target))
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])  # type: ignore[call-arg]
        elif name == "get_project_structure":
            max_depth = arguments.get("max_depth", 3)
            result = await get_project_structure(int(max_depth))
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])  # type: ignore[call-arg]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])  # type: ignore[call-arg]


if MCP_AVAILABLE and server is not None:

    @server.call_tool()  # type: ignore[misc]
    async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
        """Call a specific tool."""
        return await _call_tool_impl(name, arguments)


# Helper functions
async def get_project_info() -> dict[str, Any]:
    """Get general project information."""
    info = {"root": str(session.project_root), "file_count": 0, "dir_count": 0, "languages": [], "size_mb": 0}

    def _scan_project() -> dict[str, Any]:
        file_count = 0
        dir_count = 0
        languages: set[str] = set()
        total_size = 0

        for item in session.project_root.rglob("*"):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size
                ext = item.suffix.lower()
                if ext == ".py":
                    languages.add("Python")
                elif ext == ".js":
                    languages.add("JavaScript")
                elif ext == ".ts":
                    languages.add("TypeScript")
                elif ext == ".json":
                    languages.add("JSON")
                elif ext == ".md":
                    languages.add("Markdown")
                elif ext == ".yml" or ext == ".yaml":
                    languages.add("YAML")
            elif item.is_dir():
                dir_count += 1

        return {
            "file_count": file_count,
            "dir_count": dir_count,
            "languages": sorted(languages),
            "size_mb": round(total_size / (1024 * 1024), 2),
        }

    try:
        info.update(await asyncio.to_thread(_scan_project))
    except Exception as e:
        logger.error(f"Error getting project info: {e}")

    return info


async def analyze_codebase() -> dict[str, Any]:
    """Analyze the entire codebase."""
    analysis = {
        "complexity": "medium",
        "quality_score": 0.0,
        "test_coverage": 0.0,
        "dependencies": 0,
        "issues": 0,
        "files_analyzed": 0,
    }

    try:
        python_files = await asyncio.to_thread(lambda: list(session.project_root.rglob("*.py")))
        analysis["files_analyzed"] = len(python_files)

        # Simple heuristics for analysis
        total_lines = 0
        test_files = 0
        imports = set()

        for py_file in python_files:
            try:
                async with aiofiles.open(py_file, encoding="utf-8") as f:
                    content = await f.read()
                    lines = content.split("\n")
                    total_lines += len(lines)

                    # Count test files
                    if "test" in py_file.name.lower():
                        test_files += 1

                    # Extract imports
                    for line in lines:
                        if line.strip().startswith("import ") or line.strip().startswith("from "):
                            imports.add(line.strip())
            except Exception:
                continue

        # Calculate metrics
        analysis["dependencies"] = len(imports)
        if python_files:
            analysis["test_coverage"] = round((test_files / len(python_files)) * 100, 2)

        # Simple quality score based on test coverage and file count
        analysis["quality_score"] = min(100, analysis["test_coverage"] + (10 if len(python_files) > 50 else 5))

        # Determine complexity
        if total_lines > 10000:
            analysis["complexity"] = "high"
        elif total_lines > 5000:
            analysis["complexity"] = "medium"
        else:
            analysis["complexity"] = "low"

    except Exception as e:
        logger.error(f"Error analyzing codebase: {e}")

    return analysis


async def analyze_dependencies() -> dict[str, Any]:
    """Analyze project dependencies."""
    deps = {"internal": [], "external": [], "total": 0}

    try:
        # Look for requirements files
        req_files = [
            session.project_root / "requirements.txt",
            session.project_root / "pyproject.toml",
            session.project_root / "setup.py",
        ]

        for req_file in req_files:
            if await asyncio.to_thread(req_file.exists):
                if req_file.name == "requirements.txt":
                    async with aiofiles.open(req_file) as f:
                        content = await f.read()
                        for line in content.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                deps["external"].append(line)
                elif req_file.name == "pyproject.toml":
                    # Parse pyproject.toml for dependencies
                    try:
                        import tomllib

                        async with aiofiles.open(req_file, mode="rb") as f:
                            content = await f.read()
                            data = tomllib.loads(content.decode("utf-8"))
                            project_deps = data.get("project", {}).get("dependencies", [])
                            deps["external"].extend(project_deps)
                    except Exception:
                        pass

        # Find internal modules
        for py_file in await asyncio.to_thread(lambda: list(session.project_root.rglob("*.py"))):
            if py_file.name != "__init__.py":
                rel_path = py_file.relative_to(session.project_root)
                module_path = str(rel_path.with_suffix("")).replace("\\", ".")
                deps["internal"].append(module_path)

        deps["total"] = len(deps["internal"]) + len(deps["external"])

    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")

    return deps


async def analyze_test_coverage() -> dict[str, Any]:
    """Analyze test coverage."""
    coverage = {"test_files": 0, "source_files": 0, "coverage_percentage": 0.0, "test_directories": []}

    try:
        # Count test and source files
        test_files = await asyncio.to_thread(lambda: list(session.project_root.rglob("*test*.py")))
        all_py = await asyncio.to_thread(lambda: list(session.project_root.rglob("*.py")))
        source_files = [f for f in all_py if "test" not in f.name.lower()]

        coverage["test_files"] = len(test_files)
        coverage["source_files"] = len(source_files)

        # Find test directories
        test_dirs = set()
        for test_file in test_files:
            test_dirs.add(str(test_file.parent.relative_to(session.project_root)))
        coverage["test_directories"] = sorted(list(test_dirs))

        # Calculate coverage percentage
        if source_files:
            coverage["coverage_percentage"] = round((len(test_files) / len(source_files)) * 100, 2)

    except Exception as e:
        logger.error(f"Error analyzing test coverage: {e}")

    return coverage


async def analyze_file(file_path: str) -> dict[str, Any]:
    """Analyze a specific file."""
    result = {
        "file_path": file_path,
        "exists": False,
        "lines": 0,
        "complexity": "low",
        "functions": 0,
        "classes": 0,
        "imports": [],
        "issues": [],
    }

    try:
        # Resolve the file path and ensure it's within the project directory
        file_path_obj = (session.project_root / file_path).resolve()

        # Security check: ensure the resolved path is still within project root
        if not file_path_obj.is_relative_to(session.project_root):
            result["error"] = "Access denied: file path outside project directory"
            return result

        if not await asyncio.to_thread(file_path_obj.exists):
            result["error"] = "File not found"
            return result

        result["exists"] = True
        # Update file_path to the resolved path for consistency
        result["file_path"] = str(file_path_obj.relative_to(session.project_root))

        async with aiofiles.open(file_path_obj, encoding="utf-8") as f:
            content = await f.read()
            lines = content.split("\n")
            result["lines"] = len(lines)

            # Simple analysis
            functions = 0
            classes = 0
            imports = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def "):
                    functions += 1
                elif stripped.startswith("class "):
                    classes += 1
                elif stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped)

            result["functions"] = functions
            result["classes"] = classes
            result["imports"] = imports

            # Determine complexity
            if len(lines) > 500:
                result["complexity"] = "high"
            elif len(lines) > 200:
                result["complexity"] = "medium"

    except Exception as e:
        result["error"] = str(e)

    return result


async def search_code(pattern: str, file_pattern: str = "*") -> dict[str, Any]:
    """Search for code patterns."""
    results = {"pattern": pattern, "file_pattern": file_pattern, "matches": [], "total_matches": 0}

    try:
        import re

        regex = re.compile(pattern, re.IGNORECASE)

        all_files = await asyncio.to_thread(lambda: [
            f for f in session.project_root.rglob(file_pattern) if f.is_file()
        ])
        for file_path in all_files:
            if True:
                try:
                    async with aiofiles.open(file_path, encoding="utf-8") as f:
                        content = await f.read()
                        lines = content.split("\n")

                        file_matches = []
                        for line_num, line in enumerate(lines, 1):
                            if regex.search(line):
                                file_matches.append({"line_number": line_num, "line": line.strip()})

                        if file_matches:
                            results["matches"].append(
                                {"file": str(file_path.relative_to(session.project_root)), "matches": file_matches}
                            )
                except Exception:
                    continue

        results["total_matches"] = len(results["matches"])

    except Exception as e:
        results["error"] = str(e)

    return results


async def find_dependencies(target: str) -> dict[str, Any]:
    """Find dependencies for a target."""
    deps: dict[str, Any] = {
        "target": target,
        "imports": [],
        "imported_by": [],
        "internal_modules": [],
        "external_packages": [],
    }

    try:
        target_path = Path(target)
        if not await asyncio.to_thread(target_path.exists):
            # Try to find it
            all_py = await asyncio.to_thread(lambda: list(session.project_root.rglob("*.py")))
            for py_file in all_py:
                if py_file.name == target or str(py_file).endswith(target):
                    target_path = py_file
                    break

        if await asyncio.to_thread(target_path.exists) and target_path.suffix == ".py":
            async with aiofiles.open(target_path, encoding="utf-8") as f:
                content = await f.read()
                for line in content.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("import ") or stripped.startswith("from "):
                        deps["imports"].append(stripped)

                        # Categorize
                        if "from ." in stripped or "from grid" in stripped:
                            deps["internal_modules"].append(stripped)
                        else:
                            deps["external_packages"].append(stripped)

        # Find files that import this target
        target_name = target_path.stem if await asyncio.to_thread(target_path.exists) else target
        for py_file in await asyncio.to_thread(lambda: list(session.project_root.rglob("*.py"))):
            if py_file != target_path:
                try:
                    async with aiofiles.open(py_file, encoding="utf-8") as f:
                        content = await f.read()
                        if target_name in content:
                            deps["imported_by"].append(str(py_file.relative_to(session.project_root)))
                except Exception:
                    continue

    except Exception as e:
        deps["error"] = str(e)

    return deps


async def get_project_structure(max_depth: int = 3) -> dict[str, Any]:
    """Get project structure as a tree."""
    structure = {"root": str(session.project_root), "max_depth": max_depth, "tree": {}}

    def build_tree(path: Path, current_depth: int = 0) -> dict:
        if current_depth >= max_depth:
            return {"type": "directory", "children": "..."}

        node: dict[str, Any] = {"type": "directory", "children": {}}

        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith("."):
                    continue

                str(item.relative_to(session.project_root))
                if item.is_file():
                    node["children"][item.name] = {
                        "type": "file",
                        "size": item.stat().st_size,
                        "extension": item.suffix,
                    }
                elif item.is_dir() and current_depth < max_depth:
                    node["children"][item.name] = build_tree(item, current_depth + 1)
        except Exception:
            pass

        return node

    structure["tree"] = await asyncio.to_thread(build_tree, session.project_root)
    return structure


async def main() -> None:
    """Main server entry point."""
    if not MCP_AVAILABLE or server is None or stdio_server is None:
        logger.error("MCP library is not available. Cannot start server.")
        print("Error: MCP library is required to run the server.")
        print("Please install it with: pip install mcp")
        return

    logger.info("Starting GRID Mastermind MCP Server...")

    # Run server
    async with stdio_server() as (read_stream, write_stream):  # type: ignore[misc]
        init_options = server.create_initialization_options()  # type: ignore[union-attr]
        await server.run(read_stream, write_stream, init_options)  # type: ignore[union-attr]


if __name__ == "__main__":
    asyncio.run(main())
