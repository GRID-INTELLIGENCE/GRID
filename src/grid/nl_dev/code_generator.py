"""Code generator with file modification, deletion, and rollback support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenerationResult:
    """Result of a code generation operation."""

    success: bool = True
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CodeGenerator:
    """Generate, modify, and delete code files with rollback support."""

    def generate_modify_file(self, file_path: str, changes: list[str]) -> GenerationResult:
        """Modify an existing file by appending changes."""
        result = GenerationResult(success=True)
        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                for change in changes:
                    content += f"\n{change}"
                path.write_text(content)
                result.files_modified.append(file_path)
            else:
                result.success = False
                result.errors.append(f"File not found: {file_path}")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        return result

    def generate_delete_file(self, file_path: str) -> GenerationResult:
        """Delete a file."""
        result = GenerationResult(success=True)
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                result.files_modified.append(file_path)
            else:
                result.success = False
                result.errors.append(f"File not found: {file_path}")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        return result

    def rollback(self, result: GenerationResult) -> GenerationResult:
        """Rollback all created files from a previous generation result."""
        for file_path in result.files_created:
            try:
                Path(file_path).unlink()
            except Exception:  # noqa: S110
                pass
        return GenerationResult(success=True)
