# Documentation Freshness Policy

## Active Documentation (docs/)

Active documentation lives at the `docs/` root and in these subdirectories:

| Directory | Purpose | Owner |
|-----------|---------|-------|
| `architecture/` | System architecture diagrams and descriptions | Core team |
| `decisions/` | ADRs (Architecture Decision Records) | Any contributor |
| `guides/` | How-to guides for developers | Core team |
| `project/` | Project governance (CLAUDE.md, upnext) | Core team |
| `safeguards/` | Safety and deployment governance | Core team |
| `security/` | Security architecture and policies | Core team |
| `search/` | Search service contracts | Core team |
| `structure/` | Codebase structure rules | Core team |
| `unified_fabric/` | Event bus tracing and adapter docs | Core team |
| `visualizations/` | Mermaid diagrams and rendered PNGs | Core team |
| `visual_references/` | Cognition pattern imagery | Core team |
| `mcp/` | MCP server references | Core team |
| `governance/` | Source control policies | Core team |

## Archive (docs/archive/)

Stale documentation is moved to `docs/archive/` with these categories:

| Subdirectory | Contents |
|--------------|----------|
| `sessions/` | Completed session logs, sprint summaries, checkpoint docs |
| `misc/` | One-off analyses, creative docs, transcripts, redirects |
| `deployment_old/` | Superseded Docker/deployment docs |
| `cli/` | Old CLI documentation |
| `reports/` | Completed phase reports |
| `final_release/` | RC1-era release artifacts |
| `chatlogs/` | Saved AI chat conversations |
| `the_process/` | Raw text/HTML session scrapes |
| `journal/` | Personal work-session logs |
| `changes/` | Historical changelogs |
| `contributions/` | Old contribution logs |
| `events/` | Archived event snapshots |

## Freshness Rules

1. **Session artifacts** (summaries, transcripts, completion reports) go to `docs/archive/sessions/` immediately after the session ends.
2. **One-shot analyses** that are not referenced by active code or docs go to `docs/archive/misc/`.
3. **Decision records** in `docs/decisions/` are permanent and never archived.
4. **Quarterly review**: At the start of each quarter, scan `docs/` root for files older than 90 days with no references from code or other active docs. Archive candidates.
5. **New docs**: When creating documentation, ask: "Will this be referenced again?" If no, it belongs in archive from the start.
