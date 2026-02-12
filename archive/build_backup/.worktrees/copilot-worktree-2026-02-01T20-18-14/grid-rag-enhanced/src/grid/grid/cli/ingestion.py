"""File ingestion utilities for GRID CLI."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from ..cli import FileIngestionError

logger = logging.getLogger(__name__)


class FileIngestionManager:
    """Handles file ingestion with safety checks and format detection."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".csv"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, max_size: int | None = None):
        self.max_size = max_size or self.MAX_FILE_SIZE

    def validate_file(self, file_path: str) -> Path:
        """Validate file exists and is accessible."""
        path = Path(file_path)

        if not path.exists():
            raise FileIngestionError(f"File not found: {file_path}")

        if not path.is_file():
            raise FileIngestionError(f"Path is not a file: {file_path}")

        if path.stat().st_size > self.max_size:
            raise FileIngestionError(
                f"File too large: {file_path} ({path.stat().st_size} bytes > {self.max_size} bytes)"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file extension: {path.suffix}")

        return path

    def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read file content with error handling."""
        try:
            path = self.validate_file(file_path)
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            raise FileIngestionError(f"Encoding error in {file_path}: {e}") from e
        except OSError as e:
            raise FileIngestionError(f"OS error reading {file_path}: {e}") from e

    def get_file_metadata(self, file_path: str) -> dict[str, Any]:
        """Get file metadata for processing."""
        path = self.validate_file(file_path)
        stat = path.stat()

        return {
            "name": path.name,
            "path": str(path.absolute()),
            "size": stat.st_size,
            "extension": path.suffix.lower(),
            "modified": stat.st_mtime,
            "is_readable": os.access(path, os.R_OK),
        }


def ingest_multiple_files(
    file_paths: list[str], manager: FileIngestionManager | None = None
) -> list[dict[str, Any]]:
    """Ingest multiple files and return their contents with metadata."""
    if manager is None:
        manager = FileIngestionManager()

    results = []
    for file_path in file_paths:
        try:
            content = manager.read_file(file_path)
            metadata = manager.get_file_metadata(file_path)
            results.append({"content": content, "metadata": metadata, "success": True})
        except FileIngestionError as e:
            results.append({"content": None, "metadata": {"path": file_path}, "success": False, "error": str(e)})

    return results
