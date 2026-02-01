# GRID Repository Restructure Proposal (Staged & Safe)

**Document version:** 2026-01-01 · **Scope:** Repo restructure into a semantic, modular layout (DDD-aligned).
**Safety posture:** Non-destructive, copy-first with shims, scoped rollouts, explicit validation.

---

## Contents
1. Snapshot of current structure & pain points
2. Target structure (semantic layout)
3. Safe restructure plan (staged)
4. Source-of-fault diagnosis (what was wrong in v1.0)
5. Migration/validation checklist
6. Next steps

---

## 1) Snapshot of current structure & pain points

**Pain points**
- Duplication: `grid/`, `src/grid/`, `datakit/`
- Scattered configs (84+ loose root files)
- Mixed concerns in `scripts/` (tests + utilities)
- Deep nesting (`application/mothership/`, `application/resonance/`)
- Documentation sprawl (225+ files)
- Known Windows hazard path: `light_of_the_seven/full_datakit/visualizations/Hogwarts/great_hall/nul`

---

## 2) Target Structure (semantic layout)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     GRID REPOSITORY - SEMANTIC ORGANIZATION                   │
├────────────────────┬───────────────────┬────────────────────┬─────────────────┤
│   **Core Domain**  │ **User-Facing**   │ **Infrastructure** │ **Shared**      │
│   (Business Logic) │ (Frontend/CLI)    │ (Backend Systems)  │ (Utilities)     │
├────────────────────┴───────────────────┴────────────────────┴─────────────────┤
│                                                                               │
│   📁 GRID/                                                                    │
│   ├── .agent/                      # AI agent configurations                 │
│   ├── .context/                    # Context & intelligence layer            │
│   ├── .github/                     # GitHub workflows & CI/CD                │
│   ├── .vscode/                     # VS Code settings                        │
│   │                                                                           │
│   ├── 📂 src/                      # ════════════════════════════════════    │
│   │   │                            #   PRIMARY SOURCE CODE                   │
│   │   │                            # ════════════════════════════════════    │
│   │   │                                                                       │
│   │   ├── 📂 domain/               # CORE DOMAIN LOGIC                       │
│   │   │   ├── models/              # Data models & entities                  │
│   │   │   │   ├── __init__.py                                                │
│   │   │   │   ├── faceless.py      # ← from models/faceless.py               │
│   │   │   │   ├── products.py      # ← from core/products.py                 │
│   │   │   │   └── tool_attributes.py # ← from core/tool_attributes.py       │
│   │   │   │                                                                   │
│   │   │   ├── services/            # Business logic services                 │
│   │   │   │   ├── __init__.py                                                │
│   │   │   │   ├── cognitive/       # Cognitive processing                    │
│   │   │   │   ├── quantum/         # ← from grid/quantum/                    │
│   │   │   │   ├── processing/      # ← from grid/processing/                 │
│   │   │   │   └── senses/          # ← from grid/senses/                     │
│   │   │   │                                                                   │
│   │   │   └── entities/            # Domain entities                         │
│   │   │       ├── awareness/       # ← from grid/awareness/                  │
│   │   │       ├── essence/         # ← from grid/essence/                    │
│   │   │       └── evolution/       # ← from grid/evolution/                  │
│   │   │                                                                       │
│   │   ├── 📂 features/             # USER-FACING FEATURES                    │
│   │   │   ├── cli/                 # Command-line interface                  │
│   │   │   │   ├── __init__.py                                                │
│   │   │   │   └── commands/        # CLI commands                            │
│   │   │   │                                                                   │
│   │   │   ├── api/                 # REST/GraphQL APIs                       │
│   │   │   │   ├── __init__.py                                                │
│   │   │   │   ├── routes/          # API endpoint handlers                   │
│   │   │   │   └── middleware/      # Request/response middleware             │
│   │   │   │                                                                   │
│   │   │   ├── applications/        # Application modules                     │
│   │   │   │   ├── mothership/      # ← from application/mothership/         │
│   │   │   │   └── resonance/       # ← from application/resonance/          │
│   │   │   │                                                                   │
│   │   │   └── skills/              # ← from grid/skills/                     │
│   │   │       ├── __init__.py                                                │
│   │   │       └── ...                                                         │
│   │   │                                                                       │
│   │   ├── 📂 infrastructure/       # BACKEND SYSTEMS                         │
│   │   │   ├── database/            # Database connections                    │
│   │   │   │   ├── __init__.py                                                │
│   │   │   │   └── connection.py                                              │
│   │   │   │                                                                   │
│   │   │   ├── rag/                 # RAG engine (retrieval)                  │
│   │   │   │   ├── __init__.py      # ← from tools/rag/                       │
│   │   │   │   ├── embeddings/                                                │
│   │   │   │   ├── retriever.py                                               │
│   │   │   │   └── vector_store.py                                            │
│   │   │   │                                                                   │
│   │   │   ├── cloud/               # ← from infra/cloud/                     │
│   │   │   ├── monitoring/          # ← from infra/monitoring/                │
│   │   │   └── terraform/           # ← from infra/terraform/                 │
│   │   │                                                                       │
│   │   └── 📂 shared/               # SHARED UTILITIES                        │
│   │       ├── utils/               # General utilities                       │
│   │       │   ├── __init__.py                                                │
│   │       │   ├── logger.py        # Logging utilities                       │
│   │       │   ├── validators.py    # Data validation                         │
│   │       │   └── logging_utils.py # ← from python/logging_utils.py         │
│   │       │                                                                   │
│   │       ├── config/              # Configuration management                │
│   │       │   ├── __init__.py                                                │
│   │       │   ├── env.py           # Environment configuration               │
│   │       │   └── settings.py                                                │
│   │       │                                                                   │
│   │       └── types/               # Type definitions                        │
│   │           ├── __init__.py                                                │
│   │           └── schema_validator.py # ← from python/schema_validator.py   │
│   │                                                                           │
│   ├── 📂 lang/                     # LANGUAGE-SPECIFIC CODE                  │
│   │   ├── python/                  # Python utilities & bridges              │
│   │   │   ├── __init__.py                                                    │
│   │   │   ├── application_bridge.py                                         │
│   │   │   └── ...                                                             │
│   │   │                                                                       │
│   │   └── rust/                    # Rust crates                             │
│   │       ├── Cargo.toml                                                     │
│   │       ├── grid-core/                                                     │
│   │       └── grid-cognitive/                                                │
│   │                                                                           │
│   ├── 📂 tests/                    # TEST SUITE                              │
│   │   ├── unit/                    # Unit tests                              │
│   │   │   ├── domain/              # Domain logic tests                      │
│   │   │   ├── features/            # Feature tests                           │
│   │   │   └── infrastructure/      # Infrastructure tests                    │
│   │   │                                                                       │
│   │   ├── integration/             # Integration tests                       │
│   │   │   ├── api/                                                            │
│   │   │   └── rag/                                                            │
│   │   │                                                                       │
│   │   ├── e2e/                     # End-to-end tests                        │
│   │   ├── fixtures/                # Test fixtures                           │
│   │   └── performance/             # Performance benchmarks                  │
│   │                                                                           │
│   ├── 📂 docs/                     # DOCUMENTATION                           │
│   │   ├── 📁 architecture/         # Architecture decisions                  │
│   │   │   ├── ARCHITECTURE.md                                                │
│   │   │   ├── DECISIONS.md                                                   │
│   │   │   └── BREAKING_CHANGES.md                                            │
│   │   │                                                                       │
│   │   ├── 📁 guides/               # User guides                             │
│   │   │   ├── INSTALLATION.md                                                │
│   │   │   ├── QUICKSTART.md                                                  │
│   │   │   └── CONFIGURATION.md                                               │
│   │   │                                                                       │
│   │   ├── 📁 api/                  # API documentation                       │
│   │   │   ├── REST_API.md                                                    │
│   │   │   └── CLI_REFERENCE.md                                               │
│   │   │                                                                       │
│   │   ├── 📁 research/             # Research documentation                  │
│   │   │   └── ...                                                             │
│   │   │                                                                       │
│   │   └── 📁 archive/              # Archived/historical docs                │
│   │       └── ...                                                             │
│   │                                                                           │
│   ├── 📂 scripts/                  # BUILD & AUTOMATION SCRIPTS              │
│   │   ├── build/                   # Build scripts                           │
│   │   ├── deploy/                  # Deployment scripts                      │
│   │   ├── git/                     # Git utilities                           │
│   │   │   ├── git_intelligence.py                                           │
│   │   │   ├── git_manager.py                                                 │
│   │   │   └── git_topic_utils.py                                             │
│   │   └── data/                    # Data processing scripts                 │
│   │                                                                           │
│   ├── 📂 assets/                   # STATIC ASSETS                           │
│   │   ├── images/                                                             │
│   │   ├── media/                                                              │
│   │   └── templates/                                                          │
│   │                                                                           │
│   ├── 📂 schemas/                  # JSON/YAML SCHEMAS                       │
│   │   ├── api/                     # API schemas                             │
│   │   └── config/                  # Configuration schemas                   │
│   │                                                                           │
│   ├── 📂 config/                   # CONFIGURATION FILES                     │
│   │   │                                                                       │
│   │   └── env/                     # Environment configurations              │
│   │       ├── .env.example                                                   │
│   │                                                                           │
│   ├── 📂 data/                     # DATA FILES                              │
│   │   ├── samples/                 # Sample data                             │
│   │   └── exports/                 # Exported data                           │
│   │                                                                           │
│   ├── 📂 archive/                  # DEPRECATED/ARCHIVAL CODE               │
│   │   ├── legacy/                                                             │
│   │   ├── datakit/                 # ← from datakit/ (if deprecated)        │
│   │   └── hogwarts/                # ← from Hogwarts/                        │
│   │                                                                           │
│   ├── pyproject.toml               # Python project configuration            │
│   ├── README.md                    # Project README                          │
│   ├── LICENSE                      # License file                            │
│   └── CONTRIBUTING.md              # Contribution guidelines                 │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3) Directory Property Matrix

| Directory | Category | Purpose | Key Files |
|-----------|----------|---------|-----------|
| `src/domain/models/` | Core Domain | Data models, entities, schemas | `faceless.py`, `products.py` |
| `src/domain/services/` | Core Domain | Business logic, cognitive processing | `quantum/`, `processing/` |
| `src/domain/entities/` | Core Domain | Domain entities (awareness, essence) | `awareness/`, `evolution/` |
| `src/features/cli/` | User-Facing | Command-line interface | `commands/` |
| `src/features/api/` | User-Facing | REST/GraphQL endpoints | `routes/`, `middleware/` |
| `src/features/applications/` | User-Facing | Application modules | `mothership/`, `resonance/` |
| `src/infrastructure/database/` | Backend | Database connections, ORM | `connection.py` |
| `src/infrastructure/rag/` | Backend | RAG engine, embeddings | `retriever.py`, `vector_store.py` |
| `src/infrastructure/cloud/` | Backend | Cloud provider integrations | AWS, GCP, Azure configs |
| `src/shared/utils/` | Shared | Common utilities | `logger.py`, `validators.py` |
| `src/shared/config/` | Shared | Configuration management | `env.py`, `settings.py` |
| `tests/unit/` | Validation | Unit tests | `test_*.py` |
| `tests/integration/` | Validation | Integration tests | `test_*.py` |
| `docs/architecture/` | Documentation | Architecture docs | `ARCHITECTURE.md` |
| `docs/guides/` | Documentation | User guides | `INSTALLATION.md` |
| `scripts/build/` | Automation | Build scripts | `build.py` |
| `scripts/deploy/` | Automation | Deployment scripts | `deploy.sh` |
| `assets/` | Static | Images, media, templates | `images/`, `media/` |
| `archive/` | Archival | Deprecated code | `legacy/`, `datakit/` |

---

## 4) Safe Restructure Plan (staged, non-destructive)

```yaml
proposal:
  name: grid_repository_restructure_v1_safe
  goals:
    - increase discoverability
    - reduce duplication
    - align with domain-driven boundaries
  constraints:
    - no destructive moves in main; use feature branch only
    - no Move-Item -Force; prefer copy + shim, then cutover after tests pass
    - preserve live assets (Hogwarts/datakit) until mapped and referenced
    - handle Windows device-name hazards (e.g., great_hall/nul) by excluding
    - keep cli entrypoints working via temporary import shims
  phases:
    - pilot_scope:
        scope: narrow (one module, e.g., src/shared/utils)
        actions:
          - create target directories
          - copy files + add __init__.py
          - add compatibility imports (old paths re-export new modules)
          - update imports in touched module only
          - run lint/tests subset
    - expand_scope:
        scope: per-domain (domain/services, features/cli, infrastructure/rag)
        actions:
          - repeat pilot steps
          - update CI paths, scripts, workspace settings
          - remove shims once coverage proves green
    - archive_and_cleanup:
        guards:
          - references audited (docs/tests/tools) before moving to archive
          - no archives for active work without owner sign-off
        actions:
          - move deprecated code into archive/* with mapping doc
          - remove unused shims
  directory_map:
    domain_models:
      target: src/domain/models/
      source_examples: [models/, core/products.py, core/tool_attributes.py]
    domain_services:
      target: src/domain/services/{quantum,processing,senses,cognitive}/
      source_examples: [grid/quantum/, grid/processing/, grid/senses/]
    domain_entities:
      target: src/domain/entities/{awareness,essence,evolution}/
      source_examples: [grid/awareness/, grid/essence/, grid/evolution/]
    features_cli:
      target: src/features/cli/commands/
      source_examples: [src/cli/, application/cli/]
    features_applications:
      target: src/features/applications/{mothership,resonance}/
      source_examples: [application/mothership/, application/resonance/]
    infrastructure_rag:
      target: src/infrastructure/rag/
      source_examples: [tools/rag/]
    shared_utils:
      target: src/shared/utils/
      source_examples: [python/logging_utils.py]
    shared_types:
      target: src/shared/types/
      source_examples: [python/schema_validator.py, python/type_validator.py]
  migration_rules:
    - prefer copy then remove after validation
    - add __init__.py for every new package
    - add compatibility shims:
        pattern: old_path/module.py -> new_path/module.py re-export
        removal: after CI + tests green
    - update imports with automated tool (e.g., rewrite scripts) not manual-only
    - update docs/links and scripts simultaneously with moves
    - ensure grid CLI paths remain valid; patch entrypoints first
  validation:
    - run python -m pytest from repo root (full suite or impacted subset)
    - run lint/format (ruff/black/isort) on moved modules
    - verify CI workflows and tasks that reference paths
    - manual spot-check: launch CLI/bridge commands
  deliverables:
    - migration checklist per module
    - mapping log (old -> new) committed
    - rollback plan (git branch; no in-place irreversible ops)
```

---

## 5) Source-of-Fault Structured Schema (why v1.0 was risky)

```yaml
faulty_source:
  artifact: restructure_repository.ps1 + RESTRUCTURE_PROPOSAL.md (v1.0 initial)
  issues:
    - destructive_moves:
        description: Proposed Move-Item/Force and broad directory relocations without shims
        impact: breaks imports/tests, hard to roll back
    - missing_compat_layer:
        description: No temporary import re-exports or CLI entrypoint shims
        impact: runtime import failures during transition
    - unguarded_archives:
        description: Moves Hogwarts/datakit into archive without owner sign-off or link updates
        impact: broken references and loss of active work
    - path_hazards:
        description: No handling for Windows device-name paths (e.g., great_hall/nul)
        impact: command failures on Windows
    - overbroad_scope:
        description: Single-step migration across entire repo with Force directory creation
        impact: high blast radius; no per-domain staging
  bad_commands:
    - move_tree: Move-Item with -Force on core packages and infra
    - create_all_dirs: blanket New-Item for dozens of roots without guardrails
  missing_steps:
    - automated_import_rewrites
    - CI/task/workspace path updates before cutover
    - validation gates (tests/lint) per module
    - rollback plan and backups
  remediation_path:
    - adopt_safe_schema: use Safe Restructure Plan (above)
    - copy_then_cutover: copy with shims, validate, then remove originals post-green
    - scoped_phases: pilot (shared/utils), then expand per-domain
    - hazard_excludes: skip device-name paths; handle known bad paths
    - documentation: maintain mapping log and owner approvals for archives
```

---

## 6) Naming Conventions

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| Python Modules | `snake_case.py` | `user_service.py` |
| Python Classes | `PascalCase` | `UserService` |
| TypeScript/React | `PascalCase.tsx` | `Dashboard.tsx` |
| Test Files | `test_*.py` or `*.test.ts` | `test_user_service.py` |
| Documentation | `SCREAMING_SNAKE_CASE.md` | `ARCHITECTURE.md` |

### Directory Naming

| Type | Convention | Example |
|------|------------|---------|
| Feature Modules | `snake_case/` | `user_management/` |
| Component Folders | `PascalCase/` | `Dashboard/` |
| Utility Folders | `lowercase/` | `utils/`, `config/` |

---

## 7) Migration & Validation Checklist

- [ ] All `__init__.py` files created for Python packages
- [ ] Import paths updated in all source files
- [ ] Test imports verified and passing
- [ ] No circular dependencies introduced
- [ ] Build/lint scripts updated with new paths
- [ ] CI/CD workflows updated
- [ ] Documentation links updated
- [ ] `.gitignore` updated for new structure
- [ ] IDE workspace settings updated

---

## 8) Benefits of New Structure

| Benefit | Description |
|---------|-------------|
| **Discoverability** | Files are where you expect them based on their purpose |
| **Scalability** | Each domain can grow independently |
| **Testability** | Tests mirror source structure for easy navigation |
| **Onboarding** | New developers understand the codebase faster |
| **Maintenance** | Changes are localized to specific domains |
| **CI/CD** | Easier to set up targeted builds and tests |

---

## Corrected Structured Schema (safe, staged)

```yaml
proposal:
  name: grid_repository_restructure_v1_safe
  goals:
    - increase discoverability
    - reduce duplication
    - align with domain-driven boundaries
  constraints:
    - no destructive moves in main; use feature branch only
    - no Move-Item -Force; prefer copy + shim, then cutover after tests pass
    - preserve live assets (Hogwarts/datakit) until mapped and referenced
    - handle Windows device-name hazards (e.g., great_hall/nul) by excluding
    - keep cli entrypoints working via temporary import shims
  phases:
    - pilot_scope:
        scope: narrow (one module, e.g., src/shared/utils)
        actions:
          - create target directories
          - copy files + add __init__.py
          - add compatibility imports (old paths re-export new modules)
          - update imports in touched module only
          - run lint/tests subset
    - expand_scope:
        scope: per-domain (domain/services, features/cli, infrastructure/rag)
        actions:
          - repeat pilot steps
          - update CI paths, scripts, workspace settings
          - remove shims once coverage proves green
    - archive_and_cleanup:
        guards:
          - references audited (docs/tests/tools) before moving to archive
          - no archives for active work without owner sign-off
        actions:
          - move deprecated code into archive/* with mapping doc
          - remove unused shims
  directory_map:
    domain_models:
      target: src/domain/models/
      source_examples: [models/, core/products.py, core/tool_attributes.py]
    domain_services:
      target: src/domain/services/{quantum,processing,senses,cognitive}/
      source_examples: [grid/quantum/, grid/processing/, grid/senses/]
    domain_entities:
      target: src/domain/entities/{awareness,essence,evolution}/
      source_examples: [grid/awareness/, grid/essence/, grid/evolution/]
    features_cli:
      target: src/features/cli/commands/
      source_examples: [src/cli/, application/cli/]
    features_applications:
      target: src/features/applications/{mothership,resonance}/
      source_examples: [application/mothership/, application/resonance/]
    infrastructure_rag:
      target: src/infrastructure/rag/
      source_examples: [tools/rag/]
    shared_utils:
      target: src/shared/utils/
      source_examples: [python/logging_utils.py]
    shared_types:
      target: src/shared/types/
      source_examples: [python/schema_validator.py, python/type_validator.py]
  migration_rules:
    - prefer copy then remove after validation
    - add __init__.py for every new package
    - add compatibility shims:
        pattern: old_path/module.py -> new_path/module.py re-export
        removal: after CI + tests green
    - update imports with automated tool (e.g., rewrite scripts) not manual-only
    - update docs/links and scripts simultaneously with moves
    - ensure grid CLI paths remain valid; patch entrypoints first
  validation:
    - run python -m pytest from repo root (full suite or impacted subset)
    - run lint/format (ruff/black/isort) on moved modules
    - verify CI workflows and tasks that reference paths

---

## Next Steps

1. **Review** this proposal and provide feedback
2. **Prioritize** which migrations to execute first
3. **Test** migrations on a feature branch
4. **Update** import statements incrementally
5. **Validate** all tests pass after each migration phase

---

*Generated: 2026-01-01 | GRID Repository Restructure Proposal v1.0*
