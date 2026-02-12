#!/usr/bin/env python3
"""
Agentic MCP Server for Enhanced Workflows

Provides agentic capabilities including:
- Case execution and management
- Skill retrieval and generation
- Event-driven agent coordination
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticMCPServer:
    """Agentic MCP Server for enhanced workflow capabilities."""

    def __init__(self):
        """Initialize agentic server."""
        self.server = Server("grid-agentic")
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available agentic tools."""
            tools = [
                Tool(
                    name="execute_case",
                    description="Execute an agentic case with cognitive awareness",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string", "description": "Case identifier"},
                            "reference_file_path": {"type": "string", "description": "Path to reference file"},
                            "agent_role": {
                                "type": "string",
                                "description": "Specific agent role to use",
                                "default": None
                            },
                            "task": {
                                "type": "string",
                                "description": "Specific task to execute",
                                "default": None
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User identifier",
                                "default": "default"
                            }
                        },
                        "required": ["case_id", "reference_file_path"],
                    },
                ),
                Tool(
                    name="retrieve_skill",
                    description="Retrieve relevant skills from skill store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Query for skill retrieval"},
                            "top_k": {
                                "type": "integer",
                                "description": "Number of skills to retrieve",
                                "default": 5
                            }
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="generate_memo",
                    description="Generate a memo from execution results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "case_id": {"type": "string", "description": "Case identifier"},
                            "result": {"type": "object", "description": "Execution result"},
                        },
                        "required": ["case_id", "result"],
                    },
                ),
                Tool(
                    name="get_system_stats",
                    description="Get agentic system statistics",
                    inputSchema={"type": "object"},
                ),
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "execute_case":
                    return await self._handle_execute_case(arguments)
                elif name == "retrieve_skill":
                    return await self._handle_retrieve_skill(arguments)
                elif name == "generate_memo":
                    return await self._handle_generate_memo(arguments)
                elif name == "get_system_stats":
                    return await self._handle_get_system_stats(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True
                )

    async def _handle_execute_case(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle case execution."""
        case_id = arguments.get("case_id")
        reference_file_path = arguments.get("reference_file_path")
        agent_role = arguments.get("agent_role")
        task = arguments.get("task")
        user_id = arguments.get("user_id", "default")

        if not case_id or not reference_file_path:
            return CallToolResult(
                content=[TextContent(text="Error: case_id and reference_file_path are required", type="text")],
                isError=True
            )

        try:
            # Import agentic system
            from grid.agentic.agentic_system import AgenticSystem

            # Initialize agentic system
            knowledge_base_path = Path.home() / ".grid" / "knowledge"
            agentic_system = AgenticSystem(knowledge_base_path)

            # Execute case
            result = await agentic_system.execute_case(
                case_id=case_id,
                reference_file_path=reference_file_path,
                agent_role=agent_role,
                task=task,
                user_id=user_id
            )

            return CallToolResult(
                content=[TextContent(text=json.dumps(result, indent=2), type="text")]
            )

        except Exception as e:
            logger.error(f"Failed to execute case: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to execute case: {str(e)}", type="text")], isError=True
            )

    async def _handle_retrieve_skill(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle skill retrieval."""
        query = arguments.get("query")
        top_k = arguments.get("top_k", 5)

        if not query:
            return CallToolResult(
                content=[TextContent(text="Error: query is required", type="text")], isError=True
            )

        try:
            # Import skill retriever
            from grid.agentic.skill_retriever import SkillRetriever

            # Initialize skill retriever
            skill_store_path = Path.home() / ".grid" / "knowledge"
            skill_retriever = SkillRetriever(skill_store_path)

            # Retrieve skills
            skills = skill_retriever.retrieve(query, top_k=top_k)

            result = {
                "query": query,
                "skills_retrieved": len(skills),
                "skills": skills
            }

            return CallToolResult(
                content=[TextContent(text=json.dumps(result, indent=2), type="text")]
            )

        except Exception as e:
            logger.error(f"Failed to retrieve skills: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to retrieve skills: {str(e)}", type="text")], isError=True
            )

    async def _handle_generate_memo(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle memo generation."""
        case_id = arguments.get("case_id")
        result = arguments.get("result")

        if not case_id or not result:
            return CallToolResult(
                content=[TextContent(text="Error: case_id and result are required", type="text")], isError=True
            )

        try:
            # Import memo generator
            from grid.agentic.memo_generator import MemoGenerator

            # Generate memo
            memo_generator = MemoGenerator()
            memo = memo_generator.generate(case_id, result)

            return CallToolResult(
                content=[TextContent(text=json.dumps(memo, indent=2), type="text")]
            )

        except Exception as e:
            logger.error(f"Failed to generate memo: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to generate memo: {str(e)}", type="text")], isError=True
            )

    async def _handle_get_system_stats(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get system statistics."""
        try:
            stats = {
                "system": "grid-agentic",
                "version": "2.0.0",
                "capabilities": [
                    "case_execution",
                    "skill_retrieval",
                    "memo_generation",
                    "cognitive_awareness"
                ],
                "status": "operational"
            }

            return CallToolResult(
                content=[TextContent(text=json.dumps(stats, indent=2), type="text")]
            )

        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to get system stats: {str(e)}", type="text")], isError=True
            )

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server."""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server = AgenticMCPServer()


async def main():
    """Main server function."""
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="grid-agentic",
                server_version="2.0.0",
                capabilities={
                    "tools": {
                        "execute_case": {"description": "Execute agentic case"},
                        "retrieve_skill": {"description": "Retrieve skills"},
                        "generate_memo": {"description": "Generate memo"},
                        "get_system_stats": {"description": "Get system statistics"}
                    },
                    "resources": {}
                }
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
