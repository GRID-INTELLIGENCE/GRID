import json
from collections import defaultdict

# Load issues
with open("e:\\.github\\issues.json", "r") as f:
    data = json.load(f)

# Group by file
files = defaultdict(list)
for issue in data:
    resource = issue.get("resource", "unknown")
    files[resource].append(issue)

# Filter out apps/backend and e:/app
filtered = {
    f: v
    for f, v in files.items()
    if not f.startswith("/e:/Apps/backend") and not f.startswith("/e:/app/")
}

# Sort by count
sorted_files = sorted(filtered.items(), key=lambda x: -len(x[1]))

# Top 10 with detailed info
for idx, (resource, issues) in enumerate(sorted_files[:10], 1):
    print(f"\n{'='*100}")
    print(f"{idx}. FILE: {resource}")
    print(f"    ISSUES: {len(issues)}")
    print(f"{'='*100}")

    # Get error types
    error_types = defaultdict(int)
    for issue in issues:
        code = issue.get("code", {}).get("value", "unknown")
        error_types[code] += 1

    print("PRIMARY ERROR TYPES:")
    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1])[:5]:
        print(f"  - {error_type}: {count}")

    print(f"\nLINES WITH ISSUES:")
    lines_by_num = defaultdict(list)
    for issue in issues:
        line = issue.get("startLineNumber", 0)
        msg = issue.get("message", "No message")
        lines_by_num[line].append(msg)

    # Show up to 15 lines
    for line in sorted(lines_by_num.keys())[:15]:
        msgs = lines_by_num[line]
        print(f"  Line {line}: {len(msgs)} issue(s)")
        # Show first error message
        if msgs:
            msg = msgs[0][:80]
            print(f"    -> {msg}")
