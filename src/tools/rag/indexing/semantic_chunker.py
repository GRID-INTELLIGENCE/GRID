"""Semantic chunking for code and documentation.

Uses logical boundaries (classes, functions, headers) to create semantically coherent chunks.
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SemanticChunk:
    """A semantically coherent chunk of text."""

    content: str
    metadata: dict[str, Any]


class SemanticChunker:
    """Chunks documents at semantic boundaries."""

    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 1500, chunk_overlap: int = 150):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, content: str, file_path: str) -> list[SemanticChunk]:
        """Apply appropriate chunking strategy based on file extension."""
        ext = file_path.split(".")[-1].lower() if "." in file_path else ""

        if ext in ("py", "js", "ts", "jsx", "tsx", "go", "rs", "cpp", "c", "h"):
            return self.chunk_code(content, language=ext)
        elif ext in ("md", "txt", "markdown"):
            return self.chunk_markdown(content)
        else:
            return self.chunk_text(content)

    def chunk_code(self, content: str, language: str = "python") -> list[SemanticChunk]:
        """Chunk code files at function/class boundaries."""
        # Simple regex-based boundary detection for various languages
        if language == "py":
            pattern = r"^(def |class |async def )"
        elif language in ("js", "ts", "jsx", "tsx"):
            pattern = r"^(function |class |const \w+ = |export |import )"
        elif language in ("go", "rs", "cpp", "c", "h"):
            pattern = r"^(\w+.*\{|func |fn )"
        else:
            pattern = r"^(\w+.*\{)"  # Generic brace-based

        lines = content.split("\n")
        chunks: list[SemanticChunk] = []
        current_chunk_lines: list[str] = []
        current_start_line = 1

        for i, line in enumerate(lines, 1):
            # Check for a new semantic boundary at the start of a line
            if re.match(pattern, line.strip()) and current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(
                        SemanticChunk(
                            content=chunk_text,
                            metadata={"start_line": current_start_line, "end_line": i - 1, "type": "code_block"},
                        )
                    )
                    # Handle overlap by keeping the last few lines if needed
                    overlap_lines = chunk_text.split("\n")[-3:]  # Simple overlap
                    current_chunk_lines = overlap_lines + [line]
                    current_start_line = i - len(overlap_lines)
                else:
                    current_chunk_lines.append(line)
            else:
                current_chunk_lines.append(line)

            # Also break if the chunk is too large
            if len("\n".join(current_chunk_lines)) > self.max_chunk_size:
                chunk_text = "\n".join(current_chunk_lines)
                chunks.append(
                    SemanticChunk(
                        content=chunk_text,
                        metadata={"start_line": current_start_line, "end_line": i, "type": "code_split"},
                    )
                )
                current_chunk_lines = []
                current_start_line = i + 1

        # Finalize last chunk
        if current_chunk_lines:
            chunks.append(
                SemanticChunk(
                    content="\n".join(current_chunk_lines),
                    metadata={"start_line": current_start_line, "end_line": len(lines), "type": "code_final"},
                )
            )

        return chunks

    def chunk_markdown(self, content: str) -> list[SemanticChunk]:
        """Chunk markdown files at header boundaries."""
        # Split by markdown headers (# Header)
        lines = content.split("\n")
        chunks: list[SemanticChunk] = []
        current_chunk_lines: list[str] = []
        current_start_line = 1

        header_pattern = r"^#{1,6}\s+"

        for i, line in enumerate(lines, 1):
            if re.match(header_pattern, line.strip()) and current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(
                        SemanticChunk(
                            content=chunk_text,
                            metadata={"start_line": current_start_line, "end_line": i - 1, "type": "markdown_section"},
                        )
                    )
                    current_chunk_lines = [line]
                    current_start_line = i
                else:
                    current_chunk_lines.append(line)
            else:
                current_chunk_lines.append(line)

            if len("\n".join(current_chunk_lines)) > self.max_chunk_size:
                chunk_text = "\n".join(current_chunk_lines)
                chunks.append(
                    SemanticChunk(
                        content=chunk_text,
                        metadata={"start_line": current_start_line, "end_line": i, "type": "markdown_split"},
                    )
                )
                current_chunk_lines = []
                current_start_line = i + 1

        if current_chunk_lines:
            chunks.append(
                SemanticChunk(
                    content="\n".join(current_chunk_lines),
                    metadata={"start_line": current_start_line, "end_line": len(lines), "type": "markdown_final"},
                )
            )

        return chunks

    def chunk_text(self, content: str) -> list[SemanticChunk]:
        """Simple paragraph-based chunking for plain text."""
        # Roughly split by paragraphs
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""
        current_start_paragraph = 0

        for i, p in enumerate(paragraphs):
            if len(current_chunk) + len(p) > self.max_chunk_size and current_chunk:
                chunks.append(
                    SemanticChunk(
                        content=current_chunk.strip(),
                        metadata={"paragraphs": f"{current_start_paragraph}-{i-1}", "type": "text_block"},
                    )
                )
                current_chunk = p
                current_start_paragraph = i
            else:
                current_chunk += "\n\n" + p if current_chunk else p

        if current_chunk:
            chunks.append(
                SemanticChunk(
                    content=current_chunk.strip(),
                    metadata={"paragraphs": f"{current_start_paragraph}-{len(paragraphs)-1}", "type": "text_final"},
                )
            )

        return chunks
