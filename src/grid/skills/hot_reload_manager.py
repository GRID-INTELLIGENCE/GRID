"""
Hot-reload manager for skills with debouncing and rollback support.

Audio engineering-inspired approach:
- Debouncing: Prevent race conditions from rapid file changes
- Rollback on failure: If reload fails, restore from backup
- Sequential processing: Process changes one at a time to avoid conflicts
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import shutil
import sys
import threading
import time
import tracemalloc
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

# Import safe module utilities
from grid.security.module_utils import cleanup_module, safe_reload

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

    class FileCreatedEvent:  # type: ignore[no-redef]
        pass

    class FileModifiedEvent:  # type: ignore[no-redef]
        pass

    class FileSystemEventHandler:  # type: ignore[no-redef]
        pass

    class Observer:  # type: ignore[no-redef]
        def is_alive(self) -> bool:  # pragma: no cover - stub for typing
            return False

        def schedule(self, handler: Any, path: str, recursive: bool = False) -> None:  # pragma: no cover - stub
            return None

        def start(self) -> None:  # pragma: no cover - stub
            return None

        def stop(self) -> None:  # pragma: no cover - stub
            return None

        def join(self) -> None:  # pragma: no cover - stub
            return None


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

    _instance: ClassVar[HotReloadManager | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> HotReloadManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, skills_dir: Path | None = None) -> None:
        if self._initialized:
            return

        self._logger = logging.getLogger(__name__)
        self._skills_dir = skills_dir or Path(__file__).parent
        self._initialized = True

        # Tracking
        self._pending_changes: dict[str, float] = {}  # skill_id -> last change timestamp
        self._reload_queue: deque[str] = deque(maxlen=50)
        self._processing: bool = False
        self._observer: Observer | None = None

        self._backup_dir = Path(self.BACKUP_DIR)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        self._timer: threading.Timer | None = None

    @classmethod
    def get_instance(cls) -> HotReloadManager:
        if cls._instance is None:
            cls()
        assert cls._instance is not None
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

    @contextmanager
    def _isolate_module(self, module_name: str):
        """
        Safely isolate module state during reloading.
        Backs up the module in sys.modules and restores it if needed.
        """
        backup = sys.modules.get(module_name)
        try:
            yield
        except Exception:
            if backup:
                sys.modules[module_name] = backup
            raise
        finally:
            pass

    def _verify_module_cleanup(self, module_name: str, before_modules: set[str]) -> None:
        """Verify that no orphan sub-modules were leaked."""
        after_modules = set(sys.modules.keys())
        leaked = after_modules - before_modules
        if leaked:
            self._logger.warning(f"Detection: Module {module_name} reload leaked sub-modules: {leaked}")
        else:
            self._logger.debug(f"Integrity check passed for {module_name}")

    def _safe_reload(self, module_name: str) -> Any:
        """
        Perform a safe reload using importlib.util for fresh state.
        Avoids direct 'del sys.modules[name]' which can cause reference orphaning.
        """
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            raise ImportError(f"Cannot find module spec for {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        if spec.loader:
            spec.loader.exec_module(module)
        return module

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

            # Step 1: Record module state before reload
            before_modules = set(sys.modules.keys())

            # Start memory tracking if not already started
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()

            # Step 2: Safe reload within isolation context
            with self._isolate_module(module_name):
                # Use the new safe_reload utility instead of _safe_reload
                module = safe_reload(module_name)

            # Step 3: Verify integrity and memory
            self._verify_module_cleanup(module_name, before_modules)

            snapshot_after = tracemalloc.take_snapshot()
            stats = snapshot_after.compare_to(snapshot_before, "lineno")
            top_stats = stats[:3]
            if top_stats:
                self._logger.debug(f"Memory delta for {module_name} reload: {top_stats}")

            # Re-registry logic
            from .registry import default_registry

            # Discover Skill instances directly from the reloaded module
            skills = self._discover_skills_in_module(module)

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

    def _on_file_changed(self, skill_id: str) -> None:
        """Handle debounced file change."""
        with self._lock:
            if skill_id not in self._reload_queue:
                self._reload_queue.append(skill_id)

            if not self._processing:
                self._process_queue()

    def _process_queue(self) -> None:
        """Process reload queue sequentially."""
        if not self._reload_queue:
            self._processing = False
            return

        self._processing = True
        skill_id = self._reload_queue.popleft()

        # Run in thread to avoid blocking
        def run_reload() -> None:
            self._reload_skill(skill_id)
            with self._lock:
                self._process_queue()

        threading.Thread(target=run_reload, daemon=True).start()

    def schedule_reload(self, skill_id: str) -> None:
        """Schedule a reload with debouncing."""
        if self._timer:
            self._timer.cancel()

        self._timer = threading.Timer(self.DEBOUNCE_DELAY_S, self._on_file_changed, args=[skill_id])
        self._timer.start()

    def _discover_skills_in_module(self, module: Any) -> list[Any]:
        """Discover Skill instances in a module (used for hot reload)."""
        from .base import Skill

        discovered: list[Skill] = []
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue

            if hasattr(obj, "id") and hasattr(obj, "run") and callable(getattr(obj, "run", None)):
                if inspect.isclass(obj):
                    try:
                        obj = obj()
                    except Exception:
                        continue

                if getattr(obj, "id", None):
                    discovered.append(cast(Skill, obj))

        return discovered


class _BaseSkillFileChangeHandler:
    def __init__(self, manager: HotReloadManager) -> None:
        self.manager = manager

    def on_modified(self, event: Any) -> None:
        return None

    def on_created(self, event: Any) -> None:
        return None


if WATCHDOG_AVAILABLE:

    class SkillFileChangeHandler(FileSystemEventHandler, _BaseSkillFileChangeHandler):
        def on_modified(self, event: FileModifiedEvent) -> None:
            if not event.is_directory and event.src_path.endswith(".py"):
                skill_id = Path(event.src_path).stem
                if not skill_id.startswith("_"):
                    self.manager.schedule_reload(skill_id)

        def on_created(self, event: FileCreatedEvent) -> None:
            if not event.is_directory and event.src_path.endswith(".py"):
                skill_id = Path(event.src_path).stem
                if not skill_id.startswith("_"):
                    self.manager.schedule_reload(skill_id)

else:

    class SkillFileChangeHandler(_BaseSkillFileChangeHandler):
        def on_modified(self, event: Any) -> None:
            pass

        def on_created(self, event: Any) -> None:
            pass
