#!/usr/bin/env python3
"""
Run database migrations for safety enforcement.
Alternative to 'alembic upgrade head' when alembic.ini is not configured.
"""

import asyncio
import sys
from pathlib import Path

# Add GRID to path
grid_dir = Path(__file__).parent.parent.parent / "Projects" / "GRID"
sys.path.insert(0, str(grid_dir))

from sqlalchemy.ext.asyncio import create_async_engine
from safety.audit.models import Base

# Database URL - adjust as needed
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/grid_mothership"


async def migrate():
    """Create all tables."""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Safety audit tables created successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
