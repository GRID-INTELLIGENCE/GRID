#!/usr/bin/env python3
"""
Filesystem Monitor for Critical Files
=====================================
Uses watchdog to monitor critical files and directories for unauthorized changes.
Alerts on modifications to sensitive files like .env, certificates, and MCP server files.
"""

import logging
import os
import sys
import time
from pathlib import Path

# Calculate path relative to this file's location
_grid_src_path = Path(__file__).parent.parent.parent.parent / 'work' / 'GRID' / 'src'
sys.path.insert(0, str(_grid_src_path))

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    print("watchdog not installed. Install with: pip install watchdog")
    WATCHDOG_AVAILABLE = False
    # Create dummy classes to prevent NameError
    FileSystemEventHandler = object  # type: ignore[assignment,misc]
    Observer = None  # type: ignore[assignment,misc]

try:
    from grid.security.audit_logger import get_audit_logger, AuditEventType, initialize_audit_logger
except ImportError as e:
    print(f"Warning: Could not import audit_logger: {e}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure alerts logging
alerts_logger = logging.getLogger('filesystem.alerts')
alerts_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), '../../../security/logs/alerts.log'))
alerts_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
alerts_logger.addHandler(alerts_handler)
alerts_logger.setLevel(logging.WARNING)
alerts_logger.propagate = False


class CriticalFileHandler(FileSystemEventHandler):
    """Handler for filesystem events on critical files"""

    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        # Define critical file patterns
        self.critical_patterns = [
            '.env',
            'production_server.py',
            'server.py',
            '*.key',
            '*.pem',
            '*.crt',
            'config.json',
            'secrets.json'
        ]

    def _is_critical_file(self, path: str) -> bool:
        """Check if file is critical"""
        file_name = os.path.basename(path)
        for pattern in self.critical_patterns:
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(file_name, pattern):
                    return True
            elif file_name == pattern:
                return True
        return False

    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory and self._is_critical_file(event.src_path):
            message = f"CRITICAL FILE MODIFIED: {event.src_path}"
            alerts_logger.warning(message)
            logger.warning(message)
            self.audit_logger.log_event(
                AuditEventType.SECRET_ACCESS,
                f"Critical file modified: {event.src_path}",
                resource=event.src_path,
                outcome="warning",
                metadata={"event": "modified", "type": "critical_file"}
            )

    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory and self._is_critical_file(event.src_path):
            message = f"CRITICAL FILE CREATED: {event.src_path}"
            alerts_logger.warning(message)
            logger.warning(message)
            self.audit_logger.log_event(
                AuditEventType.SECRET_ACCESS,
                f"Critical file created: {event.src_path}",
                resource=event.src_path,
                outcome="warning",
                metadata={"event": "created", "type": "critical_file"}
            )

    def on_deleted(self, event):
        """Handle file deletion"""
        if not event.is_directory and self._is_critical_file(event.src_path):
            message = f"CRITICAL FILE DELETED: {event.src_path}"
            alerts_logger.error(message)
            logger.error(message)
            self.audit_logger.log_event(
                AuditEventType.SECRET_ACCESS,
                f"Critical file deleted: {event.src_path}",
                resource=event.src_path,
                outcome="error",
                metadata={"event": "deleted", "type": "critical_file"}
            )


def main():
    """Main monitoring function"""
    if not WATCHDOG_AVAILABLE:
        logger.error("Watchdog not available. Cannot monitor filesystem.")
        return

    audit_logger = initialize_audit_logger()

    # Define paths to monitor
    watch_paths = [
        'e:/grid/.env',
        'e:/grid/work/GRID/workspace/mcp/servers/filesystem/',
        'e:/grid/work/GRID/workspace/mcp/servers/playwright/',
        'e:/grid/security/',
        'e:/grid/config/',
    ]

    # Filter existing paths
    existing_paths = [p for p in watch_paths if os.path.exists(p)]

    if not existing_paths:
        logger.error("No valid paths to monitor")
        return

    logger.info(f"Starting filesystem monitor for: {existing_paths}")

    event_handler = CriticalFileHandler(audit_logger)
    observer = Observer()

    for path in existing_paths:
        observer.schedule(event_handler, path, recursive=True)
        logger.info(f"Monitoring: {path}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping filesystem monitor")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
