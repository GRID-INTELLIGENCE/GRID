"""
LIMITATIONS
This file implements safety patterns using keyword matching and rule-based checks.
These are insufficient for production safety without integration with a trained classifier or ML model.
All verdicts must be reviewed by human operators for high-risk scenarios.

HMAC signing and verification for DCoC records.
"""

from __future__ import annotations

import hashlib
import hmac
import os


def _get_signing_secret() -> bytes:
    secret = os.environ.get("GRID_PROVENANCE_SECRET") or os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("Missing GRID_PROVENANCE_SECRET or JWT_SECRET for provenance signing")
    return secret.encode("utf-8")


def sign_record(serialized_record: str) -> str:
    secret = _get_signing_secret()
    return hmac.new(secret, serialized_record.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(serialized_record: str, signature: str) -> bool:
    expected = sign_record(serialized_record)
    return hmac.compare_digest(expected, signature)
