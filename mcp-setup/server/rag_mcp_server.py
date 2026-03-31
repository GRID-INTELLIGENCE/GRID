#!/usr/bin/env python3
"""
Unified GRID RAG MCP Server

Merges grid_rag_mcp_server (7 tools) and enhanced_rag_server (6 tools)
into a single server with 11 tools, 3 resources, and 3 prompts.

Server name: grid-rag

Runnable as:
  python mcp-setup/server/rag_mcp_server.py
  python -m grid.mcp.rag_mcp_server
"""

import asyncio
import json
import logging
import re
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
grid_root = Path(__file__).parent.parent.parent
try:
    from grid.security.path_manager import SecurePathManager

    _path_manager = SecurePathManager(base_dir=grid_root)
    _path_manager.add_path(grid_root / "src", validate=True)
except ImportError:
    sys.path.insert(0, str(grid_root / "src"))

import site

site.main()

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        GetPromptResult,
        Prompt,
        PromptArgument,
        PromptMessage,
        Resource,
        TextContent,
        Tool,
    )
except ImportError:
    sys.stderr.write("MCP library not found. Please install: pip install mcp\n")
    sys.exit(1)

try:
    from tools.rag import RAGConfig, RAGEngine
    from tools.rag.config import ModelMode
    from tools.rag.conversational_rag import ConversationalRAGEngine, create_conversational_rag_engine
    from tools.rag.on_demand_engine import OnDemandRAGEngine
except ImportError:
    sys.stderr.write("GRID RAG tools not found. Please ensure GRID is properly installed.\n")
    sys.exit(1)

# ── Input sanitization ────────────────────────────────────────────────────────
try:
    from grid.security.input_sanitizer import InputSanitizer, SanitizationConfig

    _query_sanitizer = InputSanitizer(
        SanitizationConfig(
            encode_html=False,
            max_text_length=10000,
        )
    )
except ImportError:
    _query_sanitizer = None

# ── Prompt injection patterns ─────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|above)\s+instructions", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"<\|(?:im_start|system|endofprompt)\|>", re.I),
    re.compile(r"###\s*(?:system|instruction|override)", re.I),
    re.compile(r"(?:IMPORTANT|CRITICAL|URGENT):\s*(?:ignore|forget|disregard)", re.I),
]

# ── Allowed workspace roots for path containment ──────────────────────────────
_ALLOWED_ROOTS = [
    grid_root.resolve(),
    Path.home().resolve() / "CascadeProjects",
    Path.home().resolve() / "canopy",
    Path.home().resolve() / "roots",
]

_SENSITIVE_PATTERNS = [".ssh", ".gnupg", ".env", "credentials", "secrets"]

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _check_path(path_str: str) -> tuple[bool, str]:
    """Validate path is inside allowed workspace roots and not sensitive."""
    path_resolved = Path(path_str).resolve()
    if not any(str(path_resolved).startswith(str(r)) for r in _ALLOWED_ROOTS):
        return False, "Denied: path outside workspace"
    if any(s in str(path_resolved).lower() for s in _SENSITIVE_PATTERNS):
        return False, "Denied: sensitive directory"
    return True, ""


def _sanitize_query(query: str) -> tuple[str | None, str | None]:
    """Sanitize query text. Returns (sanitized, error)."""
    if _query_sanitizer is None:
        return query, None
    scan = _query_sanitizer.sanitize_text_full(query)
    if scan.severity.value in ("critical", "high"):
        logger.warning("RAG query blocked: severity=%s threats=%s", scan.severity, scan.threats_detected)
        return None, "Query rejected: suspicious content detected"
    return str(scan.sanitized_content), None


def _filter_sources(sources: list[dict]) -> list[dict]:
    """Filter retrieved RAG sources for prompt injection patterns."""
    filtered = []
    for s in sources:
        content = s.get("content", "") or s.get("document", "")
        if any(p.search(content) for p in _INJECTION_PATTERNS):
            logger.warning("Filtered suspicious RAG source: %s", s.get("metadata", {}).get("path", "?"))
            continue
        filtered.append(s)
    return filtered


def format_sources(sources: list[dict[str, Any]]) -> str:
    """Format sources for chat display."""
    if not sources:
        return ""
    formatted = "\n**Sources:**\n"
    for i, source in enumerate(sources[:5], 1):
        metadata = source.get("metadata", {})
        path = metadata.get("path", "Unknown")
        distance = source.get("distance", 0)
        formatted += f"  {i}. `{path}` (relevance: {1 - distance:.2f})\n"
    if len(sources) > 5:
        formatted += f"  ... and {len(sources) - 5} more sources\n"
    return formatted


def format_stats(stats: dict[str, Any]) -> str:
    """Format statistics for chat display."""
    return f"""
**Knowledge Base Stats:**
- Documents: {stats.get("document_count", 0)}
- Collection: {stats.get("collection_name", "N/A")}
- Embedding Model: {stats.get("embedding_model", "N/A")}
- LLM Model: {stats.get("llm_model", "N/A")}
- Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


# ── Session state ─────────────────────────────────────────────────────────────


@dataclass
class RAGSession:
    """Unified session state for both persistent and conversational RAG."""

    engine: RAGEngine | None = None
    conversational_engine: ConversationalRAGEngine | None = None
    on_demand_engine: OnDemandRAGEngine | None = None
    config: RAGConfig | None = None
    indexed_paths: list[str] = field(default_factory=list)
    last_query: str | None = None
    query_count: int = 0
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    _init_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


session = RAGSession()

# ── MCP Server ────────────────────────────────────────────────────────────────
server = Server("grid-rag")


async def ensure_rag_engine() -> RAGEngine | None:
    """Ensure the base RAG engine is initialized with timeout protection."""
    if session.engine is None:
        try:
            config = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, lambda: session.config or RAGConfig.from_env()),
                timeout=30.0,
            )
            config.ensure_local_only()
            session.config = config

            session.engine = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, lambda: RAGEngine(config=config)),
                timeout=60.0,
            )
            logger.info("RAG engine initialized successfully")
        except TimeoutError as err:
            logger.error("RAG engine initialization timed out")
            raise RuntimeError(
                "RAG engine initialization timed out. Please check Ollama connection and model availability."
            ) from err
        except Exception as e:
            logger.error("Failed to initialize RAG engine: %s", e)
            raise
    return session.engine


async def ensure_conversational_engine() -> ConversationalRAGEngine | None:
    """Ensure the conversational RAG engine is initialized."""
    if session.conversational_engine is None:
        with session._init_lock:
            if session.conversational_engine is None:
                config = session.config or RAGConfig.from_env()
                config.ensure_local_only()
                session.config = config
                session.conversational_engine = create_conversational_rag_engine(config=config)
    return session.conversational_engine


# ── Resources ─────────────────────────────────────────────────────────────────


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="rag://stats",
            name="RAG Knowledge Base Statistics",
            description="Current statistics about the indexed knowledge base",
            mimeType="application/json",
        ),
        Resource(
            uri="rag://config",
            name="RAG Configuration",
            description="Current RAG system configuration",
            mimeType="application/json",
        ),
        Resource(
            uri="rag://indexed-paths",
            name="Indexed Paths",
            description="List of currently indexed directory paths",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri) -> str:  # type: ignore
    try:
        if uri == "rag://stats":
            engine = await ensure_rag_engine()
            if engine is None:
                return "Error: RAG engine not initialized"
            return json.dumps(engine.get_stats(), indent=2)

        elif uri == "rag://config":
            config = session.config or RAGConfig.from_env()
            config_dict = {
                "embedding_model": config.embedding_model,
                "embedding_provider": config.embedding_provider,
                "llm_model_local": config.llm_model_local,
                "vector_store_provider": config.vector_store_provider,
                "collection_name": config.collection_name,
                "chunk_size": config.chunk_size,
                "top_k": config.top_k,
                "cache_enabled": config.cache_enabled,
            }
            return json.dumps(config_dict, indent=2)

        elif uri == "rag://indexed-paths":
            return json.dumps(session.indexed_paths, indent=2)

        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except Exception as e:
        logger.error("Error reading resource %s: %s", uri, e)
        return f"Error: {str(e)}"


# ── Tool definitions ──────────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="rag_index",
            description="Index documents from a directory for RAG search",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to index (default: current directory)",
                        "default": ".",
                    },
                    "rebuild": {
                        "type": "boolean",
                        "description": "Rebuild entire index (default: incremental update)",
                        "default": False,
                    },
                    "curated": {
                        "type": "boolean",
                        "description": "Use curated high-quality file set only",
                        "default": False,
                    },
                    "quiet": {"type": "boolean", "description": "Minimize output messages", "default": False},
                },
                "required": [],
            },
        ),
        Tool(
            name="rag_query",
            description="Search the knowledge base and get AI-generated answers",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question or search query"},
                    "top_k": {
                        "type": "integer",
                        "description": "Number of sources to retrieve (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "LLM creativity level (0.0-1.0, default: 0.3)",
                        "default": 0.3,
                        "minimum": 0.0,
                        "maximum": 2.0,
                    },
                    "include_sources": {
                        "type": "boolean",
                        "description": "Include source references in answer",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="rag_add_document",
            description="Add a single document directly to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Document text content"},
                    "source": {
                        "type": "string",
                        "description": "Source file path or identifier",
                        "default": "manual_entry",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata for the document",
                        "default": {},
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="rag_on_demand",
            description="Query-time RAG: build temporary index and answer in one step",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question or search query"},
                    "docs_path": {
                        "type": "string",
                        "description": "Documentation directory (default: docs)",
                        "default": "docs",
                    },
                    "include_codebase": {
                        "type": "boolean",
                        "description": "Also search codebase files",
                        "default": False,
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum files to consider (default: 100)",
                        "default": 100,
                        "minimum": 10,
                        "maximum": 1000,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="rag_search",
            description="Simple semantic search without AI generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum similarity threshold (0.0-1.0)",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="rag_stats",
            description="Get knowledge base statistics and status",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="rag_configure",
            description="Hotload RAG config at runtime. No server restart needed. All fields optional - only specified fields override defaults/env. Changing embedding_model, vector_store_path, or llm_model_local will reinitialize the engine on next call.",
            inputSchema={
                "type": "object",
                "properties": {
                    "embedding_model": {
                        "type": "string",
                        "description": "Embedding model name (e.g. nomic-embed-text-v2-moe:latest)",
                    },
                    "embedding_provider": {
                        "type": "string",
                        "description": "Embedding provider (ollama, huggingface, simple)",
                    },
                    "embedding_mode": {"type": "string", "description": "Embedding mode (local, auto, cloud)"},
                    "llm_model_local": {"type": "string", "description": "Local LLM model (e.g. ministral-3:latest)"},
                    "llm_mode": {"type": "string", "description": "LLM mode (local, auto, cloud, external)"},
                    "vector_store_provider": {
                        "type": "string",
                        "description": "Vector store provider (chromadb, in_memory)",
                    },
                    "vector_store_path": {"type": "string", "description": "Vector store directory path"},
                    "collection_name": {"type": "string", "description": "ChromaDB collection name"},
                    "chunk_size": {"type": "integer", "description": "Document chunk size"},
                    "chunk_overlap": {"type": "integer", "description": "Chunk overlap size"},
                    "top_k": {"type": "integer", "description": "Default retrieval top_k"},
                    "similarity_threshold": {"type": "number", "description": "Similarity threshold (0.0-1.0)"},
                    "max_context_length": {"type": "integer", "description": "Max context length for retrieval"},
                    "use_hybrid": {"type": "boolean", "description": "Enable hybrid search"},
                    "use_reranker": {"type": "boolean", "description": "Enable reranking"},
                    "reranker_type": {"type": "string", "description": "Reranker type (cross_encoder, ollama)"},
                    "cross_encoder_model": {"type": "string", "description": "Cross-encoder model name"},
                    "reranker_top_k": {"type": "integer", "description": "Max candidates to rerank"},
                    "cache_enabled": {"type": "boolean", "description": "Enable query cache"},
                    "cache_size": {"type": "integer", "description": "Cache size"},
                    "cache_ttl": {"type": "integer", "description": "Cache TTL in seconds"},
                    "ollama_base_url": {"type": "string", "description": "Ollama base URL"},
                    "conversation_enabled": {"type": "boolean", "description": "Enable conversational memory"},
                    "multi_hop_enabled": {"type": "boolean", "description": "Enable multi-hop reasoning"},
                    "use_intelligent_rag": {"type": "boolean", "description": "Enable intelligent reasoning pipeline"},
                    "reset": {"type": "boolean", "description": "Reset to env defaults (ignores all other fields)"},
                },
                "required": [],
            },
        ),
        Tool(
            name="rag_create_session",
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
            name="rag_get_session",
            description="Get information about a session",
            inputSchema={
                "type": "object",
                "properties": {"session_id": {"type": "string", "description": "Session identifier"}},
                "required": ["session_id"],
            },
        ),
        Tool(
            name="rag_delete_session",
            description="Delete a conversation session",
            inputSchema={
                "type": "object",
                "properties": {"session_id": {"type": "string", "description": "Session identifier"}},
                "required": ["session_id"],
            },
        ),
        Tool(
            name="rag_conversational_query",
            description="Query the RAG knowledge base with conversation memory and multi-hop reasoning",
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
    ]


# ── Tool dispatch ─────────────────────────────────────────────────────────────


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    try:
        handlers = {
            "rag_index": _handle_index,
            "rag_query": _handle_query,
            "rag_add_document": _handle_add_document,
            "rag_on_demand": _handle_on_demand,
            "rag_search": _handle_search,
            "rag_stats": _handle_stats,
            "rag_configure": _handle_configure,
            "rag_create_session": _handle_create_session,
            "rag_get_session": _handle_get_session,
            "rag_delete_session": _handle_delete_session,
            "rag_conversational_query": _handle_conversational_query,
        }
        handler = handlers.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(arguments)
    except Exception as e:
        logger.error("Error in tool %s: %s", name, e)
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])


# ── Tool handlers ─────────────────────────────────────────────────────────────


async def _handle_index(args: dict[str, Any]) -> CallToolResult:
    path = args.get("path", ".")
    rebuild = args.get("rebuild", False)
    curated = args.get("curated", False)
    quiet = args.get("quiet", False)

    ok, msg = _check_path(path)
    if not ok:
        return CallToolResult(content=[TextContent(type="text", text=msg)])

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        if not quiet:
            logger.info("Indexing: %s", path)

        files = None
        if curated:
            try:
                from tools.rag.cli import _build_curated_files

                files = _build_curated_files(path)
                if not quiet:
                    logger.info("Curated mode: %d files", len(files))
            except ImportError:
                if not quiet:
                    logger.info("Curated mode not available, using full directory scan")

        engine.index(repo_path=path, rebuild=rebuild, files=files, quiet=quiet)

        if path not in session.indexed_paths:
            session.indexed_paths.append(path)

        stats = engine.get_stats()

        return CallToolResult(content=[TextContent(type="text", text=f"Indexing Complete!\n{format_stats(stats)}")])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Indexing Failed: {str(e)}")])


async def _handle_query(args: dict[str, Any]) -> CallToolResult:
    query = args["query"]
    top_k = args.get("top_k", 5)
    temperature = args.get("temperature", 0.3)
    include_sources = args.get("include_sources", True)

    sanitized, error = _sanitize_query(query)
    if error:
        return CallToolResult(content=[TextContent(type="text", text=error)])
    query = sanitized

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        session.last_query = query
        session.query_count += 1

        result = await engine.query(query_text=query, top_k=top_k, temperature=temperature, include_sources=True)

        answer = result.get("answer", "No answer generated")
        sources = _filter_sources(result.get("sources", []))

        response = f"Answer:\n{answer}"

        if include_sources and sources:
            response += format_sources(sources)

        response += f"\n\n---\n*Query #{session.query_count} | Temperature: {temperature} | Sources: {len(sources)}*"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Query Failed: {str(e)}")])


async def _handle_add_document(args: dict[str, Any]) -> CallToolResult:
    text = args["text"]
    source = args.get("source", "manual_entry")
    metadata = args.get("metadata", {})

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        doc_metadata = {"source": source, "added_at": datetime.now().isoformat(), "type": "manual_entry", **metadata}

        engine.add_documents(documents=[text], metadatas=[doc_metadata])

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Document Added:\n- Source: `{source}`\n- Length: {len(text)} characters\n- ID: manual_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )
            ]
        )

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Add Failed: {str(e)}")])


async def _handle_on_demand(args: dict[str, Any]) -> CallToolResult:
    query = args["query"]
    docs_path = args.get("docs_path", "docs")
    include_codebase = args.get("include_codebase", False)
    max_files = args.get("max_files", 100)

    sanitized, error = _sanitize_query(query)
    if error:
        return CallToolResult(content=[TextContent(type="text", text=error)])
    query = sanitized

    ok, msg = _check_path(docs_path)
    if not ok:
        return CallToolResult(content=[TextContent(type="text", text=msg)])

    try:
        config = session.config or RAGConfig.from_env()
        config.ensure_local_only()

        if session.on_demand_engine is None:
            session.on_demand_engine = OnDemandRAGEngine(config=config, docs_root=docs_path, repo_root=".")

        result = session.on_demand_engine.query(
            query_text=query, max_files=max_files, include_codebase=include_codebase, temperature=0.3
        )

        answer = result.answer
        routing = result.routing
        selected_files = getattr(result, "selected_files", [])

        response = f"On-Demand Answer:\n{answer}"

        if selected_files:
            response += f"\n\nFiles Analyzed: {len(selected_files)}"
            for file_info in selected_files[:5]:
                response += f"\n  - `{file_info.get('path', 'Unknown')}` (score: {file_info.get('score', 0):.3f})"

        response += f"\n\nRouting: {routing}"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"On-Demand Failed: {str(e)}")])


async def _handle_search(args: dict[str, Any]) -> CallToolResult:
    query = args["query"]
    top_k = args.get("top_k", 10)
    threshold = args.get("threshold", 0.0)

    sanitized, error = _sanitize_query(query)
    if error:
        return CallToolResult(content=[TextContent(type="text", text=error)])
    query = sanitized

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])
        if engine.embedding_provider is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: Embedding provider not initialized")])
        if engine.vector_store is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: Vector store not initialized")])

        query_embedding = await engine.embedding_provider.async_embed(query)
        if not isinstance(query_embedding, list):
            if hasattr(query_embedding, "tolist"):
                query_embedding = query_embedding.tolist()
            else:
                query_embedding = list(query_embedding)

        results = engine.vector_store.query(query_embedding=query_embedding, n_results=top_k)

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        distances = results.get("distances", [])

        if not documents:
            return CallToolResult(content=[TextContent(type="text", text="No Results Found")])

        response = f"Search Results: {len(documents)} matches\n\n"

        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances, strict=False), 1):
            if distance <= (1.0 - threshold):
                path = metadata.get("path", "Unknown")
                similarity = 1.0 - distance
                response += f"{i}. `{path}` (similarity: {similarity:.3f})\n"
                response += f"   {doc[:200]}{'...' if len(doc) > 200 else ''}\n\n"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Search Failed: {str(e)}")])


async def _handle_stats(_args: dict[str, Any]) -> CallToolResult:
    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])
        stats = engine.get_stats()

        stats["session_queries"] = session.query_count
        stats["session_last_query"] = session.last_query or "None"
        stats["indexed_paths"] = session.indexed_paths

        return CallToolResult(content=[TextContent(type="text", text=format_stats(stats))])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Stats Failed: {str(e)}")])


async def _handle_configure(args: dict[str, Any]) -> CallToolResult:
    try:
        if args.get("reset"):
            session.config = None
            session.engine = None
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="RAG config reset. Engine will reinitialize with env defaults on next call.",
                    )
                ]
            )

        overrides = {k: v for k, v in args.items() if k != "reset" and v is not None}

        if not overrides:
            current = session.config or RAGConfig.from_env()
            config_summary = {
                "embedding_model": current.embedding_model,
                "embedding_provider": current.embedding_provider,
                "llm_model_local": current.llm_model_local,
                "llm_mode": current.llm_mode,
                "vector_store_provider": current.vector_store_provider,
                "vector_store_path": current.vector_store_path,
                "collection_name": current.collection_name,
                "chunk_size": current.chunk_size,
                "top_k": current.top_k,
                "use_hybrid": current.use_hybrid,
                "use_reranker": current.use_reranker,
                "cache_enabled": current.cache_enabled,
                "ollama_base_url": current.ollama_base_url,
            }
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Current RAG Config:\n```json\n{json.dumps(config_summary, indent=2)}\n```\n\nPass fields to override. Use `reset: true` to revert to env defaults.",
                    )
                ]
            )

        engine_reset_fields = {
            "embedding_model",
            "embedding_provider",
            "embedding_mode",
            "llm_model_local",
            "llm_mode",
            "vector_store_provider",
            "vector_store_path",
            "collection_name",
            "ollama_base_url",
        }
        needs_engine_reset = bool(set(overrides.keys()) & engine_reset_fields)

        new_config = RAGConfig.from_dict(overrides)
        new_config.ensure_local_only()

        session.config = new_config

        if needs_engine_reset:
            session.engine = None
            status_msg = "Engine will reinitialize on next call."
        else:
            status_msg = "Engine running with updated settings."

        config_summary = {
            "embedding_model": new_config.embedding_model,
            "embedding_provider": new_config.embedding_provider,
            "llm_model_local": new_config.llm_model_local,
            "llm_mode": new_config.llm_mode,
            "vector_store_provider": new_config.vector_store_provider,
            "vector_store_path": new_config.vector_store_path,
            "collection_name": new_config.collection_name,
            "chunk_size": new_config.chunk_size,
            "top_k": new_config.top_k,
            "use_hybrid": new_config.use_hybrid,
            "use_reranker": new_config.use_reranker,
            "cache_enabled": new_config.cache_enabled,
            "ollama_base_url": new_config.ollama_base_url,
        }

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"RAG config updated ({len(overrides)} fields).\n{status_msg}\n\n```json\n{json.dumps(config_summary, indent=2)}\n```",
                )
            ]
        )

    except ValueError as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Config rejected: {str(e)}")])
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Configure failed: {str(e)}")])


# ── Session management handlers ───────────────────────────────────────────────


async def _handle_create_session(args: dict[str, Any]) -> CallToolResult:
    session_id = args.get("session_id")
    metadata = args.get("metadata", {})

    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )

    try:
        engine = await ensure_conversational_engine()
        if engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Conversational engine not initialized")]
            )

        engine.create_session(session_id, metadata)

        session.sessions[session_id] = {
            "session_id": session_id,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
        }

        return CallToolResult(content=[TextContent(type="text", text=f"Session '{session_id}' created successfully")])

    except Exception as e:
        logger.error("Failed to create session: %s", e)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Failed to create session: {str(e)}")],
            isError=True,
        )


async def _handle_get_session(args: dict[str, Any]) -> CallToolResult:
    session_id = args.get("session_id")

    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )

    try:
        engine = await ensure_conversational_engine()
        if engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Conversational engine not initialized")]
            )

        session_info = engine.get_session_info(session_id)

        if not session_info:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Session '{session_id}' not found")],
                isError=True,
            )

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(session_info, indent=2))])

    except Exception as e:
        logger.error("Failed to get session: %s", e)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Failed to get session: {str(e)}")],
            isError=True,
        )


async def _handle_delete_session(args: dict[str, Any]) -> CallToolResult:
    session_id = args.get("session_id")

    if not session_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: session_id is required")],
            isError=True,
        )

    try:
        engine = await ensure_conversational_engine()
        if engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Conversational engine not initialized")]
            )

        success = engine.delete_session(session_id)

        if success:
            if session_id in session.sessions:
                del session.sessions[session_id]

            return CallToolResult(
                content=[TextContent(type="text", text=f"Session '{session_id}' deleted successfully")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Session '{session_id}' not found")],
                isError=True,
            )

    except Exception as e:
        logger.error("Failed to delete session: %s", e)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Failed to delete session: {str(e)}")],
            isError=True,
        )


async def _handle_conversational_query(args: dict[str, Any]) -> CallToolResult:
    query = args.get("query")
    session_id = args.get("session_id")
    enable_multi_hop = args.get("enable_multi_hop", False)
    temperature = args.get("temperature", 0.7)

    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: query is required")],
            isError=True,
        )

    sanitized, error = _sanitize_query(query)
    if error:
        return CallToolResult(content=[TextContent(type="text", text=error)])
    query = sanitized

    try:
        engine = await ensure_conversational_engine()
        if engine is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Conversational engine not initialized")]
            )

        result = await engine.query(
            query_text=query,
            session_id=session_id,
            enable_multi_hop=enable_multi_hop,
            temperature=temperature,
        )

        response_data = {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "conversation_metadata": result.get("conversation_metadata", {}),
            "multi_hop_used": result.get("multi_hop_used", False),
            "fallback_used": result.get("fallback_used", False),
            "latency_ms": result.get("latency_ms", 0),
        }

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(response_data, indent=2))])

    except Exception as e:
        logger.error("Conversational query failed: %s", e)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Conversational query failed: {str(e)}")],
            isError=True,
        )


# ── Prompts ───────────────────────────────────────────────────────────────────


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="rag_help",
            description="Get help with RAG operations",
            arguments=[PromptArgument(name="help", description="Help topic", required=False)],
        ),
        Prompt(
            name="rag_quick_index",
            description="Quick index current directory",
            arguments=[
                PromptArgument(name="path", description="Path to index (default: current directory)", required=False)
            ],
        ),
        Prompt(
            name="rag_research_query",
            description="Deep research query with extended context",
            arguments=[
                PromptArgument(name="topic", description="Research topic", required=True),
                PromptArgument(
                    name="depth", description="Research depth (basic|detailed|comprehensive)", required=False
                ),
            ],
        ),
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    if name == "rag_help":
        return GetPromptResult(
            description="GRID RAG Help",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""GRID RAG Operations Guide:

Indexing:
- rag_index - Index documents from directory
- rag_add_document - Add single document manually

Querying:
- rag_query - Ask questions with AI answers
- rag_conversational_query - Session-aware queries with memory
- rag_search - Simple semantic search
- rag_on_demand - Temporary index + query

Session Management:
- rag_create_session - Create a conversation session
- rag_get_session - Get session information
- rag_delete_session - Delete a session

Management:
- rag_stats - View knowledge base statistics
- rag_configure - Hotload config at runtime
- Resources: rag://stats, rag://config, rag://indexed-paths

Quick Start:
1. Index your docs: rag_index with path="docs"
2. Ask questions: rag_query with your query
3. Check status: rag_stats""",
                    ),
                )
            ],
        )

    elif name == "rag_quick_index":
        path = arguments.get("path", ".") if arguments else "."
        return GetPromptResult(
            description="Quick Index Current Directory",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Quick Index Setup:

I'll index the directory: `{path}`

This will:
- Scan for relevant documents
- Create embeddings for semantic search
- Enable AI-powered question answering

Options:
- Curated mode - High-quality files only (faster, better results)
- Rebuild - Fresh index (slower, ensures latest content)
- Incremental - Update existing index (faster)

Ready to start indexing?""",
                    ),
                )
            ],
        )

    elif name == "rag_research_query":
        topic = arguments["topic"] if arguments else "unknown"
        depth = arguments.get("depth", "detailed") if arguments else "detailed"

        depth_settings = {
            "basic": {"top_k": 5, "temperature": 0.3},
            "detailed": {"top_k": 10, "temperature": 0.4},
            "comprehensive": {"top_k": 15, "temperature": 0.5},
        }

        settings = depth_settings.get(depth, depth_settings["detailed"])

        return GetPromptResult(
            description=f"Research Query: {topic}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Research Query Setup:

Topic: {topic}
Depth: {depth}
Sources: {settings["top_k"]} documents
Creativity: {settings["temperature"]}

This will perform comprehensive research using:
- Semantic search across knowledge base
- AI synthesis of findings
- Source attribution and relevance scoring

Expected Output:
- Detailed analysis of {topic}
- Key findings and insights
- Source references with relevance scores
- Contextual relationships and patterns

Ready to begin research?""",
                    ),
                )
            ],
        )

    else:
        raise ValueError(f"Unknown prompt: {name}")


# ── Main entry point ──────────────────────────────────────────────────────────


async def main():
    """Main server entry point."""
    logger.info("Starting GRID RAG MCP Server...")

    try:
        config = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, RAGConfig.from_env),
            timeout=30.0,
        )
        session.config = config
        logger.info("RAG config loaded: %s", config.embedding_model)
    except TimeoutError:
        logger.warning("RAG config loading timed out, using defaults")
        session.config = RAGConfig()
    except Exception as e:
        logger.warning("Could not load RAG config: %s", e)
        session.config = RAGConfig()

    try:
        from tools.rag.utils import check_rag_system_health

        config = session.config
        health = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: check_rag_system_health(
                    embedding_model=config.embedding_model,
                    llm_model=config.llm_model_local,
                    base_url=config.ollama_base_url,
                ),
            ),
            timeout=15.0,
        )
        status = health.get("overall_status", "unknown")
        if status == "unhealthy":
            logger.error(
                "RAG startup validation FAILED: no required models available. "
                "Embedding='%s', LLM='%s'. Server will start but tools will fail. "
                "Run: ollama pull %s && ollama pull %s",
                config.embedding_model,
                config.llm_model_local,
                config.embedding_model,
                config.llm_model_local,
            )
        elif status == "degraded":
            logger.warning(
                "RAG startup validation: DEGRADED - some models missing. Health: %s",
                health,
            )
        else:
            logger.info("RAG startup validation: all models available")
    except TimeoutError:
        logger.warning("RAG startup model validation timed out - skipping (Ollama may be slow)")
    except Exception as e:
        logger.warning("RAG startup model validation failed: %s", e)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
