from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass
