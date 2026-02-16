"""
Minimal integration example: preparedness framework and overwatch in an AI-lab-style loop.

Loads default_boundary_config.json, creates PreparednessFramework and Overwatch,
wires the boundary logger to overwatch, then runs check_gate and enforce_biosecurity_scope
to demonstrate gates, approval, and overwatch alerts.

Run from repo root: python -m boundaries.examples.preparedness_overwatch_demo
Or from boundaries/: python -m examples.preparedness_overwatch_demo
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure boundaries package is importable when run as script
if __name__ == "__main__" and __package__ is None:
    _repo = Path(__file__).resolve().parents[2]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))

from boundaries import (
    Overwatch,
    PreparednessFramework,
    wrap_logger_with_overwatch,
)
from boundaries.logger_ws import BoundaryEventLogger, set_global_logger


def load_config(use_temp_log_dir: bool = True) -> dict:
    """Load default boundary config. Optionally use a temp dir for logs."""
    config_path = Path(__file__).resolve().parents[1] / "config" / "default_boundary_config.json"
    if not config_path.exists():
        config_path = Path(__file__).resolve().parents[2] / "boundaries" / "config" / "default_boundary_config.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    if use_temp_log_dir:
        log_dir = Path(tempfile.mkdtemp(prefix="boundary_demo_"))
        config.setdefault("websocketLogging", {})["logDir"] = str(log_dir)
        config.setdefault("overwatch", {})["logDir"] = str(log_dir)
        os.environ["BOUNDARY_LOG_DIR"] = str(log_dir)
    return config


def main() -> None:
    config = load_config(use_temp_log_dir=True)
    log_dir = config.get("overwatch", {}).get("logDir", "logs/boundaries")

    # Fresh logger for this demo (uses BOUNDARY_LOG_DIR if set)
    logger = BoundaryEventLogger(
        enabled=True,
        persist_to_file=True,
        log_dir=os.environ.get("BOUNDARY_LOG_DIR", log_dir),
    )
    set_global_logger(logger)

    prep = PreparednessFramework(config)
    ow = Overwatch(config)
    wrap_logger_with_overwatch(logger, ow)

    alerts: list[dict] = []

    def capture_alert(alert: dict) -> None:
        alerts.append(alert)

    ow.register_handler(capture_alert)

    print("=== Preparedness & Overwatch integration demo ===\n")

    # 1) gate_protocol: require_approval -> not allowed until approved
    action, allowed = prep.check_gate("gate_protocol", scope="experiment", actor_id="model")
    print(f"1. check_gate('gate_protocol') -> action={action!r}, allowed={allowed}")
    assert action == "require_approval" and not allowed

    prep.approve_gate("gate_protocol")
    action, allowed = prep.check_gate("gate_protocol", scope="experiment", actor_id="model")
    print(f"2. After approve_gate('gate_protocol'), check_gate again -> allowed={allowed}")
    assert allowed

    # 2) gate_capability: block -> never allowed (unless we approved for demo)
    action, allowed = prep.check_gate("gate_capability", scope="system", actor_id="model")
    print(f"3. check_gate('gate_capability') -> action={action!r}, allowed={allowed}")
    assert action == "block" and not allowed

    # 3) Biosecurity scope
    ok = prep.enforce_biosecurity_scope(
        benign_only=True,
        task_scope="optimization_only",
        controlled_setting=True,
    )
    print(f"4. enforce_biosecurity_scope(...) -> {ok}")
    assert ok

    ok_fail = prep.enforce_biosecurity_scope(task_scope="other_scope")
    print(f"5. enforce_biosecurity_scope(task_scope='other_scope') -> {ok_fail}")
    assert not ok_fail

    # Overwatch should have received preparedness_gate events (single alerts)
    print(f"\n6. Overwatch received {len(alerts)} alert(s) (preparedness_gate events).")
    for i, a in enumerate(alerts[:5], 1):
        payload = a.get("payload", {})
        print(f"   Alert {i}: {payload.get('alertType')} source={payload.get('sourceEventType')}")

    logger.close()
    print("\nDone. Log dir used:", log_dir)


if __name__ == "__main__":
    main()
