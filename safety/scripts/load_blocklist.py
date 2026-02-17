#!/usr/bin/env python3
"""
Load dynamic blocklist entries into Redis.

Usage:
    python -m safety.scripts.load_blocklist [--file blocklist.txt] [--clear]

The blocklist file should contain one entry per line.
Lines starting with # are ignored.
"""

from __future__ import annotations

import argparse
import os
import sys

import redis


def main() -> None:
    parser = argparse.ArgumentParser(description="Load dynamic blocklist entries into Redis")
    parser.add_argument(
        "--file",
        "-f",
        default="safety/config/blocklist.txt",
        help="Path to blocklist file (one entry per line)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing blocklist before loading",
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis connection URL",
    )
    args = parser.parse_args()

    client = redis.Redis.from_url(args.redis_url, decode_responses=True)

    # Verify connectivity
    try:
        client.ping()
    except redis.ConnectionError as exc:
        print(
            f"ERROR: Cannot connect to Redis at {args.redis_url}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.clear:
        client.delete("dynamic_blocklist")
        print("Cleared existing blocklist.")

    # Load entries
    if not os.path.exists(args.file):
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    entries = []
    with open(args.file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                entries.append(line.lower())

    if entries:
        client.sadd("dynamic_blocklist", *entries)
        print(f"Loaded {len(entries)} entries into dynamic_blocklist.")
    else:
        print("No entries to load.")

    # Show current count
    count = client.scard("dynamic_blocklist")
    print(f"Total entries in dynamic_blocklist: {count}")


if __name__ == "__main__":
    main()
