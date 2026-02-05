import os
import re
from pathlib import Path

# Common patterns for secrets
SECRET_KEYWORDS = [
    r"api[_-]?key",
    r"secret[_-]?key",
    r"auth[_-]?token",
    r"access[_-]?key",
    r"private[_-]?key",
    r"password",
    r"credential",
    r"jwt[_-]?secret",
]

# Regex to find assignments like: key = "value"
ASSIGNMENT_REGEX = re.compile(rf'({"|".join(SECRET_KEYWORDS)})[ ]*=[ ]*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)

# Regex to find high entropy strings (e.g. hex or base64 > 24 chars)
ENTROPY_REGEX = re.compile(r'[\'"]([a-zA-Z0-9_\-\.\=\+]{24,})[\'"]')

# Directories to ignore
IGNORE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", ".ruff_cache"}


def is_placeholder(value):
    placeholders = {"your-", "change-me", "placeholder", "dummy", "test-", "example-"}
    return any(p in value.lower() for p in placeholders)


def scan_file(file_path):
    issues = []
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                # Check for assignments
                for match in ASSIGNMENT_REGEX.finditer(line):
                    keyword, value = match.groups()
                    if not is_placeholder(value) and len(value) > 8:
                        issues.append(
                            {"type": "Hardcoded Assignment", "keyword": keyword, "value": value, "line": i + 1}
                        )

                # Check for high entropy strings in non-assignment contexts (optional, more noisy)
                # We only flag if they look like secrets (e.g. contain mixed case, numbers, etc.)
                for match in ENTROPY_REGEX.finditer(line):
                    value = match.group(1)
                    if (
                        not is_placeholder(value)
                        and any(c.isdigit() for c in value)
                        and any(c.islower() for c in value)
                        and any(c.isupper() for c in value)
                    ):
                        # Filter out common false positives like file paths or long class names
                        if "/" not in value and "\\" not in value and " " not in value:
                            issues.append({"type": "Potential Secret (Entropy)", "value": value, "line": i + 1})
    except Exception:
        pass
    return issues


def main():
    project_root = Path("e:/grid")
    print(f"Scanning {project_root} for hardcoded secrets...")

    total_issues = 0
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in {".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".env"}:
                # Skip the scanning script itself and the validator
                if file == "secret_scanner.py" or file == "validate_security.py":
                    continue

                relative_path = file_path.relative_to(project_root)
                issues = scan_file(file_path)
                if issues:
                    print(f"\n[!] Issues found in {relative_path}:")
                    for issue in issues:
                        print(
                            f"  Line {issue['line']}: {issue['type']} - {issue.get('keyword', '')} {'*' * len(issue['value']) if 'value' in issue else ''} (first 4: {issue['value'][:4]})"
                        )
                        total_issues += 1

    print(f"\nScan complete. Total potential issues found: {total_issues}")


if __name__ == "__main__":
    main()
