from __future__ import annotations

import re


def build_branch_name(topic: str, description: str, issue_number: str = "") -> str:
    """Build a branch name from topic, description, and issue number."""
    # Sanitize inputs
    topic = topic.lower().replace(" ", "-").replace("_", "-")
    description = description.lower().replace(" ", "-").replace("_", "-")

    # Remove special characters
    topic = re.sub(r"[^a-z0-9-]", "", topic)
    description = re.sub(r"[^a-z0-9-]", "", description)

    # Build branch name
    base = f"topic/{topic}-{description}"
    if issue_number:
        base += f"-{issue_number}"

    return base


def is_valid_branch_name(branch_name: str) -> bool:
    """Check if branch name is valid."""
    # Only allow topic branches for this utility
    pattern = r"^(refs/heads/)?topic/[a-zA-Z0-9._/-]+$"
    return bool(re.match(pattern, branch_name))
