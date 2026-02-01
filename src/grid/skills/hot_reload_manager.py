"""
Hot-reload manager for skills with debouncing and rollback support.

Audio engineering-inspired approach:
- Debouncing: Prevent race conditions from rapid file changes
- Rollback on failure: If reload fails, restore from backup
- Sequential processing: Process changes one at a time to avoid conflicts
"""

import importlib
import logging
import shutil
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

# Note: watchdog is an optional dependency for hot-reloading
try:
    from watchdog.events import (  # type: ignore[import-not-found]
        FileCreatedEvent,
        FileModifiedEvent,
        FileSystemEventHandler,
    )
    from watchdog.observers import Observer  # type: ignore[import-not-found]

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


@dataclass
class ReloadResult:
    skill_id: str
    status: str  # "success", "failed", "rollback"
    timestamp: float
    error: str | None
    rollback_from: str | None


class HotReloadManager:
    """
    Manages hot-reload for skills with robust error handling.
    """

    # CONFIRMED PARAMETERS
    DEBOUNCE_DELAY_S = 0.5  # 500ms
    MAX_RELOAD_TIMEOUT_S = 10
    BACKUP_DIR = Path("./data/skills_backups")

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, skills_dir: Path | None = None):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._logger = logging.getLogger(__name__)
        self._skills_dir = skills_dir or Path(__file__).parent
        self._initialized = True

        # Tracking
        self._pending_changes: dict[str, float] = {}  # skill_id -> last change timestamp
        self._reload_queue: deque[str] = deque(maxlen=50)
        self._processing = False
        self._observer = None

        self._backup_dir = Path(self.BACKUP_DIR)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        self._timer: threading.Timer | None = None

    @classmethod
    def get_instance(cls) -> "HotReloadManager":
        if cls._instance is None:
            cls()
        return cls._instance

    def start(self) -> bool:
        """Start hot-reload file watching."""
        if not WATCHDOG_AVAILABLE:
            self._logger.warning("Hot-reload disabled: 'watchdog' package not installed.")
            return False

        if self._observer and self._observer.is_alive():
            return True

        handler = SkillFileChangeHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._skills_dir), recursive=False)
        self._observer.start()

        self._logger.info(f"Hot-reload started for {self._skills_dir}")
        return True

    def stop(self) -> None:
        """Stop hot-reload file watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        if self._timer:
            self._timer.cancel()
            self._timer = None

        self._logger.info("Hot-reload stopped")

    def _create_backup(self, skill_id: str) -> Path | None:
        """Create backup of current skill file."""
        try:
            skill_file = self._skills_dir / f"{skill_id}.py"
            if not skill_file.exists():
                return None

            timestamp = int(time.time() * 1000)
            backup_file = self._backup_dir / f"{skill_id}_backup_{timestamp}.py"
            shutil.copy2(skill_file, backup_file)
            return backup_file
        except Exception as e:
            self._logger.error(f"Failed to create backup for {skill_id}: {e}")
            return None

    def _reload_skill(self, skill_id: str) -> ReloadResult:
        """Reload a specific skill with rollback on failure."""
        self._logger.info(f"Attempting to reload skill: {skill_id}")
        time.time()
        backup_file = None

        try:
            # Create backup before reload
            backup_file = self._create_backup(skill_id)

            # Module name resolution
            module_name = f"grid.skills.{skill_id}"

            # Clear from sys.modules to force full reload
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Import again
            module = importlib.import_module(module_name)
            importlib.reload(module)

            # Re-registry logic
            from .discovery_engine import SkillDiscoveryEngine
            from .registry import default_registry

            # We use discovery engine to find the Skill instance in the module
            engine = SkillDiscoveryEngine()
            skills = engine.discover_in_module(module_name, module)

            if not skills:
                raise ValueError(f"No Skill instances found in reloaded module {module_name}")

            for skill in skills:
                default_registry.register(skill)
                self._logger.info(f"Successfully re-registered skill: {skill.id}")

            return ReloadResult(
                skill_id=skill_id, status="success", timestamp=time.time(), error=None, rollback_from=None
            )

        except Exception as e:
            self._logger.error(f"Reload failed for {skill_id}: {e}")

            if backup_file:
                self._logger.warning(f"Rolling back {skill_id} to {backup_file.name}")
                try:
                    shutil.copy2(backup_file, self._skills_dir / f"{skill_id}.py")
                    # No need to reload again here as the file is restored
                    # Next change will trigger another reload if needed
                    return ReloadResult(
                        skill_id=skill_id,
                        status="rollback",
                        timestamp=time.time(),
                        error=str(e),
                        rollback_from=backup_file.name,
                    )
                except Exception as rb_err:
                    self._logger.error(f"Rollback failed: {rb_err}")

            return ReloadResult(
                skill_id=skill_id, status="failed", timestamp=time.time(), error=str(e), rollback_from=None
            )

    def _on_file_changed(self, skill_id: str):
        """Handle debounced file change."""
        with self._lock:
            if skill_id not in self._reload_queue:
                self._reload_queue.append(skill_id)

            if not self._processing:
                self._process_queue()

    def _process_queue(self):
        """Process reload queue sequentially."""
        if not self._reload_queue:
            self._processing = False
            return

        self._processing = True
        skill_id = self._reload_queue.popleft()

        # Run in thread to avoid blocking
        def run_reload():
            self._reload_skill(skill_id)
            with self._lock:
                self._process_queue()

        threading.Thread(target=run_reload, daemon=True).start()

    def schedule_reload(self, skill_id: str):
        """Schedule a reload with debouncing."""
        if self._timer:
            self._timer.cancel()

        self._timer = threading.Timer(self.DEBOUNCE_DELAY_S, self._on_file_changed, args=[skill_id])
        self._timer.start()


if WATCHDOG_AVAILABLE:

    class SkillFileChangeHandler(FileSystemEventHandler):
        def __init__(self, manager: HotReloadManager):
            self.manager = manager

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                skill_id = Path(event.src_path).stem
                if not skill_id.startswith("_"):
                    self.manager.schedule_reload(skill_id)

        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                skill_id = Path(event.src_path).stem
                if not skill_id.startswith("_"):
                    self.manager.schedule_reload(skill_id)

else:

    class SkillFileChangeHandler:
        pass
