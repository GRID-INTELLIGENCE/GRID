"""
GRID Intelligence MCP Server

Exposes GRID's core intelligence layer as MCP tools:
- Pattern detection (hybrid, agentic species, detector listing)
- Knowledge graph (query, neighborhood, store entity/relationship)
- Action tracing (query, lineage, record)
- Coherence analysis
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

import site

site.main()

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool
except ImportError as e:
    raise ImportError("MCP library not found. Install: uv add 'mcp[cli]>=1.25.0'") from e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


class _SlidingWindowRateLimiter:
    """Sliding-window rate limiter (thread-safe)."""

    def __init__(self, max_calls: int = 60, window_seconds: float = 60.0) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        with self._lock:
            # Evict expired entries
            while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.max_calls:
                return False
            self._timestamps.append(now)
            return True


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_essential_state(args: dict[str, Any]) -> Any:
    """Validate and construct an EssentialState from tool arguments.

    Returns the EssentialState instance or raises ValueError.
    """
    from grid.essence.core_state import EssentialState

    pattern_signature = args.get("pattern_signature")
    if not pattern_signature or not isinstance(pattern_signature, str):
        raise ValueError("pattern_signature is required and must be a non-empty string")

    quantum_state = args.get("quantum_state")
    if not isinstance(quantum_state, dict):
        raise ValueError("quantum_state is required and must be an object")

    context_depth = args.get("context_depth", 1.0)
    coherence_factor = args.get("coherence_factor", 0.5)

    if not isinstance(context_depth, (int, float)):
        raise ValueError("context_depth must be a number")
    if not isinstance(coherence_factor, (int, float)):
        raise ValueError("coherence_factor must be a number")

    return EssentialState(
        pattern_signature=pattern_signature,
        quantum_state=quantum_state,
        context_depth=float(context_depth),
        coherence_factor=float(coherence_factor),
    )


def _get_subgraph_from_store(
    store: Any,
    entity_id: str,
    depth: int = 2,
) -> dict[str, Any]:
    """BFS traversal to extract a subgraph neighborhood from a PersistentJSONKnowledgeStore."""
    if not store._initialized:
        store.connect()

    visited_entities: set[str] = set()
    visited_rels: set[str] = set()
    queue: list[tuple[str, int]] = [(entity_id, 0)]
    entities_out: list[dict[str, Any]] = []
    rels_out: list[dict[str, Any]] = []

    while queue:
        current_id, current_depth = queue.pop(0)
        if current_id in visited_entities:
            continue
        visited_entities.add(current_id)

        entity = store.entities.get(current_id)
        if entity:
            entities_out.append(entity.to_dict())

        if current_depth >= depth:
            continue

        # Find adjacent relationships
        for rid, rel in store.relationships.items():
            if rid in visited_rels:
                continue
            neighbor_id: str | None = None
            if rel.from_entity_id == current_id:
                neighbor_id = rel.to_entity_id
            elif rel.to_entity_id == current_id:
                neighbor_id = rel.from_entity_id
            if neighbor_id is not None:
                visited_rels.add(rid)
                rels_out.append(rel.to_dict())
                if neighbor_id not in visited_entities:
                    queue.append((neighbor_id, current_depth + 1))

    return {
        "center_entity_id": entity_id,
        "depth": depth,
        "entities": entities_out,
        "relationships": rels_out,
        "entity_count": len(entities_out),
        "relationship_count": len(rels_out),
    }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_ESSENTIAL_STATE_SCHEMA: dict[str, Any] = {
    "pattern_signature": {"type": "string", "description": "Pattern signature string to analyze"},
    "quantum_state": {"type": "object", "description": "Quantum state dictionary for pattern context"},
    "context_depth": {"type": "number", "description": "Context depth (default 1.0)", "default": 1.0},
    "coherence_factor": {"type": "number", "description": "Coherence factor 0-1 (default 0.5)", "default": 0.5},
}

TOOLS: list[Tool] = [
    # --- Pattern Detection ---
    Tool(
        name="detect_patterns",
        description="Run hybrid pattern detection (statistical + syntactic + neural) on an EssentialState input",
        inputSchema={
            "type": "object",
            "properties": {
                **_ESSENTIAL_STATE_SCHEMA,
                "weights": {
                    "type": "object",
                    "description": "Optional weights for combining methods (keys: statistical, syntactic, neural)",
                },
            },
            "required": ["pattern_signature", "quantum_state"],
        },
    ),
    Tool(
        name="detect_agentic_species",
        description="Detect embedded agentic species (neural networks, information flow, network structures) in behavioral signatures",
        inputSchema={
            "type": "object",
            "properties": _ESSENTIAL_STATE_SCHEMA,
            "required": ["pattern_signature", "quantum_state"],
        },
    ),
    Tool(
        name="list_pattern_detectors",
        description="List available pattern detector types and their capabilities",
        inputSchema={"type": "object", "properties": {}},
    ),
    # --- Knowledge Graph ---
    Tool(
        name="query_knowledge",
        description="Search knowledge graph entities by query string, with optional entity type and limit filters",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "entity_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by entity types (Agent, Skill, Event, Context, Artifact, Task, Decision)",
                },
                "limit": {"type": "integer", "description": "Max results (default 50)", "default": 50},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_entity_neighborhood",
        description="Get the subgraph neighborhood around an entity via BFS traversal",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Center entity ID"},
                "depth": {"type": "integer", "description": "BFS depth (default 2, max 5)", "default": 2},
            },
            "required": ["entity_id"],
        },
    ),
    Tool(
        name="store_entity",
        description="Create or update an entity in the knowledge graph",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "Unique entity identifier"},
                "entity_type": {
                    "type": "string",
                    "description": "Entity type (Agent, Skill, Event, Context, Artifact, Task, Decision)",
                },
                "properties": {"type": "object", "description": "Entity properties"},
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional labels",
                },
            },
            "required": ["entity_id", "entity_type", "properties"],
        },
    ),
    Tool(
        name="store_relationship",
        description="Create a relationship between two entities in the knowledge graph",
        inputSchema={
            "type": "object",
            "properties": {
                "from_entity_id": {"type": "string", "description": "Source entity ID"},
                "to_entity_id": {"type": "string", "description": "Target entity ID"},
                "relationship_type": {
                    "type": "string",
                    "description": "Relationship type (EXECUTED_BY, DEPENDS_ON, GENERATED, OCCURRED_AT, HAS_PARENT, REFERENCES)",
                },
                "properties": {"type": "object", "description": "Relationship properties", "default": {}},
            },
            "required": ["from_entity_id", "to_entity_id", "relationship_type"],
        },
    ),
    # --- Tracing ---
    Tool(
        name="query_traces",
        description="Search action traces by action type, origin, user, time range, or tags",
        inputSchema={
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "description": "Filter by action type"},
                "origin": {"type": "string", "description": "Filter by trace origin"},
                "user_id": {"type": "string", "description": "Filter by user ID"},
                "start_time": {"type": "string", "description": "ISO datetime lower bound"},
                "end_time": {"type": "string", "description": "ISO datetime upper bound"},
                "limit": {"type": "integer", "description": "Max results (default 50)", "default": 50},
            },
        },
    ),
    Tool(
        name="get_trace_lineage",
        description="Follow the parent chain from a trace ID to build a provenance tree",
        inputSchema={
            "type": "object",
            "properties": {
                "trace_id": {"type": "string", "description": "Trace ID to trace lineage from"},
            },
            "required": ["trace_id"],
        },
    ),
    Tool(
        name="record_trace",
        description="Record a new action trace with optional AI safety metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "description": "Type of action"},
                "action_name": {"type": "string", "description": "Human-readable action name"},
                "origin": {
                    "type": "string",
                    "description": "Trace origin (default: api_request)",
                    "default": "api_request",
                },
                "metadata": {"type": "object", "description": "Additional metadata"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                "input_data": {"type": "object", "description": "Input data snapshot"},
                "model_used": {"type": "string", "description": "AI model name (safety field)"},
                "safety_score": {"type": "number", "description": "Safety assessment score 0-1"},
                "risk_level": {"type": "string", "description": "Risk level: low/medium/high"},
            },
            "required": ["action_type", "action_name"],
        },
    ),
    # --- Analysis ---
    Tool(
        name="analyze_coherence",
        description="Run coherence analysis on a pattern signature using extended pattern recognition",
        inputSchema={
            "type": "object",
            "properties": _ESSENTIAL_STATE_SCHEMA,
            "required": ["pattern_signature", "quantum_state"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class GridIntelligenceMCPServer:
    """MCP server exposing GRID's intelligence layer."""

    def __init__(
        self,
        pattern_detector_factory: Callable[[], Any] | None = None,
        agentic_detector_factory: Callable[[], Any] | None = None,
        extended_recognition_factory: Callable[[], Any] | None = None,
        knowledge_store_factory: Callable[[], Any] | None = None,
        trace_manager_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.server = Server("grid-intelligence")
        self._rate_limiter = _SlidingWindowRateLimiter(max_calls=60, window_seconds=60.0)

        # Factory storage
        self._pattern_detector_factory = pattern_detector_factory
        self._agentic_detector_factory = agentic_detector_factory
        self._extended_recognition_factory = extended_recognition_factory
        self._knowledge_store_factory = knowledge_store_factory
        self._trace_manager_factory = trace_manager_factory

        # Lazy-init instances
        self._pattern_detector: Any = None
        self._agentic_detector: Any = None
        self._extended_recognition: Any = None
        self._knowledge_store: Any = None
        self._trace_manager: Any = None

        self._init_lock = threading.Lock()
        self._register_handlers()

    # -- Lazy init helpers (double-check lock) --

    def _ensure_patterns(self) -> Any:
        if self._pattern_detector is None:
            with self._init_lock:
                if self._pattern_detector is None:
                    if self._pattern_detector_factory:
                        self._pattern_detector = self._pattern_detector_factory()
                    else:
                        from grid.patterns import HybridPatternDetector

                        self._pattern_detector = HybridPatternDetector()
        return self._pattern_detector

    def _ensure_agentic(self) -> Any:
        if self._agentic_detector is None:
            with self._init_lock:
                if self._agentic_detector is None:
                    if self._agentic_detector_factory:
                        self._agentic_detector = self._agentic_detector_factory()
                    else:
                        from grid.patterns import EmbeddedAgenticDetector

                        self._agentic_detector = EmbeddedAgenticDetector()
        return self._agentic_detector

    def _ensure_extended(self) -> Any:
        if self._extended_recognition is None:
            with self._init_lock:
                if self._extended_recognition is None:
                    if self._extended_recognition_factory:
                        self._extended_recognition = self._extended_recognition_factory()
                    else:
                        from grid.patterns import ExtendedPatternRecognition

                        self._extended_recognition = ExtendedPatternRecognition()
        return self._extended_recognition

    def _ensure_knowledge(self) -> Any:
        if self._knowledge_store is None:
            with self._init_lock:
                if self._knowledge_store is None:
                    if self._knowledge_store_factory:
                        self._knowledge_store = self._knowledge_store_factory()
                    else:
                        from grid.knowledge import PersistentJSONKnowledgeStore

                        storage_path = os.environ.get("GRID_KG_STORAGE_PATH", str(Path.home() / ".grid" / "knowledge"))
                        self._knowledge_store = PersistentJSONKnowledgeStore(
                            storage_path=Path(storage_path) / "knowledge_graph.json"
                        )
                        self._knowledge_store.connect()
        return self._knowledge_store

    def _ensure_tracing(self) -> Any:
        if self._trace_manager is None:
            with self._init_lock:
                if self._trace_manager is None:
                    if self._trace_manager_factory:
                        self._trace_manager = self._trace_manager_factory()
                    else:
                        from grid.tracing import TraceManager
                        from grid.tracing.trace_store import TraceStore

                        storage_path = os.environ.get(
                            "GRID_TRACE_STORAGE_PATH", str(Path.home() / ".grid" / "traces")
                        )
                        store = TraceStore(storage_path=Path(storage_path))
                        self._trace_manager = TraceManager(store=store)
        return self._trace_manager

    # -- Handler registration --

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(tools=TOOLS)

        self.server._handle_list_tools = lambda req=None: list_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            return await self._dispatch_tool(name, arguments)

        async def _call_tool_handler(name: str, arguments: dict[str, Any]) -> CallToolResult:
            return await self._dispatch_tool(name, arguments)

        self.server._call_tool_handler = _call_tool_handler

    async def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Central dispatch with rate limiting."""
        if not self._rate_limiter.allow():
            return CallToolResult(
                content=[TextContent(text="Rate limit exceeded. Try again shortly.", type="text")],
                isError=True,
            )

        try:
            match name:
                # Pattern Detection
                case "detect_patterns":
                    return await self._handle_detect_patterns(arguments)
                case "detect_agentic_species":
                    return await self._handle_detect_agentic_species(arguments)
                case "list_pattern_detectors":
                    return await self._handle_list_pattern_detectors(arguments)
                # Knowledge Graph
                case "query_knowledge":
                    return await self._handle_query_knowledge(arguments)
                case "get_entity_neighborhood":
                    return await self._handle_get_entity_neighborhood(arguments)
                case "store_entity":
                    return await self._handle_store_entity(arguments)
                case "store_relationship":
                    return await self._handle_store_relationship(arguments)
                # Tracing
                case "query_traces":
                    return await self._handle_query_traces(arguments)
                case "get_trace_lineage":
                    return await self._handle_get_trace_lineage(arguments)
                case "record_trace":
                    return await self._handle_record_trace(arguments)
                # Analysis
                case "analyze_coherence":
                    return await self._handle_analyze_coherence(arguments)
                case _:
                    return CallToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}", type="text")],
                        isError=True,
                    )
        except Exception as e:
            logger.error("Error in tool %s: %s", name, e)
            return CallToolResult(
                content=[TextContent(text=f"Error: {e}", type="text")],
                isError=True,
            )

    # -- Pattern Detection handlers --

    async def _handle_detect_patterns(self, args: dict[str, Any]) -> CallToolResult:
        state = _validate_essential_state(args)
        weights = args.get("weights")
        detector = self._ensure_patterns()
        result = await detector.detect(state, weights=weights)

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps(asdict(result), indent=2, default=str),
                    type="text",
                )
            ]
        )

    async def _handle_detect_agentic_species(self, args: dict[str, Any]) -> CallToolResult:
        state = _validate_essential_state(args)
        detector = self._ensure_agentic()
        result = await detector.detect_embedded_agentic(state)

        return CallToolResult(
            content=[TextContent(text=json.dumps(result, indent=2, default=str), type="text")]
        )

    async def _handle_list_pattern_detectors(self, args: dict[str, Any]) -> CallToolResult:
        detectors = [
            {
                "name": "StatisticalPatternDetector",
                "category": "statistical",
                "description": "Trend and distribution analysis using statistical methods",
            },
            {
                "name": "SyntacticPatternDetector",
                "category": "syntactic",
                "description": "Structural pattern recognition via syntactic analysis",
            },
            {
                "name": "NeuralPatternDetector",
                "category": "neural",
                "description": "Deep pattern learning with neural approaches",
            },
            {
                "name": "HybridPatternDetector",
                "category": "hybrid",
                "description": "Combines statistical, syntactic, and neural detection into a unified result",
            },
            {
                "name": "EmbeddedAgenticDetector",
                "category": "agentic",
                "description": "Detects embedded agentic species — neural networks, information flow, network structures",
            },
            {
                "name": "ExtendedPatternRecognition",
                "category": "extended",
                "description": "Extended pattern recognition with embedded agentic detection and coherence analysis",
            },
        ]
        return CallToolResult(
            content=[TextContent(text=json.dumps({"detectors": detectors}, indent=2), type="text")]
        )

    # -- Knowledge Graph handlers --

    async def _handle_query_knowledge(self, args: dict[str, Any]) -> CallToolResult:
        from grid.knowledge.graph_schema import EntityType

        query = args.get("query", "")
        if not query:
            raise ValueError("query is required")

        raw_types = args.get("entity_types")
        entity_types: list[EntityType] | None = None
        if raw_types:
            entity_types = [EntityType(t) for t in raw_types]

        limit = args.get("limit", 50)
        store = self._ensure_knowledge()

        from grid.knowledge.graph_store import SearchContext

        context = SearchContext(query=query, entity_types=entity_types, limit=limit)
        entities = store.semantic_search(query, context)

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps(
                        {"query": query, "count": len(entities), "entities": [e.to_dict() for e in entities]},
                        indent=2,
                        default=str,
                    ),
                    type="text",
                )
            ]
        )

    async def _handle_get_entity_neighborhood(self, args: dict[str, Any]) -> CallToolResult:
        entity_id = args.get("entity_id", "")
        if not entity_id:
            raise ValueError("entity_id is required")

        depth = min(args.get("depth", 2), 5)
        store = self._ensure_knowledge()
        subgraph = _get_subgraph_from_store(store, entity_id, depth)

        return CallToolResult(
            content=[TextContent(text=json.dumps(subgraph, indent=2, default=str), type="text")]
        )

    async def _handle_store_entity(self, args: dict[str, Any]) -> CallToolResult:
        from grid.knowledge.graph_schema import EntityType
        from grid.knowledge.graph_store import Entity

        entity_id = args.get("entity_id", "")
        entity_type_str = args.get("entity_type", "")
        properties = args.get("properties", {})
        labels = args.get("labels")

        if not entity_id:
            raise ValueError("entity_id is required")
        if not entity_type_str:
            raise ValueError("entity_type is required")

        entity_type = EntityType(entity_type_str)
        now = datetime.now()
        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            properties=properties,
            created_at=now,
            updated_at=now,
            labels=set(labels) if labels else None,
        )

        store = self._ensure_knowledge()
        result_id = store.store_entity(entity)

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps({"stored": True, "entity_id": str(result_id)}, indent=2),
                    type="text",
                )
            ]
        )

    async def _handle_store_relationship(self, args: dict[str, Any]) -> CallToolResult:
        from grid.knowledge.graph_schema import RelationType
        from grid.knowledge.graph_store import EntityId

        from_id = args.get("from_entity_id", "")
        to_id = args.get("to_entity_id", "")
        rel_type_str = args.get("relationship_type", "")
        properties = args.get("properties", {})

        if not from_id or not to_id:
            raise ValueError("from_entity_id and to_entity_id are required")
        if not rel_type_str:
            raise ValueError("relationship_type is required")

        rel_type = RelationType(rel_type_str)
        store = self._ensure_knowledge()
        result_id = store.create_relationship(
            from_id=EntityId(from_id),
            to_id=EntityId(to_id),
            relationship_type=rel_type,
            properties=properties,
        )

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps({"stored": True, "relationship_id": str(result_id)}, indent=2),
                    type="text",
                )
            ]
        )

    # -- Tracing handlers --

    async def _handle_query_traces(self, args: dict[str, Any]) -> CallToolResult:
        manager = self._ensure_tracing()

        if not manager.store:
            return CallToolResult(
                content=[TextContent(text="No trace store configured", type="text")],
                isError=True,
            )

        action_type = args.get("action_type")
        origin_str = args.get("origin")
        user_id = args.get("user_id")
        limit = args.get("limit", 50)

        start_time = None
        end_time = None
        if args.get("start_time"):
            start_time = datetime.fromisoformat(args["start_time"])
        if args.get("end_time"):
            end_time = datetime.fromisoformat(args["end_time"])

        origin = None
        if origin_str:
            from grid.tracing.action_trace import TraceOrigin

            origin = TraceOrigin(origin_str)

        traces = manager.store.query_traces(
            action_type=action_type,
            origin=origin,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps(
                        {
                            "count": len(traces),
                            "traces": [t.model_dump(mode="json") for t in traces],
                        },
                        indent=2,
                        default=str,
                    ),
                    type="text",
                )
            ]
        )

    async def _handle_get_trace_lineage(self, args: dict[str, Any]) -> CallToolResult:
        trace_id = args.get("trace_id", "")
        if not trace_id:
            raise ValueError("trace_id is required")

        manager = self._ensure_tracing()
        chain = manager.get_trace_chain(trace_id)

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps(
                        {
                            "trace_id": trace_id,
                            "lineage_depth": len(chain),
                            "chain": [t.model_dump(mode="json") for t in chain],
                        },
                        indent=2,
                        default=str,
                    ),
                    type="text",
                )
            ]
        )

    async def _handle_record_trace(self, args: dict[str, Any]) -> CallToolResult:
        from grid.tracing.action_trace import TraceOrigin

        action_type = args.get("action_type", "")
        action_name = args.get("action_name", "")
        if not action_type or not action_name:
            raise ValueError("action_type and action_name are required")

        origin_str = args.get("origin", "api_request")
        origin = TraceOrigin(origin_str)
        metadata = args.get("metadata", {})
        tags = set(args.get("tags", []))
        input_data = args.get("input_data", {})

        # AI safety fields
        model_used = args.get("model_used")
        safety_score = args.get("safety_score")
        risk_level = args.get("risk_level")

        manager = self._ensure_tracing()
        trace = manager.create_trace(
            action_type=action_type,
            action_name=action_name,
            origin=origin,
            metadata=metadata,
            tags=tags,
            skip_frames=1,
        )

        if input_data:
            trace.input_data = input_data
        if model_used:
            trace.model_used = model_used
        if safety_score is not None:
            trace.safety_score = safety_score
        if risk_level:
            trace.risk_level = risk_level

        # Complete and persist
        trace.complete(success=True)
        if manager.store:
            manager.store.save_trace(trace)

        return CallToolResult(
            content=[
                TextContent(
                    text=json.dumps(
                        {
                            "recorded": True,
                            "trace_id": trace.trace_id,
                            "action_type": trace.action_type,
                            "action_name": trace.action_name,
                        },
                        indent=2,
                    ),
                    type="text",
                )
            ]
        )

    # -- Analysis handlers --

    async def _handle_analyze_coherence(self, args: dict[str, Any]) -> CallToolResult:
        state = _validate_essential_state(args)
        extended = self._ensure_extended()
        analysis = await extended.get_embedded_analysis(state)

        # Add coherence metrics from the state itself
        analysis["coherence_factor"] = state.coherence_factor
        analysis["context_depth"] = state.context_depth
        analysis["pattern_signature"] = state.pattern_signature

        return CallToolResult(
            content=[TextContent(text=json.dumps(analysis, indent=2, default=str), type="text")]
        )

    # -- Server lifecycle --

    async def run(self, read_stream: Any, write_stream: Any, options: Any) -> None:
        await self.server.run(read_stream, write_stream, options)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

server: GridIntelligenceMCPServer | None = None


def get_server() -> GridIntelligenceMCPServer:
    global server
    if server is None:
        server = GridIntelligenceMCPServer()
    return server


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await get_server().run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="grid-intelligence",
                server_version="1.0.0",
                capabilities={
                    "tools": {t.name: {"description": t.description} for t in TOOLS},
                    "resources": {},
                },
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
