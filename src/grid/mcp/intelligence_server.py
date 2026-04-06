#!/usr/bin/env python3
"""
GRID Intelligence MCP Server

Provides AI-brain and knowledge-graph intelligence tools over the MCP protocol.
Wraps the ``grid.intelligence`` module (AIBrain, AIBrainSession, KnowledgeGraphBridge)
to expose session management, graph queries, and navigation enhancement as MCP tools.

Server name: grid-intelligence

Runnable as:
  python -m grid.mcp.intelligence_server
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
# File lives at  src/grid/mcp/intelligence_server.py
# Four levels up from here is the grid root.
_here = Path(__file__).parent
_grid_root = _here.parent.parent.parent  # src/grid/mcp -> src/grid -> src -> grid_root

try:
    from grid.security.path_manager import SecurePathManager

    _path_manager = SecurePathManager(base_dir=_grid_root)
    _path_manager.add_path(_grid_root / "src", validate=True)
except ImportError:
    sys.path.insert(0, str(_grid_root / "src"))

import site  # noqa: E402

site.main()

# ── MCP availability ──────────────────────────────────────────────────────────
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        Resource,
        TextContent,
        Tool,
    )

    MCP_AVAILABLE = True
except ImportError:
    sys.stderr.write("MCP library not found. Please install: pip install mcp\n")
    sys.exit(1)

# ── Intelligence module availability ─────────────────────────────────────────
try:
    from grid.intelligence.ai_brain_bridge import (
        KnowledgeGraphBridge,
        NavigationEnhancement,
    )
    from grid.intelligence.brain import AIBrain, AIBrainSession  # noqa: F401

    INTELLIGENCE_AVAILABLE = True
except ImportError as _ie:
    logging.getLogger(__name__).warning("grid.intelligence not available: %s", _ie)
    INTELLIGENCE_AVAILABLE = False
    AIBrain = None  # type: ignore[assignment,misc]
    KnowledgeGraphBridge = None  # type: ignore[assignment,misc]

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Session state ─────────────────────────────────────────────────────────────


@dataclass
class IntelligenceSession:
    """Runtime state for the intelligence server."""

    brain: Any | None = None  # AIBrain instance when available
    bridge: Any | None = None  # KnowledgeGraphBridge instance
    active_sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    query_count: int = 0
    last_query: str | None = None


_state = IntelligenceSession()

# ── MCP Server ────────────────────────────────────────────────────────────────
server = Server("grid-intelligence")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _ensure_brain() -> tuple[Any | None, str | None]:
    """Return (brain, error).  Lazily initialises the AIBrain singleton."""
    if not INTELLIGENCE_AVAILABLE:
        return None, "grid.intelligence module not available"
    if _state.brain is None:
        try:
            _state.brain = AIBrain(auth_context={"source": "mcp"})
        except Exception as exc:
            return None, f"Failed to initialise AIBrain: {exc}"
    return _state.brain, None


def _ensure_bridge() -> tuple[Any | None, str | None]:
    """Return (bridge, error).  Lazily initialises the KnowledgeGraphBridge."""
    if not INTELLIGENCE_AVAILABLE:
        return None, "grid.intelligence module not available"
    if _state.bridge is None:
        try:
            _state.bridge = KnowledgeGraphBridge()
        except Exception as exc:
            return None, f"Failed to initialise KnowledgeGraphBridge: {exc}"
    return _state.bridge, None


# ── Resources ─────────────────────────────────────────────────────────────────


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="intelligence://status",
            name="Intelligence Server Status",
            description="Current status of AIBrain and KnowledgeGraphBridge",
            mimeType="application/json",
        ),
        Resource(
            uri="intelligence://sessions",
            name="Active Brain Sessions",
            description="Currently active AIBrain sessions",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri) -> str:  # type: ignore[misc]
    try:
        if uri == "intelligence://status":
            status = {
                "intelligence_available": INTELLIGENCE_AVAILABLE,
                "brain_initialised": _state.brain is not None,
                "bridge_initialised": _state.bridge is not None,
                "active_sessions": len(_state.active_sessions),
                "query_count": _state.query_count,
                "last_query": _state.last_query,
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(status, indent=2)

        elif uri == "intelligence://sessions":
            return json.dumps(
                {
                    "sessions": list(_state.active_sessions.values()),
                    "count": len(_state.active_sessions),
                },
                indent=2,
            )

        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except Exception as exc:
        logger.error("Error reading resource %s: %s", uri, exc)
        return f"Error: {exc}"


# ── Tool definitions ──────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="intelligence_status",
            description="Check the status of the GRID Intelligence server — module availability, initialisation state, and session count.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="intelligence_create_session",
            description="Create a new AIBrain session with an optional user context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Unique session identifier",
                    },
                    "user_context": {
                        "type": "object",
                        "description": "Optional context key-value pairs for this session",
                        "default": {},
                    },
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="intelligence_get_session",
            description="Retrieve metadata for an existing AIBrain session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="intelligence_list_sessions",
            description="List all active AIBrain sessions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="intelligence_delete_session",
            description="Delete an existing AIBrain session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"},
                },
                "required": ["session_id"],
            },
        ),
        Tool(
            name="intelligence_graph_query",
            description="Query the knowledge graph for entities and their relationships.  Returns matching nodes with confidence scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language or keyword query to match against graph entities",
                    },
                    "entity_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional filter: entity type names to include (e.g. ENTITY, EVENT, PATTERN)",
                        "default": [],
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="intelligence_add_navigation_data",
            description="Feed spatial / navigation data into the KnowledgeGraphBridge to enrich the graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 3,
                        },
                        "description": "List of [x, y] or [x, y, z] coordinate points",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata attached to this navigation record",
                        "default": {},
                    },
                },
                "required": ["coordinates"],
            },
        ),
        Tool(
            name="intelligence_enhance_navigation",
            description="Use the KnowledgeGraphBridge to generate path suggestions and spatial insights for a given set of coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "description": "List of [x, y] 2-D waypoints to enhance",
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context passed to the bridge",
                        "default": {},
                    },
                },
                "required": ["coordinates"],
            },
        ),
    ]


# ── Tool dispatch ─────────────────────────────────────────────────────────────


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    try:
        handlers: dict[str, Any] = {
            "intelligence_status": _handle_status,
            "intelligence_create_session": _handle_create_session,
            "intelligence_get_session": _handle_get_session,
            "intelligence_list_sessions": _handle_list_sessions,
            "intelligence_delete_session": _handle_delete_session,
            "intelligence_graph_query": _handle_graph_query,
            "intelligence_add_navigation_data": _handle_add_navigation_data,
            "intelligence_enhance_navigation": _handle_enhance_navigation,
        }
        handler = handlers.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(arguments)
    except Exception as exc:
        logger.error("Error in tool %s: %s", name, exc)
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {exc}")])


# ── Tool handlers ─────────────────────────────────────────────────────────────


async def _handle_status(_args: dict[str, Any]) -> CallToolResult:
    status = {
        "server": "grid-intelligence",
        "intelligence_available": INTELLIGENCE_AVAILABLE,
        "brain_initialised": _state.brain is not None,
        "bridge_initialised": _state.bridge is not None,
        "active_sessions": len(_state.active_sessions),
        "query_count": _state.query_count,
        "timestamp": datetime.now().isoformat(),
    }
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(status, indent=2))])


async def _handle_create_session(args: dict[str, Any]) -> CallToolResult:
    session_id: str = args.get("session_id", "")
    user_context: dict[str, Any] = args.get("user_context", {})

    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )

    if session_id in _state.active_sessions:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Session '{session_id}' already exists")],
            isError=True,
        )

    brain, err = _ensure_brain()
    if err:
        # Graceful degradation: record session locally even without a live brain.
        logger.warning("AIBrain unavailable (%s) — session stored locally only", err)
        _state.active_sessions[session_id] = {
            "session_id": session_id,
            "user_context": user_context,
            "created_at": datetime.now().isoformat(),
            "brain_backed": False,
        }
        return CallToolResult(
            content=[TextContent(type="text", text=f"Session '{session_id}' created (local only — brain: {err})")]
        )

    try:
        brain_session = brain.create_session(user_context=user_context)
        _state.active_sessions[session_id] = {
            "session_id": session_id,
            "brain_session_id": getattr(brain_session, "session_id", session_id),
            "user_context": user_context,
            "created_at": datetime.now().isoformat(),
            "brain_backed": True,
        }
        return CallToolResult(content=[TextContent(type="text", text=f"Session '{session_id}' created successfully")])
    except Exception as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Failed to create session: {exc}")],
            isError=True,
        )


async def _handle_get_session(args: dict[str, Any]) -> CallToolResult:
    session_id: str = args.get("session_id", "")
    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )
    info = _state.active_sessions.get(session_id)
    if info is None:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Session '{session_id}' not found")],
            isError=True,
        )
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(info, indent=2))])


async def _handle_list_sessions(_args: dict[str, Any]) -> CallToolResult:
    payload = {
        "sessions": list(_state.active_sessions.values()),
        "count": len(_state.active_sessions),
    }
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, indent=2))])


async def _handle_delete_session(args: dict[str, Any]) -> CallToolResult:
    session_id: str = args.get("session_id", "")
    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )
    if session_id not in _state.active_sessions:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Session '{session_id}' not found")],
            isError=True,
        )
    del _state.active_sessions[session_id]
    return CallToolResult(content=[TextContent(type="text", text=f"Session '{session_id}' deleted successfully")])


async def _handle_graph_query(args: dict[str, Any]) -> CallToolResult:
    query: str = args.get("query", "")
    entity_types: list[str] = args.get("entity_types", [])
    max_results: int = args.get("max_results", 10)

    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: query is required")],
            isError=True,
        )

    _state.query_count += 1
    _state.last_query = query

    bridge, err = _ensure_bridge()
    if err:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Knowledge graph unavailable: {err}")],
            isError=True,
        )

    try:
        # KnowledgeGraphBridge wraps a networkx DiGraph; perform a substring
        # match against node attributes for now.  A full embedding-based search
        # can be wired in later when the bridge exposes it.
        graph = bridge.graph  # type: ignore[attr-defined]
        results: list[dict[str, Any]] = []

        query_lower = query.lower()
        for node_id, attrs in graph.nodes(data=True):
            node_type = str(attrs.get("type", "")).lower()
            if entity_types and node_type not in [t.lower() for t in entity_types]:
                continue
            # Simple relevance: count query tokens appearing in node attributes.
            text_repr = json.dumps(attrs, default=str).lower()
            score = sum(1 for token in query_lower.split() if token in text_repr)
            if score > 0:
                results.append(
                    {
                        "id": node_id,
                        "type": attrs.get("type", "unknown"),
                        "attributes": {k: v for k, v in attrs.items() if k != "type"},
                        "relevance_score": score,
                    }
                )

        results.sort(key=lambda r: r["relevance_score"], reverse=True)
        results = results[:max_results]

        payload = {
            "query": query,
            "total_nodes_searched": graph.number_of_nodes(),
            "results_returned": len(results),
            "results": results,
        }
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, indent=2))])

    except Exception as exc:
        logger.error("Graph query failed: %s", exc)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Graph query failed: {exc}")],
            isError=True,
        )


async def _handle_add_navigation_data(args: dict[str, Any]) -> CallToolResult:
    coordinates: list[list[float]] = args.get("coordinates", [])
    metadata: dict[str, Any] = args.get("metadata", {})

    if not coordinates:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: coordinates are required")],
            isError=True,
        )

    bridge, err = _ensure_bridge()
    if err:
        return CallToolResult(
            content=[TextContent(type="text", text=f"KnowledgeGraphBridge unavailable: {err}")],
            isError=True,
        )

    try:
        nav_data = {"coordinates": coordinates, "metadata": metadata, "timestamp": datetime.now().isoformat()}
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: bridge.add_navigation_data(nav_data),  # type: ignore[attr-defined]
        )
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Navigation data added: {len(coordinates)} coordinate points",
                )
            ]
        )
    except Exception as exc:
        logger.error("add_navigation_data failed: %s", exc)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Failed to add navigation data: {exc}")],
            isError=True,
        )


async def _handle_enhance_navigation(args: dict[str, Any]) -> CallToolResult:
    raw_coords: list[list[float]] = args.get("coordinates", [])
    context: dict[str, Any] = args.get("context", {})

    if not raw_coords:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: coordinates are required")],
            isError=True,
        )

    bridge, err = _ensure_bridge()
    if err:
        return CallToolResult(
            content=[TextContent(type="text", text=f"KnowledgeGraphBridge unavailable: {err}")],
            isError=True,
        )

    try:
        # KnowledgeGraphBridge.enhance_navigation expects list[tuple[float, float]]
        coords_as_tuples = [tuple(c[:2]) for c in raw_coords]  # type: ignore[misc]
        result: NavigationEnhancement = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: bridge.enhance_navigation(coords_as_tuples, context),  # type: ignore[attr-defined]
        )

        payload = {
            "path_suggestions": result.path_suggestions,
            "spatial_insights": result.spatial_insights,
            "confidence_scores": result.confidence_scores,
            "reasoning_explanation": result.reasoning_explanation,
        }
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, indent=2))])

    except Exception as exc:
        logger.error("enhance_navigation failed: %s", exc)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Navigation enhancement failed: {exc}")],
            isError=True,
        )


# ── Main entry point ──────────────────────────────────────────────────────────


async def main() -> None:
    """Main server entry point."""
    logger.info("Starting GRID Intelligence MCP Server...")

    if not INTELLIGENCE_AVAILABLE:
        logger.warning(
            "grid.intelligence module not available — session tools will work, "
            "graph/navigation tools will return errors until the module is installed."
        )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
