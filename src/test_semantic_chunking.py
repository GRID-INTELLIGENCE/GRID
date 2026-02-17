#!/usr/bin/env python3
"""Test script for SemanticChunker."""

import sys

# Add src to path
sys.path.insert(0, "src")

from tools.rag.semantic_chunker import SemanticChunker


def test_code_chunking() -> None:
    content = """
class MyClass:
    def method_one(self):
        print("Hello")

    def method_two(self):
        print("World")

def top_level_function():
    return 42
"""
    chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=500)
    chunks = chunker.chunk_file(content, "test.py")

    print(f"Code Chunks found: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(
            f"\n--- Chunk {i} ({chunk.metadata['type']}) lines {chunk.metadata['start_line']}-{chunk.metadata['end_line']} ---"
        )
        print(chunk.content)


def test_markdown_chunking() -> None:
    content = """
# Header 1
Content under header 1.

## Subheader 1.1
Content under subheader 1.1.

# Header 2
Content under header 2.
"""
    chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=500)
    chunks = chunker.chunk_file(content, "test.md")

    print(f"\nMarkdown Chunks found: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(
            f"\n--- Chunk {i} ({chunk.metadata['type']}) lines {chunk.metadata['start_line']}-{chunk.metadata['end_line']} ---"
        )
        print(chunk.content)


if __name__ == "__main__":
    test_code_chunking()
    test_markdown_chunking()
