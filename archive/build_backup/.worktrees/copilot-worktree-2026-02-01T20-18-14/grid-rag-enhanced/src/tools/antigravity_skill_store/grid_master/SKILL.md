---
name: GRID Mastermind
description: Comprehensive knowledge and operational protocols for the Geometric Resonance Intelligence Driver (GRID) project.
---

# GRID Mastermind Skill

## 1. Core Mission
GRID (Geometric Resonance Intelligence Driver) bridges human intuition with computational logic via event-driven architecture and cognitive load management.

## 2. Architectural Pillars
- **Layered Isolation**: [Core → Service → Database → API].
- **Event-Driven**: Central Event Bus (`src/grid/events/`) handles all async communication.
- **Cognitive Load Integration**: Dynamic response simplification based on mental effort estimation (`src/grid/io/outputs.py`).
- **Sovereign Tier**: Local-first, RAG-enhanced intelligence using ChromaDB and Ollama.

## 3. The Mastication Protocol
When developing for GRID, you MUST adhere to the **Mastication Layer** checkpoints:
- **Flavor Density**: Ensure 100% context awareness before proposing changes.
- **Stickiness**: New code must adhere to strict PEP 8 (120 char) and MyPy strict typing.
- **Jaw Strength**: Perform deep logic traces for complex event flows.
- **Elasticity**: Adapt to environment constraints (e.g., WSL availability, Ollama status).

## 4. Key Operational Commands
```bash
# Analyze text with cognitive load management
python -m src.grid analyze "text" --output json|table

# Start Mothership (Backend)
python -m src.grid serve

# Run core test suite (730+ tests)
pytest tests/
```

## 5. Development Standards
- **Python**: 3.13.11.
- **Formatters**: Ruff (line-length: 120), Black.
- **Docs**: Google-style docstrings mandatory.
- **Secret Management**: Use local `SecretManager` or GCP; NEVER hardcode tokens.

## 6. High-Signal File Index
- `GRID_COMPREHENSIVE_CONTEXT_SUMMARY.md`: Current system state.
- `GRID_OPERATIONS_PLAYBOOK.md`: Troubleshooting and deployments.
- `src/grid/io/outputs.py`: Cognitive load logic.
- `src/grid/events/bus.py`: Core messaging hub.
