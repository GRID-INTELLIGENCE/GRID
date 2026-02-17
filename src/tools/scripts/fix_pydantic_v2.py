#!/usr/bin/env python3
"""
Pydantic v2 Migration Script

Automatically migrates Pydantic v1 patterns to v2 across the codebase.

Changes:
1. class Config: -> model_config = ConfigDict(...)
2. datetime.now(timezone.utc) -> datetime.now(timezone.utc)
3. @field_validator(...) -> @field_validator(...)
4. @model_validator(mode='after', ...) -> @model_validator(...)

Usage:
    python scripts/fix_pydantic_v2.py                    # Dry run
    python scripts/fix_pydantic_v2.py --apply            # Apply changes
    python scripts/fix_pydantic_v2.py --path grid/       # Specific path
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from re import Match


@dataclass
class FileChange:
    """Represents a change to a file."""

    file_path: Path
    original_content: str
    new_content: str
    changes_made: list[str]

    @property
    def has_changes(self) -> bool:
        return self.original_content != self.new_content


class PydanticV2Migrator:
    """Migrates Pydantic v1 patterns to v2."""

    def __init__(self, root_path: Path, dry_run: bool = True):
        self.root_path = root_path
        self.dry_run = dry_run
        self.files_processed = 0
        self.files_changed = 0
        self.total_changes = 0

    def migrate_file(self, file_path: Path) -> FileChange | None:
        """
        Migrate a single Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            FileChange if changes were made, None otherwise
        """
        try:
            original_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            return None

        self.files_processed += 1
        content = original_content
        changes_made = []

        # 1. Migrate class Config: to model_config = ConfigDict(...)
        content, config_changes = self._migrate_class_config(content)
        changes_made.extend(config_changes)

        # 2. Migrate datetime.now(timezone.utc) to datetime.now(timezone.utc)
        content, datetime_changes = self._migrate_datetime_utcnow(content)
        changes_made.extend(datetime_changes)

        # 3. Migrate @validator to @field_validator
        content, validator_changes = self._migrate_validator(content)
        changes_made.extend(validator_changes)

        # 4. Migrate @root_validator to @model_validator
        content, root_validator_changes = self._migrate_root_validator(content)
        changes_made.extend(root_validator_changes)

        # 5. Migrate .model_dump() to .model_dump() and .model_dump_json() to .model_dump_json()
        content, dict_json_changes = self._migrate_dict_json(content)
        changes_made.extend(dict_json_changes)

        # 6. Add missing imports
        content = self._add_missing_imports(content, changes_made)

        if content != original_content:
            self.files_changed += 1
            self.total_changes += len(changes_made)
            return FileChange(
                file_path=file_path,
                original_content=original_content,
                new_content=content,
                changes_made=changes_made,
            )

        return None

    def _migrate_class_config(self, content: str) -> tuple[str, list[str]]:
        """Migrate class Config: to model_config = ConfigDict(...)."""
        changes = []

        # Pattern: class Config: followed by config attributes
        pattern = r"(\s+)class Config:\s*\n((?:\1    .+\n)*)"

        def replace_config(match: Match[str]) -> str:
            indent = match.group(1)
            config_body = match.group(2)

            # Extract configuration attributes
            config_attrs = []
            for line in config_body.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Remove trailing comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                if "=" in line:
                    config_attrs.append(line)

            if not config_attrs:
                return match.group(0)

            # Build ConfigDict
            config_dict_content = ", ".join(config_attrs)
            result = f"{indent}model_config = ConfigDict({config_dict_content})\n"

            changes.append("class Config -> model_config = ConfigDict(...)")
            return result

        new_content = re.sub(pattern, replace_config, content)
        return new_content, changes

    def _migrate_datetime_utcnow(self, content: str) -> tuple[str, list[str]]:
        """Migrate datetime.utcnow() to datetime.now(timezone.utc)."""
        changes = []

        # Pattern: datetime.utcnow()
        pattern = r"datetime\.utcnow\(\)"
        count = len(re.findall(pattern, content))

        if count > 0:
            new_content = re.sub(pattern, "datetime.now(timezone.utc)", content)
            changes.append(f"datetime.utcnow() -> datetime.now(timezone.utc) ({count} occurrences)")
            return new_content, changes

        return content, changes

    def _migrate_validator(self, content: str) -> tuple[str, list[str]]:
        """Migrate @validator to @field_validator."""
        changes = []

        # Pattern: @field_validator('field_name')
        # Note: This is a simplified migration. Complex validators may need manual review.
        pattern = r"@validator\("
        count = len(re.findall(pattern, content))

        if count > 0:
            new_content = content.replace("@validator(", "@field_validator(")
            changes.append(f"@validator -> @field_validator ({count} occurrences)")
            return new_content, changes

        return content, changes

    def _migrate_root_validator(self, content: str) -> tuple[str, list[str]]:
        """Migrate @root_validator to @model_validator."""
        changes = []

        # Pattern: @model_validator(mode='after', ...)
        pattern = r"@root_validator\("
        count = len(re.findall(pattern, content))

        if count > 0:
            # Replace @root_validator with @model_validator(mode='after')
            new_content = re.sub(
                r"@root_validator\((.*?)\)",
                lambda m: (
                    f"@model_validator(mode='after', {m.group(1)})" if m.group(1) else "@model_validator(mode='after')"
                ),
                content,
            )
            changes.append(f"@root_validator -> @model_validator ({count} occurrences)")
            return new_content, changes

        return content, changes

    def _migrate_dict_json(self, content: str) -> tuple[str, list[str]]:
        """Migrate .model_dump() to .model_dump() and .model_dump_json() to .model_dump_json()."""
        changes = []

        # Pattern: .model_dump( or .dict
        # We need to be careful not to replace .dict in other contexts (like dictionary objects)
        # But in a Pydantic-heavy codebase, most .model_dump() on Pydantic models should be migrated.

        # .model_dump() -> .model_dump()
        dict_pattern = r"\.dict\("
        dict_count = len(re.findall(dict_pattern, content))
        if dict_count > 0:
            content = content.replace(".model_dump(", ".model_dump(")
            changes.append(f".model_dump() -> .model_dump() ({dict_count} occurrences)")

        # .model_dump_json() -> .model_dump_json()
        json_pattern = r"\.json\("
        json_count = len(re.findall(json_pattern, content))
        if json_count > 0:
            content = content.replace(".model_dump_json(", ".model_dump_json(")
            changes.append(f".model_dump_json() -> .model_dump_json() ({json_count} occurrences)")

        return content, changes

    def _add_missing_imports(self, content: str, changes_made: list[str]) -> str:
        """Add missing imports based on changes made."""
        lines = content.split("\n")
        import_section_end = 0

        # Find the end of the import section
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith(("#", "from ", "import ", '"""', "'''")):
                import_section_end = i
                break

        imports_to_add = []

        # Check if ConfigDict is needed
        if any("ConfigDict" in change for change in changes_made):
            if "ConfigDict" not in content:
                imports_to_add.append("from pydantic import ConfigDict")

        # Check if timezone is needed
        if any("timezone.utc" in change for change in changes_made):
            # Check if timezone is imported
            has_timezone_import = any("from datetime import" in line and "timezone" in line for line in lines)
            if not has_timezone_import:
                # Find existing datetime import and update it
                for i, line in enumerate(lines[:import_section_end]):
                    if "from datetime import" in line and "timezone" not in line:
                        # Add timezone to existing import
                        if line.strip().endswith(")"):
                            # Multi-line import
                            lines[i] = line.replace(")", ", timezone)")
                        else:
                            # Single-line import
                            lines[i] = line.rstrip() + ", timezone"
                        break
                else:
                    # No datetime import found, add new one
                    imports_to_add.append("from datetime import datetime, timezone")

        # Check if field_validator is needed
        if any("field_validator" in change for change in changes_made):
            if "field_validator" not in content:
                # Update existing pydantic import or add new one
                for i, line in enumerate(lines[:import_section_end]):
                    if "from pydantic import" in line:
                        if "field_validator" not in line:
                            if line.strip().endswith(")"):
                                lines[i] = line.replace(")", ", field_validator)")
                            else:
                                lines[i] = line.rstrip() + ", field_validator"
                        break
                else:
                    imports_to_add.append("from pydantic import field_validator")

        # Check if model_validator is needed
        if any("model_validator" in change for change in changes_made):
            if "model_validator" not in content:
                # Update existing pydantic import or add new one
                for i, line in enumerate(lines[:import_section_end]):
                    if "from pydantic import" in line:
                        if "model_validator" not in line:
                            if line.strip().endswith(")"):
                                lines[i] = line.replace(")", ", model_validator)")
                            else:
                                lines[i] = line.rstrip() + ", model_validator"
                        break
                else:
                    imports_to_add.append("from pydantic import model_validator")

        # Add new imports if needed
        if imports_to_add:
            # Insert after the last import statement
            insert_position = import_section_end
            for import_stmt in imports_to_add:
                lines.insert(insert_position, import_stmt)
                insert_position += 1

        return "\n".join(lines)

    def migrate_directory(self, directory: Path) -> list[FileChange]:
        """
        Migrate all Python files in a directory recursively.

        Args:
            directory: Directory to scan

        Returns:
            List of FileChange objects
        """
        changes = []

        for file_path in directory.rglob("*.py"):
            # Skip virtual environments and build directories
            if any(part in file_path.parts for part in [".venv", "venv", "__pycache__", "build", "dist", ".git"]):
                continue

            change = self.migrate_file(file_path)
            if change:
                changes.append(change)

        return changes

    def apply_changes(self, changes: list[FileChange]) -> None:
        """Apply changes to files."""
        for change in changes:
            if self.dry_run:
                print(f"\n{'=' * 80}")
                print(f"Would modify: {change.file_path}")
                print(f"Changes: {', '.join(change.changes_made)}")
            else:
                try:
                    change.file_path.write_text(change.new_content, encoding="utf-8")
                    print(f"✓ Modified: {change.file_path}")
                    for change_desc in change.changes_made:
                        print(f"  - {change_desc}")
                except Exception as e:
                    print(f"✗ Error writing {change.file_path}: {e}", file=sys.stderr)

    def print_summary(self) -> None:
        """Print migration summary."""
        print(f"\n{'=' * 80}")
        print("Migration Summary")
        print(f"{'=' * 80}")
        print(f"Files processed: {self.files_processed}")
        print(f"Files changed:   {self.files_changed}")
        print(f"Total changes:   {self.total_changes}")

        if self.dry_run:
            print("\nDRY RUN - No files were modified")
            print("Run with --apply to apply changes")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Pydantic v1 patterns to v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("grid"),
        help="Path to migrate (default: grid/)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry run)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    print("Pydantic v2 Migration Tool")
    print(f"{'=' * 80}")
    print(f"Path: {args.path}")
    print(f"Mode: {'APPLY CHANGES' if args.apply else 'DRY RUN'}")
    print(f"{'=' * 80}\n")

    migrator = PydanticV2Migrator(args.path, dry_run=not args.apply)

    if args.path.is_file():
        changes = [migrator.migrate_file(args.path)]
        changes = [c for c in changes if c is not None]
    else:
        changes = migrator.migrate_directory(args.path)

    if changes:
        migrator.apply_changes(changes)
    else:
        print("No changes needed - all files are already using Pydantic v2 patterns")

    migrator.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
