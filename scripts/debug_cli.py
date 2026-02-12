#!/usr/bin/env python
"""
Debug CLI for THE GRID.

Usage:
  uv run python scripts/debug_cli.py tasks       # Show async tasks
  uv run python scripts/debug_cli.py health      # Integration health
  uv run python scripts/debug_cli.py pools       # Connection pools
  uv run python scripts/debug_cli.py guardian    # Guardian stats
  uv run python scripts/debug_cli.py logs TRACE_ID  # Find logs by trace

  # Enable async tracking (PowerShell):
  $env:DEBUG_ASYNC="true"; uv run python scripts/debug_cli.py tasks

  # Enable async tracking (bash/zsh):
  DEBUG_ASYNC=true uv run python scripts/debug_cli.py tasks
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Ensure workspace root is FIRST (local safety/ overrides pip safety), then work/GRID/src (grid)
_root = Path(__file__).resolve().parent.parent
_src = _root / "work" / "GRID" / "src"
for p in (_root, _src):
    if p.exists():
        s = str(p)
        if s in sys.path:
            sys.path.remove(s)
        sys.path.insert(0, s)

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def cli() -> None:
    """THE GRID Debug CLI."""
    pass


@cli.command()
def tasks() -> None:
    """Show active async tasks."""
    from grid.debug.async_tracker import debug_dump_tasks, enable_async_tracking

    enable_async_tracking()

    async def run() -> None:
        data = await debug_dump_tasks()

        table = Table(title="Active Async Tasks")
        table.add_column("Name", style="cyan")
        table.add_column("Coroutine", style="magenta")
        table.add_column("Age (s)", style="yellow")
        table.add_column("Trace ID", style="green")

        for task in data["active_tasks"]:
            table.add_row(
                task["name"],
                task["coro"],
                f"{task['age_seconds']:.2f}",
                task["trace_id"],
            )

        console.print(table)
        console.print(f"\n[bold]Stats:[/bold] {data['stats']}")

    asyncio.run(run())


@cli.command()
def health() -> None:
    """Check integration health."""
    from grid.debug.integration_health import health_checker

    async def run() -> None:
        results = await health_checker.check_all()

        table = Table(title="Integration Health")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Latency (ms)", style="yellow")
        table.add_column("Details", style="dim")

        for result in results:
            status = "[green]OK Healthy[/green]" if result.healthy else "[red]FAIL Unhealthy[/red]"
            details = result.error or str(result.details)
            if len(details) > 50:
                details = details[:47] + "..."

            table.add_row(
                result.service,
                status,
                f"{result.latency_ms:.2f}",
                details,
            )

        console.print(table)

    asyncio.run(run())


@cli.command()
def pools() -> None:
    """Show connection pool status."""
    try:
        from safety.audit.db import _engine
    except ImportError:
        console.print("[yellow]safety.audit.db not available (safety module not installed)[/yellow]")
        return

    if not _engine:
        console.print("[red]Database engine not initialized[/red]")
        console.print("[dim]Run Mothership or call safety.audit.db.init_db() first[/dim]")
        return

    pool = _engine.pool

    table = Table(title="PostgreSQL Connection Pool")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    size = getattr(pool, "size", lambda: 0)()
    checkedin = getattr(pool, "checkedin", lambda: 0)()
    overflow = getattr(pool, "overflow", lambda: 0)()
    table.add_row("Pool Size", str(size))
    table.add_row("Checked In", str(checkedin))
    table.add_row("Overflow", str(overflow))
    table.add_row("Checked Out", str(size - checkedin))

    console.print(table)


@cli.command()
def guardian() -> None:
    """Show Guardian rule engine stats."""
    try:
        from safety.guardian.engine import get_guardian_engine
        from safety.guardian.loader import init_guardian_rules

        # Load rules from safety/config/rules if it exists, else use default path
        rules_dir = _root / "safety" / "config" / "rules"
        if rules_dir.exists():
            engine = init_guardian_rules(rules_dir=str(rules_dir), auto_reload=False)
        else:
            engine = get_guardian_engine()
        stats = engine.get_stats() if hasattr(engine, "get_stats") else {}
    except ImportError as e:
        console.print(f"[yellow]safety.guardian.engine not available: {e}[/yellow]")
        return

    table = Table(title="Guardian Rule Engine Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    for key, value in stats.items():
        if isinstance(value, dict):
            table.add_row(key, json.dumps(value, default=str))
        else:
            table.add_row(key, str(value))

    console.print(table)


@cli.command()
@click.argument("trace_id", type=str)
def logs(trace_id: str) -> None:
    """Find logs by trace ID."""
    log_dir = Path("safety/logs")
    from datetime import date

    today = date.today().strftime("%Y-%m-%d")
    log_file = log_dir / f"safety_{today}.jsonl"

    if not log_file.exists():
        console.print(f"[red]Log file not found: {log_file}[/red]")
        return

    matches: list[dict] = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                if event.get("trace_id") == trace_id:
                    matches.append(event)
            except json.JSONDecodeError:
                continue

    if not matches:
        console.print(f"[yellow]No logs found for trace_id={trace_id}[/yellow]")
        return

    console.print(f"[bold]Found {len(matches)} log events:[/bold]\n")
    for event in matches:
        console.print(
            f"[dim]{event.get('timestamp')}[/dim] [{event.get('level', 'info').upper()}] {event.get('event', '')}"
        )
        console.print(f"  {event}\n")


if __name__ == "__main__":
    cli()
