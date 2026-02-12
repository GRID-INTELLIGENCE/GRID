#!/usr/bin/env python3
"""
Spawn Monitor - Persistent, Reactive, Cautious MCP Enforcement
Watches MCP configs for enabled servers that violate the denylist.

Features:
- PERSISTENT: Auto-restart, scheduled task integration, state recovery
- REACTIVE: File system watching with immediate response to changes
- CAUTIOUS: Read-only validation, extensive logging, no config mutation
- ALWAYS ACTIVE: Health checks, heartbeat logging, crash recovery
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Try to import watchdog for reactive file monitoring
try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent  # type: ignore
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore


ROOT_DIR = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT_DIR / "scripts"
GRID_SRC_DIR = ROOT_DIR / "grid" / "src"

if SCRIPTS_DIR.exists():
    sys.path.insert(0, str(SCRIPTS_DIR))

if GRID_SRC_DIR.exists():
    sys.path.insert(0, str(GRID_SRC_DIR))

try:
    from safety_aware_server_manager import SafetyAwareServerManager  # type: ignore
    from init_safety_logging import EventType, Severity, create_safety_event  # type: ignore
except Exception as exc:
    raise RuntimeError(f"Failed to import safety modules from {SCRIPTS_DIR}: {exc}") from exc

try:
    from infrastructure.event_bus.event_system import EventBus, EventPriority  # type: ignore
except Exception:
    EventBus = None  # type: ignore
    EventPriority = None  # type: ignore

try:
    from unified_fabric.audit import AuditEventType, init_audit_logger  # type: ignore
except Exception:
    AuditEventType = None  # type: ignore
    init_audit_logger = None  # type: ignore


DEFAULT_DENYLIST_CONFIG = ROOT_DIR / "config" / "server_denylist.json"
DEFAULT_MCP_CONFIGS = [
    ROOT_DIR / "grid" / "mcp-setup" / "mcp_config.json",
    Path("C:/Users/irfan/.cursor/mcp.json"),
]
DEFAULT_SAFETY_LOGS = ROOT_DIR / "wellness_studio" / "ai_safety" / "logs"
DEFAULT_STATE_FILE = ROOT_DIR / "wellness_studio" / "ai_safety" / "monitoring" / ".monitor_state.json"
DEFAULT_BLOCKLIST_CONFIG = ROOT_DIR / "config" / "python_entrypoint_blocklist.json"
HEARTBEAT_INTERVAL = 60  # seconds
REACTIVE_DEBOUNCE = 2  # seconds to wait after file change before validation


@dataclass
class Violation:
    server_name: str
    reason: str
    config_path: Path
    detected_at: str = field(default_factory=lambda: _now_iso())


@dataclass
class BlocklistViolation:
    """Violation for blocked Python commands (py.exe, pyw.exe)"""
    command: str
    pattern_name: str
    config_path: Path
    context: str = ""  # Surrounding text for debugging
    detected_at: str = field(default_factory=lambda: _now_iso())


@dataclass
class MonitorState:
    """Persistent state for crash recovery"""
    started_at: str
    last_heartbeat: str
    total_checks: int = 0
    total_violations: int = 0
    last_violations: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "total_checks": self.total_checks,
            "total_violations": self.total_violations,
            "last_violations": self.last_violations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitorState":
        return cls(
            started_at=data.get("started_at", _now_iso()),
            last_heartbeat=data.get("last_heartbeat", _now_iso()),
            total_checks=data.get("total_checks", 0),
            total_violations=data.get("total_violations", 0),
            last_violations=data.get("last_violations", {}),
        )


class ConfigFileHandler(FileSystemEventHandler):
    """Reactive file watcher for MCP config changes"""

    def __init__(self, callback: Callable[[Path], None], watched_files: Set[Path]):
        self.callback = callback
        self.watched_files = {str(p.resolve()) for p in watched_files}
        self._last_trigger: Dict[str, float] = {}

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path).resolve()
        path_str = str(path)

        # Check if this is a watched file
        if path_str not in self.watched_files:
            return

        # Debounce rapid changes
        now = time.time()
        last = self._last_trigger.get(path_str, 0)
        if now - last < REACTIVE_DEBOUNCE:
            return

        self._last_trigger[path_str] = now
        logging.info("[REACTIVE] Config change detected: %s", path)
        self.callback(path)


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _severity_for_reason(reason: Optional[str]) -> Severity:
    if reason in {"security-concern", "startup-failure"}:
        return Severity.CRITICAL
    if reason in {"missing-dependencies", "resource-intensive"}:
        return Severity.WARNING
    return Severity.ERROR


async def _init_event_bus() -> Optional[EventBus]:
    if EventBus is None:
        return None

    try:
        event_bus = EventBus()
        await event_bus.start()
        return event_bus
    except Exception as exc:
        logging.warning("Event bus unavailable: %s", exc)
        return None


async def _init_audit_logger():
    if init_audit_logger is None:
        return None

    try:
        return await init_audit_logger()
    except Exception as exc:
        logging.warning("Audit logger unavailable: %s", exc)
        return None


async def _emit_violation_events(
    manager: SafetyAwareServerManager,
    violation: Violation,
    event_bus: Optional[EventBus],
    audit_logger,
):
    if manager.safety_logger:
        event = create_safety_event(
            event_type=EventType.VIOLATION_DETECTED,
            severity=_severity_for_reason(violation.reason),
            server_name=violation.server_name,
            denylist_reason=violation.reason,
            context={
                "action": "enabled_denied_server",
                "config_path": str(violation.config_path),
                "monitor": "spawn_monitor",
                "detected_at": violation.detected_at,
            },
        )
        manager.safety_logger.log_event(event)

    if event_bus:
        payload = {
            "server": violation.server_name,
            "reason": violation.reason,
            "config_path": str(violation.config_path),
            "detected_at": violation.detected_at,
        }
        try:
            if EventPriority:
                await event_bus.publish(
                    "safety.violation.detected",
                    payload,
                    source="spawn_monitor",
                    priority=EventPriority.CRITICAL,
                )
            else:
                await event_bus.publish("safety.violation.detected", payload, source="spawn_monitor")
        except Exception as exc:
            logging.warning("Failed to publish safety event: %s", exc)

    if audit_logger and AuditEventType:
        try:
            await audit_logger.log(
                event_type=AuditEventType.SAFETY_VIOLATION,
                project_id="wellness_studio",
                domain="ai_safety",
                action="denylist_violation",
                status="blocked",
                details={
                    "server": violation.server_name,
                    "reason": violation.reason,
                    "config_path": str(violation.config_path),
                    "detected_at": violation.detected_at,
                },
            )
        except Exception as exc:
            logging.warning("Failed to write audit log: %s", exc)


class PersistentSpawnMonitor:
    """
    Persistent, Reactive, Cautious MCP spawn monitor.

    PERSISTENT: Saves state, recovers from crashes, scheduled task integration
    REACTIVE: File system watching for immediate response to config changes
    CAUTIOUS: Read-only, extensive logging, no config mutation
    """

    def __init__(
        self,
        denylist_config: Path,
        mcp_configs: List[Path],
        safety_logs: Path,
        state_file: Path,
        interval_seconds: int = 30,
        total_deny: bool = False,
        blocklist_config: Optional[Path] = None,
    ):
        self.denylist_config = denylist_config
        self.mcp_configs = mcp_configs
        self.safety_logs = safety_logs
        self.state_file = state_file
        self.interval_seconds = interval_seconds
        self.total_deny = total_deny
        self.blocklist_config = blocklist_config or DEFAULT_BLOCKLIST_CONFIG

        self.mode_label = "TOTAL-DENY" if total_deny else "DENYLIST"
        self.running = False
        self.manager: Optional[SafetyAwareServerManager] = None
        self.event_bus: Optional[Any] = None  # type: ignore
        self.audit_logger = None
        self.observer: Optional[Any] = None  # type: ignore

        # State tracking
        self.state: Optional[MonitorState] = None
        self.last_mtimes: Dict[Path, float] = {}
        self.last_denials: Dict[Path, Dict[str, str]] = {}
        self.denylist_mtime: Optional[float] = None

        # Blocklist tracking
        self.blocklist_data: Optional[Dict[str, Any]] = None
        self.blocklist_patterns: Dict[str, re.Pattern] = {}
        self.blocklist_mtime: Optional[float] = None
        self.last_blocklist_violations: Dict[Path, List[str]] = {}

        # Reactive queue for file changes
        self._pending_checks: asyncio.Queue = asyncio.Queue()

    def _load_state(self) -> MonitorState:
        """Load persistent state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    state = MonitorState.from_dict(data)
                    logging.info("[PERSISTENT] Recovered state from %s (started: %s, checks: %d)",
                                 self.state_file, state.started_at, state.total_checks)
                    return state
            except Exception as exc:
                logging.warning("[PERSISTENT] Failed to load state: %s", exc)

        return MonitorState(started_at=_now_iso(), last_heartbeat=_now_iso())

    def _save_state(self):
        """Save persistent state to disk"""
        if self.state is None:
            return

        self.state.last_heartbeat = _now_iso()
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as exc:
            logging.warning("[PERSISTENT] Failed to save state: %s", exc)

    def _load_blocklist(self) -> bool:
        """Load and compile Python entrypoint blocklist patterns"""
        if not self.blocklist_config.exists():
            logging.debug("[BLOCKLIST] Config not found: %s", self.blocklist_config)
            return False

        try:
            current_mtime = self.blocklist_config.stat().st_mtime
            if self.blocklist_mtime is not None and current_mtime == self.blocklist_mtime:
                return True  # Already loaded

            with open(self.blocklist_config, "r") as f:
                self.blocklist_data = json.load(f)

            # Compile regex patterns
            self.blocklist_patterns = {}
            if self.blocklist_data is not None:
                for name, pattern in self.blocklist_data.get("patterns", {}).items():
                try:
                    self.blocklist_patterns[name] = re.compile(pattern)
                except re.error as exc:
                    logging.warning("[BLOCKLIST] Invalid pattern %s: %s", name, exc)

            self.blocklist_mtime = current_mtime
            logging.info("[BLOCKLIST] Loaded %d patterns from %s",
                        len(self.blocklist_patterns), self.blocklist_config)
            return True

        except Exception as exc:
            logging.warning("[BLOCKLIST] Failed to load: %s", exc)
            return False

    def _check_blocklist_violations(self, config_path: Path) -> List[BlocklistViolation]:
        """Check a config file for blocked Python commands (py.exe, pyw.exe)"""
        violations: List[BlocklistViolation] = []

        if not self.blocklist_data or not self.blocklist_patterns:
            return violations

        if not config_path.exists():
            return violations

        try:
            content = config_path.read_text(encoding="utf-8", errors="ignore")

            # Check blocked commands in JSON "command" fields
            blocked_commands = self.blocklist_data.get("blocked_commands", [])

            # Parse JSON to check command fields specifically
            try:
                data = json.loads(content)
                servers = data.get("servers", [])
                if not servers and data.get("mcpServers"):
                    # Cursor format: mcpServers is an object
                    servers = [
                        {"name": k, **v}
                        for k, v in data.get("mcpServers", {}).items()
                    ]

                for server in servers:
                    command = server.get("command", "")
                    name = server.get("name", "unknown")

                    # Check if command is a blocked Python launcher
                    cmd_lower = command.lower()
                    for blocked in blocked_commands:
                        if cmd_lower == blocked.lower() or cmd_lower.endswith(f"\\{blocked.lower()}"):
                            violations.append(BlocklistViolation(
                                command=command,
                                pattern_name="blocked_command",
                                config_path=config_path,
                                context=f"server={name}",
                            ))

                    # Check blocked paths
                    for blocked_path in self.blocklist_data.get("blocked_paths", []):
                        if Path(command).resolve() == Path(blocked_path).resolve():
                            violations.append(BlocklistViolation(
                                command=command,
                                pattern_name="blocked_path",
                                config_path=config_path,
                                context=f"server={name}",
                            ))

            except json.JSONDecodeError:
                # Fall back to regex matching for non-JSON or invalid JSON
                pass

            # Also check for py_launcher pattern in content (catches edge cases)
            if "py_launcher" in self.blocklist_patterns:
                for match in self.blocklist_patterns["py_launcher"].finditer(content):
                    # Get surrounding context
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 30)
                    context = content[start:end].replace("\n", " ").strip()

                    violations.append(BlocklistViolation(
                        command=match.group(0),
                        pattern_name="py_launcher",
                        config_path=config_path,
                        context=context,
                    ))

        except Exception as exc:
            logging.error("[BLOCKLIST] Error checking %s: %s", config_path, exc)

        return violations

    async def _process_blocklist_violations(self, violations: List[BlocklistViolation], config_path: Path):
        """Process blocklist violations with logging"""
        current_keys = [f"{v.command}:{v.pattern_name}" for v in violations]
        previous_keys = self.last_blocklist_violations.get(config_path, [])
        self.last_blocklist_violations[config_path] = current_keys

        for violation in violations:
            key = f"{violation.command}:{violation.pattern_name}"
            if key in previous_keys:
                continue  # Already logged

            logging.warning(
                "[BLOCKLIST VIOLATION] command=%s pattern=%s config=%s context=%s",
                violation.command,
                violation.pattern_name,
                violation.config_path,
                violation.context,
            )

            # Emit safety event
            if self.manager and self.manager.safety_logger:
                event = create_safety_event(
                    event_type=EventType.VIOLATION_DETECTED,
                    severity=Severity.WARNING,
                    server_name=f"blocklist:{violation.command}",
                    denylist_reason="blocked_python_launcher",
                    context={
                        "action": "blocked_command_detected",
                        "command": violation.command,
                        "pattern": violation.pattern_name,
                        "config_path": str(violation.config_path),
                        "context": violation.context,
                        "detected_at": violation.detected_at,
                    },
                )
                self.manager.safety_logger.log_event(event)

            if self.state:
                self.state.total_violations += 1

    def _on_config_change(self, path: Path):
        """Callback for reactive file watching"""
        try:
            self._pending_checks.put_nowait(path)
        except asyncio.QueueFull:
            logging.warning("[REACTIVE] Check queue full, dropping: %s", path)

    def _setup_file_watcher(self):
        """Setup reactive file system watcher"""
        if not WATCHDOG_AVAILABLE:
            logging.warning("[REACTIVE] watchdog not installed, using polling only")
            return

        # Collect all directories to watch
        watch_dirs: Set[Path] = set()
        watched_files: Set[Path] = {self.denylist_config, self.blocklist_config}

        for config in self.mcp_configs:
            watched_files.add(config)
            if config.parent.exists():
                watch_dirs.add(config.parent)

        if self.denylist_config.parent.exists():
            watch_dirs.add(self.denylist_config.parent)

        if self.blocklist_config.parent.exists():
            watch_dirs.add(self.blocklist_config.parent)

        handler = ConfigFileHandler(self._on_config_change, watched_files)
        if Observer is not None:
            self.observer = Observer()

            for watch_dir in watch_dirs:
                try:
                    self.observer.schedule(handler, str(watch_dir), recursive=False)
                    logging.info("[REACTIVE] Watching directory: %s", watch_dir)
                except Exception as exc:
                    logging.warning("[REACTIVE] Failed to watch %s: %s", watch_dir, exc)

            self.observer.start()
        else:
            self.observer = None
        logging.info("[REACTIVE] File watcher started (watching %d files)", len(watched_files))

    async def _validate_config(self, config_path: Path) -> List[Violation]:
        """Validate a single config (CAUTIOUS: read-only)"""
        if self.manager is None:
            return []

        if not config_path.exists():
            return []

        violations: List[Violation] = []
        try:
            # CAUTIOUS: Read-only validation, no mutation
            found_violations, _ = self.manager.validate_mcp_config(
                str(config_path), total_deny=self.total_deny
            )

            for v in found_violations:
                violations.append(Violation(
                    server_name=v["name"],
                    reason=v.get("reason", "total-deny-scope"),
                    config_path=config_path,
                ))
        except Exception as exc:
            logging.error("[CAUTIOUS] Validation error for %s: %s", config_path, exc)

        return violations

    async def _process_violations(self, violations: List[Violation], config_path: Path):
        """Process violations with extensive logging (CAUTIOUS)"""
        current = {v.server_name: v.reason for v in violations}
        previous = self.last_denials.get(config_path, {})
        self.last_denials[config_path] = current

        for violation in violations:
            # Only log new violations (CAUTIOUS: avoid log spam)
            if previous.get(violation.server_name) == violation.reason:
                continue

            logging.warning(
                "[%s VIOLATION] server=%s reason=%s config=%s detected_at=%s",
                self.mode_label,
                violation.server_name,
                violation.reason,
                violation.config_path,
                violation.detected_at,
            )

            # Emit events
            await _emit_violation_events(
                self.manager, violation, self.event_bus, self.audit_logger
            )

            # Update state
            if self.state:
                self.state.total_violations += 1
                config_key = str(config_path)
                if config_key not in self.state.last_violations:
                    self.state.last_violations[config_key] = []
                if violation.server_name not in self.state.last_violations[config_key]:
                    self.state.last_violations[config_key].append(violation.server_name)

    async def _check_all_configs(self):
        """Check all MCP configs"""
        # Reload manager if denylist changed
        if self.denylist_config.exists():
            current_mtime = self.denylist_config.stat().st_mtime
            if self.denylist_mtime is None or current_mtime != self.denylist_mtime:
                self.denylist_mtime = current_mtime
                self.manager = SafetyAwareServerManager(
                    str(self.denylist_config), str(self.safety_logs)
                )
                logging.info("[PERSISTENT] Reloaded denylist config")

        # Reload blocklist if changed
        self._load_blocklist()

        for config_path in self.mcp_configs:
            if not config_path.exists():
                continue

            current_mtime = config_path.stat().st_mtime
            if (config_path in self.last_mtimes and
                current_mtime == self.last_mtimes[config_path]):
                continue

            self.last_mtimes[config_path] = current_mtime

            # Check denylist violations
            violations = await self._validate_config(config_path)
            await self._process_violations(violations, config_path)

            # Check blocklist violations (py.exe, pyw.exe)
            blocklist_violations = self._check_blocklist_violations(config_path)
            await self._process_blocklist_violations(blocklist_violations, config_path)

        if self.state:
            self.state.total_checks += 1

    async def _heartbeat_loop(self):
        """Periodic heartbeat for health monitoring (PERSISTENT)"""
        while self.running:
            self._save_state()
            logging.debug("[HEARTBEAT] alive, checks=%d violations=%d",
                         self.state.total_checks if self.state else 0,
                         self.state.total_violations if self.state else 0)
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _reactive_loop(self):
        """Process reactive file change events"""
        while self.running:
            try:
                # Wait for file change with timeout
                config_path = await asyncio.wait_for(
                    self._pending_checks.get(), timeout=self.interval_seconds
                )

                # Small delay for debouncing
                await asyncio.sleep(REACTIVE_DEBOUNCE)

                logging.info("[REACTIVE] Processing change: %s", config_path)

                # If denylist changed, reload it
                if config_path == self.denylist_config:
                    self.denylist_mtime = None

                # If blocklist changed, reload it
                if config_path == self.blocklist_config:
                    self.blocklist_mtime = None
                    logging.info("[BLOCKLIST] Config changed, will reload")

                # Validate the changed config
                await self._check_all_configs()

            except asyncio.TimeoutError:
                # No reactive events, do periodic check
                await self._check_all_configs()

    async def run(self, run_once: bool = False):
        """Main monitor loop (ALWAYS ACTIVE)"""
        self.running = True
        self.state = self._load_state()

        logging.info(
            "[PERSISTENT] Spawn monitor starting (%s mode, interval=%ds, reactive=%s)",
            self.mode_label, self.interval_seconds, WATCHDOG_AVAILABLE
        )

        # Initialize integrations
        self.event_bus = await _init_event_bus()
        self.audit_logger = await _init_audit_logger()

        # Setup reactive file watching
        self._setup_file_watcher()

        # Initial check
        await self._check_all_configs()

        if run_once:
            self._save_state()
            return

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            await self._reactive_loop()
        except asyncio.CancelledError:
            logging.info("[PERSISTENT] Monitor cancelled")
        finally:
            self.running = False
            heartbeat_task.cancel()

            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)

            if self.event_bus:
                await self.event_bus.stop()
            if self.audit_logger:
                await self.audit_logger.stop()

            self._save_state()
            logging.info("[PERSISTENT] Monitor stopped, state saved")

    def stop(self):
        """Signal the monitor to stop"""
        self.running = False


# Legacy function for backward compatibility
async def run_monitor(
    denylist_config: Path,
    mcp_configs: List[Path],
    safety_logs: Path,
    interval_seconds: int = 30,
    run_once: bool = False,
    total_deny: bool = False,
):
    """Legacy wrapper for PersistentSpawnMonitor"""
    monitor = PersistentSpawnMonitor(
        denylist_config=denylist_config,
        mcp_configs=mcp_configs,
        safety_logs=safety_logs,
        state_file=DEFAULT_STATE_FILE,
        interval_seconds=interval_seconds,
        total_deny=total_deny,
    )
    await monitor.run(run_once=run_once)


def _parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Persistent, Reactive MCP spawn monitor for denylist enforcement"
    )
    parser.add_argument(
        "--denylist-config",
        default=str(DEFAULT_DENYLIST_CONFIG),
        help="Path to denylist config",
    )
    parser.add_argument(
        "--mcp-config",
        action="append",
        dest="mcp_configs",
        help="Path to an MCP config file (repeatable)",
    )
    parser.add_argument(
        "--safety-logs",
        default=str(DEFAULT_SAFETY_LOGS),
        help="Path to safety log directory",
    )
    parser.add_argument(
        "--state-file",
        default=str(DEFAULT_STATE_FILE),
        help="Path to persistent state file",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (reactive mode responds immediately)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single validation pass and exit",
    )
    parser.add_argument(
        "--total-deny",
        action="store_true",
        help="Total-deny mode: treat ALL enabled MCP servers as violations",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (ALWAYS ACTIVE mode with crash recovery)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current monitor status from state file",
    )

    return parser.parse_args()


def _show_status(state_file: Path):
    """Show current monitor status"""
    if not state_file.exists():
        print("[STATUS] No state file found - monitor may not be running")
        return

    try:
        with open(state_file, "r") as f:
            data = json.load(f)

        print("=" * 60)
        print("SPAWN MONITOR STATUS")
        print("=" * 60)
        print(f"State file:      {state_file}")
        print(f"Started at:      {data.get('started_at', 'unknown')}")
        print(f"Last heartbeat:  {data.get('last_heartbeat', 'unknown')}")
        print(f"Total checks:    {data.get('total_checks', 0)}")
        print(f"Total violations: {data.get('total_violations', 0)}")

        violations = data.get("last_violations", {})
        if violations:
            print("\nLast violations by config:")
            for config, servers in violations.items():
                print(f"  {config}:")
                for server in servers:
                    print(f"    - {server}")
        print("=" * 60)
    except Exception as exc:
        print(f"[ERROR] Failed to read state: {exc}")


def _setup_signal_handlers(monitor: PersistentSpawnMonitor):
    """Setup graceful shutdown handlers"""
    def signal_handler(signum, frame):
        logging.info("[PERSISTENT] Received signal %d, shutting down...", signum)
        monitor.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    args = _parse_args()

    # Show status and exit
    if args.status:
        _show_status(Path(args.state_file))
        return

    # Configure logging
    log_level = logging.DEBUG if os.environ.get("DEBUG") else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    if args.daemon:
        # Daemon mode: log to file
        log_file = Path(args.safety_logs) / "spawn_monitor.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ]
        )
    else:
        logging.basicConfig(level=log_level, format=log_format)

    mcp_configs = [Path(p) for p in args.mcp_configs] if args.mcp_configs else DEFAULT_MCP_CONFIGS

    monitor = PersistentSpawnMonitor(
        denylist_config=Path(args.denylist_config),
        mcp_configs=mcp_configs,
        safety_logs=Path(args.safety_logs),
        state_file=Path(args.state_file),
        interval_seconds=args.interval,
        total_deny=args.total_deny,
    )

    _setup_signal_handlers(monitor)

    try:
        asyncio.run(monitor.run(run_once=args.once))
    except KeyboardInterrupt:
        logging.info("[PERSISTENT] Interrupted by user")
    except Exception as exc:
        logging.error("[PERSISTENT] Fatal error: %s", exc)
        raise


if __name__ == "__main__":
    main()
