"""Databricks connector for GRID Mothership database."""

from __future__ import annotations

import logging
import os
import re
import socket
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded from .env file")


def _redact_token(token: str) -> str:
    """Redact token for logging."""
    if not token or len(token) < 8:
        return "***"
    return f"{token[:4]}***{token[-4:]}"


class DatabricksConnector:
    """Manages Databricks SQL connections for GRID."""

    def __init__(
        self,
        server_hostname: str | None = None,
        http_path: str | None = None,
        access_token: str | None = None,
    ):
        """Initialize Databricks connector.

        Args:
            server_hostname: Databricks server hostname (from env: DATABRICKS_SERVER_HOSTNAME or DATABRICKS_HOST)
            http_path: HTTP path (from env: DATABRICKS_HTTP_PATH)
            access_token: Access token (from env: local_databricks, DATABRICKS_TOKEN, or DATABRICKS_ACCESS_TOKEN)
        """
        # Support multiple environment variable names for compatibility
        # Priority: DATABRICKS_HOST (standard) > DATABRICKS_SERVER_HOSTNAME (legacy)
        host = (
            server_hostname
            or os.getenv("DATABRICKS_HOST", "").strip()
            or os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip()
        )
        if host:
            # Normalize hostname (remove https://, extract hostname from URL)
            if host.startswith("https://"):
                host = host.replace("https://", "")
            elif host.startswith("http://"):
                host = host.replace("http://", "")
            self.server_hostname = host
        else:
            self.server_hostname = ""

        self.http_path = http_path or os.getenv("DATABRICKS_HTTP_PATH", "").strip()

        # Priority: DATABRICKS_TOKEN (standard) > DATABRICKS_ACCESS_TOKEN > local_databricks (custom)
        self.access_token = (
            access_token
            or os.getenv("DATABRICKS_TOKEN", "").strip()
            or os.getenv("DATABRICKS_ACCESS_TOKEN", "").strip()
            or os.getenv("local_databricks", "").strip()
        )

        if not self.server_hostname:
            raise ValueError("DATABRICKS_SERVER_HOSTNAME is required")
        if not self.http_path:
            raise ValueError("DATABRICKS_HTTP_PATH is required")
        if not self.access_token:
            raise ValueError("DATABRICKS_ACCESS_TOKEN is required")

        # Validate token format (Databricks tokens start with 'dapi')
        if not self.access_token.startswith("dapi"):
            logger.warning(
                f"Access token format may be invalid (expected 'dapi' prefix). "
                f"Token: {_redact_token(self.access_token)}"
            )

        # Try to find working hostname if DNS resolution fails
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
        """Create SQLAlchemy engine for Databricks.

        Returns:
            SQLAlchemy engine configured for Databricks
        """
        if self._engine is not None:
            return self._engine

        from importlib.util import find_spec

        if find_spec("databricks.sql") is None:
            raise ImportError(
                "databricks-sql-connector is not installed. " "Install with: pip install databricks-sql-connector"
            ) from None

        # Build connection string for Databricks
        # Use working hostname instead of original
        connection_string = f"databricks://token:{self.access_token}@" f"{self.working_hostname}:443{self.http_path}"

        # Create engine with appropriate settings
        self._engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=False,  # Don't log SQL queries (security)
        )
        logger.info(f"Databricks engine created for {self.working_hostname}{self.http_path}")
        return self._engine

    def validate_connection(self) -> bool:
        """Validate Databricks connection with retry logic.

        Returns:
            True if connection is valid, False otherwise
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Use databricks connector directly for validation
                from databricks import sql  # noqa: F401

                with sql.connect(
                    server_hostname=self.working_hostname,
                    http_path=self.http_path,
                    access_token=self.access_token,
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
                    error_msg = str(e)
                    error_msg = re.sub(
                        r"token:[^\s@]+",
                        lambda m: f"token:{_redact_token(m.group(0).split(':')[1])}",
                        error_msg,
                    )
                    logger.error(f"All connection attempts failed for {self.working_hostname}: {error_msg}")
                    return False

        return False

    def get_connection_string(self, mask_token: bool = True) -> str:
        """Get connection string (for logging/debugging).

        Args:
            mask_token: If True, mask the token in the output

        Returns:
            Connection string
        """
        token = _redact_token(self.access_token) if mask_token else self.access_token
        return f"databricks://token:{token}@{self.working_hostname}:443{self.http_path}"


def create_databricks_engine() -> Engine:
    """Create Databricks engine from environment variables.

    Returns:
        SQLAlchemy engine for Databricks

    Raises:
        ValueError: If required environment variables are missing
    """
    connector = DatabricksConnector()
    return connector.create_engine()


def validate_databricks_connection() -> bool:
    """Validate Databricks connection from environment variables.

    Returns:
        True if connection is valid, False otherwise
    """
    try:
        connector = DatabricksConnector()
        return connector.validate_connection()
    except Exception as e:
        logger.error(f"Databricks connection validation error: {str(e)}")
        return False
