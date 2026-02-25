"""Hash chain computation and verification for DCoC."""

from __future__ import annotations

import hashlib


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_chain_hash(parent_chain_hash: str | None, serialized_record: str) -> str:
    seed = parent_chain_hash or "genesis"
    return compute_hash(seed + serialized_record)


def verify_chain_integrity(
    chain_hashes: list[str],
    recompute_hash: callable,
) -> tuple[bool, int | None]:
    """
    Verify integrity of a sequence of chain hashes.
    recompute_hash(index) should return the expected chain_hash for that index.
    Returns (valid, broken_at_index).
    """
    for i, stored_hash in enumerate(chain_hashes):
        expected = recompute_hash(i)
        if stored_hash != expected:
            return (False, i)
    return (True, None)
