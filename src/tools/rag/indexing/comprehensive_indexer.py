"""
Comprehensive NLP-Optimized Indexer with Rich CLI for GRID RAG.

This module provides a sophisticated indexing pipeline that:
1. Uses BGE-M3 or all-MiniLM-L6-v2 for high-quality embeddings
2. Implements NLP-aware chunking for natural, simple responses
3. Rich CLI with beautiful progress bars and time estimates
4. Comprehensive codebase indexing with context preservation
5. Function call interface for workflow integration

The goal: Enable the system to answer complex technical questions
with simple, natural language by deeply understanding the codebase.

Usage:
    # CLI
    python -m tools.rag.comprehensive_indexer index /path/to/repo

    # Python API
    from tools.rag.comprehensive_indexer import comprehensive_index
    comprehensive_index("/path/to/repo")
"""

import asyncio
import hashlib
import json
import os
import re
import sys
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# Rich imports for beautiful CLI
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Add grid root to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root))


class EmbeddingModelType(Enum):
    """Supported embedding models."""

    BGE_M3 = "BAAI/bge-m3"  # Best open-source, 1024 dim, multilingual
    BGE_LARGE = "BAAI/bge-large-en-v1.5"  # Good for English, 1024 dim
    MINILM_L6 = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, 384 dim
    MINILM_L12 = "sentence-transformers/all-MiniLM-L12-v2"  # Better, 384 dim
    NOMIC = "nomic-ai/nomic-embed-text-v1.5"  # Ollama compatible
    E5_LARGE = "intfloat/e5-large-v2"  # Strong retrieval, 1024 dim


class ContentType(Enum):
    """Content types for adaptive chunking."""

    CODE_PYTHON = "python"
    CODE_JAVASCRIPT = "javascript"
    CODE_RUST = "rust"
    CODE_OTHER = "code_other"
    MARKDOWN = "markdown"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    DATA = "data"
    UNKNOWN = "unknown"


@dataclass
class ChunkMetadata:
    """Rich metadata for each chunk enabling NLP understanding."""

    chunk_id: str
    file_path: str
    content_type: ContentType
    start_line: int
    end_line: int

    # NLP context
    summary: str  # Brief description of chunk content
    symbols: list[str]  # Functions, classes, variables defined
    imports: list[str]  # Dependencies
    references: list[str]  # Cross-references to other files/symbols

    # Hierarchy
    parent_section: str | None = None  # e.g., class name for methods
    document_title: str | None = None  # File-level title/description

    # Quality metrics
    semantic_density: float = 0.0  # How information-dense
    code_ratio: float = 0.0  # % that is code vs comments

    # Timestamps
    indexed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage (ChromaDB compatible)."""
        # ChromaDB only accepts str, int, float, bool, or None
        # Convert lists to comma-separated strings
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "content_type": self.content_type.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "summary": self.summary[:500] if self.summary else "",  # Limit summary length
            "symbols": ",".join(self.symbols) if self.symbols else "",
            "imports": ",".join(self.imports) if self.imports else "",
            "references": ",".join(self.references) if self.references else "",
            "parent_section": self.parent_section or "",
            "document_title": self.document_title or "",
            "semantic_density": self.semantic_density,
            "code_ratio": self.code_ratio,
            "indexed_at": self.indexed_at,
        }


@dataclass
class IndexingStats:
    """Comprehensive indexing statistics."""

    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    # File counts
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0

    # Chunk counts
    total_chunks: int = 0
    code_chunks: int = 0
    doc_chunks: int = 0
    config_chunks: int = 0

    # Size metrics
    total_bytes: int = 0
    total_tokens_approx: int = 0

    # Quality metrics
    avg_chunk_size: float = 0.0
    avg_semantic_density: float = 0.0

    # Skip reasons
    skip_reasons: dict[str, int] = field(default_factory=dict)

    # Embedding info
    embedding_model: str = ""
    embedding_dimension: int = 0

    @property
    def duration(self) -> timedelta:
        """Calculate total duration."""
        end = self.end_time or datetime.now()
        return end - self.start_time

    @property
    def chunks_per_second(self) -> float:
        """Calculate indexing throughput."""
        secs = self.duration.total_seconds()
        return self.total_chunks / secs if secs > 0 else 0.0

    def add_skip(self, reason: str) -> None:
        """Track skip reason."""
        self.skip_reasons[reason] = self.skip_reasons.get(reason, 0) + 1
        self.skipped_files += 1

    def finalize(self) -> None:
        """Mark indexing complete."""
        self.end_time = datetime.now()
        if self.total_chunks > 0:
            # These would be calculated from actual chunks
            pass


class NLPChunker:
    """
    NLP-aware chunker that creates chunks optimized for natural language responses.

    Key principles:
    1. Preserve semantic coherence (don't split mid-concept)
    2. Include context (what file, what class, what does it do)
    3. Extract structured information (symbols, imports, references)
    4. Balance chunk size for optimal embedding
    """

    # Optimal chunk sizes by content type
    CHUNK_SIZES = {
        ContentType.CODE_PYTHON: (600, 1200),  # (min, max) chars
        ContentType.CODE_JAVASCRIPT: (600, 1200),
        ContentType.CODE_RUST: (600, 1200),
        ContentType.CODE_OTHER: (500, 1000),
        ContentType.MARKDOWN: (400, 800),
        ContentType.DOCUMENTATION: (400, 800),
        ContentType.CONFIG: (300, 600),
        ContentType.DATA: (200, 500),
        ContentType.UNKNOWN: (400, 800),
    }

    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1500):
        """Initialize chunker."""
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # Patterns for extracting information
        self.python_class_pattern = re.compile(r"^class\s+(\w+)")
        self.python_func_pattern = re.compile(r"^(?:async\s+)?def\s+(\w+)")
        self.python_import_pattern = re.compile(r"^(?:from\s+([\w.]+)\s+)?import\s+(.+)")
        self.markdown_header_pattern = re.compile(r"^(#{1,6})\s+(.+)")
        self.docstring_pattern = re.compile(r'"""(.+?)"""', re.DOTALL)

    def detect_content_type(self, file_path: Path) -> ContentType:
        """Detect content type from file extension and content."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        # Code files
        if suffix == ".py":
            return ContentType.CODE_PYTHON
        elif suffix in (".js", ".ts", ".jsx", ".tsx"):
            return ContentType.CODE_JAVASCRIPT
        elif suffix == ".rs":
            return ContentType.CODE_RUST
        elif suffix in (".c", ".cpp", ".h", ".hpp", ".go", ".java", ".rb", ".php"):
            return ContentType.CODE_OTHER

        # Documentation
        elif suffix == ".md":
            return ContentType.MARKDOWN
        elif suffix in (".rst", ".txt", ".adoc"):
            return ContentType.DOCUMENTATION

        # Config
        elif suffix in (".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"):
            return ContentType.CONFIG
            return ContentType.CONFIG

        # Data
        elif suffix in (".csv", ".xml"):
            return ContentType.DATA

        return ContentType.UNKNOWN

    def chunk_file(
        self,
        file_path: Path,
        content: str,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """
        Chunk a file with NLP-aware boundaries and rich metadata.

        Yields: (chunk_text, chunk_metadata) tuples
        """
        content_type = self.detect_content_type(file_path)
        min_size, max_size = self.CHUNK_SIZES.get(content_type, (400, 800))

        # Extract file-level information
        doc_title = self._extract_document_title(content, content_type, file_path)

        # Choose chunking strategy based on content type
        if content_type == ContentType.CODE_PYTHON:
            yield from self._chunk_python(file_path, content, doc_title, min_size, max_size)
        elif content_type == ContentType.MARKDOWN:
            yield from self._chunk_markdown(file_path, content, doc_title, min_size, max_size)
        elif content_type in (ContentType.CODE_JAVASCRIPT, ContentType.CODE_RUST, ContentType.CODE_OTHER):
            yield from self._chunk_code_generic(file_path, content, content_type, doc_title, min_size, max_size)
        else:
            yield from self._chunk_generic(file_path, content, content_type, doc_title, min_size, max_size)

    def _extract_document_title(
        self,
        content: str,
        content_type: ContentType,
        file_path: Path,
    ) -> str:
        """Extract document title/description."""
        lines = content.split("\n")[:20]  # First 20 lines

        if content_type == ContentType.CODE_PYTHON:
            # Look for module docstring
            match = self.docstring_pattern.search("\n".join(lines))
            if match:
                docstring = match.group(1).strip()
                # Get first line/sentence
                first_line = docstring.split("\n")[0].strip()
                if len(first_line) > 10:
                    return first_line[:200]

        elif content_type == ContentType.MARKDOWN:
            # Look for first header
            for line in lines:
                match = self.markdown_header_pattern.match(line)
                if match:
                    return match.group(2).strip()[:200]

        # Fallback to filename
        return file_path.stem.replace("_", " ").replace("-", " ").title()

    def _chunk_python(
        self,
        file_path: Path,
        content: str,
        doc_title: str,
        min_size: int,
        max_size: int,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Chunk Python code with class/function awareness."""
        lines = content.split("\n")

        # Extract imports first
        imports = self._extract_python_imports(content)

        # Find class and function boundaries
        boundaries = self._find_python_boundaries(lines)

        if not boundaries:
            # No classes/functions, chunk by size
            yield from self._chunk_by_size(
                file_path, content, ContentType.CODE_PYTHON, doc_title, min_size, max_size, imports
            )
            return

        # Chunk by class/function
        for _i, (start_line, end_line, symbol_name, parent) in enumerate(boundaries):
            chunk_lines = lines[start_line : end_line + 1]
            chunk_text = "\n".join(chunk_lines)

            # Skip tiny chunks
            if len(chunk_text) < self.min_chunk_size:
                continue

            # Split large chunks
            if len(chunk_text) > self.max_chunk_size:
                yield from self._split_large_chunk(
                    file_path,
                    chunk_text,
                    ContentType.CODE_PYTHON,
                    doc_title,
                    start_line,
                    end_line,
                    [symbol_name],
                    imports,
                    parent,
                )
                continue

            # Generate chunk ID
            chunk_id = self._generate_chunk_id(str(file_path), start_line, chunk_text)

            # Extract symbols and references
            symbols = [symbol_name] if symbol_name else []
            references = self._extract_references(chunk_text)

            # Calculate metrics
            code_ratio = self._calculate_code_ratio(chunk_text)
            semantic_density = self._calculate_semantic_density(chunk_text)

            # Create summary
            summary = self._generate_summary(chunk_text, symbols, ContentType.CODE_PYTHON)

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                file_path=str(file_path),
                content_type=ContentType.CODE_PYTHON,
                start_line=start_line + 1,  # 1-indexed
                end_line=end_line + 1,
                summary=summary,
                symbols=symbols,
                imports=imports,
                references=references,
                parent_section=parent,
                document_title=doc_title,
                semantic_density=semantic_density,
                code_ratio=code_ratio,
            )

            yield chunk_text, metadata

    def _find_python_boundaries(
        self,
        lines: list[str],
    ) -> list[tuple[int, int, str, str | None]]:
        """Find class and function boundaries in Python code."""
        boundaries = []
        current_class = None
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # Check for class definition
            class_match = self.python_class_pattern.match(stripped)
            if class_match and indent == 0:
                class_name = class_match.group(1)
                # Find class end
                end = self._find_block_end(lines, i, 0)
                boundaries.append((i, end, class_name, None))
                current_class = class_name
                i = end + 1
                continue

            # Check for function definition
            func_match = self.python_func_pattern.match(stripped)
            if func_match:
                func_name = func_match.group(1)
                # Find function end
                end = self._find_block_end(lines, i, indent)
                parent = current_class if indent > 0 else None
                boundaries.append((i, end, func_name, parent))
                i = end + 1
                continue

            i += 1

        return boundaries

    def _find_block_end(
        self,
        lines: list[str],
        start: int,
        base_indent: int,
    ) -> int:
        """Find the end of a Python code block."""
        for i in range(start + 1, len(lines)):
            line = lines[i]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Check indent
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                return i - 1

        return len(lines) - 1

    def _extract_python_imports(self, content: str) -> list[str]:
        """Extract import statements from Python code."""
        imports = []
        for match in self.python_import_pattern.finditer(content):
            if match.group(1):
                imports.append(match.group(1))
            imports.extend([imp.strip().split(" as ")[0] for imp in match.group(2).split(",")])
        return list(set(imports))[:10]  # Limit to 10

    def _chunk_markdown(
        self,
        file_path: Path,
        content: str,
        doc_title: str,
        min_size: int,
        max_size: int,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Chunk Markdown by headers."""
        lines = content.split("\n")
        sections = []
        current_start = 0
        current_header = doc_title

        for i, line in enumerate(lines):
            match = self.markdown_header_pattern.match(line)
            if match and i > 0:
                # Save previous section
                if i > current_start:
                    sections.append((current_start, i - 1, current_header))
                current_start = i
                current_header = match.group(2).strip()

        # Add last section
        if current_start < len(lines):
            sections.append((current_start, len(lines) - 1, current_header))

        # Generate chunks from sections
        for start_line, end_line, header in sections:
            chunk_lines = lines[start_line : end_line + 1]
            chunk_text = "\n".join(chunk_lines)

            if len(chunk_text) < self.min_chunk_size:
                continue

            # Split large sections
            if len(chunk_text) > self.max_chunk_size:
                yield from self._split_large_chunk(
                    file_path, chunk_text, ContentType.MARKDOWN, doc_title, start_line, end_line, [header], [], None
                )
                continue

            chunk_id = self._generate_chunk_id(str(file_path), start_line, chunk_text)
            references = self._extract_references(chunk_text)

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                file_path=str(file_path),
                content_type=ContentType.MARKDOWN,
                start_line=start_line + 1,
                end_line=end_line + 1,
                summary=f"Documentation section: {header}",
                symbols=[header],
                imports=[],
                references=references,
                parent_section=None,
                document_title=doc_title,
                semantic_density=self._calculate_semantic_density(chunk_text),
                code_ratio=self._calculate_code_ratio(chunk_text),
            )

            yield chunk_text, metadata

    def _chunk_code_generic(
        self,
        file_path: Path,
        content: str,
        content_type: ContentType,
        doc_title: str,
        min_size: int,
        max_size: int,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Generic code chunking (for JS, Rust, etc.)."""
        yield from self._chunk_by_size(file_path, content, content_type, doc_title, min_size, max_size, [])

    def _chunk_generic(
        self,
        file_path: Path,
        content: str,
        content_type: ContentType,
        doc_title: str,
        min_size: int,
        max_size: int,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Generic chunking by size with overlap."""
        yield from self._chunk_by_size(file_path, content, content_type, doc_title, min_size, max_size, [])

    def _chunk_by_size(
        self,
        file_path: Path,
        content: str,
        content_type: ContentType,
        doc_title: str,
        min_size: int,
        max_size: int,
        imports: list[str],
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Chunk by size with smart boundaries (paragraph/line breaks)."""
        lines = content.split("\n")
        current_chunk_lines = []
        current_chunk_size = 0
        start_line = 0

        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline

            # Check if adding this line exceeds max
            if current_chunk_size + line_size > max_size and current_chunk_lines:
                # Emit current chunk
                chunk_text = "\n".join(current_chunk_lines)
                if len(chunk_text) >= min_size:
                    yield from self._emit_chunk(
                        file_path, chunk_text, content_type, doc_title, start_line, i - 1, imports
                    )

                # Start new chunk with overlap (last 2 lines)
                overlap = current_chunk_lines[-2:] if len(current_chunk_lines) >= 2 else []
                current_chunk_lines = overlap + [line]
                current_chunk_size = sum(len(l) + 1 for l in current_chunk_lines)
                start_line = i - len(overlap)
            else:
                current_chunk_lines.append(line)
                current_chunk_size += line_size

        # Emit final chunk
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines)
            if len(chunk_text) >= min_size:
                yield from self._emit_chunk(
                    file_path, chunk_text, content_type, doc_title, start_line, len(lines) - 1, imports
                )

    def _emit_chunk(
        self,
        file_path: Path,
        chunk_text: str,
        content_type: ContentType,
        doc_title: str,
        start_line: int,
        end_line: int,
        imports: list[str],
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Emit a single chunk with metadata."""
        chunk_id = self._generate_chunk_id(str(file_path), start_line, chunk_text)
        symbols = self._extract_symbols(chunk_text, content_type)
        references = self._extract_references(chunk_text)

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            file_path=str(file_path),
            content_type=content_type,
            start_line=start_line + 1,
            end_line=end_line + 1,
            summary=self._generate_summary(chunk_text, symbols, content_type),
            symbols=symbols,
            imports=imports,
            references=references,
            document_title=doc_title,
            semantic_density=self._calculate_semantic_density(chunk_text),
            code_ratio=self._calculate_code_ratio(chunk_text),
        )

        yield chunk_text, metadata

    def _split_large_chunk(
        self,
        file_path: Path,
        chunk_text: str,
        content_type: ContentType,
        doc_title: str,
        start_line: int,
        end_line: int,
        symbols: list[str],
        imports: list[str],
        parent: str | None,
    ) -> Generator[tuple[str, ChunkMetadata]]:
        """Split a large chunk into smaller pieces."""
        lines = chunk_text.split("\n")
        num_lines = len(lines)

        # Calculate lines per chunk
        chars_per_line = len(chunk_text) / num_lines if num_lines > 0 else 50
        target_lines = int(self.max_chunk_size / chars_per_line)

        for i in range(0, num_lines, target_lines):
            sub_lines = lines[i : i + target_lines]
            sub_text = "\n".join(sub_lines)

            if len(sub_text) < self.min_chunk_size:
                continue

            sub_start = start_line + i
            sub_end = start_line + min(i + target_lines, num_lines) - 1

            chunk_id = self._generate_chunk_id(str(file_path), sub_start, sub_text)
            sub_symbols = self._extract_symbols(sub_text, content_type)

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                file_path=str(file_path),
                content_type=content_type,
                start_line=sub_start + 1,
                end_line=sub_end + 1,
                summary=self._generate_summary(sub_text, sub_symbols or symbols, content_type),
                symbols=sub_symbols or symbols,
                imports=imports,
                references=self._extract_references(sub_text),
                parent_section=parent,
                document_title=doc_title,
                semantic_density=self._calculate_semantic_density(sub_text),
                code_ratio=self._calculate_code_ratio(sub_text),
            )

            yield sub_text, metadata

    def _extract_symbols(self, text: str, content_type: ContentType) -> list[str]:
        """Extract defined symbols from text."""
        symbols = []

        if content_type == ContentType.CODE_PYTHON:
            # Classes
            for match in self.python_class_pattern.finditer(text):
                symbols.append(match.group(1))
            # Functions
            for match in self.python_func_pattern.finditer(text):
                symbols.append(match.group(1))

        return symbols[:10]  # Limit

    def _extract_references(self, text: str) -> list[str]:
        """Extract references to other files/symbols."""
        references = []

        # Markdown links
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            url = match.group(2)
            if not url.startswith("http"):
                references.append(url)

        # Python imports (simplified)
        for match in re.finditer(r"from\s+([\w.]+)\s+import", text):
            references.append(match.group(1))

        # File paths in quotes/backticks
        for match in re.finditer(r'[`"\']([a-zA-Z0-9_/\\.-]+\.\w{1,4})[`"\']', text):
            references.append(match.group(1))

        return list(set(references))[:10]

    def _generate_summary(
        self,
        text: str,
        symbols: list[str],
        content_type: ContentType,
    ) -> str:
        """Generate a brief summary of the chunk content."""
        # Look for docstring or first comment
        lines = text.strip().split("\n")

        if content_type == ContentType.CODE_PYTHON:
            # Check for docstring
            match = self.docstring_pattern.search(text[:500])
            if match:
                docstring = match.group(1).strip()
                first_line = docstring.split("\n")[0].strip()
                if len(first_line) > 10:
                    return first_line[:150]

            # Check for comment
            for line in lines[:5]:
                if line.strip().startswith("#") and not line.strip().startswith("#!"):
                    comment = line.strip()[1:].strip()
                    if len(comment) > 10:
                        return comment[:150]

        # Fallback: describe symbols
        if symbols:
            symbol_type = "function" if content_type in (ContentType.CODE_PYTHON,) else "section"
            return f"Defines {symbol_type}: {', '.join(symbols[:3])}"

        # Last resort
        return f"Code segment from {content_type.value} file"

    def _calculate_code_ratio(self, text: str) -> float:
        """Calculate ratio of code vs comments/whitespace."""
        lines = text.split("\n")
        code_lines = 0
        total_lines = 0

        for line in lines:
            stripped = line.strip()
            if stripped:
                total_lines += 1
                if not stripped.startswith(("#", "//", "/*", "*", "'''", '"""')):
                    code_lines += 1

        return code_lines / total_lines if total_lines > 0 else 0.0

    def _calculate_semantic_density(self, text: str) -> float:
        """Estimate semantic information density."""
        # Simple heuristic: unique words / total words
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0

        unique_words = set(words)
        return len(unique_words) / len(words)

    def _generate_chunk_id(self, file_path: str, start_line: int, content: str) -> str:
        """Generate unique chunk ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"chunk_{hashlib.md5(file_path.encode()).hexdigest()[:8]}_{start_line}_{content_hash}"


class HuggingFaceEmbedder:
    """
    HuggingFace sentence-transformers based embedder.

    Uses BGE-M3 or all-MiniLM-L6-v2 for high-quality embeddings.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "auto",
        batch_size: int = 32,
    ):
        """Initialize embedder with specified model."""
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.dimension = 0

        # Model dimensions
        self.MODEL_DIMS = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-MiniLM-L12-v2": 384,
            "BAAI/bge-m3": 1024,
            "BAAI/bge-large-en-v1.5": 1024,
            "intfloat/e5-large-v2": 1024,
        }

        self._load_model(device)

    def _load_model(self, device: str) -> None:
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            # Determine device
            if device == "auto":
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"

            self.model = SentenceTransformer(self.model_name, device=device)
            self.dimension = self.MODEL_DIMS.get(self.model_name, 384)

        except ImportError as e:
            raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers") from e

    def embed(self, text: str) -> list[float]:
        """Embed a single text."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    async def async_embed(self, text: str) -> list[float]:
        """Async embed (runs sync in executor)."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed, text)

    async def async_embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Async batch embed."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_batch, texts)


class RichProgressDisplay:
    """Beautiful Rich CLI progress display for indexing."""

    def __init__(self):
        """Initialize Rich display."""
        if not RICH_AVAILABLE:
            raise ImportError("Rich is required for progress display. Install with: pip install rich")

        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        self.stats = IndexingStats()
        self.current_file = ""
        self.live = None

    def create_header_panel(self) -> Panel:
        """Create header panel."""
        header = Text()
        header.append("🔍 ", style="bold")
        header.append("GRID Comprehensive Indexer", style="bold cyan")
        header.append("\n")
        header.append("NLP-Optimized • Rich Context • Deep Understanding", style="dim")
        return Panel(header, border_style="cyan")

    def create_stats_table(self) -> Table:
        """Create live stats table."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="dim")
        table.add_column("Value", style="bold")

        duration = self.stats.duration.total_seconds()
        throughput = self.stats.total_chunks / duration if duration > 0 else 0

        table.add_row("📁 Files Processed", f"{self.stats.processed_files}")
        table.add_row("📦 Chunks Created", f"{self.stats.total_chunks}")
        table.add_row("⚡ Throughput", f"{throughput:.1f} chunks/s")
        table.add_row(
            "📄 Current", f"{self.current_file[:50]}..." if len(self.current_file) > 50 else self.current_file
        )

        return table

    def create_layout(self) -> Layout:
        """Create full layout."""
        layout = Layout()
        layout.split_column(
            Layout(self.create_header_panel(), size=4),
            Layout(name="progress", size=3),
            Layout(self.create_stats_table(), size=6),
        )
        return layout

    def start(self) -> None:
        """Start live display."""
        self.console.print(self.create_header_panel())
        self.progress.start()

    def stop(self) -> None:
        """Stop live display."""
        self.progress.stop()

    def add_task(self, description: str, total: int) -> TaskID:
        """Add a progress task."""
        return self.progress.add_task(description, total=total)

    def update_task(self, task_id: TaskID, advance: int = 1, **kwargs) -> None:
        """Update task progress."""
        self.progress.update(task_id, advance=advance, **kwargs)

    def update_stats(self, current_file: str = "", **updates) -> None:
        """Update statistics."""
        self.current_file = current_file
        for key, value in updates.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)

    def print_summary(self) -> None:
        """Print final summary."""
        self.stats.finalize()

        summary = Table(title="📊 Indexing Complete", box=None)
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="bold green")

        summary.add_row("Duration", f"{self.stats.duration.total_seconds():.1f}s")
        summary.add_row("Files Processed", str(self.stats.processed_files))
        summary.add_row("Files Skipped", str(self.stats.skipped_files))
        summary.add_row("Total Chunks", str(self.stats.total_chunks))
        summary.add_row("Code Chunks", str(self.stats.code_chunks))
        summary.add_row("Doc Chunks", str(self.stats.doc_chunks))
        summary.add_row("Throughput", f"{self.stats.chunks_per_second:.1f} chunks/s")
        summary.add_row("Embedding Model", self.stats.embedding_model)
        summary.add_row("Embedding Dims", str(self.stats.embedding_dimension))

        self.console.print()
        self.console.print(Panel(summary, border_style="green"))

        if self.stats.skip_reasons:
            skip_table = Table(title="⏭️ Skip Reasons", box=None)
            skip_table.add_column("Reason", style="yellow")
            skip_table.add_column("Count", style="bold")
            for reason, count in sorted(self.stats.skip_reasons.items(), key=lambda x: x[1], reverse=True):
                skip_table.add_row(reason, str(count))
            self.console.print(skip_table)


def get_files_to_index(
    repo_path: Path,
    exclude_patterns: list[str] | None = None,
    include_patterns: list[str] | None = None,
) -> Generator[Path]:
    """Get all files to index from repository."""
    exclude_patterns = exclude_patterns or []
    include_patterns = include_patterns or []

    # Default excludes
    default_excludes = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "dist",
        "build",
        ".egg-info",
        ".rag_db",
        ".eggs",
        "htmlcov",
        ".coverage",
    }

    # Default includes (file extensions)
    default_includes = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".rs",
        ".go",
        ".java",
        ".md",
        ".rst",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
    }

    for root, dirs, files in os.walk(repo_path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in default_excludes]

        for file in files:
            file_path = Path(root) / file

            # Check extension
            if file_path.suffix.lower() not in default_includes:
                continue

            # Check size (skip very large files)
            try:
                if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                    continue
            except OSError:
                continue

            yield file_path


async def comprehensive_index(
    repo_path: str,
    db_path: str = ".rag_db",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    rebuild: bool = False,
    quiet: bool = False,
) -> IndexingStats:
    """
    Comprehensively index a repository for intelligent RAG.

    This is the main function call interface for workflow integration.

    Args:
        repo_path: Path to repository
        db_path: Path to vector database
        embedding_model: HuggingFace model to use
        rebuild: Whether to rebuild from scratch
        quiet: Suppress progress output

    Returns:
        IndexingStats with complete indexing metrics
    """
    repo = Path(repo_path).resolve()
    if not repo.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")

    # Initialize components
    chunker = NLPChunker()
    embedder = HuggingFaceEmbedder(model_name=embedding_model)

    # Initialize vector store
    from tools.rag.vector_store.chromadb_store import ChromaDBVectorStore

    vector_store = ChromaDBVectorStore(
        collection_name="grid_comprehensive",
        persist_directory=db_path,
    )

    if rebuild:
        vector_store.clear()

    # Get files
    files = list(get_files_to_index(repo))
    total_files = len(files)

    # Initialize progress display
    display = None
    if not quiet and RICH_AVAILABLE:
        display = RichProgressDisplay()
        display.stats.embedding_model = embedding_model
        display.stats.embedding_dimension = embedder.dimension
        display.stats.total_files = total_files
        display.start()
        file_task = display.add_task("📁 Processing files", total=total_files)
    else:
        stats = IndexingStats()
        stats.embedding_model = embedding_model
        stats.embedding_dimension = embedder.dimension
        stats.total_files = total_files

    # Process files
    all_chunks = []
    all_embeddings = []
    all_metadatas = []
    all_ids = []

    batch_size = 50  # Embedding batch size

    for _i, file_path in enumerate(files):
        rel_path = file_path.relative_to(repo)

        if display:
            display.update_stats(current_file=str(rel_path))

        try:
            # Read file
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if len(content) < 50:  # Skip tiny files
                if display:
                    display.stats.add_skip("too_small")
                else:
                    stats.add_skip("too_small")
                continue

            # Chunk file
            for chunk_text, metadata in chunker.chunk_file(file_path, content):
                all_chunks.append(chunk_text)
                all_metadatas.append(metadata.to_dict())
                all_ids.append(metadata.chunk_id)

                # Track chunk types
                if display:
                    if metadata.content_type in (
                        ContentType.CODE_PYTHON,
                        ContentType.CODE_JAVASCRIPT,
                        ContentType.CODE_RUST,
                        ContentType.CODE_OTHER,
                    ):
                        display.stats.code_chunks += 1
                    elif metadata.content_type in (ContentType.MARKDOWN, ContentType.DOCUMENTATION):
                        display.stats.doc_chunks += 1
                    else:
                        display.stats.config_chunks += 1
                    display.stats.total_chunks += 1
                else:
                    if metadata.content_type in (ContentType.CODE_PYTHON, ContentType.CODE_JAVASCRIPT):
                        stats.code_chunks += 1
                    elif metadata.content_type in (ContentType.MARKDOWN, ContentType.DOCUMENTATION):
                        stats.doc_chunks += 1
                    stats.total_chunks += 1

            if display:
                display.stats.processed_files += 1
            else:
                stats.processed_files += 1

            # Batch embed when we have enough
            if len(all_chunks) >= batch_size:
                embeddings = embedder.embed_batch(all_chunks)
                all_embeddings.extend(embeddings)

                # Store in vector store
                vector_store.add(
                    ids=all_ids[: len(embeddings)],
                    documents=all_chunks[: len(embeddings)],
                    embeddings=embeddings,
                    metadatas=all_metadatas[: len(embeddings)],
                )

                # Clear batches
                all_chunks = all_chunks[len(embeddings) :]
                all_metadatas = all_metadatas[len(embeddings) :]
                all_ids = all_ids[len(embeddings) :]

        except Exception as e:
            if display:
                display.stats.add_skip(f"error: {type(e).__name__}")
                display.stats.failed_files += 1
            else:
                stats.add_skip(f"error: {type(e).__name__}")
                stats.failed_files += 1

        if display:
            display.update_task(file_task)

    # Process remaining chunks
    if all_chunks:
        embeddings = embedder.embed_batch(all_chunks)
        vector_store.add(
            ids=all_ids,
            documents=all_chunks,
            embeddings=embeddings,
            metadatas=all_metadatas,
        )

    # Finalize
    if display:
        display.stop()
        display.print_summary()
        return display.stats
    else:
        stats.finalize()
        return stats


def index_sync(
    repo_path: str,
    db_path: str = ".rag_db",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    rebuild: bool = False,
    quiet: bool = False,
) -> IndexingStats:
    """Synchronous wrapper for comprehensive_index."""
    return asyncio.run(
        comprehensive_index(
            repo_path=repo_path,
            db_path=db_path,
            embedding_model=embedding_model,
            rebuild=rebuild,
            quiet=quiet,
        )
    )


# =============================================================================
# CONVENIENT FUNCTION CALL INTERFACE FOR WORKFLOW INTEGRATION
# =============================================================================


def index_codebase(
    path: str = ".",
    model: str = "auto",
    rebuild: bool = False,
) -> dict[str, Any]:
    """
    🔍 Index a codebase for intelligent RAG - Simple workflow function.

    This is the primary function call for integrating indexing into workflows.
    Call this once to comprehensively index, then use incremental updates.

    Args:
        path: Path to codebase (default: current directory)
        model: Embedding model - "auto", "fast", "quality", or full model name
               - "auto": Uses all-MiniLM-L6-v2 (good balance)
               - "fast": Uses all-MiniLM-L6-v2 (384 dim, fastest)
               - "quality": Uses BGE-M3 (1024 dim, best quality)
        rebuild: If True, clears existing index first

    Returns:
        Dictionary with indexing results:
        {
            "success": bool,
            "files_processed": int,
            "chunks_created": int,
            "duration_seconds": float,
            "embedding_model": str,
            "db_path": str
        }

    Example:
        # Simple indexing
        result = index_codebase(".")

        # High quality indexing
        result = index_codebase(".", model="quality", rebuild=True)

        # In a workflow
        if not index_exists():
            index_codebase(".", rebuild=True)
    """
    # Model selection
    MODEL_MAP = {
        "auto": "sentence-transformers/all-MiniLM-L6-v2",
        "fast": "sentence-transformers/all-MiniLM-L6-v2",
        "quality": "BAAI/bge-m3",
        "bge": "BAAI/bge-m3",
        "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    }

    embedding_model = MODEL_MAP.get(model.lower(), model)
    db_path = ".rag_db_comprehensive"

    try:
        stats = index_sync(
            repo_path=path,
            db_path=db_path,
            embedding_model=embedding_model,
            rebuild=rebuild,
            quiet=False,
        )

        return {
            "success": True,
            "files_processed": stats.processed_files,
            "chunks_created": stats.total_chunks,
            "code_chunks": stats.code_chunks,
            "doc_chunks": stats.doc_chunks,
            "duration_seconds": stats.duration.total_seconds(),
            "throughput_chunks_per_sec": stats.chunks_per_second,
            "embedding_model": embedding_model,
            "embedding_dimension": stats.embedding_dimension,
            "db_path": db_path,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


def quick_index(path: str = ".") -> bool:
    """
    ⚡ Quick index - fastest way to index a codebase.

    Returns True if successful, False otherwise.
    Uses the fast MiniLM model for quick indexing.

    Example:
        if quick_index("."):
            print("Ready to query!")
    """
    result = index_codebase(path=path, model="fast", rebuild=True)
    return result.get("success", False)


def quality_index(path: str = ".") -> bool:
    """
    🎯 Quality index - highest quality embeddings for best retrieval.

    Uses BGE-M3 (1024 dimensions) for maximum semantic understanding.
    Takes longer but produces better results for complex queries.

    Returns True if successful, False otherwise.
    """
    result = index_codebase(path=path, model="quality", rebuild=True)
    return result.get("success", False)


def incremental_index(
    path: str = ".",
    files: list[str] | None = None,
) -> dict[str, Any]:
    """
    📝 Incremental index - add/update specific files without full rebuild.

    Use this for regular workflow updates after initial comprehensive index.

    Args:
        path: Base path
        files: Optional list of specific files to index (relative to path)
               If None, indexes all changed files since last index

    Returns:
        Dictionary with update results
    """
    # For now, just do a regular index without rebuild
    # Future: implement smart diffing
    return index_codebase(path=path, model="auto", rebuild=False)


def index_exists(db_path: str = ".rag_db_comprehensive") -> bool:
    """Check if an index already exists."""
    return Path(db_path).exists() and any(Path(db_path).iterdir())


def get_index_stats(db_path: str = ".rag_db_comprehensive") -> dict[str, Any]:
    """Get statistics about an existing index."""
    try:
        from tools.rag.vector_store.chromadb_store import ChromaDBVectorStore

        store = ChromaDBVectorStore(
            collection_name="grid_comprehensive",
            persist_directory=db_path,
        )

        count = store.count()
        return {
            "exists": True,
            "chunk_count": count,
            "db_path": db_path,
        }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e),
        }


# CLI Entry Point
def main():
    """CLI entry point for comprehensive indexer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🔍 GRID Comprehensive Indexer - NLP-Optimized RAG Indexing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index current directory with default model
  python -m tools.rag.comprehensive_indexer index .

  # Index with BGE-M3 (best quality)
  python -m tools.rag.comprehensive_indexer index . --model BAAI/bge-m3

  # Full rebuild with custom database path
  python -m tools.rag.comprehensive_indexer index . --rebuild --db-path ./my_index
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index a repository")
    index_parser.add_argument("path", help="Path to repository")
    index_parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        choices=[
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-MiniLM-L12-v2",
            "BAAI/bge-m3",
            "BAAI/bge-large-en-v1.5",
            "intfloat/e5-large-v2",
        ],
        help="Embedding model to use",
    )
    index_parser.add_argument("--db-path", default=".rag_db", help="Vector database path")
    index_parser.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    index_parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    if args.command == "index":
        try:
            stats = index_sync(
                repo_path=args.path,
                db_path=args.db_path,
                embedding_model=args.model,
                rebuild=args.rebuild,
                quiet=args.quiet,
            )

            if args.quiet:
                print(
                    json.dumps(
                        {
                            "files_processed": stats.processed_files,
                            "chunks_created": stats.total_chunks,
                            "duration_seconds": stats.duration.total_seconds(),
                        }
                    )
                )

            return 0

        except Exception as e:
            if RICH_AVAILABLE:
                console = Console()
                console.print(f"[red]Error:[/red] {e}")
            else:
                print(f"Error: {e}")
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
