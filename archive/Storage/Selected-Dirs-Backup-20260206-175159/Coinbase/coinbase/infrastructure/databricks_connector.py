"""
Databricks Connector
=====================
Seamless local-to-cloud connection for Coinbase.

Reference: Compass - Points to direction (cloud connection)
"""

import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

try:
    from databricks import sql
except ImportError:  # pragma: no cover - handled via offline mode
    sql = None

logger = logging.getLogger(__name__)


class DatabricksConnector:
    """
    Seamless Databricks connection manager.

    Like a Compass pointing to the cloud direction.
    Auto-manages connections with context managers.
    """

    def __init__(self) -> None:
        """Initialize connector from environment variables."""
        self.offline_mode = os.getenv("DATABRICKS_OFFLINE", "").lower() in {"1", "true", "yes"}
        self.connection_params = {
            "server_hostname": os.getenv("DATABRICKS_HOST"),
            "http_path": os.getenv("DATABRICKS_HTTP_PATH"),
            "access_token": os.getenv("DATABRICKS_TOKEN"),
        }
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """Validate required credentials are present."""
        if self.offline_mode:
            logger.info("DatabricksConnector running in offline mode")
            return

        missing = [k for k, v in self.connection_params.items() if not v]

        if missing:
            logger.warning(f"Missing Databricks credentials: {missing}")
            raise ValueError(f"Databricks credentials not found. Set: {', '.join(missing)}")

    @contextmanager
    def connect(self) -> Iterator[Any]:
        """
        Auto-managed connection context.

        Yields connection and auto-closes on exit.
        """
        conn = None
        try:
            if self.offline_mode:
                conn = _DummyConnection()
                logger.info("Databricks offline connection established")
            else:
                if sql is None:
                    raise ImportError("databricks-sql-connector is not installed")
                conn = sql.connect(**self.connection_params)
                logger.info("Databricks connection established")
            yield conn
        except Exception as e:
            logger.error(f"Databricks connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Databricks connection closed")

    def test_connection(self) -> bool:
        """
        Test Databricks connectivity.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            logger.info("✓ Databricks connection test successful")
            return True
        except Exception as e:
            logger.error(f"✗ Databricks connection test failed: {e}")
            return False

    def execute_query(
        self, query: str, params: tuple | None = None, fetch: bool = True
    ) -> Any | None:
        """
        Execute SQL query with parameterized safety.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            Query results if fetch=True, else None
        """
        with self.connect() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                return cursor.fetchall()

            conn.commit()
            return None

    def get_connection_info(self) -> dict[str, Any]:
        """
        Get connection information.

        Returns:
            Connection metadata
        """
        return {
            "server_hostname": self.connection_params["server_hostname"],
            "http_path": self.connection_params["http_path"],
            "has_token": bool(self.connection_params["access_token"]),
            "timestamp": datetime.now().isoformat(),
        }


# Singleton instance
_connector: DatabricksConnector | None = None


def get_connector() -> DatabricksConnector:
    """
    Get singleton Databricks connector instance.

    Returns:
        DatabricksConnector instance
    """
    global _connector
    if _connector is None:
        _connector = DatabricksConnector()
    return _connector


class _DummyCursor:
    """Offline cursor stub."""

    def execute(self, _query: str, _params: tuple | None = None) -> None:
        return None

    def fetchall(self) -> list[Any]:
        return []

    def fetchone(self) -> tuple[Any, ...]:
        return (1,)


class _DummyConnection:
    """Offline connection stub."""

    def cursor(self) -> _DummyCursor:
        return _DummyCursor()

    def commit(self) -> None:
        return None

    def close(self) -> None:
        return None


# Example usage
def example_usage() -> None:
    """Example usage of DatabricksConnector."""
    import os

    # Check if credentials available
    if not all(
        [
            os.getenv("DATABRICKS_HOST"),
            os.getenv("DATABRICKS_HTTP_PATH"),
            os.getenv("DATABRICKS_TOKEN"),
        ]
    ):
        print("⚠ Databricks credentials not found")
        print("Set DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN")
        return

    # Initialize connector
    connector = DatabricksConnector()

    # Test connection
    if connector.test_connection():
        print("✓ Connection successful")

        # Get connection info
        info = connector.get_connection_info()
        print(f"Server: {info['server_hostname']}")
        print(f"HTTP Path: {info['http_path']}")

        # Execute query
        results = connector.execute_query("SELECT 1 as test")
        print(f"Query result: {results[0] if results else 'None'}")
    else:
        print("✗ Connection failed")


if __name__ == "__main__":
    example_usage()
