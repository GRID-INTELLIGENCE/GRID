#!/usr/bin/env python3
"""
Interactive RAG Chat CLI for GRID.

Provides an interactive, streaming chat interface where local LLMs can
answer questions with full codebase context from the indexed RAG knowledge base.

Usage:
    python -m tools.rag.chat                    # Default model
    python -m tools.rag.chat --model ministral-3:3b
    python -m tools.rag.chat --model qwen2.5-coder:latest

Or via grid CLI:
    grid chat                                   # Interactive RAG chat
    grid chat --model qwen2.5-coder:latest     # With specific model
"""

from __future__ import annotations

import logging

# Set quiet mode BEFORE any other imports to suppress noisy logging
import os
import warnings

os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"
os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Aggressively suppress logging before any heavy imports occur
logging.basicConfig(level=logging.CRITICAL, force=True)
logging.getLogger().setLevel(logging.CRITICAL)
logging.disable(logging.WARNING)

_noisy_loggers = [
    "application",
    "application.mothership",
    "application.mothership.config",
    "application.mothership.main",
    "application.mothership.security",
    "application.mothership.security.api_sentinels",
    "chromadb",
    "httpx",
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
    "urllib3",
    "asyncio",
    "uvicorn",
    "fastapi",
]

for name in _noisy_loggers:
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.handlers = []

# Suppress warnings globally
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import argparse
import asyncio
import io
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass  # Already wrapped or not available

# Ensure grid root is in path (but don't import anything yet)
# _grid_root points to grid/src (where tools/rag lives)
_grid_root = Path(__file__).parent.parent.parent
if str(_grid_root) not in sys.path:
    sys.path.insert(0, str(_grid_root))

# Default RAG database path (relative to src/ where the index lives)
_default_rag_db = str(_grid_root / ".rag_db")

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from tools.rag.intelligence.query_understanding import QueryUnderstandingLayer
    from tools.rag.intelligence.retrieval_orchestrator import RetrievalOrchestrator
    from tools.rag.rag_engine import RAGEngine


# ANSI color codes for terminal styling
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"


def _supports_color() -> bool:
    """Check if terminal supports color output."""
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("FORCE_COLOR"):
        return True
    if sys.platform == "win32":
        return os.getenv("TERM") is not None or os.getenv("WT_SESSION") is not None
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOR = _supports_color()


def c(text: str, *styles: str) -> str:
    """Apply color styles to text if terminal supports it."""
    if not _USE_COLOR:
        return text
    return "".join(styles) + text + Colors.RESET


def _suppress_noisy_imports() -> None:
    """Suppress noisy loggers and warnings before importing heavy modules."""
    import logging
    import warnings

    # Environment variables
    os.environ["USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Configure root logger
    logging.basicConfig(level=logging.CRITICAL, force=True)
    logging.getLogger().setLevel(logging.CRITICAL)

    # Suppress specific noisy loggers
    noisy_loggers = [
        "httpx",
        "sentence_transformers",
        "application",
        "chromadb",
        "transformers",
        "huggingface_hub",
        "urllib3",
        "asyncio",
        "application.mothership",
        "application.mothership.security",
        "application.mothership.security.api_sentinels",
        "application.mothership.main",
        "uvicorn",
        "fastapi",
    ]
    for name in noisy_loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False

    # Suppress warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)


@dataclass
class ChatConfig:
    """Configuration for the chat session."""

    model: str = "ministral-3:3b"
    ollama_base_url: str = "http://localhost:11434"
    top_k: int = 8
    temperature: float = 0.7
    system_prompt: str | None = None
    show_sources: bool = True
    show_context: bool = False
    stream: bool = True
    use_intelligence: bool = True
    collection_name: str = "grid_knowledge_base"
    vector_store_path: str = ""  # Will be resolved to src/.rag_db

    def __post_init__(self) -> None:
        """Resolve vector store path if not explicitly set."""
        if not self.vector_store_path:
            self.vector_store_path = _default_rag_db


@dataclass
class RetrievedContext:
    """Context retrieved from RAG."""

    documents: list[str]
    metadatas: list[dict[str, Any]]
    distances: list[float]
    intent: str = "other"
    entities: list = field(default_factory=list)

    @property
    def context_text(self) -> str:
        """Format context for LLM prompt."""
        parts = []
        for i, (doc, meta) in enumerate(zip(self.documents, self.metadatas), 1):
            path = meta.get("path", "unknown")
            parts.append(f"[{i}] {path}\n{doc}")
        return "\n\n---\n\n".join(parts)

    @property
    def source_summary(self) -> str:
        """Get a brief summary of sources."""
        sources = []
        for i, (meta, dist) in enumerate(zip(self.metadatas, self.distances), 1):
            path = meta.get("path", "unknown")
            chunk = meta.get("chunk_index", "?")
            sources.append(f"  {i}. {path} (chunk {chunk}, dist: {dist:.3f})")
        return "\n".join(sources)


class RAGChatSession:
    """Interactive RAG chat session with streaming support."""

    def __init__(self, config: ChatConfig):
        self.config = config
        self.history: list[dict[str, str]] = []
        self._engine: RAGEngine | None = None
        self._intelligence: Any | None = None
        self._retrieval_orchestrator: Any | None = None

    async def initialize(self) -> None:
        """Initialize RAG engine and Ollama client."""
        # Capture stderr to suppress import noise
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        try:
            # Suppress noisy imports
            _suppress_noisy_imports()

            # Now import heavy modules
            from tools.rag.config import RAGConfig
            from tools.rag.intelligence.query_understanding import QueryUnderstandingLayer
            from tools.rag.intelligence.retrieval_orchestrator import RetrievalOrchestrator
            from tools.rag.rag_engine import RAGEngine

            # Initialize RAG engine
            rag_config = RAGConfig.from_env()
            rag_config.ensure_local_only()
            rag_config.collection_name = self.config.collection_name
            rag_config.vector_store_path = self.config.vector_store_path

            self._engine = RAGEngine(config=rag_config)

            # Initialize Intelligence Layer if enabled
            if self.config.use_intelligence:
                self._intelligence = QueryUnderstandingLayer()
                self._retrieval_orchestrator = RetrievalOrchestrator(engine=self._engine)

        finally:
            # Restore stderr
            sys.stderr = old_stderr

        # Check if index exists
        stats = self._engine.get_stats()
        doc_count = stats.get("document_count", 0)

        if doc_count == 0:
            print(c("[!] No index", Colors.YELLOW))
            print(c("    Run: python -m tools.rag.cli index .", Colors.DIM))
        else:
            print(c(f"[OK] {doc_count:,} chunks", Colors.GREEN), end=" | ", flush=True)

        # Verify Ollama model availability
        await self._check_model()
        print()  # Final newline

    async def _check_model(self) -> None:
        """Check if the specified model is available in Ollama."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.config.ollama_base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                model_base = self.config.model.split(":")[0]
                available = any(m.startswith(model_base) for m in models)

                if available:
                    print(c(f"Model: {self.config.model}", Colors.GREEN))
                else:
                    print(c(f"[!] Model '{self.config.model}' not found", Colors.YELLOW))
                    print(c(f"\n    Available: {', '.join(models[:5])}", Colors.DIM))
                    print(c(f"    Run: ollama pull {self.config.model}", Colors.DIM))
        except Exception as e:
            print(c(f"[!] Ollama: {e}", Colors.YELLOW))

    async def retrieve(self, query: str) -> RetrievedContext:
        """Retrieve relevant context from RAG."""
        if self._engine is None or self._engine.vector_store is None:
            return RetrievedContext(documents=[], metadatas=[], distances=[])

        # Phase 1 & 2: Intelligent Query Understanding & Multi-Stage Retrieval
        intent = "other"
        entities = []

        if self._intelligence and self.config.use_intelligence:
            understanding = self._intelligence.understand(query)
            intent = understanding.intent.value
            entities = [e.text for e in understanding.entities]

            if self._retrieval_orchestrator:
                # Multi-stage retrieval: Hybrid + Expansion + Reranking
                results = await self._retrieval_orchestrator.retrieve(understanding, top_k=self.config.top_k)
            else:
                # Fallback to simple vector search with expanded query
                search_query = understanding.expanded_queries[0] if understanding.expanded_queries else query
                query_embedding = await self._engine.embedding_provider.async_embed(search_query)
                results = self._engine.vector_store.query(query_embedding=query_embedding, n_results=self.config.top_k)
        else:
            # Baseline: Standard vector search
            query_embedding = await self._engine.embedding_provider.async_embed(query)
            results = self._engine.vector_store.query(query_embedding=query_embedding, n_results=self.config.top_k)

        return RetrievedContext(
            documents=results.get("documents", []),
            metadatas=results.get("metadatas", []),
            distances=results.get("distances", []),
            intent=intent,
            entities=entities,
        )

    def _build_system_prompt(self, context: RetrievedContext) -> str:
        """Build system prompt with RAG context."""
        base_prompt = (
            self.config.system_prompt
            or """You are a knowledgeable assistant for the GRID project codebase.
You have access to relevant code snippets and documentation from the project.
Answer questions accurately based on the provided context.
If the context doesn't contain enough information, say so honestly.
When referencing code, mention the file path."""
        )

        if context.documents:
            intent_context = f"\nDetected Intent: {context.intent}\n" if context.intent != "other" else ""
            entity_context = f"Relevant Entities: {', '.join(context.entities)}\n" if context.entities else ""

            return f"""{base_prompt}

{intent_context}{entity_context}
## Relevant Context from Codebase:

{context.context_text}

---
Use the above context to answer the user's question. Cite specific files when relevant."""

        return base_prompt

    async def stream_response(self, query: str, context: RetrievedContext) -> AsyncIterator[str]:
        """Stream response from Ollama with RAG context."""
        import httpx

        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 6 exchanges max)
        for msg in self.history[-12:]:
            messages.append(msg)

        messages.append({"role": "user", "content": query})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": self.config.temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.config.ollama_base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def chat(self, query: str) -> str:
        """Process a chat query with RAG context."""
        context = await self.retrieve(query)

        if self.config.use_intelligence and context.intent != "other":
            print(c(f"[Intent: {context.intent}]", Colors.DIM + Colors.MAGENTA))

        if self.config.show_sources and context.documents:
            print(c("\n[Sources]", Colors.CYAN))
            print(c(context.source_summary, Colors.DIM))
            print()

        if self.config.show_context and context.documents:
            print(c("\n[Full Context]", Colors.CYAN))
            print(c(context.context_text[:2000] + "...", Colors.DIM))
            print()

        print(c("[AI] ", Colors.GREEN), end="", flush=True)

        full_response = []
        start_time = time.time()

        try:
            async for chunk in self.stream_response(query, context):
                print(chunk, end="", flush=True)
                full_response.append(chunk)
        except Exception as e:
            print(c(f"\n\nError: {e}", Colors.RED))
            return ""

        elapsed = time.time() - start_time
        response_text = "".join(full_response)

        print()
        tokens_approx = len(response_text.split())
        print(c(f"\n[{elapsed:.1f}s, {tokens_approx} words]", Colors.DIM))

        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response_text})

        return response_text

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        print(c("[OK] Conversation history cleared", Colors.GREEN))


def print_banner(config: ChatConfig) -> None:
    """Print welcome banner."""
    banner = f"""
{c("+==============================================================+", Colors.CYAN)}
{c("|", Colors.CYAN)}  {c("GRID RAG Chat", Colors.BOLD + Colors.WHITE)}                                            {c("|", Colors.CYAN)}
{c("|", Colors.CYAN)}  {c(f"Model: {config.model:<50}", Colors.DIM)}  {c("|", Colors.CYAN)}
{c("+==============================================================+", Colors.CYAN)}

{c("Commands:", Colors.YELLOW)}
  {c("/help", Colors.GREEN)}     - Show this help
  {c("/clear", Colors.GREEN)}    - Clear conversation history
  {c("/sources", Colors.GREEN)}  - Toggle source display
  {c("/context", Colors.GREEN)}  - Toggle full context display (debug)
  {c("/model", Colors.GREEN)} X  - Switch to model X
  {c("/intel", Colors.GREEN)}    - Toggle intelligence layer
  {c("/stats", Colors.GREEN)}    - Show RAG statistics
  {c("/quit", Colors.GREEN)}     - Exit chat

{c("Tips:", Colors.YELLOW)}
  * Ask about code, architecture, patterns
  * Reference @file.py to focus on specific files
  * Use natural language - the model sees your codebase context
"""
    print(banner)


def print_help() -> None:
    """Print help information."""
    help_text = f"""
{c("Available Commands:", Colors.YELLOW)}

  {c("/help", Colors.GREEN)}          Show this help message
  {c("/clear", Colors.GREEN)}         Clear conversation history
  {c("/sources", Colors.GREEN)}       Toggle showing retrieved sources
  {c("/context", Colors.GREEN)}       Toggle showing full context (debug mode)
  {c("/model <name>", Colors.GREEN)}  Switch to a different Ollama model
  {c("/stats", Colors.GREEN)}         Show RAG knowledge base statistics
  {c("/top_k <n>", Colors.GREEN)}     Set number of chunks to retrieve
  {c("/temp <t>", Colors.GREEN)}      Set temperature (0.0-1.0)
  {c("/quit", Colors.GREEN)}          Exit the chat

{c("Example queries:", Colors.YELLOW)}

  "What is the GRID architecture?"
  "How does the RAG indexer work?"
  "Explain the embeddings module"
  "Show me how to use the CLI"
"""
    print(help_text)


async def handle_command(command: str, session: RAGChatSession, config: ChatConfig) -> bool:
    """Handle a slash command. Returns True if should continue, False to quit."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    if cmd in ("/quit", "/exit", "/q"):
        print(c("\nGoodbye!", Colors.CYAN))
        return False

    elif cmd in ("/help", "/h", "/?"):
        print_help()

    elif cmd == "/clear":
        session.clear_history()

    elif cmd == "/sources":
        config.show_sources = not config.show_sources
        status = "enabled" if config.show_sources else "disabled"
        print(c(f"[OK] Source display {status}", Colors.GREEN))

    elif cmd == "/context":
        config.show_context = not config.show_context
        status = "enabled" if config.show_context else "disabled"
        print(c(f"[OK] Full context display {status}", Colors.GREEN))

    elif cmd == "/intel":
        config.use_intelligence = not config.use_intelligence
        status = "enabled" if config.use_intelligence else "disabled"
        print(c(f"[OK] Intelligence layer {status}", Colors.GREEN))

    elif cmd == "/model":
        if arg:
            config.model = arg
            print(c(f"[OK] Switched to model: {arg}", Colors.GREEN))
            await session._check_model()
        else:
            print(c(f"Current model: {config.model}", Colors.CYAN))
            print(c("Usage: /model <model_name>", Colors.DIM))

    elif cmd == "/stats":
        if session._engine:
            stats = session._engine.get_stats()
            print(c("\n[RAG Statistics]", Colors.CYAN))
            print(c(f"  Documents: {stats.get('document_count', 0):,}", Colors.WHITE))
            print(c(f"  Collection: {stats.get('collection_name', 'N/A')}", Colors.WHITE))
            print(c(f"  Embedding Model: {stats.get('embedding_model', 'N/A')}", Colors.WHITE))
        else:
            print(c("RAG engine not initialized", Colors.YELLOW))

    elif cmd == "/top_k":
        if arg and arg.isdigit():
            config.top_k = int(arg)
            print(c(f"[OK] top_k set to {config.top_k}", Colors.GREEN))
        else:
            print(c(f"Current top_k: {config.top_k}", Colors.CYAN))

    elif cmd == "/temp":
        if arg:
            try:
                config.temperature = float(arg)
                print(c(f"[OK] Temperature set to {config.temperature}", Colors.GREEN))
            except ValueError:
                print(c("Invalid temperature value", Colors.RED))
        else:
            print(c(f"Current temperature: {config.temperature}", Colors.CYAN))

    else:
        print(c(f"Unknown command: {cmd}", Colors.YELLOW))
        print(c("Type /help for available commands", Colors.DIM))

    return True


async def interactive_loop(config: ChatConfig) -> None:
    """Main interactive chat loop."""
    print(c("Initializing RAG Chat...", Colors.DIM), end=" ", flush=True)

    session = RAGChatSession(config)

    try:
        await session.initialize()
    except Exception as e:
        print(c(f"Failed to initialize: {e}", Colors.RED))
        return

    print_banner(config)

    while True:
        try:
            user_input = input(c("\n> ", Colors.CYAN + Colors.BOLD)).strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                should_continue = await handle_command(user_input, session, config)
                if not should_continue:
                    break
                continue

            await session.chat(user_input)

        except KeyboardInterrupt:
            print(c("\n\nInterrupted. Type /quit to exit.", Colors.YELLOW))
        except EOFError:
            print(c("\n\nGoodbye!", Colors.CYAN))
            break


def setup_parser() -> argparse.ArgumentParser:
    """Setup argument parser."""
    parser = argparse.ArgumentParser(
        description="Interactive RAG Chat for GRID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tools.rag.chat
  python -m tools.rag.chat --model qwen2.5-coder:latest
  python -m tools.rag.chat --top-k 15 --temp 0.5
""",
    )

    parser.add_argument(
        "--model",
        "-m",
        default=os.getenv("RAG_CHAT_MODEL", "ministral-3:3b"),
        help="Ollama model to use (default: ministral-3:3b)",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=8,
        help="Number of context chunks to retrieve (default: 8)",
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.7,
        help="LLM temperature (default: 0.7)",
    )
    parser.add_argument("--no-sources", action="store_true", help="Don't show retrieved sources")
    parser.add_argument("--show-context", action="store_true", help="Show full retrieved context (debug mode)")
    parser.add_argument("--no-intel", action="store_true", help="Disable intelligence layer")
    parser.add_argument("--collection", default="grid_knowledge_base", help="ChromaDB collection name")
    parser.add_argument("--db-path", default="", help="Path to vector store (default: src/.rag_db)")
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL",
    )
    parser.add_argument("--query", "-q", help="Single query mode (non-interactive)")

    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Async main entry point."""
    config = ChatConfig(
        model=args.model,
        ollama_base_url=args.ollama_url,
        top_k=args.top_k,
        temperature=args.temperature,
        show_sources=not args.no_sources,
        show_context=args.show_context,
        use_intelligence=not args.no_intel,
        collection_name=args.collection,
        vector_store_path=args.db_path,
    )

    if args.query:
        print(c("Initializing RAG Chat...", Colors.DIM), end=" ", flush=True)
        session = RAGChatSession(config)
        await session.initialize()
        await session.chat(args.query)
        return 0

    await interactive_loop(config)
    return 0


def main() -> int:
    """Main entry point."""
    parser = setup_parser()
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
