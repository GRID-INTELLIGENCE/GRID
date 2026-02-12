#!/usr/bin/env python3
"""
Runtime Bug Scanner
===================
Scans Python files for common runtime bug patterns:
- NaN handling issues
- None/null check issues
- Type conversion errors
- Division by zero
- Missing error handling
"""

import ast
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BugReport:
    """Report of a potential runtime bug."""

    file_path: str
    line_number: int
    pattern_type: str
    severity: str
    code_snippet: str
    description: str
    suggested_fix: str


class RuntimeBugScanner(ast.NodeVisitor):
    """AST-based scanner for runtime bugs."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.bugs: list[BugReport] = []
        self.current_line = 0

    def visit(self, node: ast.AST):
        """Visit AST node and check for bugs."""
        self.current_line = node.lineno if hasattr(node, "lineno") else self.current_line  # type: ignore[reportOptionalMemberAccess]
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check function calls for potential issues."""
        # Check for float() calls without NaN checks
        if isinstance(node.func, ast.Name) and node.func.id == "float":
            if len(node.args) > 0:
                # Check if argument is a row.get() or df[] call
                arg = node.args[0]
                if isinstance(arg, ast.Call):
                    if isinstance(arg.func, ast.Attribute):
                        if arg.func.attr == "get":
                            # Pattern: float(row.get(...))
                            code = ast.unparse(node)
                            self.bugs.append(
                                BugReport(
                                    file_path=str(self.file_path),
                                    line_number=node.lineno,
                                    pattern_type="NaN_HANDLING",
                                    severity="HIGH",
                                    code_snippet=code,
                                    description="float() conversion without NaN check on pandas Series.get()",
                                    suggested_fix="Check pd.notna() before conversion",
                                )
                            )

        # Check for division operations
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        """Check binary operations for division by zero."""
        if isinstance(node.op, ast.Div):
            # Check if denominator could be zero
            code = ast.unparse(node)
            self.bugs.append(
                BugReport(
                    file_path=str(self.file_path),
                    line_number=node.lineno,
                    pattern_type="DIVISION_BY_ZERO",
                    severity="HIGH",
                    code_snippet=code,
                    description="Division operation without zero check",
                    suggested_fix="Add zero check: (x / y) if y != 0 else 0.0",
                )
            )
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """Check for truthy checks that should be explicit None checks."""
        if isinstance(node.test, ast.Name):
            # Simple truthy check - might need explicit None check
            pass
        self.generic_visit(node)


def scan_file_with_regex(file_path: Path) -> list[BugReport]:
    """Use regex to find patterns that AST might miss."""
    bugs: list[BugReport] = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.split("\n")

    # Pattern A: NaN handling - float(row.get(...)) or float(df[...])
    # Only flag if there's no NaN check in nearby lines
    pattern_nan = re.compile(
        r"float\s*\(\s*(?:row|df|series|dataframe)\.(?:get|__getitem__|iloc|loc)\s*\([^)]+\)", re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if pattern_nan.search(line):
            # Check if NaN check exists in previous 3 lines or same line
            context_start = max(0, i - 3)
            context = "\n".join(lines[context_start:i])
            if "pd.notna" not in context and "pd.isna" not in context and "notna" not in context.lower():
                bugs.append(
                    BugReport(
                        file_path=str(file_path),
                        line_number=i,
                        pattern_type="NaN_HANDLING",
                        severity="HIGH",
                        code_snippet=line.strip(),
                        description="float() conversion without NaN check on pandas data",
                        suggested_fix="Add pd.notna() check before conversion",
                    )
                )

    # Pattern B: Truthy checks that might need explicit None
    # Only flag if variable is typed as Optional or used in None context
    pattern_truthy = re.compile(r"if\s+(\w+)(?:\s*:|\s+and)", re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        match = pattern_truthy.search(line)
        if match and "is not None" not in line and "is None" not in line:
            var_name = match.group(1)
            # Skip common patterns that are fine
            if var_name.lower() not in ["true", "false", "self", "cls", "none", "len", "bool"]:
                # Check if this variable is typed as Optional or used with None
                # Look for type hints or None assignments
                context_start = max(0, i - 20)
                context = "\n".join(lines[context_start:i])
                # Only flag if there's evidence this could be None
                if (
                    f"Optional[{var_name}" in context
                    or f"{var_name}: Optional" in context
                    or f"{var_name} = None" in context
                    or f"{var_name} | None" in context
                ):
                    # Check if it's accessing attributes (more risky)
                    if "." in line and var_name in line:
                        bugs.append(
                            BugReport(
                                file_path=str(file_path),
                                line_number=i,
                                pattern_type="NONE_CHECK",
                                severity="MEDIUM",
                                code_snippet=line.strip(),
                                description=f"Truthy check on Optional {var_name} before attribute access",
                                suggested_fix=f"Change to: if {var_name} is not None:",
                            )
                        )

    # Pattern C: Type conversions without try/except
    # Only flag conversions of user input or external data
    pattern_conversion = re.compile(
        r"(int|float|str)\s*\((?:request|input|row|df|data|value|arg|param|config|env)", re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if pattern_conversion.search(line):
            # Check if it's in a try block (look backwards)
            context_start = max(0, i - 10)
            context = "\n".join(lines[context_start:i])
            if "try:" not in context:
                # Skip if it's a safe conversion (e.g., str(123))
                if not re.search(r"(int|float|str)\s*\(\s*\d+", line, re.IGNORECASE):
                    bugs.append(
                        BugReport(
                            file_path=str(file_path),
                            line_number=i,
                            pattern_type="TYPE_CONVERSION",
                            severity="MEDIUM",
                            code_snippet=line.strip(),
                            description="Type conversion of external data without try/except",
                            suggested_fix="Wrap in try/except or add validation",
                        )
                    )

    # Pattern D: Division without zero check
    # Only flag division by variables (not constants) that could be zero
    pattern_division = re.compile(r"(\w+)\s*/\s*(\w+)", re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        match = pattern_division.search(line)
        if match:
            denominator = match.group(2)
            # Skip if denominator is a constant (number) or common safe patterns
            if denominator.isdigit() or denominator in ["1", "2", "100", "1000", "len", "count", "size"]:
                continue
            # Skip if it's already in a conditional expression
            if "if" in line.lower() and "else" in line.lower():
                continue
            # Check if denominator is checked for zero in nearby context
            context_start = max(0, i - 5)
            context = "\n".join(lines[context_start : i + 1])
            # Check for zero checks
            if (
                f"{denominator} != 0" not in context
                and f"{denominator} > 0" not in context
                and f"{denominator} == 0" not in context
                and f"if {denominator}" not in context.lower()
            ):
                # Only flag if denominator could plausibly be zero (user input, calculation result)
                if any(
                    keyword in context.lower()
                    for keyword in ["input", "request", "calculate", "compute", "get", "fetch", "parse"]
                ):
                    bugs.append(
                        BugReport(
                            file_path=str(file_path),
                            line_number=i,
                            pattern_type="DIVISION_BY_ZERO",
                            severity="HIGH",
                            code_snippet=line.strip(),
                            description=f"Division by {denominator} (could be zero) without check",
                            suggested_fix=f"Add check: (x / {denominator}) if {denominator} != 0 else 0.0",
                        )
                    )

    # Pattern E: Functions without error handling
    # This is harder to detect automatically - will flag functions with risky operations

    return bugs


def scan_file(file_path: Path) -> list[BugReport]:
    """Scan a single file for runtime bugs."""
    bugs: list[BugReport] = []

    try:
        # Try AST-based scanning
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
        scanner = RuntimeBugScanner(file_path)
        scanner.visit(tree)
        bugs.extend(scanner.bugs)
    except SyntaxError:
        # File has syntax errors - skip AST scanning
        pass
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    # Also use regex-based scanning
    regex_bugs = scan_file_with_regex(file_path)
    bugs.extend(regex_bugs)

    # Deduplicate by line number and pattern type
    seen = set()
    unique_bugs = []
    for bug in bugs:
        key = (bug.file_path, bug.line_number, bug.pattern_type)
        if key not in seen:
            seen.add(key)
            unique_bugs.append(bug)

    return unique_bugs


def scan_directory(directory: Path, include_patterns: list[str] | None = None) -> list[BugReport]:
    """Scan all Python files in a directory."""
    all_bugs: list[BugReport] = []

    # Exclude patterns (virtual envs, test files with mocks, etc.)
    exclude_patterns = [
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "site-packages",
        ".git",
        "node_modules",
        ".mypy_cache",
        ".ruff_cache",
    ]

    if include_patterns:
        # Only scan files matching patterns
        for pattern in include_patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file() and file_path.suffix == ".py":
                    # Skip excluded paths
                    if any(exclude in str(file_path) for exclude in exclude_patterns):
                        continue
                    bugs = scan_file(file_path)
                    all_bugs.extend(bugs)
    else:
        # Scan all Python files
        for file_path in directory.rglob("*.py"):
            if file_path.is_file():
                # Skip excluded paths
                if any(exclude in str(file_path) for exclude in exclude_patterns):
                    continue
                bugs = scan_file(file_path)
                all_bugs.extend(bugs)

    return all_bugs


def generate_report(bugs: list[BugReport], output_dir: Path):
    """Generate JSON inventory and Markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group bugs by pattern type
    by_pattern: dict[str, list[BugReport]] = {}
    for bug in bugs:
        if bug.pattern_type not in by_pattern:
            by_pattern[bug.pattern_type] = []
        by_pattern[bug.pattern_type].append(bug)

    # Generate JSON inventory
    inventory = {
        "scan_date": datetime.now().isoformat(),
        "total_bugs": len(bugs),
        "by_pattern": {pattern: len(bug_list) for pattern, bug_list in by_pattern.items()},
        "bugs": [asdict(bug) for bug in bugs],
    }

    json_path = output_dir / "runtime_bugs_inventory.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    # Generate Markdown report
    md_lines = [
        "# Runtime Bug Scan Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Issues Found:** {len(bugs)}",
        "",
        "## Summary by Pattern Type",
        "",
    ]

    for pattern_type, bug_list in sorted(by_pattern.items()):
        md_lines.append(f"### {pattern_type.replace('_', ' ').title()} ({len(bug_list)} issues)")
        md_lines.append("")

        # Group by file
        by_file: dict[str, list[BugReport]] = {}
        for bug in bug_list:
            if bug.file_path not in by_file:
                by_file[bug.file_path] = []
            by_file[bug.file_path].append(bug)

        for file_path, file_bugs in sorted(by_file.items()):
            md_lines.append(f"**{file_path}**")
            for bug in file_bugs:
                md_lines.append(f"- Line {bug.line_number}: {bug.description}")
                md_lines.append(f"  - Code: `{bug.code_snippet}`")
                md_lines.append(f"  - Fix: {bug.suggested_fix}")
            md_lines.append("")

    md_path = output_dir / "runtime_bugs_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Scan complete: {len(bugs)} issues found")
    print(f"JSON inventory: {json_path}")
    print(f"Markdown report: {md_path}")

    return inventory


def main():
    """Main entry point."""

    # Target directories from the plan
    target_dirs = [
        Path("safety"),
        Path("boundaries"),
        Path("security"),
        Path("src"),
    ]

    all_bugs: list[BugReport] = []

    for target_dir in target_dirs:
        if target_dir.exists():
            print(f"Scanning {target_dir}...")
            bugs = scan_directory(target_dir)
            all_bugs.extend(bugs)
            print(f"Found {len(bugs)} issues in {target_dir}")
        else:
            print(f"Warning: {target_dir} does not exist")

    # Generate reports
    output_dir = Path("docs/fixes")
    inventory = generate_report(all_bugs, output_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    print(f"Total issues: {inventory['total_bugs']}")
    for pattern, count in inventory["by_pattern"].items():
        print(f"  {pattern}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
