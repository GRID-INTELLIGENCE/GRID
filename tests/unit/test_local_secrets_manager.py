from __future__ import annotations

from pathlib import Path

from src.grid.security.local_secrets_manager import LocalSecretsManager


def test_local_secrets_manager_round_trip(tmp_path: Path) -> None:
    storage_path = tmp_path / "secrets.db"
    manager = LocalSecretsManager(storage_path=storage_path, master_key=b"x" * 32)

    assert manager.set("api_key", "secret-value") is True
    assert manager.get("api_key") == "secret-value"
    assert manager.exists("api_key") is True

    secrets = manager.get_all()
    assert "api_key" in secrets
    assert isinstance(secrets["api_key"].created_at, float)
    assert isinstance(secrets["api_key"].updated_at, float)
