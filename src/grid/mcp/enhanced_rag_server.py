VEISON = "v2.2.0"
#!/usr/bin/env python3
"""
Enhanced RAG MCP Server with Conversational Capabilities

Provides RAG functionality with:
- Conversation memory and context
- Multi-hop reasoning
- Streaming support
- Session management
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

# Also add the global Python site-packages to path
import site

site.main()

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        ListToolsResult,
        TextContent,
        Tool,
    )
except ImportError as e:
    raise ImportError("MCP library not found. Please install: pip install mcp") from e

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGSession:
    """Manages RAG session state."""

    session_id: str
    created_at: datetime = datetime.now()
    last_accessed: datetime = datetime.now()
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedRAGMCPServer:
    """Enhanced RAG MCP Server with conversational capabilities."""

    def __init__(
        self,
        rag_engine_factory: Callable[[], Any] | None = None,
        ollama_checker: Callable[[], bool] | None = None,
    ):
        """Initialize enhanced RAG server."""
        if rag_engine_factory is None or ollama_checker is None:
            try:
                import importlib

                rag_module = importlib.import_module("tools.rag.conversational_rag")
                utils_module = importlib.import_module("tools.rag.utils")
                rag_engine_factory = rag_engine_factory or rag_module.create_conversational_rag_engine
                ollama_checker = ollama_checker or utils_module.check_ollama_connection
            except ImportError as e:
                raise ImportError("GRID RAG tools not found. Please ensure GRID is properly installed.") from e

        self.server = Server("grid-rag-enhanced")
        self.rag_engine = rag_engine_factory()
        self.sessions: dict[str, RAGSession] = {}
        self._register_handlers()

        # Expose tool handler for direct invocation (testing, tool dispatch)
        async def _call_tool_handler(name: str, arguments: dict[str, Any]) -> CallToolResult:
            return await self._dispatch_tool(name, arguments)

        self.server._call_tool_handler = _call_tool_handler

        async def _handle_list_tools(_req: Any) -> ListToolsResult:
            return self._get_list_tools_result()

        self.server._handle_list_tools = _handle_list_tools

        # Check Ollama connection
        if not ollama_checker():
            logger.warning("Ollama connection not available. Some features may be limited.")

    def _register_handlers(self):
        """Register MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available RAG tools."""
            tools = [
                Tool(
                    name="query",
                    description="Query the RAG knowledge base with conversation support",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Query text"},
                            "session_id": {
                                "type": "string",
                                "description": "Session ID for conversation continuity",
                                "default": None,
                            },
                            "enable_multi_hop": {
                                "type": "boolean",
                                "description": "Enable multi-hop reasoning",
                                "default": False,
                            },
                            "temperature": {"type": "number", "description": "LLM temperature", "default": 0.7},
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="create_session",
                    description="Create a new conversation session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session identifier"},
                            "metadata": {"type": "object", "description": "Session metadata", "default": {}},
                        },
                        "required": ["session_id"],
                    },
                ),
                Tool(
                    name="get_session",
                    description="Get information about a session",
                    inputSchema={
                        "type": "object",
                        "properties": {"session_id": {"type": "string", "description": "Session identifier"}},
                        "required": ["session_id"],
                    },
                ),
                Tool(
                    name="delete_session",
                    description="Delete a conversation session",
                    inputSchema={
                        "type": "object",
                        "properties": {"session_id": {"type": "string", "description": "Session identifier"}},
                        "required": ["session_id"],
                    },
                ),
                Tool(
                    name="get_stats",
                    description="Get RAG system statistics",
                    inputSchema={"type": "object"},
                ),
                Tool(
                    name="index_documents",
                    description="Index documents for RAG",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to documents"},
                            "rebuild": {"type": "boolean", "description": "Rebuild index", "default": False},
                        },
                        "required": ["path"],
                    },
                ),
            ]
            return ListToolsResult(tools=tools)

        # Expose for tests
        self.server._handle_list_tools = lambda req=None: list_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "query":
                    return await self._handle_query(arguments)
                elif name == "create_session":
                    return await self._handle_create_session(arguments)
                elif name == "get_session":
                    return await self._handle_get_session(arguments)
                elif name == "delete_session":
                    return await self._handle_delete_session(arguments)
                elif name == "get_stats":
                    return await self._handle_get_stats(arguments)
                elif name == "index_documents":
                    return await self._handle_index_documents(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")], isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(content=[TextContent(text=f"Error: {str(e)}", type="text")], isError=True)

    def _get_list_tools_result(self) -> ListToolsResult:
        """Return list of tools. Used by _handle_list_tools for testing."""
        tools = [
            Tool(
                name="query",
                description="Query the RAG knowledge base with conversation support",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query text"},
                        "session_id": {"type": "string", "description": "Session ID", "default": None},
                        "enable_multi_hop": {"type": "boolean", "default": False},
                        "temperature": {"type": "number", "default": 0.7},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="create_session",
                description="Create session",
                inputSchema={
                    "type": "object",
                    "properties": {"session_id": {"type": "string"}},
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="get_session",
                description="Get session",
                inputSchema={
                    "type": "object",
                    "properties": {"session_id": {"type": "string"}},
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="delete_session",
                description="Delete session",
                inputSchema={
                    "type": "object",
                    "properties": {"session_id": {"type": "string"}},
                    "required": ["session_id"],
                },
            ),
            Tool(name="get_stats", description="Get stats", inputSchema={"type": "object"}),
            Tool(
                name="index_documents",
                description="Index documents",
                inputSchema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            ),
        ]
        return ListToolsResult(tools=tools)

    async def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Dispatch tool calls by name. Used by _call_tool_handler for testing."""
        if name == "query":
            return await self._handle_query(arguments)
        elif name == "create_session":
            return await self._handle_create_session(arguments)
        elif name == "get_session":
            return await self._handle_get_session(arguments)
        elif name == "delete_session":
            return await self._handle_delete_session(arguments)
        elif name == "get_stats":
            return await self._handle_get_stats(arguments)
        elif name == "index_documents":
            return await self._handle_index_documents(arguments)
        else:
            return CallToolResult(
                content=[TextContent(text=json.dumps({"error": f"Unknown tool: {name}"}), type="text")],
                isError=True,
            )

    async def _handle_query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle RAG query with conversation support."""
        query = arguments.get("query")
        session_id = arguments.get("session_id")
        enable_multi_hop = arguments.get("enable_multi_hop", False)
        temperature = arguments.get("temperature", 0.7)

        if not query:
            return CallToolResult(content=[TextContent(text="Error: query is required", type="text")], isError=True)

        try:
            # Execute query with conversation support
            result = await self.rag_engine.query(
                query_text=query, session_id=session_id, enable_multi_hop=enable_multi_hop, temperature=temperature
            )

            # Format response
            response_data = {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "conversation_metadata": result.get("conversation_metadata", {}),
                "multi_hop_used": result.get("multi_hop_used", False),
                "fallback_used": result.get("fallback_used", False),
                "latency_ms": result.get("latency_ms", 0),
            }

            return CallToolResult(content=[TextContent(text=json.dumps(response_data, indent=2), type="text")])

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return CallToolResult(content=[TextContent(text=f"Query failed: {str(e)}", type="text")], isError=True)

    async def _handle_create_session(self, arguments: dict[str, Any]) -> CallToolResult:
        """Create a new conversation session."""
        session_id = arguments.get("session_id")
        metadata = arguments.get("metadata", {})

        if not session_id:
            return CallToolResult(
                content=[TextContent(text="Error: session_id is required", type="text")], isError=True
            )

        try:
            # Create session in RAG engine
            self.rag_engine.create_session(session_id, metadata)

            # Store session info
            self.sessions[session_id] = RAGSession(session_id=session_id, metadata=metadata)

            return CallToolResult(
                content=[TextContent(text=f"Session '{session_id}' created successfully", type="text")]
            )

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to create session: {str(e)}", type="text")], isError=True
            )

    async def _handle_get_session(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get session information."""
        session_id = arguments.get("session_id")

        if not session_id:
            return CallToolResult(
                content=[TextContent(text="Error: session_id is required", type="text")], isError=True
            )

        try:
            # Get session info from RAG engine
            session_info = self.rag_engine.get_session_info(session_id)

            if not session_info:
                return CallToolResult(
                    content=[TextContent(text=f"Session '{session_id}' not found", type="text")], isError=True
                )

            return CallToolResult(content=[TextContent(text=json.dumps(session_info, indent=2), type="text")])

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to get session: {str(e)}", type="text")], isError=True
            )

    async def _handle_delete_session(self, arguments: dict[str, Any]) -> CallToolResult:
        """Delete a conversation session."""
        session_id = arguments.get("session_id")

        if not session_id:
            return CallToolResult(
                content=[TextContent(text="Error: session_id is required", type="text")], isError=True
            )

        try:
            # Delete session from RAG engine
            success = self.rag_engine.delete_session(session_id)

            if success:
                # Remove from local sessions
                if session_id in self.sessions:
                    del self.sessions[session_id]

                return CallToolResult(
                    content=[TextContent(text=f"Session '{session_id}' deleted successfully", type="text")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(text=f"Session '{session_id}' not found", type="text")], isError=True
                )

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to delete session: {str(e)}", type="text")], isError=True
            )

    async def _handle_get_stats(self, arguments: dict[str, Any]) -> CallToolResult:
        """Get RAG system statistics."""
        try:
            # Get stats from RAG engine
            stats = self.rag_engine.get_conversation_stats()

            # Add server-specific stats
            stats["server_stats"] = {
                "active_sessions": len(self.sessions),
                "total_sessions_created": len(self.sessions),  # This would be tracked properly in production
            }

            return CallToolResult(content=[TextContent(text=json.dumps(stats, indent=2), type="text")])

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to get stats: {str(e)}", type="text")], isError=True
            )

    async def _handle_index_documents(self, arguments: dict[str, Any]) -> CallToolResult:
        """Index documents for RAG."""
        path = arguments.get("path")
        rebuild = arguments.get("rebuild", False)

        if not path:
            return CallToolResult(content=[TextContent(text="Error: path is required", type="text")], isError=True)

        try:
            # Index documents using RAG engine
            await self.rag_engine.index(path, rebuild=rebuild)

            stats = self.rag_engine.get_stats()

            return CallToolResult(
                content=[
                    TextContent(
                        text=f"Indexed documents from '{path}'. Total documents: {stats.get('document_count', 0)}",
                        type="text",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return CallToolResult(
                content=[TextContent(text=f"Failed to index documents: {str(e)}", type="text")], isError=True
            )

    async def run(self, read_stream, write_stream, options):
        """Run the MCP server."""
        await self.server.run(read_stream, write_stream, options)


# Create global server instance for MCP CLI
server: EnhancedRAGMCPServer | None = None


def get_server() -> EnhancedRAGMCPServer:
    """Get or create global server instance."""
    global server
    if server is None:
        server = EnhancedRAGMCPServer()
    return server


async def main():
    """Main server function."""
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await get_server().run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="grid-rag-enhanced",
                server_version="2.0.0",
                capabilities={
                    "tools": {
                        "query": {"description": "Conversational RAG query with memory"},
                        "create_session": {"description": "Create conversation session"},
                        "get_session": {"description": "Get session information"},
                        "delete_session": {"description": "Delete conversation session"},
                        "get_stats": {"description": "Get system statistics"},
                        "index_documents": {"description": "Index documents for RAG"},
                    },
                    "resources": {},
                },
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
