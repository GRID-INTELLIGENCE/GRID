from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.mothership.db.engine import dispose_async_engine, get_async_engine


@pytest.mark.asyncio
async def test_db_engine_metrics_and_disposal():
    """Test engine creation updates metrics and disposal clears them."""

    # Mock sqlalchemy create_async_engine to avoid real DB connections
    with (
        patch("application.mothership.db.engine.create_async_engine") as mock_create,
        patch("application.mothership.db.engine.METRICS_ENABLED", True),
        patch("application.mothership.db.engine._db_connections") as mock_gauge,
        patch("application.mothership.db.engine._should_auto_init_sqlite", return_value=False),
    ):

        # Setup mock engine
        mock_engine = AsyncMock()
        mock_engine.pool = MagicMock()
        mock_engine.pool.size.return_value = 5
        mock_create.return_value = mock_engine

        # 1. Create Engine
        engine = get_async_engine()

        assert engine == mock_engine
        # Verify metric set to pool size
        mock_gauge.set.assert_called_with(5)

        # 2. Dispose Engine
        await dispose_async_engine()

        # Verify dispose called
        mock_engine.dispose.assert_called_once()
        # Verify metric reset to 0
        mock_gauge.set.assert_called_with(0)

        # 3. Dispose again (idempotence)
        await dispose_async_engine()
        # Should not call dispose again on the same object (removed from global)
        assert mock_engine.dispose.call_count == 1


@pytest.mark.asyncio
async def test_db_engine_databricks_fallback():
    """Verify fallback logic isn't broken by our changes."""
    # This just ensures we didn't break existing logic
    # Partial mock of settings
    with patch("application.mothership.db.engine.get_settings") as mock_settings:
        mock_settings.return_value.database.use_databricks = False
        mock_settings.return_value.database.url = "sqlite+aiosqlite:///:memory:"
        mock_settings.return_value.database.echo = False

        engine = get_async_engine()
        assert engine is not None
        await dispose_async_engine()
