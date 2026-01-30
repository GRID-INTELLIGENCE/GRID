#!/usr/bin/env python3
"""
Multi-Repository Git MCP Server

Provides Git operations for multiple repositories.
Can switch between repositories or work with multiple at once.
"""

import asyncio
import json
import os
import subprocess
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
    from mcp.types import (
        CallToolResult,
        TextContent,
        Tool,
    )
except ImportError:
    print("MCP library not found. Please install: pip install mcp")
    sys.exit(1)

# Configure logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GitRepo:
    """Represents a Git repository."""

    name: str
    path: Path
    description: str | None = None
    is_active: bool = False


class MultiGitMCPServer:
    """Multi-Repository Git MCP Server"""

    def __init__(self):
        self.server = Server("multi-git")
        self.repositories: dict[str, GitRepo] = {}
        self.active_repo: str | None = None
        self._load_repositories()
        self._register_handlers()

    def _load_repositories(self):
        """Load repositories from environment or defaults"""
        # Default repository (current directory)
        current_dir = Path.cwd()
        self.repositories["default"] = GitRepo(
            name="default", path=current_dir, description="Current working directory", is_active=True
        )
        self.active_repo = "default"

        # Load additional repositories from environment
        repos_env = os.getenv("GIT_MCP_REPOSITORIES", "")
        if repos_env:
            for repo_def in repos_env.split(";"):
                if not repo_def.strip():
                    continue
                parts = repo_def.split(":")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    path = Path(parts[1].strip())
                    desc = parts[2].strip() if len(parts) > 2 else None

                    if path.exists() and (path / ".git").exists():
                        self.repositories[name] = GitRepo(name=name, path=path, description=desc)
                        logger.info(f"Loaded repository: {name} -> {path}")
                    else:
                        logger.warning(f"Repository not found or not a git repo: {path}")

    def _register_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available Git tools"""
            return [
                Tool(
                    name="git_list_repos",
                    description="List all configured repositories",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="git_switch_repo",
                    description="Switch to a different repository",
                    inputSchema={
                        "type": "object",
                        "properties": {"repo": {"type": "string", "description": "Repository name to switch to"}},
                        "required": ["repo"],
                    },
                ),
                Tool(
                    name="git_status",
                    description="Show repository status (porcelain)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository name (optional, uses active repo)",
                                "default": None,
                            }
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="git_log",
                    description="Show recent commits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository name (optional, uses active repo)",
                                "default": None,
                            },
                            "max_count": {"type": "integer", "description": "Maximum number of commits", "default": 50},
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="git_diff",
                    description="Show diff between refs or working tree",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository name (optional, uses active repo)",
                                "default": None,
                            },
                            "ref1": {
                                "type": "string",
                                "description": "First reference (default: working tree)",
                                "default": None,
                            },
                            "ref2": {"type": "string", "description": "Second reference", "default": None},
                            "file": {"type": "string", "description": "Specific file to diff", "default": None},
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="git_branches",
                    description="List branches",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository name (optional, uses active repo)",
                                "default": None,
                            }
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="git_show_file",
                    description="Show file content at specific ref",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository name (optional, uses active repo)",
                                "default": None,
                            },
                            "file": {"type": "string", "description": "File path"},
                            "ref": {
                                "type": "string",
                                "description": "Git reference (default: HEAD)",
                                "default": "HEAD",
                            },
                        },
                        "required": ["file"],
                    },
                ),
                Tool(
                    name="git_add_repo",
                    description="Add a new repository to the list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Repository name"},
                            "path": {"type": "string", "description": "Repository path"},
                            "description": {"type": "string", "description": "Repository description", "default": None},
                        },
                        "required": ["name", "path"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "git_list_repos":
                    return await self._list_repos(arguments)
                elif name == "git_switch_repo":
                    return await self._switch_repo(arguments)
                elif name == "git_status":
                    return await self._git_status(arguments)
                elif name == "git_log":
                    return await self._git_log(arguments)
                elif name == "git_diff":
                    return await self._git_diff(arguments)
                elif name == "git_branches":
                    return await self._git_branches(arguments)
                elif name == "git_show_file":
                    return await self._git_show_file(arguments)
                elif name == "git_add_repo":
                    return await self._git_add_repo(arguments)
                else:
                    return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

    def _get_repo(self, repo_name: str | None = None) -> GitRepo:
        """Get repository by name or active repo"""
        if repo_name:
            if repo_name not in self.repositories:
                raise ValueError(f"Repository '{repo_name}' not found")
            return self.repositories[repo_name]
        else:
            if not self.active_repo:
                raise ValueError("No active repository")
            return self.repositories[self.active_repo]

    def _run_git(self, repo: GitRepo, args: list[str]) -> str:
        """Run git command in repository"""
        cmd = ["git", "-C", str(repo.path)] + args
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)

    async def _list_repos(self, _args: dict[str, Any]) -> CallToolResult:
        """List all repositories"""
        repos_info = []
        for name, repo in self.repositories.items():
            repos_info.append(
                {
                    "name": name,
                    "path": str(repo.path),
                    "description": repo.description or "",
                    "is_active": name == self.active_repo,
                    "branch": self._get_current_branch(repo) if repo.path.exists() else "N/A",
                }
            )

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(repos_info, indent=2))])

    async def _switch_repo(self, args: dict[str, Any]) -> CallToolResult:
        """Switch to a different repository"""
        repo_name = args["repo"]
        if repo_name not in self.repositories:
            return CallToolResult(content=[TextContent(type="text", text=f"Repository '{repo_name}' not found")])

        self.active_repo = repo_name
        repo = self.repositories[repo_name]
        branch = self._get_current_branch(repo)

        return CallToolResult(
            content=[
                TextContent(
                    type="text", text=f"Switched to repository '{repo_name}' at {repo.path}\nCurrent branch: {branch}"
                )
            ]
        )

    async def _git_status(self, args: dict[str, Any]) -> CallToolResult:
        """Get git status"""
        repo = self._get_repo(args.get("repo"))
        try:
            output = self._run_git(repo, ["status", "--porcelain"])
            return CallToolResult(content=[TextContent(type="text", text=output)])
        except subprocess.CalledProcessError as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Git status failed: {e.output}")])

    async def _git_log(self, args: dict[str, Any]) -> CallToolResult:
        """Get git log"""
        repo = self._get_repo(args.get("repo"))
        max_count = args.get("max_count", 50)
        try:
            output = self._run_git(repo, ["log", "--oneline", f"-n{max_count}"])
            return CallToolResult(content=[TextContent(type="text", text=output)])
        except subprocess.CalledProcessError as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Git log failed: {e.output}")])

    async def _git_diff(self, args: dict[str, Any]) -> CallToolResult:
        """Get git diff"""
        repo = self._get_repo(args.get("repo"))
        ref1 = args.get("ref1")
        ref2 = args.get("ref2")
        file_path = args.get("file")

        git_args = ["diff"]
        if ref1:
            git_args.append(ref1)
        if ref2:
            git_args.append(ref2)
        if file_path:
            git_args.append("--")
            git_args.append(file_path)

        try:
            output = self._run_git(repo, git_args)
            return CallToolResult(content=[TextContent(type="text", text=output)])
        except subprocess.CalledProcessError as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Git diff failed: {e.output}")])

    async def _git_branches(self, args: dict[str, Any]) -> CallToolResult:
        """Get git branches"""
        repo = self._get_repo(args.get("repo"))
        try:
            output = self._run_git(repo, ["branch", "-a"])
            return CallToolResult(content=[TextContent(type="text", text=output)])
        except subprocess.CalledProcessError as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Git branches failed: {e.output}")])

    async def _git_show_file(self, args: dict[str, Any]) -> CallToolResult:
        """Show file content at ref"""
        repo = self._get_repo(args.get("repo"))
        file_path = args["file"]
        ref = args.get("ref", "HEAD")

        try:
            output = self._run_git(repo, ["show", f"{ref}:{file_path}"])
            return CallToolResult(content=[TextContent(type="text", text=output)])
        except subprocess.CalledProcessError as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Git show failed: {e.output}")])

    async def _git_add_repo(self, args: dict[str, Any]) -> CallToolResult:
        """Add a new repository"""
        name = args["name"]
        path = Path(args["path"])
        description = args.get("description")

        if not path.exists():
            return CallToolResult(content=[TextContent(type="text", text=f"Path does not exist: {path}")])

        if not (path / ".git").exists():
            return CallToolResult(content=[TextContent(type="text", text=f"Not a git repository: {path}")])

        if name in self.repositories:
            return CallToolResult(content=[TextContent(type="text", text=f"Repository '{name}' already exists")])

        self.repositories[name] = GitRepo(name=name, path=path, description=description)

        return CallToolResult(content=[TextContent(type="text", text=f"Added repository '{name}' at {path}")])

    def _get_current_branch(self, repo: GitRepo) -> str:
        """Get current branch of repository"""
        try:
            output = self._run_git(repo, ["branch", "--show-current"])
            return output.strip()
        except Exception:
            return "unknown"


async def main():
    """Main server entry point"""
    logger.info("Starting Multi-Repository Git MCP Server...")
    server = MultiGitMCPServer()

    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream, server.server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
