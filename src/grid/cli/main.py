"""GRID CLI entry point."""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """GRID command-line interface."""


@cli.command("list-events")
def list_events() -> None:
    """List all tracked events."""
    events = _get_events()
    for event in events:
        click.echo(f"- {event}")


def _get_events() -> list[str]:
    """Retrieve events from the event store."""
    try:
        from grid.events import event_store

        return event_store.get_all()
    except Exception:
        # Fallback: return default events when store is unavailable
        return ["event1", "event2"]
