"""Enhanced Databricks connector with improved DNS resolution and error handling."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _redact_token(token: str) -> str:
    """Redact token for logging."""
    if not token or len(token) < 8:
        return "***"
    return f"{token[:4]}***{token[-4:]}"


class EnhancedDatabricksConnector:
    """Enhanced Databricks connector with better DNS resolution."""

    def __init__(
        self,
        server_hostname: str | None = None,
        http_path: str | None = None,
        access_token: str | None = None,
    ):
        """Initialize enhanced Databricks connector."""
        self.server_hostname = server_hostname or os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip()
        self.http_path = http_path or os.getenv("DATABRICKS_HTTP_PATH", "").strip()
        self.access_token = access_token or os.getenv("DATABRICKS_ACCESS_TOKEN", "").strip()

        if not self.server_hostname:
            raise ValueError("DATABRICKS_SERVER_HOSTNAME is required")
        if not self.http_path:
            raise ValueError("DATABRICKS_HTTP_PATH is required")
        if not self.access_token:
            raise ValueError("DATABRICKS_ACCESS_TOKEN is required")

        # Try to find working hostname if the original fails
        self.working_hostname = self._find_working_hostname()

        self._engine: Engine | None = None

    def _find_working_hostname(self) -> str:
        """Find a working hostname by trying alternatives."""

        # If original hostname works, use it
        if self._test_hostname(self.server_hostname):
            return self.server_hostname

        # Try alternative formats
        if "dbc-" in self.server_hostname and ".cloud.databricks.com" in self.server_hostname:
            parts = self.server_hostname.split(".")
            workspace_id = parts[0]

            alternatives = [
                f"{workspace_id}.databricks.com",
                f"{workspace_id}.cloud.databricks.com",
                f"{workspace_id}.az.databricks.com",
                f"{workspace_id}.gcp.databricks.com",
                f"{workspace_id}.aws.databricks.com",
            ]

            for alt_hostname in alternatives:
                if self._test_hostname(alt_hostname):
                    logger.info(f"Using alternative hostname: {alt_hostname}")
                    return alt_hostname

        # Fall back to original
        logger.warning(f"Using original hostname despite DNS issues: {self.server_hostname}")
        return self.server_hostname

    def _test_hostname(self, hostname: str) -> bool:
        """Test if a hostname is resolvable and accessible."""
        try:
            # Test DNS resolution
            socket.gethostbyname(hostname)

            # Test TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((hostname, 443))
            sock.close()

            return result == 0
        except Exception:
            return False

    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with retry logic."""
        if self._engine is not None:
            return self._engine

        from importlib.util import find_spec

        if find_spec("databricks.sql") is None:
            raise ImportError(
                "databricks-sql-connector is not installed. Install with: pip install databricks-sql-connector"
            ) from None

        # Use working hostname
        connection_string = f"databricks://token:{self.access_token}@{self.working_hostname}:443{self.http_path}"

        # Create engine with enhanced settings
        self._engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=False,
            # Add retry logic
            connect_args={
                "retry_delay": 1,
                "max_retries": 3,
            },
        )

        logger.info(f"Databricks engine created for {self.working_hostname}{self.http_path}")
        return self._engine

    def validate_connection(self) -> bool:
        """Validate connection with enhanced error handling."""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                from databricks import sql

                with sql.connect(
                    server_hostname=self.working_hostname,
                    http_path=self.http_path,
                    access_token=self.access_token,
                    # Add connection timeout
                    connection_timeout=30,
                ) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result:
                            logger.info(f"Databricks connection validated successfully (attempt {attempt + 1})")
                            return True

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All connection attempts failed for {self.working_hostname}")
                    return False

        return False

    async def validate_connection_async(self) -> bool:
        """Validate connection with enhanced error handling (async)."""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                from databricks import sql

                def _connect():
                    return sql.connect(
                        server_hostname=self.working_hostname,
                        http_path=self.http_path,
                        access_token=self.access_token,
                        connection_timeout=30,
                    )

                conn = await asyncio.to_thread(_connect)
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result:
                            logger.info(f"Databricks connection validated successfully (attempt {attempt + 1})")
                            return True

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"All connection attempts failed for {self.working_hostname}")
                    return False

        return False

    def get_connection_string(self, mask_token: bool = True) -> str:
        """Get connection string for debugging."""
        token = _redact_token(self.access_token) if mask_token else self.access_token
        return f"databricks://token:{token}@{self.working_hostname}:443{self.http_path}"


# Factory functions
def create_enhanced_databricks_engine() -> Engine:
    """Create enhanced Databricks engine."""
    connector = EnhancedDatabricksConnector()
    return connector.create_engine()


def validate_enhanced_databricks_connection() -> bool:
    """Validate enhanced Databricks connection."""
    try:
        connector = EnhancedDatabricksConnector()
        return connector.validate_connection()
    except Exception as e:
        logger.error(f"Enhanced Databricks connection validation error: {e}")
        return False
