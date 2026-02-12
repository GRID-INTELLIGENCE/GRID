import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

# Also add the global Python site-packages to path
import site

site.main()

try:
    from mcp.server import Server
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
    print("MCP library not found. Please install: pip install mcp")
    sys.exit(1)

try:
    from tools.rag import RAGConfig, RAGEngine
    from tools.rag.on_demand_engine import OnDemandRAGEngine
except ImportError:
    print("GRID RAG tools not found. Please ensure GRID is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGSession:
    """Manages RAG session state."""

    engine: RAGEngine | None = None
    on_demand_engine: OnDemandRAGEngine | None = None
    config: RAGConfig | None = None
    last_query: str | None = None
    query_count: int = 0
    indexed_paths: list[str] | None = None

    def __post_init__(self):
        if self.indexed_paths is None:
            self.indexed_paths = []


# Global session state
session = RAGSession()

# Initialize MCP server
server = Server("grid-rag")


def format_sources(sources: list[dict[str, Any]]) -> str:
    """Format sources for chat display."""
    if not sources:
        return ""

    formatted = "\n📚 **Sources:**\n"
    for i, source in enumerate(sources[:5], 1):  # Limit to top 5
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
📊 **Knowledge Base Stats:**
- Documents: {stats.get("document_count", 0)}
- Collection: {stats.get("collection_name", "N/A")}
- Embedding Model: {stats.get("embedding_model", "N/A")}
- LLM Model: {stats.get("llm_model", "N/A")}
- Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


async def ensure_rag_engine() -> RAGEngine | None:
    """Ensure RAG engine is initialized with timeout protection."""
    if session.engine is None:
        try:
            # Initialize config with timeout
            config = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, RAGConfig.from_env),
                timeout=30.0,  # 30 second timeout
            )
            config.ensure_local_only()

            # Initialize engine with timeout
            session.engine = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, lambda: RAGEngine(config=config)),
                timeout=60.0,  # 60 second timeout for engine initialization
            )
            logger.info("RAG engine initialized successfully")
        except TimeoutError as err:
            logger.error("RAG engine initialization timed out")
            raise RuntimeError(
                "RAG engine initialization timed out. Please check Ollama connection and model availability."
            ) from err
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            raise
    return session.engine


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available RAG resources."""
    return [
        Resource(
            uri="rag://stats",  # type: ignore
            name="RAG Knowledge Base Statistics",
            description="Current statistics about the indexed knowledge base",
            mimeType="application/json",
        ),
        Resource(
            uri="rag://config",  # type: ignore
            name="RAG Configuration",
            description="Current RAG system configuration",
            mimeType="application/json",
        ),
        Resource(
            uri="rag://indexed-paths",  # type: ignore
            name="Indexed Paths",
            description="List of currently indexed directory paths",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri) -> str:  # type: ignore
    """Read a RAG resource."""
    try:
        if uri == "rag://stats":
            engine = await ensure_rag_engine()
            if engine is None:
                return "Error: RAG engine not initialized"
            stats = engine.get_stats()
            return json.dumps(stats, indent=2)

        elif uri == "rag://config":
            config = session.config or RAGConfig.from_env()
            config_dict = {
                "embedding_model": config.embedding_model,
                "embedding_provider": config.embedding_provider,
                "llm_model": config.llm_model_local,
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
        logger.error(f"Error reading resource {uri}: {e}")
        return f"Error: {str(e)}"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available RAG tools."""
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Execute a RAG tool."""
    try:
        if name == "rag_index":
            return await handle_index(arguments)
        elif name == "rag_query":
            return await handle_query(arguments)
        elif name == "rag_add_document":
            return await handle_add_document(arguments)
        elif name == "rag_on_demand":
            return await handle_on_demand(arguments)
        elif name == "rag_search":
            return await handle_search(arguments)
        elif name == "rag_stats":
            return await handle_stats(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Error:** {str(e)}")])


async def handle_index(args: dict[str, Any]) -> CallToolResult:
    """Handle document indexing."""
    path = args.get("path", ".")
    rebuild = args.get("rebuild", False)
    curated = args.get("curated", False)
    quiet = args.get("quiet", False)

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        if not quiet:
            print(f"🔍 **Indexing:** {path}")

        # Determine files to index
        files = None
        if curated:
            # Use curated file set
            try:
                from tools.rag.cli import _build_curated_files

                files = _build_curated_files(path)
                if not quiet:
                    print(f"📋 **Curated mode:** {len(files)} files")
            except ImportError:
                if not quiet:
                    print("⚠️ Curated mode not available, using full directory scan")

        # Perform indexing
        engine.index(repo_path=path, rebuild=rebuild, files=files, quiet=quiet)

        # Track indexed path
        if session.indexed_paths is not None and path not in session.indexed_paths:
            session.indexed_paths.append(path)

        # Get updated stats
        stats = engine.get_stats()

        return CallToolResult(
            content=[TextContent(type="text", text=f"✅ **Indexing Complete!**\n{format_stats(stats)}")]
        )

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Indexing Failed:** {str(e)}")])


async def handle_query(args: dict[str, Any]) -> CallToolResult:
    """Handle RAG queries with AI generation."""
    query = args["query"]
    top_k = args.get("top_k", 5)
    temperature = args.get("temperature", 0.3)
    include_sources = args.get("include_sources", True)

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        # Update session
        session.last_query = query
        session.query_count += 1

        # Generate response
        result = await engine.query(query_text=query, top_k=top_k, temperature=temperature, include_sources=True)

        # Format response
        answer = result.get("answer", "No answer generated")
        sources = result.get("sources", [])

        response = f"🤖 **Answer:**\n{answer}"

        if include_sources and sources:
            response += format_sources(sources)

        # Add query metadata
        response += f"\n\n---\n*Query #{session.query_count} • Temperature: {temperature} • Sources: {len(sources)}*"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Query Failed:** {str(e)}")])


async def handle_add_document(args: dict[str, Any]) -> CallToolResult:
    """Handle adding individual documents."""
    text = args["text"]
    source = args.get("source", "manual_entry")
    metadata = args.get("metadata", {})

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])

        # Prepare metadata
        doc_metadata = {"source": source, "added_at": datetime.now().isoformat(), "type": "manual_entry", **metadata}

        # Add document
        engine.add_documents(documents=[text], metadatas=[doc_metadata])

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"✅ **Document Added:**\n- Source: `{source}`\n- Length: {len(text)} characters\n- ID: manual_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )
            ]
        )

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Add Failed:** {str(e)}")])


async def handle_on_demand(args: dict[str, Any]) -> CallToolResult:
    """Handle on-demand RAG queries."""
    query = args["query"]
    docs_path = args.get("docs_path", "docs")
    include_codebase = args.get("include_codebase", False)
    max_files = args.get("max_files", 100)

    try:
        # Initialize on-demand engine
        config = RAGConfig.from_env()
        config.ensure_local_only()

        if session.on_demand_engine is None:
            session.on_demand_engine = OnDemandRAGEngine(config=config, docs_root=docs_path, repo_root=".")

        # Process query
        result = session.on_demand_engine.query(
            query_text=query, max_files=max_files, include_codebase=include_codebase, temperature=0.3
        )

        # Format response
        answer = result.answer
        routing = result.routing
        selected_files = getattr(result, "selected_files", [])

        response = f"🔍 **On-Demand Answer:**\n{answer}"

        if selected_files:
            response += f"\n\n📁 **Files Analyzed:** {len(selected_files)}"
            for file_info in selected_files[:5]:
                response += f"\n  - `{file_info.get('path', 'Unknown')}` (score: {file_info.get('score', 0):.3f})"

        response += f"\n\n🎯 **Routing:** {routing}"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **On-Demand Failed:** {str(e)}")])


async def handle_search(args: dict[str, Any]) -> CallToolResult:
    """Handle simple semantic search."""
    query = args["query"]
    top_k = args.get("top_k", 10)
    threshold = args.get("threshold", 0.0)

    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])
        if engine.embedding_provider is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: Embedding provider not initialized")])
        if engine.vector_store is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: Vector store not initialized")])

        # Generate query embedding
        query_embedding = await engine.embedding_provider.async_embed(query)
        # Ensure it's a list of floats
        if not isinstance(query_embedding, list):
            if hasattr(query_embedding, "tolist"):
                query_embedding = query_embedding.tolist()
            else:
                query_embedding = list(query_embedding)

        # Search vector store
        results = engine.vector_store.query(query_embedding=query_embedding, n_results=top_k)

        # Format results
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        distances = results.get("distances", [])

        if not documents:
            return CallToolResult(content=[TextContent(type="text", text="🔍 **No Results Found")])

        response = f"🔍 **Search Results:** {len(documents)} matches\n\n"

        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances, strict=False), 1):
            if distance <= (1.0 - threshold):  # Convert distance to similarity
                path = metadata.get("path", "Unknown")
                similarity = 1.0 - distance
                response += f"**{i}.** `{path}` (similarity: {similarity:.3f})\n"
                response += f"   {doc[:200]}{'...' if len(doc) > 200 else ''}\n\n"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Search Failed:** {str(e)}")])


async def handle_stats(_args: dict[str, Any]) -> CallToolResult:
    """Handle statistics requests."""
    try:
        engine = await ensure_rag_engine()
        if engine is None:
            return CallToolResult(content=[TextContent(type="text", text="Error: RAG engine not initialized")])
        stats = engine.get_stats()

        # Add session info
        stats["session_queries"] = session.query_count
        stats["session_last_query"] = session.last_query or "None"
        stats["indexed_paths"] = session.indexed_paths

        return CallToolResult(content=[TextContent(type="text", text=format_stats(stats))])

    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"❌ **Stats Failed:** {str(e)}")])


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available RAG prompts."""
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
    """Get a specific RAG prompt."""
    if name == "rag_help":
        return GetPromptResult(
            description="GRID RAG Help",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""🔍 **GRID RAG Operations Guide:**

**Indexing:**
- `rag_index` - Index documents from directory
- `rag_add_document` - Add single document manually

**Querying:**
- `rag_query` - Ask questions with AI answers
- `rag_search` - Simple semantic search
- `rag_on_demand` - Temporary index + query

**Management:**
- `rag_stats` - View knowledge base statistics
- Resources: `rag://stats`, `rag://config`, `rag://indexed-paths`

**Quick Start:**
1. Index your docs: `rag_index` with path="docs"
2. Ask questions: `rag_query` with your query
3. Check status: `rag_stats`

Need more help? Ask me anything about RAG operations!""",
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
                        text=f"""🚀 **Quick Index Setup:**

I'll index the directory: `{path}`

This will:
- Scan for relevant documents
- Create embeddings for semantic search
- Enable AI-powered question answering

**Options:**
- **Curated mode** - High-quality files only (faster, better results)
- **Rebuild** - Fresh index (slower, ensures latest content)
- **Incremental** - Update existing index (faster)

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
                        text=f"""🔬 **Research Query Setup:**

**Topic:** {topic}
**Depth:** {depth}
**Sources:** {settings["top_k"]} documents
**Creativity:** {settings["temperature"]}

This will perform comprehensive research using:
- Semantic search across knowledge base
- AI synthesis of findings
- Source attribution and relevance scoring

**Expected Output:**
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


async def main():
    """Main server entry point."""
    logger.info("Starting GRID RAG MCP Server...")

    # Initialize session with timeout protection
    try:
        # Set a timeout for config loading
        config = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, RAGConfig.from_env),
            timeout=30.0,  # 30 second timeout
        )
        session.config = config
        logger.info(f"RAG config loaded: {config.embedding_model}")
    except TimeoutError:
        logger.warning("RAG config loading timed out, using defaults")
        session.config = RAGConfig()  # Use defaults
    except Exception as e:
        logger.warning(f"Could not load RAG config: {e}")
        session.config = RAGConfig()  # Use defaults

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
