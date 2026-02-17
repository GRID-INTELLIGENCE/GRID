"""Refined scan: find ACTUAL blocking I/O patterns inside async functions in src/."""

import re
import os

src_dir = "src"

# Patterns that are truly blocking inside async functions
patterns = {
    "time.sleep": r"time\.sleep\(",
    "subprocess.run/check_output": r"subprocess\.(run|check_output)\(",
    ".read_text/.write_text": r"\.(read_text|write_text)\(",
    ".exists()": r"\.exists\(\)",
    ".mkdir/os.makedirs": r"(\.mkdir\(|os\.makedirs\()",
    "sync open(": r"(?<!aiofiles\.)(?<!\w)open\(",  # open( but NOT aiofiles.open(
    "requests HTTP call": r"requests\.(get|post|put|delete|patch|head|request|session)\(",
    ".unlink/.rename/shutil": r"(\.unlink\(|\.rename\(|shutil\.\w+\()",
    "json.load(file)": r"json\.(load|dump)\(",  # sync json with file handle
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
        async_start_line = 0

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
                async_start_line = i
                continue

            # Check if we left the async function
            if in_async and stripped.strip():
                current_indent = len(line) - len(line.lstrip())
                check = stripped.strip()
                if current_indent <= async_indent:
                    if re.match(r"(def |class )\w+", check):
                        in_async = False
                        continue
                    if re.match(r"async\s+def\s+\w+", check):
                        m2 = re.match(r"^(\s*)async\s+def\s+(\w+)", line)
                        if m2:
                            async_indent = len(m2.group(1))
                            async_func_name = m2.group(2)
                            async_start_line = i
                        continue
                    if check.startswith("@"):
                        continue
                    if current_indent < async_indent:
                        in_async = False
                        continue

            if not in_async:
                continue

            # Get code part (before comments)
            code_part = line.split("#")[0]

            for pat_name, pat_re in patterns.items():
                if not re.search(pat_re, code_part):
                    continue

                # Filter out false positives
                trimmed = code_part.strip()

                # "sync open(" - skip aiofiles.open which is correct
                if pat_name == "sync open(":
                    if "aiofiles.open" in code_part or "aiofiles.tempfile" in code_part:
                        continue

                # "requests HTTP call" - skip self._requests.get() or dict lookups
                if pat_name == "requests HTTP call":
                    if "self._requests." in code_part or "self._tracked_requests." in code_part:
                        continue
                    if "self.requests." in code_part:
                        continue
                    # Must actually be the requests library
                    if not re.search(r"(?<!\.)(?<!\w)requests\.", code_part):
                        continue

                # ".exists()" - skip await or to_thread wrapped
                if pat_name == ".exists()":
                    if "await" in code_part or "to_thread" in code_part:
                        continue

                # json.load/dump - skip json.loads/json.dumps (string versions are fine)
                if pat_name == "json.load(file)":
                    if re.search(r"json\.(loads|dumps)\(", code_part):
                        continue

                findings.append((pat_name, fpath, i, async_func_name, trimmed))

# Also check for requests import (not specific to async)
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
                content = f.read()
        except Exception:
            continue
        if re.search(r"^import requests\b", content, re.MULTILINE):
            for j, line in enumerate(content.splitlines(), 1):
                if re.search(r"^import requests\b", line):
                    requests_imports.append((fpath, j, line.strip()))
        if re.search(r"^from requests ", content, re.MULTILINE):
            for j, line in enumerate(content.splitlines(), 1):
                if re.search(r"^from requests ", line):
                    requests_imports.append((fpath, j, line.strip()))

# Print findings
print("=" * 90)
print("BLOCKING I/O PATTERNS INSIDE ASYNC FUNCTIONS (src/ only, production code)")
print("=" * 90)

grouped = {}
for pat_name, fpath, lineno, func_name, code in findings:
    grouped.setdefault(pat_name, []).append((fpath, lineno, func_name, code))

for pat_name in patterns:
    items = grouped.get(pat_name, [])
    if items:
        print(f"\n{'─' * 85}")
        print(f"  PATTERN: {pat_name} ({len(items)} findings)")
        print(f"{'─' * 85}")
        for fpath, lineno, func_name, code in items:
            rel = fpath.replace("\\", "/")
            print(f"  {rel}:{lineno}")
            print(f"    in async def {func_name}()")
            print(f"    >>> {code[:120]}")
            print()

print(f"\n{'─' * 85}")
print(f"  PATTERN: import requests (anywhere in src/) ({len(requests_imports)} findings)")
print(f"  [Should use httpx for async-compatible HTTP]")
print(f"{'─' * 85}")
for fpath, lineno, code in requests_imports:
    rel = fpath.replace("\\", "/")
    print(f"  {rel}:{lineno}")
    print(f"    >>> {code}")
    print()

async_total = len(findings)
print(f"\n{'=' * 90}")
print(f"SUMMARY")
print(f"{'=' * 90}")
for pat_name in patterns:
    count = len(grouped.get(pat_name, []))
    if count:
        print(f"  {pat_name}: {count}")
print(f"  import requests: {len(requests_imports)}")
print(f"  ─────────────────────────")
print(f"  Total async-context issues: {async_total}")
print(f"  Total requests imports: {len(requests_imports)}")
print(f"{'=' * 90}")
