"""Databricks Notebooks management."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class DatabricksNotebooksManager:
    """Manage Databricks notebooks."""

    def __init__(self, client) -> None:
        """Initialize notebooks manager.

        Args:
            client: DatabricksClient instance
        """
        self.client = client

    def read_notebook(self, path: str) -> str:
        """Read notebook content.

        Args:
            path: Notebook path in workspace

        Returns:
            Notebook content
        """
        try:
            notebook = self.client.workspace.read(path=path)
            logger.info(f"Read notebook from {path}")
            return notebook.content
        except Exception as e:
            logger.error(f"Failed to read notebook {path}: {e}")
            raise

    def write_notebook(self, path: str, content: str, format: str = "SOURCE") -> None:
        """Write notebook content.

        Args:
            path: Notebook path in workspace
            content: Notebook content
            format: Format (SOURCE, HTML, JUPYTER, DBC)
        """
        try:
            self.client.workspace.write(path=path, content=content, format=format, overwrite=True)
            logger.info(f"Wrote notebook to {path}")
        except Exception as e:
            logger.error(f"Failed to write notebook {path}: {e}")
            raise

    def list_directory(self, path: str) -> list[dict[str, str]]:
        """List directory contents.

        Args:
            path: Directory path

        Returns:
            List of objects (notebooks, directories, etc.)
        """
        try:
            objects = self.client.workspace.list(path=path)
            return [
                {
                    "path": obj.path,
                    "object_type": obj.object_type,
                }
                for obj in objects
            ]
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return []

    def delete_notebook(self, path: str) -> bool:
        """Delete a notebook.

        Args:
            path: Notebook path

        Returns:
            True if successful
        """
        try:
            self.client.workspace.delete(path=path)
            logger.info(f"Deleted notebook {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete notebook {path}: {e}")
            return False
