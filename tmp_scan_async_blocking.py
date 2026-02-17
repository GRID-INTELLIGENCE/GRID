"""Scan src/ for synchronous blocking I/O patterns inside async functions."""

import re
import os

src_dir = "src"
patterns = {
    "time.sleep": r"time\.sleep\(",
    "subprocess.run/check_output": r"subprocess\.(run|check_output)\(",
    ".read_text/.write_text": r"\.(read_text|write_text)\(",
    ".exists()": r"\.exists\(\)",
    ".mkdir/os.makedirs": r"(\.mkdir\(|os\.makedirs\()",
    "open(": r"(?<!\w)open\(",
    "requests.verb": r"requests\.(get|post|put|delete|patch|head)\(",
    ".unlink/.rename/shutil": r"(\.unlink\(|\.rename\(|shutil\.\w+\()",
}

findings = []

for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in ("archive", ".venv", "__pycache__", "node_modules")]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        if "test" in fname.lower() and fname != "__init__.py":
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        in_async = False
        async_indent = 0
        async_func_name = ""

        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if not stripped:
                continue

            # Check for async def
            m = re.match(r"^(\s*)async\s+def\s+(\w+)", line)
            if m:
                in_async = True
                async_indent = len(m.group(1))
                async_func_name = m.group(2)
                continue

            # Check for sync def or class at same/lesser indent => leaves async
            if in_async and stripped.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= async_indent:
                    check = stripped.strip()
                    if check.startswith("def ") or check.startswith("class "):
                        in_async = False
                        continue
                    if check.startswith("async def "):
                        m2 = re.match(r"^(\s*)async\s+def\s+(\w+)", line)
                        if m2:
                            async_indent = len(m2.group(1))
                            async_func_name = m2.group(2)
                        continue
                    # Decorators, docstrings, comments - still inside
                    if check.startswith("@") or check.startswith("#"):
                        # Could be decorator for next function
                        pass
                    elif not check.startswith(("'", '"')):
                        # Non-indented code at module level means we left
                        if current_indent == 0 and async_indent == 0:
                            pass  # top-level async, unlikely but keep
                        elif current_indent < async_indent:
                            in_async = False
                            continue

            if in_async:
                for pat_name, pat_re in patterns.items():
                    if re.search(pat_re, line):
                        # Skip comments
                        code_part = line.split("#")[0]
                        if re.search(pat_re, code_part):
                            findings.append((pat_name, fpath, i, async_func_name, stripped.strip()))

# Also find requests import everywhere (not just async)
requests_imports = []
for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in ("archive", ".venv", "__pycache__", "node_modules")]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        if "test" in fname.lower() and fname != "__init__.py":
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if re.search(r"import requests\b", line):
                requests_imports.append((fpath, i, line.strip()))

# Print findings grouped by pattern
print("=" * 80)
print("BLOCKING I/O PATTERNS INSIDE ASYNC FUNCTIONS")
print("=" * 80)

grouped = {}
for pat_name, fpath, lineno, func_name, code in findings:
    grouped.setdefault(pat_name, []).append((fpath, lineno, func_name, code))

for pat_name in patterns:
    items = grouped.get(pat_name, [])
    if items:
        print(f"\n{'─' * 70}")
        print(f"  PATTERN: {pat_name} ({len(items)} findings)")
        print(f"{'─' * 70}")
        for fpath, lineno, func_name, code in items:
            print(f"  {fpath}:{lineno}")
            print(f"    async def {func_name}()")
            print(f"    >>> {code}")
            print()

print(f"\n{'─' * 70}")
print(f"  PATTERN: import requests (anywhere in src/) ({len(requests_imports)} findings)")
print(f"{'─' * 70}")
for fpath, lineno, code in requests_imports:
    print(f"  {fpath}:{lineno}")
    print(f"    >>> {code}")
    print()

total = len(findings) + len(requests_imports)
print(f"\n{'=' * 80}")
print(f"TOTAL: {len(findings)} blocking patterns in async functions + {len(requests_imports)} requests imports")
print(f"{'=' * 80}")
