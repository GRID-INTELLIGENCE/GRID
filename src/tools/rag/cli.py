#!/usr/bin/env python3
"""
RAG CLI interface for GRID.

Provides command-line interface for indexing repositories and querying
the RAG system using the unified RAG engine.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the grid root to Python path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))

from tools.rag.config import RAGConfig
from tools.rag.rag_engine import RAGEngine


def _read_manifest(manifest_path: str) -> list[str]:
    path = Path(manifest_path)
    if not path.exists():
        raise SystemExit(f"Manifest file not found: {manifest_path}")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # support list[str] or list[{'rel_path': ...}]
            files: list[str] = []
            for item in data:
                if isinstance(item, str):
                    files.append(item)
                elif isinstance(item, dict) and "rel_path" in item:
                    files.append(str(item["rel_path"]))
            if not files:
                raise SystemExit("Manifest JSON must be a list of file paths or objects with 'rel_path'")
            return files
        raise SystemExit("Manifest JSON must be a list")

    # newline-delimited paths
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    return [ln for ln in lines if ln and not ln.startswith("#")]


def _build_curated_files(repo_path: str) -> list[str]:
    repo = Path(repo_path)
    if not repo.exists():
        raise SystemExit(f"Repo path does not exist: {repo_path}")

    curated: set[str] = set()

    # Seed with automatically scored "important" files (if present)
    important_json = repo / "important_files.json"
    if important_json.exists():
        try:
            items = json.loads(important_json.read_text(encoding="utf-8"))
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("rel_path"):
                        curated.add(str(it["rel_path"]))
        except Exception:
            pass

    # Core project entry points + docs (kept intentionally small)
    curated.update(
        {
            "README.md",
            "pyproject.toml",
            "requirements.txt",
            "CONTEXTUAL_BRIEF.md",
            "INITIAL_REQUEST_SUMMARY.md",
            "GROWTH_STRATEGY_Q1_2026.md",
            "grid/application.py",
            "grid/__main__.py",
            "grid/awareness/context.py",
            "grid/patterns/recognition.py",
            "grid/interfaces/bridge.py",
            "grid/entry_points/api_entry.py",
            "grid/entry_points/cli_entry.py",
            "application/mothership/main.py",
            "application/mothership/routers/__init__.py",
            "application/mothership/routers/intelligence.py",
            "tools/rag/README.md",
            "tools/rag/rag_engine.py",
            "tools/rag/indexer.py",
            "tools/rag/cli.py",
            "tools/rag/config.py",
            "tools/rag/embeddings/nomic_v2.py",
            "tools/rag/llm/ollama_local.py",
            "tests/test_grid_intelligence.py",
            "tests/test_grid_benchmark.py",
            "async_stress_harness.py",
            "docs/ARCHITECTURE_STRATEGY.md",
            "docs/ARCHITECTURE_ENHANCEMENTS.md",
            "docs/BREAKING_CHANGES.md",
            "docs/RAG_INDEXING_PLAN.md",
            ".windsurf/structural-intelligence/IMPLEMENTATION_GUIDE.md",
            ".windsurf/structural-intelligence/MISSION_CONTROL.md",
            ".windsurf/structural-intelligence/AWARENESS_LAYER.md",
            # Reference: existing YouTube client implementation
            "light_of_the_seven/datakit/Hogwarts/spellbook_api.py",
        }
    )

    # Filter to files that actually exist
    existing: list[str] = []
    for rel in sorted(curated):
        p = repo / rel
        if p.exists() and p.is_file():
            existing.append(rel)
    return existing


def setup_parser():
    """Setup argument parser for RAG CLI."""
    parser = argparse.ArgumentParser(description="RAG (Retrieval-Augmented Generation) CLI for GRID")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index a repository")
    index_parser.add_argument(
        "path", nargs="?", default=".", help="Path to repository to index (default: current directory)"
    )
    index_parser.add_argument(
        "--update",
        action="store_true",
        default=True,
        help="Incremental update - only re-index changed files (default behavior)",
    )
    index_parser.add_argument(
        "--rebuild", action="store_true", help="Full rebuild - delete existing index and re-index everything"
    )
    index_parser.add_argument(
        "--curate",
        action="store_true",
        help="Curated rebuild index using a small high-signal file set (recommended for fast/high-quality retrieval)",
    )
    index_parser.add_argument(
        "--manifest",
        help="Path to manifest file (newline-delimited or JSON list) of files to index, relative to repo path",
    )
    index_parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.0,
        help="Minimum quality score (0.0-1.0) for files to be indexed (default: 0.0 = no filtering)",
    )
    index_parser.add_argument("--db-path", help="Path to vector store (default: .rag_db)")
    index_parser.add_argument("--skip-preflight", action="store_true", help="Skip pre-flight checks before indexing")
    index_parser.add_argument("--json", action="store_true", help="Output indexing summary as JSON (quiet mode)")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument("query", help="Query string")
    query_parser.add_argument(
        "--top-k", type=int, default=None, help="Number of results to retrieve (default: from config)"
    )
    query_parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature (default: 0.7)")
    query_parser.add_argument("--hybrid", action="store_true", help="Enable hybrid search (BM25 + vector)")
    query_parser.add_argument("--rerank", action="store_true", help="Enable cross-encoder reranking")

    # On-demand query command
    ondemand_parser = subparsers.add_parser(
        "ondemand", help="Query-time RAG: build an ephemeral index from docs/ (and optional codebase) per query"
    )
    ondemand_parser.add_argument("query", help="Query string")
    ondemand_parser.add_argument("--docs", default="docs", help="Docs root (default: docs)")
    ondemand_parser.add_argument("--repo", default=".", help="Repo root (default: .)")
    ondemand_parser.add_argument("--depth", type=int, default=0, help="Recursive scope expansion depth (default: 0)")
    ondemand_parser.add_argument(
        "--prefilter-k-files",
        type=int,
        default=50,
        help="Number of docs files to preselect before embedding/indexing (default: 50)",
    )
    ondemand_parser.add_argument(
        "--max-chunks",
        type=int,
        default=2000,
        help="Hard cap on number of chunks to embed/index per query (default: 2000)",
    )
    ondemand_parser.add_argument(
        "--include-codebase",
        action="store_true",
        help="Also search and expand into the whole repo (default: docs-only)",
    )
    ondemand_parser.add_argument("--top-k", type=int, default=None, help="Top K chunks to retrieve")
    ondemand_parser.add_argument("--max-files", type=int, default=600, help="Max files to consider initially")
    ondemand_parser.add_argument("--temperature", type=float, default=0.3, help="LLM temperature (default: 0.3)")
    ondemand_parser.add_argument(
        "--gguf",
        default=None,
        help="Optional local GGUF path for llama-cpp-python generation (overrides Ollama LLM)",
    )
    ondemand_parser.add_argument(
        "--json",
        action="store_true",
        help="Output full on-demand result as JSON (answer, routing, stats, selected_files, sources)",
    )

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate RAG system")
    eval_parser.add_argument("--queries", nargs="+", help="List of queries to evaluate")
    eval_parser.add_argument("--output", help="Output file for results")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show RAG system statistics")
    stats_parser.add_argument("--db-path", help="Path to vector store database")

    # Intelligent query command (Phase 3: Reasoning Layer)
    intelligent_parser = subparsers.add_parser(
        "intelligent-query", help="Query using intelligent RAG with reasoning (Phase 3)"
    )
    intelligent_parser.add_argument("query", help="Query string")
    intelligent_parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    intelligent_parser.add_argument(
        "--temperature", type=float, default=0.3, help="LLM temperature for synthesis (default: 0.3)"
    )
    intelligent_parser.add_argument(
        "--show-reasoning", action="store_true", help="Show chain-of-thought reasoning steps"
    )
    intelligent_parser.add_argument("--show-metrics", action="store_true", help="Show pipeline performance metrics")
    intelligent_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def preflight_check(repo_path: str, config: RAGConfig, skip_preflight: bool = False) -> None:
    """Run pre-flight checks before indexing.

    Args:
        repo_path: Path to repository
        config: RAG configuration
        skip_preflight: Skip all checks
    """
    if skip_preflight:
        return

    print("\n" + "=" * 60)
    print("PRE-FLIGHT CHECKS".center(60))
    print("=" * 60)

    # 1. Check embedding model availability
    print("\n[1/3] Checking embedding model...")
    if config.embedding_provider == "huggingface":
        try:
            from sentence_transformers import SentenceTransformer

            print(f"  Loading model: {config.embedding_model}")
            model = SentenceTransformer(config.embedding_model)
            print(f"  ✓ Model loaded successfully (dim={model.get_sentence_embedding_dimension()})")
        except Exception as e:
            raise SystemExit(f"  ✗ Failed to load embedding model: {e}") from e
    elif config.embedding_provider == "ollama":
        from .utils import check_ollama_connection

        if not check_ollama_connection(config.ollama_base_url):
            raise SystemExit(f"  ✗ Ollama not accessible at {config.ollama_base_url}")
        print(f"  ✓ Ollama accessible at {config.ollama_base_url}")

    # 2. Estimate index size
    print("\n[2/3] Estimating index size...")
    from pathlib import Path

    repo = Path(repo_path)
    if not repo.exists():
        raise SystemExit(f"  ✗ Repository path does not exist: {repo_path}")

    # Count files, skipping symlinks and inaccessible paths
    total_files = 0
    for item in repo.rglob("*"):
        try:
            if item.is_file() and not item.is_symlink():
                total_files += 1
        except (OSError, PermissionError):
            # Skip inaccessible files/symlinks
            continue

    estimated_chunks = total_files * 10  # Rough estimate

    print(f"  Files found: {total_files:,}")
    print(f"  Estimated chunks: {estimated_chunks:,}")

    if estimated_chunks > 50000:
        print(f"  ⚠️  WARNING: Very large index ({estimated_chunks:,} chunks)")
        print("  Consider using --curate flag for selective indexing")
        response = input("  Continue anyway? [y/N]: ")
        if response.lower() != "y":
            raise SystemExit("Indexing cancelled by user")
    else:
        print("  ✓ Index size looks reasonable")

    # 3. Check disk space
    print("\n[3/3] Checking disk space...")
    import shutil

    stats = shutil.disk_usage(repo_path)
    free_gb = stats.free / (1024**3)

    if free_gb < 5.0:
        print(f"  ⚠️  WARNING: Low disk space ({free_gb:.2f} GB free)")
    else:
        print(f"  ✓ Disk space: {free_gb:.2f} GB free")

    print("\n" + "=" * 60)
    print("Pre-flight checks complete\n")


async def index_command(args):
    """Handle index command."""
    mode = "rebuild" if args.rebuild else "incremental"
    quiet = args.json
    if not quiet:
        print(f"Indexing repository at: {args.path} (mode: {mode})")

    try:
        config = RAGConfig.from_env()
        if hasattr(args, "db_path") and args.db_path:
            config.vector_store_path = args.db_path
        config.ensure_local_only()

        engine = RAGEngine(config=config)

        files = None
        if args.curate:
            if not args.rebuild:
                raise SystemExit("--curate currently requires --rebuild")
            files = _build_curated_files(args.path)
            print(f"Curated indexing enabled. Files: {len(files)}")
        elif args.manifest:
            if not args.rebuild:
                raise SystemExit("--manifest currently requires --rebuild")
            files = _read_manifest(args.manifest)
            print(f"Manifest indexing enabled. Files: {len(files)}")

        # Run pre-flight checks
        if args.rebuild:
            preflight_check(args.path, config, skip_preflight=args.skip_preflight)

        if args.rebuild:
            # Full rebuild with quality threshold
            engine.index(
                repo_path=args.path, rebuild=True, files=files, quality_threshold=args.quality_threshold, quiet=quiet
            )
        else:
            # Incremental update
            from tools.rag.indexer import update_index

            update_index(
                repo_path=args.path,
                vector_store=engine.vector_store,
                embedding_provider=engine.embedding_provider,
                config=config,
                quiet=quiet,
            )

        if quiet:
            import json

            stats = engine.get_stats()
            result = {
                "status": "success",
                "mode": mode,
                "stats": stats,
            }
            # Include file tracker stats for incremental mode
            if not args.rebuild:
                from tools.rag.file_tracker import FileTracker

                tracker = FileTracker(persist_dir=config.vector_store_path)
                tracker_stats = tracker.get_stats()
                result["tracked_files"] = tracker_stats["tracked_files"]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Indexing completed successfully!")
            stats = engine.get_stats()
            print(f"Total documents indexed: {stats['document_count']}")

            # Show file tracker stats for incremental mode
            if not args.rebuild:
                from tools.rag.file_tracker import FileTracker

                tracker = FileTracker(persist_dir=config.vector_store_path)
                tracker_stats = tracker.get_stats()
                print(f"Tracked files: {tracker_stats['tracked_files']}")

    except Exception as e:
        print(f"Error indexing repository: {e}")
        import traceback

        traceback.print_exc()

        # Check for metadata mismatch
        if "path" in str(e).lower() or "metadata" in str(e).lower():
            print("\n[!] Hint: If you see metadata errors, try --rebuild to migrate to new metadata format.")

        return 1

    return 0


async def ondemand_command(args):
    """Handle on-demand query command."""
    print(f"On-demand query: {args.query}")

    try:
        from tools.rag.on_demand_engine import OnDemandRAGEngine

        config = RAGConfig.from_env()
        config.ensure_local_only()

        engine = OnDemandRAGEngine(config=config, docs_root=args.docs, repo_root=args.repo)
        res = engine.query(
            query_text=args.query,
            depth=args.depth,
            top_k=getattr(args, "top_k", None),
            max_files=args.max_files,
            prefilter_k_files=args.prefilter_k_files,
            max_chunks=args.max_chunks,
            temperature=args.temperature,
            include_codebase=args.include_codebase,
            gguf_model_path=args.gguf,
        )

        if args.json:
            import json
            from dataclasses import asdict

            # OnDemandRAGResult is a dataclass
            print(json.dumps(asdict(res), indent=2, ensure_ascii=False))
            return 0

        print("\nRouting:")
        for k, v in res.routing.items():
            print(f"  {k}: {v}")

        print("\nAnswer:")
        print(res.answer)

        if getattr(res, "stats", None):
            print("\nOn-demand stats:")
            for k, v in res.stats.items():
                print(f"  {k}: {v}")

        if getattr(res, "selected_files", None):
            print(f"\nSelected files ({len(res.selected_files)}):")
            for i, item in enumerate(res.selected_files[:20], 1):
                print(f"  {i}. {item.get('path')} (score={item.get('score')})")
            if len(res.selected_files) > 20:
                print(f"  ... (+{len(res.selected_files) - 20} more)")

        if res.sources:
            print(f"\nSources ({len(res.sources)}):")
            for i, s in enumerate(res.sources, 1):
                meta = s.get("metadata") or {}
                print(
                    f"  {i}. {meta.get('path', 'Unknown')} (chunk={meta.get('chunk_index', '?')}, distance={s.get('distance'):.4f})"
                )

    except Exception as e:
        print(f"Error running on-demand RAG query: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


async def query_command(args):
    """Handle query command."""
    print(f"Querying: {args.query}")

    try:
        config = RAGConfig.from_env()
        config.ensure_local_only()

        # Override config based on flags
        if args.hybrid:
            config.use_hybrid = True
            print("Hybrid search enabled (BM25 + vector)")
        if args.rerank:
            config.use_reranker = True
            print("Cross-encoder reranking enabled")

        engine = RAGEngine(config=config)
        result = await engine.query(query_text=args.query, top_k=args.top_k, temperature=args.temperature)

        print("\nAnswer:")
        print(result["answer"])

        if result.get("sources"):
            print(f"\nSources ({len(result['sources'])}):")
            for i, source in enumerate(result["sources"], 1):
                print(f"  {i}. {source['metadata'].get('path', 'Unknown')} (distance: {source['distance']:.3f})")

    except Exception as e:
        print(f"Error querying RAG system: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


async def intelligent_query_command(args):
    """Handle intelligent query command (Phase 3: Reasoning Layer)."""
    if not args.json:
        print(f"\n🧠 Intelligent RAG Query: {args.query}")
        print("=" * 70)

    try:
        config = RAGConfig.from_env()
        config.ensure_local_only()

        # Ensure intelligent RAG is enabled
        if not config.use_intelligent_rag:
            config.use_intelligent_rag = True

        engine = RAGEngine(config=config)

        if not engine._intelligent_orchestrator:
            print("❌ Error: Intelligent RAG orchestrator not initialized.")
            print("This may be due to missing dependencies for the reasoning layer.")
            return 1

        # Execute intelligent query
        result = await engine.intelligent_query(
            query_text=args.query,
            top_k=args.top_k,
            temperature=args.temperature,
            include_reasoning=args.show_reasoning,
            include_metrics=args.show_metrics,
        )

        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Pretty print results
            print("\n📝 Answer:")
            print("-" * 70)
            print(result["answer"])
            print("-" * 70)

            # Confidence indicator
            confidence = result.get("confidence", 0.0)
            conf_emoji = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.5 else "🔴"
            print(f"\n{conf_emoji} Confidence: {confidence:.0%}")

            # Citations
            if result.get("citations"):
                print(f"\n📚 Sources ({len(result['citations'])} citations):")
                for citation in result["citations"]:
                    print(f"  • {citation}")

            # Reasoning steps (if requested)
            if args.show_reasoning and "reasoning" in result:
                reasoning = result["reasoning"]
                print(f"\n🧠 Reasoning Chain ({len(reasoning.get('steps', []))} steps):")
                print("-" * 70)
                for step in reasoning.get("steps", []):
                    step_type = step.get("type", "unknown")
                    content = step.get("content", "")
                    conf = step.get("confidence", 0.0)
                    print(f"\n{step['step']}. [{step_type.upper()}] (confidence: {conf:.0%})")
                    print(f"   {content}")

                if reasoning.get("warnings"):
                    print("\n⚠️  Warnings:")
                    for warning in reasoning["warnings"]:
                        print(f"  • {warning}")

            # Metrics (if requested)
            if args.show_metrics and "metrics" in result:
                metrics = result["metrics"]
                print("\n📊 Pipeline Metrics:")
                print("-" * 70)

                if "timing" in metrics:
                    print("Timing:")
                    for stage, time_str in metrics["timing"].items():
                        print(f"  • {stage}: {time_str}")

                if "pipeline" in metrics:
                    print("\nPipeline:")
                    for key, val in metrics["pipeline"].items():
                        print(f"  • {key}: {val}")

                if "quality" in metrics:
                    print("\nQuality:")
                    for key, val in metrics["quality"].items():
                        print(f"  • {key}: {val}")

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"\n❌ Error: {e}")
        return 1


async def evaluate_command(args):
    """Handle evaluate command."""
    print("Evaluating RAG system performance...")

    config = RAGConfig.from_env()
    engine = RAGEngine(config=config)

    queries = args.queries or [
        "What is the GRID system?",
        "How is context handled in RAG?",
        "What are the default models?",
    ]

    results = []
    for query in queries:
        print(f"Testing query: {query}")
        res = engine.query(query, top_k=config.top_k)
        # Calculate some basic metrics
        distances = [s["distance"] for s in res.get("sources", [])]
        avg_dist = sum(distances) / len(distances) if distances else 1.0

        results.append(
            {
                "query": query,
                "avg_distance": avg_dist,
                "source_count": len(res.get("sources", [])),
                "answer_length": len(res.get("answer", "")),
            }
        )

    print("\nEvaluation Summary:")
    print(f"{'Query':<40} | {'Avg Dist':<10} | {'Sources':<8}")
    print("-" * 65)
    for r in results:
        print(f"{r['query'][:40]:<40} | {r['avg_distance']:.4f}     | {r['source_count']}")

    return 0


async def stats_command(args):
    """Handle stats command."""
    try:
        config = RAGConfig.from_env()
        if hasattr(args, "db_path") and args.db_path:
            config.vector_store_path = args.db_path
        engine = RAGEngine(config=config)
        stats = engine.get_stats()

        print("RAG System Statistics:")
        print(f"  Documents: {stats['document_count']}")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Embedding Model: {stats['embedding_model']}")
        print(f"  LLM Model: {stats['llm_model']}")

    except Exception as e:
        print(f"Error getting stats: {e}")
        return 1

    return 0


async def main():
    """Main CLI entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "index":
        return await index_command(args)
    elif args.command == "ondemand":
        return await ondemand_command(args)
    elif args.command == "query":
        return await query_command(args)
    elif args.command == "intelligent-query":
        return await intelligent_query_command(args)
    elif args.command == "evaluate":
        return await evaluate_command(args)
    elif args.command == "stats":
        return await stats_command(args)
    else:
        parser.print_help()
        return 1


# Standalone entry points for pyproject.toml scripts
def query() -> None:
    """Entry point for rag-query command."""
    parser = argparse.ArgumentParser(description="Query the RAG system")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--top-k", type=int, default=None, help="Number of results")
    parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature")
    parser.add_argument("--hybrid", action="store_true", help="Enable hybrid search")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking")
    args = parser.parse_args()
    sys.exit(asyncio.run(query_command(args)))


def index() -> None:
    """Entry point for rag-index command."""
    parser = argparse.ArgumentParser(description="Index a repository")
    parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    parser.add_argument("--rebuild", action="store_true", help="Full rebuild")
    parser.add_argument("--curate", action="store_true", help="Curated indexing")
    parser.add_argument("--manifest", help="Path to manifest file")
    parser.add_argument("--quality-threshold", type=float, default=0.0, help="Minimum quality score")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip pre-flight checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    # Set update default
    args.update = True
    sys.exit(asyncio.run(index_command(args)))


def stats() -> None:
    """Entry point for rag-stats command."""
    args = argparse.Namespace()
    sys.exit(asyncio.run(stats_command(args)))


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
