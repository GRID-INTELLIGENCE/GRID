"""
Alembic Environment Configuration for GRID Mothership.

Configured to:
- Use MOTHERSHIP_DATABASE_URL environment variable
- Import all Mothership models for autogenerate support
- Support both sync and async database operations
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src to path for imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from environment variable if set
database_url = os.getenv("MOTHERSHIP_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models for autogenerate support
# This allows Alembic to detect schema changes automatically
from application.mothership.db.models_base import Base

# Import all model modules to register them with Base.metadata
try:
    from application.mothership.db import (
        models_agentic,  # noqa: F401
        models_audit,  # noqa: F401
        models_billing,  # noqa: F401
        models_cockpit,  # noqa: F401
        models_drt,  # noqa: F401
    )
except ImportError as e:
    print(f"Warning: Could not import all models: {e}")

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
