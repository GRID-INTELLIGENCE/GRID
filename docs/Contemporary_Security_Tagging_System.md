# Contemporary Security Tagging System

## Tag Taxonomy

| Tag Category | Identifier | Description |
| :--- | :--- | :--- |
| **Divergent Event** | `[DIVERGENT]` | Marks an event or code path that deviates from the approved safety baseline, indicating potential unauthorized observance. |
| **Primary Evidence** | `[LENS-PRIMARY]` | Direct, irrefutable evidence of a security event or architectural flaw. Used for audit-critical artifacts. |
| **Agentic Safety** | `[AGENTIC-GUARD]` | Protocols and checks specifically designed to contain and monitor AI agent behavior. |
| **Audit Status** | `[PENDING-AUDIT]` | Items or reports that require formal verification by the security audit team. |

## Usage Guidelines
- Apply `[DIVERGENT]` to any log entry where model output contradicts system prompt constraints.
- Use `[LENS-PRIMARY]` for all core incident transcripts and root cause analysis documents.
- Tag all LLM-facing middleware logs with `[AGENTIC-GUARD]`.
