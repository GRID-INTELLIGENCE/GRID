# Raincoat Architecture: Stability & Persistence

## Concept
The "Raincoat" is a protective configuration layer that sits on top of dynamic workflows. It ensures stability by explicitly defining and enforcing safe patterns, acting as a shield against configuration drift and unsafe execution states.

## Core Components

### 1. Stability Profile (`config/stability_profile.json`)
The source of truth for stability logic. It defines:
- **Governance**: Policies for MCP, Terminal, and AI assistance.
- **Persistence Patterns**: Links to deep configurations (Path Protection, Server Denylist).
- **Workflow Preferences**: UI/UX settings that promote stability.

### 2. Raincoat Enforcer (`scripts/raincoat_enforcer.py`)
A tool to translate the abstract profile into concrete VS Code settings.
- Generates compliant `settings.json` blocks.
- Can be extended to validate existing settings.

## Persistence Logic

The system uses a "Deep Configuration" approach:

1.  **Layer 1: File System (Concrete)**
    - `PROJECT_PATH_PROTECTION.json` (Immutable paths)
    - `SERVER_DENYLIST.json` (Runtime execution blocks)

2.  **Layer 2: Configuration (Abstract)**
    - `STABILITY_PROFILE.json` (Preferences & Policy)

3.  **Layer 3: User Interface (Ephemeral)**
    - `settings.json` (Generated/Enforced by Layer 2)

## Explicit Patterns

### MCP Governance
- **Policy**: `autostart: "never"`
- **Reason**: Prevents "Error spawn python ENOENT" loops and unverified server execution.

### Terminal Safety
- **Policy**: `least_privilege`
- **Pattern**: Whitelist safe read operations. Explicitly block destructive operations (`rm`, `kill`, `curl`).

## Live Workflow Integration

To maintain this stability during live workflows:
1.  **Profile**: Update `stability_profile.json` when new safe patterns are identified.
2.  **Enforce**: Run `raincoat_enforcer.py` to generate the updated settings block.
3.  **Monitor**: Use the AI Safety logging (established previously) to detect deviations.
