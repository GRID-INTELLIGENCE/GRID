#!/usr/bin/env python3
"""
Profile Python entrypoints across dev roots and emit a blocklist profile.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

DEFAULT_ROOTS = [
    Path("E:/grid"),
    Path("E:/Coinbase"),
    Path("E:/wellness_studio"),
    Path("E:/scripts"),
    Path("E:/config"),
]

DEFAULT_GLOBS = [
    "*.ps1",
    "*.bat",
    "*.cmd",
    "*.py",
    "*.json",
    "*.yml",
    "*.yaml",
    "*.toml",
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "target",
    "bin",
    "obj",
}

PATTERNS = {
    "py_launcher": re.compile(r"(?i)\bpy\.exe\b"),
    "python_exe": re.compile(r"(?i)\bpython\.exe\b"),
    "py_command": re.compile(r"(?i)(?:^|[^\w-])py(?:\s|$)"),
    "python_command": re.compile(r"(?i)(?:^|[^\w-])python(?:\s|$)"),
    "json_command": re.compile(r"\"command\"\s*:\s*\"(python|py)\"", re.IGNORECASE),
}


def iter_files(roots: Iterable[Path], globs: Iterable[str]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for pattern in globs:
            for path in root.rglob(pattern):
                if any(part in EXCLUDE_DIRS for part in path.parts):
                    continue
                yield path


def scan_file(path: Path) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return matches

    ext = path.suffix.lower()
    if ext in {".ps1", ".bat", ".cmd"}:
        active_patterns = [
            "py_launcher",
            "python_exe",
            "py_command",
            "python_command",
        ]
    elif ext in {".json", ".yml", ".yaml", ".toml"}:
        active_patterns = ["json_command", "py_launcher", "python_exe"]
    elif ext == ".py":
        active_patterns = ["py_launcher", "python_exe"]
    else:
        active_patterns = list(PATTERNS.keys())

    for idx, line in enumerate(text.splitlines(), start=1):
        for name in active_patterns:
            regex = PATTERNS[name]
            if regex.search(line):
                matches.append(
                    {
                        "file": str(path),
                        "line": str(idx),
                        "pattern": name,
                        "preview": line.strip()[:240],
                    }
                )
    return matches


def summarize(matches: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    by_pattern = Counter(m["pattern"] for m in matches)
    by_ext = Counter(Path(m["file"]).suffix.lower() for m in matches)
    by_root = Counter(Path(m["file"]).parts[0:2] for m in matches)

    def normalize_root(parts: tuple[str, ...]) -> str:
        return "\\".join(parts)

    return {
        "by_pattern": dict(by_pattern),
        "by_extension": dict(by_ext),
        "by_root": {normalize_root(k): v for k, v in by_root.items()},
    }


def recent_hits(matches: list[dict[str, str]], limit: int = 25) -> list[dict[str, str]]:
    seen = {}
    for match in matches:
        path = Path(match["file"])
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            continue
        prev = seen.get(path)
        if prev is None or mtime > prev:
            seen[path] = mtime

    recent = sorted(seen.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"file": str(path), "mtime": datetime.fromtimestamp(mtime).isoformat()} for path, mtime in recent]


def build_blocklist() -> dict[str, object]:
    return {
        "version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "allowed_python": "C:\\Users\\irfan\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
        "blocked_commands": ["py", "py.exe", "pyw", "pyw.exe"],
        "blocked_paths": ["C:\\WINDOWS\\py.exe"],
        "monitored_commands": ["python", "python.exe"],
        "globs": DEFAULT_GLOBS,
        "patterns": {k: v.pattern for k, v in PATTERNS.items()},
    }


def render_markdown(
    matches: list[dict[str, str]],
    summary: dict[str, dict[str, int]],
    recent: list[dict[str, str]],
    blocklist: dict[str, object],
) -> str:
    lines = []
    lines.append("# Python Entrypoint Profile")
    lines.append("")
    lines.append(f"Generated: {datetime.now(UTC).isoformat()}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total matches: {len(matches)}")
    lines.append(f"- Patterns: {summary['by_pattern']}")
    lines.append(f"- Extensions: {summary['by_extension']}")
    lines.append("")
    lines.append("## Recent Files With Entrypoint Signals")
    for item in recent:
        lines.append(f"- {item['file']} ({item['mtime']})")
    lines.append("")
    lines.append("## Tight Coupling Signals")
    lines.append("- File association uses py.exe (Python Launcher).")
    lines.append("- Scripts/configs that call `py` or `python` directly.")
    lines.append('- JSON configs using `"command": "python"`.')
    lines.append("")
    lines.append("## Recommended Blocklist Layer")
    lines.append("```json")
    lines.append(json.dumps(blocklist, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Sample Matches (Top 50)")
    for match in matches[:50]:
        lines.append(f"- {match['file']}:{match['line']} [{match['pattern']}] {match['preview']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile Python entrypoints in dev roots")
    parser.add_argument("--root", action="append", dest="roots", help="Root directory to scan")
    parser.add_argument("--output-md", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.md")
    parser.add_argument("--output-json", default="E:/analysis_outputs/PY_ENTRYPOINT_PROFILE.json")
    parser.add_argument("--blocklist-out", default="E:/config/python_entrypoint_blocklist.json")
    args = parser.parse_args()

    roots = [Path(r) for r in (args.roots or [])] or DEFAULT_ROOTS
    matches: list[dict[str, str]] = []

    for path in iter_files(roots, DEFAULT_GLOBS):
        matches.extend(scan_file(path))

    summary = summarize(matches)
    recent = recent_hits(matches)
    blocklist = build_blocklist()

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "roots": [str(r) for r in roots],
        "summary": summary,
        "recent_files": recent,
        "matches": matches,
        "blocklist": blocklist,
    }

    Path(args.output_json).write_text(json.dumps(output, indent=2), encoding="utf-8")
    Path(args.blocklist_out).write_text(json.dumps(blocklist, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(matches, summary, recent, blocklist), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
