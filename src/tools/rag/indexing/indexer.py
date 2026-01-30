"""Repository indexing functionality for RAG."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..embeddings.base import BaseEmbeddingProvider
from ..utils import get_agent_ignore_patterns
from ..vector_store.base import BaseVectorStore
from .semantic_chunker import SemanticChunker

if TYPE_CHECKING:
    from ..config import RAGConfig


@dataclass
class IndexingMetrics:
    """Track indexing performance and quality metrics."""

    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    files_processed: int = 0
    files_skipped: int = 0
    chunks_created: int = 0
    chunks_failed: int = 0
    total_bytes: int = 0
    skip_reasons: dict[str, int] = field(default_factory=dict)

    def add_skip_reason(self, reason: str) -> None:
        """Track why a file was skipped."""
        self.skip_reasons[reason] = self.skip_reasons.get(reason, 0) + 1

    @property
    def duration_seconds(self) -> float:
        """Calculate indexing duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def chunks_per_second(self) -> float:
        """Calculate throughput."""
        duration = self.duration_seconds
        return self.chunks_created / duration if duration > 0 else 0.0

    def finalize(self) -> None:
        """Mark indexing as complete."""
        self.end_time = datetime.now()

    def report(self) -> str:
        """Generate human-readable report."""
        report_lines = [
            "",
            "═" * 60,
            "INDEXING METRICS REPORT".center(60),
            "═" * 60,
            f"Duration:           {self.duration_seconds:.2f}s",
            f"Files Processed:    {self.files_processed}",
            f"Files Skipped:      {self.files_skipped}",
            f"Chunks Created:     {self.chunks_created}",
            f"Chunks Failed:      {self.chunks_failed}",
            f"Total Bytes:        {self.total_bytes / 1024:.2f} KB",
            f"Throughput:         {self.chunks_per_second:.2f} chunks/s",
        ]

        if self.skip_reasons:
            report_lines.append("")
            report_lines.append("Skip Reasons:")
            for reason, count in sorted(self.skip_reasons.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  - {reason}: {count}")

        report_lines.append("═" * 60)
        return "\n".join(report_lines)


def read_file_content(path: Path, max_size: int = 1024 * 1024) -> str | None:
    """Read file content with size limit."""
    try:
        if path.stat().st_size > max_size:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
    separator: str = "\n\n",
    max_chunk_size: int = 4000,  # Nomic V1 handles this easily
    min_chunk_size: int = 50,
) -> list[str]:
    """Split text into overlapping chunks with recursive splitting for oversized sections."""
    if not text:
        return []

    # Split by separator first
    sections = text.split(separator)
    chunks = []
    current_chunk = ""

    for section in sections:
        # Check if the individual section alone exceeds max_chunk_size
        if len(section) > max_chunk_size:
            # Recursive split instead of truncation
            sub_sections = [section[i : i + max_chunk_size] for i in range(0, len(section), max_chunk_size - overlap)]
            sections.extend(sub_sections[1:])  # Add remaining to processing queue
            section = sub_sections[0]

        if len(current_chunk) + len(section) + len(separator) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            overlap_words = words[-overlap:] if len(words) > overlap else words
            current_chunk = " ".join(overlap_words) + separator + section
        else:
            if current_chunk:
                current_chunk += separator + section
            else:
                current_chunk = section

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Final hard limit check (Safety split)
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
            # Should have been handled by recursive section logic, but as a last resort:
            sub = [chunk[i : i + max_chunk_size] for i in range(0, len(chunk), max_chunk_size - overlap)]
            final_chunks.extend(sub)
        else:
            final_chunks.append(chunk)

    # Final filter for minimum chunk quality
    return [c for c in final_chunks if len(c) >= min_chunk_size]


def is_text_file(path: Path, text_extensions: set[str]) -> bool:
    """Check if file is likely a text file."""
    # Check extension
    if path.suffix.lower() in text_extensions:
        return True

    # Check for common text files without extension
    if path.name.lower() in {"readme", "license", "changelog", "dockerfile"}:
        return True

    # Check for shebang
    try:
        # Security: This function should only be called with validated paths
        # from the indexing process which already restricts to repo_path
        with open(path, encoding="utf-8", errors="ignore") as f:
            first_line = f.readline(100)
            return first_line.startswith("#!")
    except Exception:
        return False


def index_repository(
    repo_path: str,
    store_path: str | None = None,
    chunk_size: int = 3000,
    overlap: int = 300,
    rebuild: bool = False,
    embedding_provider: BaseEmbeddingProvider | None = None,
    exclude_dirs: list[str] | set[str] | None = None,
    include_patterns: list[str] | None = None,
    vector_store: BaseVectorStore | None = None,
    files: list[str] | None = None,
    quality_threshold: float = 0.0,
    quiet: bool = False,
) -> BaseVectorStore:
    """Index a repository into a vector store.

    Args:
        repo_path: Path to the repository to index
        store_path: Path to save/load the vector store (deprecated, use vector_store)
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        rebuild: Whether to rebuild the index even if store exists
        embedding_provider: Provider for generating embeddings (must return dense vectors)
        exclude_dirs: Directory names to exclude
        include_patterns: File patterns to include (glob patterns)
        vector_store: Vector store instance to use (if None, creates ChromaDB store)

    Returns:
        VectorStore with indexed documents
    """
    from ..embeddings.simple import SimpleEmbedding
    from ..vector_store.chromadb_store import ChromaDBVectorStore

    repo = Path(repo_path)
    if not repo.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")

    debug = os.getenv("RAG_INDEX_DEBUG", "").lower() in {"1", "true", "yes"}

    try:
        repo_resolved = repo.resolve()
    except Exception:
        repo_resolved = repo

    # Default exclude directories
    exclude_dirs_set: set[str]
    if exclude_dirs is None:
        exclude_dirs_set = {
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            ".idea",
            ".vscode",
            "dist",
            "build",
            ".tox",
            ".rag_db",
            ".rag_logs",
            "research_snapshots",
            "archival",
            "ui_backup",
            "ui_node_modules_orphan",
            "Hogwarts",
            "visualizations",
            "Arena",
            "datakit",
            "legacy_src",
            "artifacts",
            "analysis_report",
            "logs",
            "media",
            "assets",
            "temp",
            "rust",
            "interfaces",
            "acoustics",
            "awareness",
            "evolution",
            "motion",
        }
    else:
        exclude_dirs_set = set(exclude_dirs) if isinstance(exclude_dirs, list) else exclude_dirs

    # Load patterns from .agentignore
    agent_ignore = get_agent_ignore_patterns(
        str(repo_resolved if "repo_resolved" in locals() else repo_path if "repo_path" in locals() else ".")
    )
    if agent_ignore:
        exclude_dirs_set.update(agent_ignore)

    # Default text file extensions
    text_extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".md",
        ".txt",
        ".rst",
        ".yml",
        ".yaml",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
        ".cfg",
        ".ini",
        ".toml",
        ".lock",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".m",
        ".pl",
        ".lua",
        ".vim",
        ".el",
        ".lisp",
        ".hs",
        ".ml",
    }

    # Files to explicitly exclude by name
    exclude_files = {
        "artifact.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
    }

    # Initialize vector store
    if vector_store is None:
        vector_store = ChromaDBVectorStore()

    # Check if store has documents and rebuild is False
    if not rebuild and vector_store.count() > 0:
        print(f"Using existing vector store with {vector_store.count()} documents")
        if not rebuild:
            return vector_store

    if rebuild:
        reset_fn = getattr(vector_store, "reset", None)
        if callable(reset_fn):
            reset_fn()
        print("Rebuilding index...")

    print(f"Indexing repository: {repo_path}")

    # Initialize metrics
    metrics = IndexingMetrics()

    # Walk the repository or use provided file list
    chunk_ids = []
    chunk_texts = []
    chunk_metadatas = []

    if files:
        print(f"Indexing {len(files)} specific files from manifest...")
        file_iterator = []
        seen: set[str] = set()
        for f in files:
            # Normalize separators to reduce Windows '\\' vs '/' duplication.
            f_norm = str(f).replace("\\\\", "/")
            p = Path(f_norm)
            if not p.is_absolute():
                p = repo / p
            try:
                p_resolved = p.resolve()
            except Exception:
                p_resolved = p

            key = os.path.normcase(os.path.normpath(str(p_resolved)))
            if key in seen:
                continue
            seen.add(key)
            file_iterator.append(str(p_resolved))
    else:
        file_iterator = []
        for root, dirs, f_list in os.walk(repo):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
            for f in f_list:
                file_iterator.append(str(Path(root) / f))

    for file_str in file_iterator:
        file_path = Path(file_str)
        if debug:
            print(f"DEBUG: Processing {file_path}")

        if not file_path.exists():
            if debug:
                print(f"DEBUG: File not found: {file_path}")
            continue

        # Check if file matches include patterns
        if include_patterns:
            if not any(file_path.match(pattern) for pattern in include_patterns):
                continue

        # Check if it's a text file and not too large
        if file_path.name in exclude_files:
            continue

        if not is_text_file(file_path, text_extensions):
            if debug:
                print(f"DEBUG: Not a text file: {file_path.name}, suffix: {file_path.suffix}")
            continue

        # Skip files larger than 1MB to avoid indexing huge artifacts
        try:
            if file_path.stat().st_size > 1024 * 1024:
                print(f"Skipping large file: {file_path}")
                continue
        except Exception:
            continue

        # Read file content
        if debug:
            print(f"DEBUG: Reading content for {file_path}")
        content = read_file_content(file_path)
        if content is None:
            if debug:
                print(f"DEBUG: Content is None for {file_path}")
            metrics.files_skipped += 1
            metrics.add_skip_reason("Failed to read")
            continue
        if not content.strip():
            if debug:
                print(f"DEBUG: Content is empty for {file_path}")
            metrics.files_skipped += 1
            metrics.add_skip_reason("Empty file")
            continue

        # Quality scoring (if threshold > 0)
        if quality_threshold > 0.0:
            from ..quality import should_index_file

            should_index, quality = should_index_file(file_path, quality_threshold, content)
            if not should_index:
                if debug:
                    print(f"DEBUG: Skipping {file_path}: quality={quality.score:.2f}, reasons={quality.reasons}")
                metrics.files_skipped += 1
                metrics.add_skip_reason(f"Low quality ({quality.score:.2f})")
                continue

        # Track file processing
        metrics.files_processed += 1
        metrics.total_bytes += len(content)

        # Create relative path
        try:
            rel_path = file_path.resolve().relative_to(repo_resolved)
        except Exception:
            try:
                rel_path = file_path.relative_to(repo)
            except Exception:
                rel_path = Path(file_path.name)

        rel_path_str = rel_path.as_posix()

        # Chunk the document semantically
        chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=chunk_size, chunk_overlap=overlap)
        semantic_chunks = chunker.chunk_file(content, rel_path_str)

        for i, sc in enumerate(semantic_chunks):
            chunk_id = f"{rel_path_str}#{i}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(sc.content)

            # Merge chunker metadata with standard metadata
            metadata = {"path": rel_path_str, "chunk_index": i, "type": "chunk", "file_size": len(content)}
            metadata.update(sc.metadata)

            chunk_metadatas.append(metadata)
            metrics.chunks_created += 1

    total_chunks = len(chunk_texts)
    if total_chunks > 50000:
        print(f"\n⚠️  WARNING: {total_chunks:,} chunks detected!")
        print("   This is unusually high. Recommended: < 20,000")
        print("   Consider:")
        print(f"   - Increasing chunk_size (current: {chunk_size})")
        print("   - Using --curate flag for selective indexing")
        print("   - Adding more exclude directories")

        # Non-interactive mode: just warn and continue
        print("Continuing with warning...")

    print(f"Created {total_chunks} chunks from repository")

    # Initialize progress tracker
    from ..progress import IndexProgress

    progress = IndexProgress()
    progress.start(total_chunks)

    # Generate embeddings
    if embedding_provider is None:
        if not quiet:
            print("Warning: No embedding provider provided, using simple fallback")
        embedding_provider = SimpleEmbedding()

    if not quiet:
        print(f"Generating embeddings using {embedding_provider.__class__.__name__}...")

    # Filter out chunks that are too long (will be handled by embedding provider, but warn)
    # Using 4000 as a safe upper bound for Nomic V1, or the provided max_chunk_size
    limit = 4000
    long_chunks = [i for i, text in enumerate(chunk_texts) if len(text) > limit]
    if long_chunks:
        print(f"Warning: {len(long_chunks)} chunks exceed recommended length ({limit} chars) and will be truncated")

    # Generate embeddings with batch support for performance
    embeddings_list = []
    valid_indices = []

    # Check if provider supports batch embeddings
    has_batch = hasattr(embedding_provider, "embed_batch")
    batch_size = 32 if has_batch else 1

    if has_batch and total_chunks > 1:
        # Use batch embedding for better performance
        print(f"Using batch embedding (batch_size={batch_size}) for {total_chunks} chunks...")

        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_texts = chunk_texts[batch_start:batch_end]

            try:
                batch_embs = embedding_provider.embed_batch(batch_texts)

                for j, emb in enumerate(batch_embs):
                    idx = batch_start + j
                    if isinstance(emb, list):
                        embeddings_list.append(emb)
                    else:
                        embeddings_list.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))
                    valid_indices.append(idx)

            except Exception as e:
                error_str = str(e).lower()
                if "context length" in error_str or "exceeds" in error_str:
                    # Fall back to sequential for this batch
                    print(
                        f"Warning: Batch embedding failed, falling back to sequential for batch {batch_start}-{batch_end}"
                    )
                    for j, text in enumerate(batch_texts):
                        idx = batch_start + j
                        try:
                            emb = embedding_provider.embed(text)
                            if isinstance(emb, list):
                                embeddings_list.append(emb)
                            else:
                                embeddings_list.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))
                            valid_indices.append(idx)
                        except Exception as inner_e:
                            inner_error_str = str(inner_e).lower()
                            if "context length" in inner_error_str or "exceeds" in inner_error_str:
                                print(f"Warning: Skipping chunk {idx} (length: {len(text)} chars) - too long")
                                metrics.chunks_failed += 1
                                metrics.chunks_created -= 1
                                continue
                            else:
                                raise
                else:
                    raise

            if (batch_end // batch_size) % 5 == 0:
                progress.tick(batch_end - progress.completed)
                if not quiet and progress.should_report():
                    print(f"Embedded {progress.format()}")
    else:
        # Sequential embedding (fallback)
        if not quiet:
            print(f"Using sequential embedding for {total_chunks} chunks...")
        for i, text in enumerate(chunk_texts):
            try:
                emb = embedding_provider.embed(text)
                if isinstance(emb, list):
                    embeddings_list.append(emb)
                else:
                    # Convert numpy array to list
                    embeddings_list.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))
                valid_indices.append(i)
                progress.tick()
                if not quiet and progress.should_report():
                    print(f"Embedded {progress.format()}")
            except Exception as e:
                error_str = str(e).lower()
                if "context length" in error_str or "exceeds" in error_str:
                    print(f"Warning: Skipping chunk {i} (length: {len(text)} chars) - too long even after truncation")
                    # Skip this chunk - don't add to valid_indices
                    metrics.chunks_failed += 1
                    metrics.chunks_created -= 1  # Decrement since we counted it earlier
                    continue
                else:
                    raise  # Re-raise other errors

    # Filter lists to only include valid chunks
    if not quiet:
        print(f"DEBUG: Total chunks: {len(chunk_texts)}, Valid: {len(valid_indices)}", flush=True)

    if len(valid_indices) < len(chunk_texts):
        print(f"Info: Processed {len(valid_indices)}/{len(chunk_texts)} chunks successfully")
        chunk_ids = [chunk_ids[i] for i in valid_indices]
        chunk_texts = [chunk_texts[i] for i in valid_indices]
        chunk_metadatas = [chunk_metadatas[i] for i in valid_indices]

    # Add to vector store in batches to avoid memory issues
    batch_size = 100
    for i in range(0, len(chunk_ids), batch_size):
        batch_ids = chunk_ids[i : i + batch_size]
        batch_texts = chunk_texts[i : i + batch_size]
        batch_embeddings = embeddings_list[i : i + batch_size]
        batch_metadatas = chunk_metadatas[i : i + batch_size]

        if not quiet:
            print(f"DEBUG: Adding batch {i // batch_size + 1} ({len(batch_ids)} items) to store...", flush=True)

        vector_store.add(ids=batch_ids, documents=batch_texts, embeddings=batch_embeddings, metadatas=batch_metadatas)

        if not quiet:
            print(f"DEBUG: Current store count: {vector_store.count()}", flush=True)

        if (i // batch_size + 1) % 10 == 0:
            if not quiet:
                print(f"Indexed {min(i + batch_size, len(chunk_ids))} chunks...")

    if not quiet:
        print(f"Indexing completed. Total documents: {vector_store.count()}")

    # Finalize and display metrics
    metrics.finalize()
    if not quiet:
        print(metrics.report())

    return vector_store


def update_index(
    repo_path: str,
    vector_store: BaseVectorStore,
    embedding_provider: BaseEmbeddingProvider | None = None,
    exclude_dirs: list[str] | set[str] | None = None,
    include_patterns: list[str] | None = None,
    config: "RAGConfig | None" = None,
    quiet: bool = False,
) -> BaseVectorStore:
    """Update an existing index with new/modified files (true incremental).

    Uses FileTracker to detect changes and only re-index modified files.
    Deletes chunks for removed files.

    Args:
        repo_path: Path to the repository
        vector_store: Existing vector store to update
        embedding_provider: Provider for generating embeddings
        exclude_dirs: Directory names to exclude
        include_patterns: File patterns to include

    Returns:
        Updated VectorStore
    """
    from ..config import RAGConfig
    from ..embeddings.simple import SimpleEmbedding
    from .file_tracker import FileTracker, compute_file_hash

    repo = Path(repo_path)
    if not repo.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")
    repo_resolved = repo.resolve()

    if config is None:
        config = RAGConfig.from_env()

    is_databricks_store = vector_store.__class__.__name__ == "DatabricksVectorStore"

    # Guard: embedding dimension mismatch can hard-fail incremental updates (e.g. Chroma collection)
    # If the existing store has a dimension and it differs from the current embedding model,
    # reset the store so indexing can proceed.
    if not is_databricks_store and embedding_provider is not None:
        existing_dim = 0
        try:
            existing_dim = int(getattr(vector_store, "get_dimension", lambda: 0)())
        except Exception:
            existing_dim = 0

        current_dim = 0
        try:
            current_dim = int(getattr(embedding_provider, "dimension", 0) or 0)
        except Exception:
            current_dim = 0

        if current_dim <= 0:
            try:
                current_dim = len(embedding_provider.embed("dimension probe"))
            except Exception:
                current_dim = 0

        if existing_dim > 0 and current_dim > 0 and existing_dim != current_dim:
            print(
                f"⚠️  Embedding dimension mismatch for incremental update: store={existing_dim}D, model={current_dim}D. "
                "Resetting vector store collection to avoid corruption..."
            )
            reset_fn = getattr(vector_store, "reset", None)
            if callable(reset_fn):
                reset_fn()
            else:
                raise RuntimeError(
                    f"Vector store dimension mismatch (store={existing_dim}D, model={current_dim}D) and store has no reset(). "
                    "Run with --rebuild or delete the existing index."
                )

    # Tracker selection:
    # - Databricks store: use Delta manifest table (cross-machine, persistent)
    # - Other stores: use local FileTracker JSON
    persist_dir = getattr(vector_store, "persist_directory", ".rag_db")
    tracker = None
    dbx_tracker = None
    if is_databricks_store:
        from ..databricks_manifest import DatabricksManifestTracker

        dbx_tracker = DatabricksManifestTracker(
            schema=getattr(config, "databricks_schema", "default"),
            table=getattr(config, "databricks_manifest_table", "file_manifest"),
            repo=str(Path(repo_path).resolve()),
        )
    else:
        tracker = FileTracker(persist_dir=persist_dir)

    # Default exclude directories
    exclude_dirs_set: set[str]
    if exclude_dirs is None:
        exclude_dirs_set = {
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            ".idea",
            ".vscode",
            "dist",
            "build",
            ".tox",
            ".rag_db",
            ".rag_logs",
            "research_snapshots",
            "archival",
            "ui_backup",
            "ui_node_modules_orphan",
            "Hogwarts",
            "visualizations",
            "Arena",
            "datakit",
            "legacy_src",
            "artifacts",
            "analysis_report",
            "logs",
            "media",
            "assets",
            "temp",
            "rust",
            "interfaces",
            "acoustics",
            "awareness",
            "evolution",
            "motion",
        }
    else:
        exclude_dirs_set = set(exclude_dirs) if isinstance(exclude_dirs, list) else exclude_dirs

    # Load patterns from .agentignore
    agent_ignore = get_agent_ignore_patterns(
        str(repo_resolved if "repo_resolved" in locals() else repo_path if "repo_path" in locals() else ".")
    )
    if agent_ignore:
        exclude_dirs_set.update(agent_ignore)

    # Text file extensions
    text_extensions = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".md",
        ".txt",
        ".rst",
        ".yml",
        ".yaml",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
        ".cfg",
        ".ini",
        ".toml",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".m",
        ".pl",
        ".lua",
    }

    exclude_files = {
        "artifact.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
    }

    # Collect current files
    current_files = []
    for root, dirs, f_list in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in exclude_dirs_set]
        for f in f_list:
            file_path = Path(root) / f
            if file_path.name in exclude_files:
                continue
            if not is_text_file(file_path, text_extensions):
                continue
            try:
                if file_path.stat().st_size > 1024 * 1024:
                    continue
            except Exception:
                continue
            current_files.append(file_path)

    # Deterministic ordering helps stable progress and reproducibility
    current_files.sort(key=lambda p: str(p).lower())

    # Databricks manifest path: use remote manifest for deleted/changed detection
    if dbx_tracker is not None:
        from ..databricks_manifest import DatabricksFileState

        manifest = dbx_tracker.fetch_all()
        current_rel_paths = set()
        for p in current_files:
            rel_path_posix = str(p.relative_to(repo))
            current_rel_paths.add(Path(rel_path_posix).as_posix())

        deleted_paths = sorted([p for p in manifest.keys() if p not in current_rel_paths])
        for rel_path_str in deleted_paths:
            if not quiet:
                print(f"Removing chunks for deleted file: {rel_path_str}")
            try:
                vector_store.delete(where={"path": rel_path_str})
                vector_store.delete(where={"path": Path(rel_path_str).as_posix()})
            except Exception as e:
                if not quiet:
                    print(f"Warning: Could not delete chunks for {rel_path_str}: {e}")

        if deleted_paths:
            dbx_tracker.delete_paths(deleted_paths)

        # Detect changed/new files (fast path using size+mtime, hash only on mismatch)
        changed_files = []
        for p in current_files:
            rel_path = str(p.relative_to(repo))
            rel_path_str = Path(rel_path).as_posix()
            try:
                st = p.stat()
                size = int(st.st_size)
                mtime_ms = int(st.st_mtime * 1000)
            except Exception:
                continue

            prev = manifest.get(rel_path_str)
            if prev is not None and prev.file_size == size and prev.mtime_ms == mtime_ms:
                continue

            # Hash only when necessary
            file_hash = compute_file_hash(p)
            if prev is not None and prev.file_hash == file_hash:
                continue

            changed_files.append(p)

        if not changed_files:
            if not quiet:
                print("No changes detected. Index is up to date.")
            return vector_store

        if not quiet:
            print(f"Found {len(changed_files)} changed/new files to index")

        if embedding_provider is None:
            if not quiet:
                print("Warning: No embedding provider provided, using simple fallback")
            embedding_provider = SimpleEmbedding()

        updated_states = []
        for file_path in changed_files:
            rel_path = str(file_path.relative_to(repo))
            rel_path_str = Path(rel_path).as_posix()

            try:
                vector_store.delete(where={"path": rel_path})
                vector_store.delete(where={"path": rel_path_str})
            except Exception:
                pass

            content = read_file_content(file_path)
            if content is None or not content.strip():
                continue

            chunk_size_val = getattr(config, "chunk_size", 3000) if config else 3000
            chunk_overlap_val = getattr(config, "chunk_overlap", 300) if config else 300
            chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=chunk_size_val, chunk_overlap=chunk_overlap_val)
            semantic_chunks = chunker.chunk_file(content, rel_path_str)
            if not semantic_chunks:
                continue

            file_hash = compute_file_hash(file_path)
            try:
                st = file_path.stat()
                size = int(st.st_size)
                mtime_ms = int(st.st_mtime * 1000)
            except Exception:
                size = len(content)
                mtime_ms = 0

            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            embeddings_list = []

            for i, sc in enumerate(semantic_chunks):
                try:
                    if embedding_provider is None:
                        raise RuntimeError("Embedding provider is required")
                    emb = embedding_provider.embed(sc.content)
                    if isinstance(emb, list):
                        embeddings_list.append(emb)
                    else:
                        embeddings_list.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))

                    chunk_id = f"{rel_path_str}#{i}"
                    chunk_ids.append(chunk_id)
                    chunk_texts.append(sc.content)

                    metadata = {
                        "path": rel_path_str,
                        "chunk_index": i,
                        "type": "chunk",
                        "file_size": len(content),
                        "file_hash": file_hash,
                    }
                    metadata.update(sc.metadata)
                    chunk_metadatas.append(metadata)
                except Exception as e:
                    error_str = str(e).lower()
                    if "context length" in error_str or "exceeds" in error_str:
                        print(f"Warning: Skipping chunk {i} in {rel_path_str} - too long")
                        continue
                    raise

            if chunk_ids:
                vector_store.add(
                    ids=chunk_ids, documents=chunk_texts, embeddings=embeddings_list, metadatas=chunk_metadatas
                )
                updated_states.append(
                    DatabricksFileState(
                        repo=str(Path(repo_path).resolve()),
                        path=rel_path_str,
                        file_hash=file_hash,
                        file_size=size,
                        mtime_ms=mtime_ms,
                        chunk_count=len(chunk_ids),
                    )
                )
                if not quiet:
                    print(f"Indexed {len(chunk_ids)} chunks from {rel_path_str}")

        if updated_states and dbx_tracker is not None:
            dbx_tracker.upsert_states(updated_states)

        if not quiet:
            print(f"Incremental update completed. Total documents: {vector_store.count()}")
        return vector_store

    # Ensure tracker is available for non-Databricks path
    if tracker is None:
        raise RuntimeError("File tracker is required for non-Databricks vector stores")

    # Detect deleted files and remove their chunks
    deleted_files = tracker.get_deleted_files(repo, current_files)
    for rel_path in deleted_files:
        if not quiet:
            print(f"Removing chunks for deleted file: {rel_path}")
        try:
            # Backward/forward compatibility: older indexes may store Windows-style paths
            # while curated/normalized indexes store POSIX paths.
            vector_store.delete(where={"path": rel_path})
            vector_store.delete(where={"path": Path(rel_path).as_posix()})
        except Exception as e:
            if not quiet:
                print(f"Warning: Could not delete chunks for {rel_path}: {e}")
        tracker.remove_file(rel_path)

    # Detect changed files
    changed_files = tracker.get_changed_files(repo, current_files)

    if not changed_files:
        if not quiet:
            print("No changes detected. Index is up to date.")
        tracker.save()
        return vector_store

    if not quiet:
        print(f"Found {len(changed_files)} changed/new files to index")

    # Initialize embedding provider
    if embedding_provider is None:
        if not quiet:
            print("Warning: No embedding provider provided, using simple fallback")
        embedding_provider = SimpleEmbedding()

    # Process changed files
    for file_path in changed_files:
        rel_path = str(file_path.relative_to(repo))
        rel_path_str = Path(rel_path).as_posix()

        # Delete existing chunks for this file
        try:
            vector_store.delete(where={"path": rel_path})
            vector_store.delete(where={"path": rel_path_str})
        except Exception:
            pass  # May not exist

        # Read and chunk file
        content = read_file_content(file_path)
        if content is None or not content.strip():
            tracker.remove_file(rel_path)
            continue

        chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=3000, chunk_overlap=300)
        semantic_chunks = chunker.chunk_file(content, rel_path_str)
        if not semantic_chunks:
            tracker.remove_file(rel_path)
            continue

        # Compute hash
        file_hash = compute_file_hash(file_path)

        # Generate embeddings and add chunks
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        embeddings_list = []

        for i, sc in enumerate(semantic_chunks):
            try:
                if embedding_provider is None:
                    raise RuntimeError("Embedding provider is required")
                emb = embedding_provider.embed(sc.content)
                if isinstance(emb, list):
                    embeddings_list.append(emb)
                else:
                    embeddings_list.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))

                chunk_id = f"{rel_path_str}#{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(sc.content)
                metadata_base = {
                    "source": rel_path_str,
                    "chunk": i,
                    "total_chunks": len(semantic_chunks),
                }
                full_metadata = {
                    "path": rel_path_str,
                    "chunk_index": i,
                    "type": "chunk",
                    "file_size": len(content),
                    "file_hash": file_hash,
                    "indexed_at": (tracker.state.last_updated if tracker else "") or "",
                    **metadata_base,
                }
                full_metadata.update(sc.metadata)
                chunk_metadatas.append(full_metadata)
            except Exception as e:
                error_str = str(e).lower()
                if "context length" in error_str or "exceeds" in error_str:
                    print(f"Warning: Skipping chunk {i} in {rel_path} - too long")
                    continue
                raise

        if chunk_ids:
            vector_store.add(
                ids=chunk_ids, documents=chunk_texts, embeddings=embeddings_list, metadatas=chunk_metadatas
            )
            tracker.update_file(rel_path, file_hash, len(content), len(chunk_ids))
            print(f"Indexed {len(chunk_ids)} chunks from {rel_path}")

    # Save tracker state after successful indexing
    tracker.save()

    print(f"Incremental update completed. Total documents: {vector_store.count()}")
    return vector_store
