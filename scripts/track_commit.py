#!/usr/bin/env python3
"""
GRID Commit Tracker
Tracks commits manually since git is not available in this environment.
Usage: python scripts/track_commit.py "Commit message" [author]
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

COMMITS_FILE = Path(".commits.json")


def generate_commit_hash(message: str, timestamp: str, author: str) -> str:
    """Generate a unique hash for the commit."""
    content = f"{message}{timestamp}{author}".encode()
    return hashlib.sha1(content).hexdigest()[:7]


def load_commits() -> list:
    """Load existing commits."""
    if COMMITS_FILE.exists():
        with open(COMMITS_FILE) as f:
            return json.load(f)
    return []


def save_commits(commits: list):
    """Save commits to file."""
    with open(COMMITS_FILE, "w") as f:
        json.dump(commits, f, indent=2)


def add_commit(message: str, author: str = "Irfan Kabir"):
    """Add a new commit."""
    commits = load_commits()
    timestamp = datetime.now(UTC).isoformat()
    commit_hash = generate_commit_hash(message, timestamp, author)

    commit = {
        "hash": commit_hash,
        "message": message,
        "author": author,
        "timestamp": timestamp,
        "branch": "main",
    }
    commits.append(commit)
    save_commits(commits)
    print(f"[{commit_hash}] {message}")
    print(f"Author: {author}")
    print(f"Date: {timestamp}")
    print("Branch: main")
    print(f"\nTotal commits: {len(commits)}")


def log_commits(n: int = None):
    """Display commit log."""
    commits = load_commits()
    if not commits:
        print("No commits yet.")
        return

    display_commits = commits[-n:] if n else commits
    for commit in reversed(display_commits):
        print(f"\ncommit {commit['hash']}")
        print(f"Author: {commit['author']}")
        print(f"Date: {commit['timestamp']}")
        print(f"Branch: {commit['branch']}")
        print(f"\n    {commit['message']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python track_commit.py <message> [author]")
        print("       python track_commit.py log [n]")
        sys.exit(1)

    if sys.argv[1] == "log":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else None
        log_commits(n)
    else:
        message = sys.argv[1]
        author = sys.argv[2] if len(sys.argv) > 2 else "Irfan Kabir"
        add_commit(message, author)
