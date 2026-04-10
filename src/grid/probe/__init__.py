"""Governance probe — maps middleware, auth, gating, and security entities.

The probe system provides four integrated layers:
- YAML config (config/probe/) — integration wiring and entity definitions
- JSON schemas (schemas/probe-*) — structured data contracts for reports
- Python execution (this package) — scanner, registry, reporter engine
- Markdown docs (docs/probe/) — architecture and usage documentation

Phase 3 adds ecosystem integration:
- ecosystem.py — bridge to echoes-server (enforcement) and seeds-server (health)
- lumos.py — 6-phase ecosystem illumination pipeline orchestrator

Usage:
    from grid.probe import ProbeEngine, ProbeConfig
    from grid.probe.models import Entity, Finding, ProbeReport
    from grid.probe.ecosystem import EcosystemBridge
    from grid.probe.lumos import LumosOrchestrator

    # Run internal probe
    engine = ProbeEngine.from_config()
    report = engine.run()

    # Run full ecosystem merge
    bridge = EcosystemBridge()
    bridge.ingest_ecosystem(seeds_data)
    bridge.ingest_enforcement(echoes_data)
    bridge.ingest_line_audit(eligibility_data)
    orchestrator = LumosOrchestrator(bridge)
    result = orchestrator.run_full(probe_report=report)
"""

from __future__ import annotations

from grid.probe.config import ProbeConfig
from grid.probe.ecosystem import EcosystemBridge
from grid.probe.engine import ProbeEngine
from grid.probe.lumos import LumosOrchestrator, LumosResult
from grid.probe.models import Domain, Entity, EntityType, Finding, FindingCategory, ProbeReport
from grid.probe.registry import EntityRegistry
from grid.probe.reporter import ProbeReporter
from grid.probe.scanner import EntityScanner

__all__ = [
    "ProbeConfig",
    "ProbeEngine",
    "Entity",
    "EntityType",
    "Domain",
    "Finding",
    "FindingCategory",
    "ProbeReport",
    "EntityRegistry",
    "EntityScanner",
    "ProbeReporter",
    "EcosystemBridge",
    "LumosOrchestrator",
    "LumosResult",
]
