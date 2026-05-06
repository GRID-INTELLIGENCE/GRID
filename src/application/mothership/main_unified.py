"""Compatibility shim for the canonical Mothership app.

Historically this module carried a second app assembly path. That drifted from
`application.mothership.main` and produced duplicated route prefixes. Keep this
module importable, but delegate all runtime behavior to the canonical app.
"""

from __future__ import annotations

from fastapi import FastAPI

from .main import app, create_app as _create_app, main as _main


def create_app() -> FastAPI:
    """Return the canonical Mothership FastAPI application."""
    return _create_app()


def main() -> None:
    """Run the canonical Mothership entry point."""
    _main()


if __name__ == "__main__":
    main()
