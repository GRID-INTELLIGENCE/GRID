from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URI,
    pool_pre_ping=True,  # Check connection health before usage
    pool_size=20,  # Maximum number of permanent connections
    max_overflow=10,  # Maximum number of temporary connections
    pool_recycle=3600,  # Recycle connections every hour
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session]:
    """
    Dependency to get a database session.
    Yields the session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
