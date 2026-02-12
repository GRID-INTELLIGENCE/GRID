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

# Show top 15 with error details
for resource, issues in sorted_files[:15]:
    print(f"\n{'='*80}")
    print(f"{len(issues):3d} issues: {resource}")
    print(f"{'='*80}")

    # Get error types
    error_types = defaultdict(int)
    for issue in issues:
        code = issue.get("code", {}).get("value", "unknown")
        error_types[code] += 1

    print("Error types:")
    for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  - {error_type}: {count}")

    print(f"\nFirst 5 issues:")
    for i, issue in enumerate(issues[:5], 1):
        line = issue.get("startLineNumber", "?")
        msg = issue.get("message", "No message")[:100]
        print(f"  {i}. Line {line}: {msg}")
