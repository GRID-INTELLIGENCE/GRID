"""
Backup and Recovery System
===========================
Comprehensive backup strategy for database, configuration, and disaster recovery.

Usage:
    from coinbase.core.backup_manager import BackupManager, BackupConfig

    config = BackupConfig(
        backup_dir="backups",
        retention_days=30
    )

    manager = BackupManager(config)
    manager.create_full_backup()
"""

import gzip
import hashlib
import json
import logging
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """Configuration for backup system."""

    backup_dir: str = "backups"
    retention_days: int = 30
    compress_backups: bool = True
    encrypt_backups: bool = False
    encryption_key: str | None = None
    include_databases: bool = True
    include_configs: bool = True
    include_logs: bool = False
    auto_cleanup: bool = True


@dataclass
class BackupInfo:
    """Information about a backup."""

    id: str
    timestamp: datetime
    type: str
    size_bytes: int
    checksum: str
    status: str
    components: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class BackupManager:
    """
    Comprehensive backup and recovery manager.

    Features:
    - Database backups
    - Configuration backups
    - Automated cleanup
    - Integrity verification
    - Disaster recovery
    """

    def __init__(self, config: BackupConfig | None = None):
        """
        Initialize backup manager.

        Args:
            config: Backup configuration
        """
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.db_backup_dir = self.backup_dir / "database"
        self.config_backup_dir = self.backup_dir / "config"
        self.full_backup_dir = self.backup_dir / "full"

        for dir_path in [self.db_backup_dir, self.config_backup_dir, self.full_backup_dir]:
            dir_path.mkdir(exist_ok=True)

        self._backup_manifest: dict[str, BackupInfo] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load backup manifest."""
        manifest_file = self.backup_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    data = json.load(f)
                    for backup_id, info_data in data.items():
                        self._backup_manifest[backup_id] = BackupInfo(
                            id=info_data["id"],
                            timestamp=datetime.fromisoformat(info_data["timestamp"]),
                            type=info_data["type"],
                            size_bytes=info_data["size_bytes"],
                            checksum=info_data["checksum"],
                            status=info_data["status"],
                            components=info_data["components"],
                            metadata=info_data.get("metadata", {}),
                        )
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")

    def _save_manifest(self) -> None:
        """Save backup manifest."""
        manifest_file = self.backup_dir / "manifest.json"
        try:
            data = {}
            for backup_id, info in self._backup_manifest.items():
                data[backup_id] = {
                    "id": info.id,
                    "timestamp": info.timestamp.isoformat(),
                    "type": info.type,
                    "size_bytes": info.size_bytes,
                    "checksum": info.checksum,
                    "status": info.status,
                    "components": info.components,
                    "metadata": info.metadata,
                }

            with open(manifest_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")

    def create_database_backup(self, db_path: str | None = None) -> BackupInfo | None:
        """
        Create database backup.

        Args:
            db_path: Optional database path

        Returns:
            BackupInfo or None
        """
        if not self.config.include_databases:
            logger.info("Database backups disabled")
            return None

        try:
            backup_id = f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.db_backup_dir / backup_id

            # Create backup based on database type
            if db_path and Path(db_path).exists():
                # SQLite backup
                import sqlite3

                backup_db_path = backup_path / "database.db"
                backup_path.mkdir(parents=True, exist_ok=True)

                source = sqlite3.connect(db_path)
                dest = sqlite3.connect(backup_db_path)
                source.backup(dest)
                source.close()
                dest.close()

                # Compress if enabled
                if self.config.compress_backups:
                    compressed_path = self._compress_file(backup_db_path)
                    shutil.rmtree(backup_path)
                    backup_path = compressed_path
            else:
                # Databricks schema backup
                backup_path = self._backup_databricks_schema(backup_id)

            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            size = backup_path.stat().st_size if backup_path.exists() else 0

            info = BackupInfo(
                id=backup_id,
                timestamp=datetime.now(),
                type="database",
                size_bytes=size,
                checksum=checksum,
                status="completed",
                components=["database"],
            )

            self._backup_manifest[backup_id] = info
            self._save_manifest()

            logger.info(f"Database backup created: {backup_id}")
            return info

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None

    def create_config_backup(self) -> BackupInfo | None:
        """
        Create configuration backup.

        Returns:
            BackupInfo or None
        """
        if not self.config.include_configs:
            logger.info("Config backups disabled")
            return None

        try:
            backup_id = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.config_backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup configuration files
            config_files = [".env", "pyproject.toml", "env.template"]

            for config_file in config_files:
                if Path(config_file).exists():
                    shutil.copy2(config_file, backup_path / config_file)

            # Create tar archive
            archive_path = self.config_backup_dir / f"{backup_id}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=".")

            # Cleanup temp directory
            shutil.rmtree(backup_path)

            # Calculate checksum
            checksum = self._calculate_checksum(archive_path)
            size = archive_path.stat().st_size

            info = BackupInfo(
                id=backup_id,
                timestamp=datetime.now(),
                type="config",
                size_bytes=size,
                checksum=checksum,
                status="completed",
                components=["configuration"],
            )

            self._backup_manifest[backup_id] = info
            self._save_manifest()

            logger.info(f"Config backup created: {backup_id}")
            return info

        except Exception as e:
            logger.error(f"Config backup failed: {e}")
            return None

    def create_full_backup(self) -> BackupInfo | None:
        """
        Create full system backup.

        Returns:
            BackupInfo or None
        """
        try:
            backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.full_backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)

            components = []

            # Database backup
            if self.config.include_databases:
                db_backup = self.create_database_backup()
                if db_backup:
                    components.append("database")

            # Config backup
            if self.config.include_configs:
                config_backup = self.create_config_backup()
                if config_backup:
                    components.append("configuration")

            # Create manifest for this backup
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "components": components,
                "system_info": self._get_system_info(),
            }

            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)

            # Create archive
            archive_path = self.full_backup_dir / f"{backup_id}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=".")

            # Cleanup
            shutil.rmtree(backup_path)

            # Calculate checksum
            checksum = self._calculate_checksum(archive_path)
            size = archive_path.stat().st_size

            info = BackupInfo(
                id=backup_id,
                timestamp=datetime.now(),
                type="full",
                size_bytes=size,
                checksum=checksum,
                status="completed",
                components=components,
                metadata={"system_info": manifest["system_info"]},
            )

            self._backup_manifest[backup_id] = info
            self._save_manifest()

            # Cleanup old backups
            if self.config.auto_cleanup:
                self.cleanup_old_backups()

            logger.info(f"Full backup created: {backup_id}")
            return info

        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return None

    def restore_backup(self, backup_id: str, target_dir: str | None = None) -> bool:
        """
        Restore from backup.

        Args:
            backup_id: Backup ID to restore
            target_dir: Optional target directory

        Returns:
            True if restore successful
        """
        try:
            info = self._backup_manifest.get(backup_id)
            if not info:
                logger.error(f"Backup not found: {backup_id}")
                return False

            # Determine backup location
            if info.type == "database":
                backup_path = self.db_backup_dir / backup_id
            elif info.type == "config":
                backup_path = self.config_backup_dir / f"{backup_id}.tar.gz"
            else:
                backup_path = self.full_backup_dir / f"{backup_id}.tar.gz"

            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Verify checksum
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != info.checksum:
                logger.error("Backup checksum mismatch")
                return False

            # Restore based on type
            target = Path(target_dir) if target_dir else Path("restored")
            target.mkdir(parents=True, exist_ok=True)

            if backup_path.suffix == ".gz":
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(target)
            else:
                shutil.copytree(backup_path, target / backup_id)

            logger.info(f"Backup restored: {backup_id} -> {target}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_id: Backup ID to verify

        Returns:
            True if backup is valid
        """
        try:
            info = self._backup_manifest.get(backup_id)
            if not info:
                return False

            # Determine backup location
            if info.type == "database":
                backup_path = self.db_backup_dir / backup_id
                if backup_path.suffix == ".gz":
                    backup_path = self.db_backup_dir / f"{backup_id}.db.gz"
            elif info.type == "config":
                backup_path = self.config_backup_dir / f"{backup_id}.tar.gz"
            else:
                backup_path = self.full_backup_dir / f"{backup_id}.tar.gz"

            if not backup_path.exists():
                return False

            # Verify checksum
            current_checksum = self._calculate_checksum(backup_path)
            return current_checksum == info.checksum

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period.

        Returns:
            Number of backups removed
        """
        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        removed = 0

        for backup_id, info in list(self._backup_manifest.items()):
            if info.timestamp < cutoff:
                # Remove backup files
                if info.type == "database":
                    backup_path = self.db_backup_dir / backup_id
                    if backup_path.exists():
                        if backup_path.is_dir():
                            shutil.rmtree(backup_path)
                        else:
                            backup_path.unlink()
                elif info.type == "config":
                    backup_path = self.config_backup_dir / f"{backup_id}.tar.gz"
                    if backup_path.exists():
                        backup_path.unlink()
                else:
                    backup_path = self.full_backup_dir / f"{backup_id}.tar.gz"
                    if backup_path.exists():
                        backup_path.unlink()

                del self._backup_manifest[backup_id]
                removed += 1

        if removed > 0:
            self._save_manifest()
            logger.info(f"Cleaned up {removed} old backups")

        return removed

    def list_backups(self, backup_type: str | None = None) -> list[BackupInfo]:
        """
        List available backups.

        Args:
            backup_type: Optional filter by type

        Returns:
            List of backup information
        """
        backups = list(self._backup_manifest.values())

        if backup_type:
            backups = [b for b in backups if b.type == backup_type]

        return sorted(backups, key=lambda x: x.timestamp, reverse=True)

    def get_backup_stats(self) -> dict[str, Any]:
        """Get backup statistics."""
        total_size = sum(b.size_bytes for b in self._backup_manifest.values())

        by_type: dict[str, int] = {}
        for b in self._backup_manifest.values():
            by_type[b.type] = by_type.get(b.type, 0) + 1

        return {
            "total_backups": len(self._backup_manifest),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": by_type,
            "retention_days": self.config.retention_days,
        }

    def _compress_file(self, file_path: Path) -> Path:
        """Compress a file with gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        return compressed_path

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _backup_databricks_schema(self, backup_id: str) -> Path:
        """Backup Databricks schema definition."""
        backup_path = self.db_backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        # Export schema DDL
        from coinbase.database.databricks_schema import get_schema_ddl

        schema_ddl = get_schema_ddl()

        with open(backup_path / "schema.sql", "w") as f:
            f.write(schema_ddl)

        return backup_path

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information for backup manifest."""
        import platform
        import sys

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "backup_timestamp": datetime.now().isoformat(),
            "coinbase_version": "0.1.0",
        }


# Global backup manager instance
_global_backup_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    """Get global backup manager instance."""
    global _global_backup_manager
    if _global_backup_manager is None:
        _global_backup_manager = BackupManager()
    return _global_backup_manager


# Convenience functions
def create_backup(backup_type: str = "full") -> BackupInfo | None:
    """Quick function to create backup."""
    manager = get_backup_manager()

    if backup_type == "database":
        return manager.create_database_backup()
    elif backup_type == "config":
        return manager.create_config_backup()
    else:
        return manager.create_full_backup()


def restore_from_backup(backup_id: str, target_dir: str | None = None) -> bool:
    """Quick function to restore backup."""
    manager = get_backup_manager()
    return manager.restore_backup(backup_id, target_dir)
