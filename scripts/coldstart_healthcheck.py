#!/usr/bin/env python3
"""Fast coldstart runtime healthcheck for import-path and boundary drift."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModuleExportCheck:
    module: str
    exports: tuple[str, ...]


def _append_pythonpath(paths: list[Path]) -> None:
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _is_true_like(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_false_like(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in {"0", "false", "no", "off", ""}


def _check_paths() -> list[str]:
    required_paths = [
        ROOT / "src",
        ROOT / "work" / "GRID" / "src",
        ROOT / "safety",
        ROOT / "security",
        ROOT / "boundaries",
    ]
    failures: list[str] = []
    for path in required_paths:
        if not path.exists():
            failures.append(f"Missing required path: {path.relative_to(ROOT)}")
    _append_pythonpath(required_paths)
    return failures


def _check_imports() -> list[str]:
    module_checks = [
        "src.grid.api.main",
        "src.grid.core.security",
        "src.grid.core.passwords",
        "src.grid.crud.user",
        "src.tools.rag.config",
        "application.mothership.main",
    ]
    export_checks = [
        ModuleExportCheck("src.grid.core.security", ("get_password_hash", "verify_password")),
    ]

    failures: list[str] = []

    for module_name in module_checks:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Import failed for '{module_name}': {exc}")

    for check in export_checks:
        try:
            module = importlib.import_module(check.module)
            for export in check.exports:
                if not hasattr(module, export):
                    failures.append(f"Missing expected export '{check.module}.{export}'")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Export check failed for '{check.module}': {exc}")

    return failures


def _check_boundaries(mode: str) -> list[str]:
    failures: list[str] = []
    warnings: list[str] = []

    allow_unauth = os.getenv("MOTHERSHIP_ALLOW_UNAUTHENTICATED_DEV")
    if not _is_false_like(allow_unauth):
        failures.append("Boundary violation: MOTHERSHIP_ALLOW_UNAUTHENTICATED_DEV must be false-like.")

    rate_limit = os.getenv("MOTHERSHIP_RATE_LIMIT_ENABLED")
    if not _is_true_like(rate_limit):
        failures.append("Boundary violation: MOTHERSHIP_RATE_LIMIT_ENABLED must be true-like.")

    payments_mode = (os.getenv("GRID_PAYMENTS_MODE") or "").strip().lower()
    allowed_modes = {"legacy", "shadow", "dual", "primary", "retire"}
    if payments_mode and payments_mode not in allowed_modes:
        failures.append("Boundary violation: GRID_PAYMENTS_MODE must be legacy|shadow|dual|primary|retire.")

    stripe_enabled = os.getenv("STRIPE_ENABLED")
    if _is_true_like(stripe_enabled):
        stripe_secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
        if not stripe_secret:
            failures.append("Boundary violation: STRIPE_ENABLED=true but STRIPE_SECRET_KEY is empty.")
    elif not _is_false_like(stripe_enabled):
        warnings.append(f"Non-standard STRIPE_ENABLED value '{stripe_enabled}' in mode '{mode}'.")

    for warning in warnings:
        print(f"[WARN] {warning}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate coldstart runtime baseline health.")
    parser.add_argument("--mode", choices=["dev", "test"], default="dev")
    parser.add_argument(
        "--strict-boundaries",
        action="store_true",
        help="Enforce boundary env variable contracts used by coldstart sessions.",
    )
    args = parser.parse_args()

    failures: list[str] = []
    failures.extend(_check_paths())
    failures.extend(_check_imports())

    if args.strict_boundaries:
        failures.extend(_check_boundaries(args.mode))

    if failures:
        print("Coldstart runtime healthcheck FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Coldstart runtime healthcheck PASSED")
    print(" - Import surface and path baseline validated")
    if args.strict_boundaries:
        print(f" - Strict boundary checks enabled (mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
