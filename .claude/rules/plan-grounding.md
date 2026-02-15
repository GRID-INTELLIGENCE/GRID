---
description: Pull conversation thread when given plan outlines; resolve to concrete references; apply format pivot or flow trace when requested
alwaysApply: false
---

# Plan Grounding Rule

## Purpose

Instruct agents to pull the conversation thread when given plan outlines, resolve items to concrete references before generation, and apply format pivot or flow trace when user requests visualization or conversion.

## Activation Conditions

Activate Plan-to-Reference behavior when user provides **at least one** of:

### 1. Explicit Activation Triggers (Seed Point 1)
**Direct user requests for plan-to-reference functionality:**
- "resolve this plan", "turn into reference map", "map to files"
- "create flow trace", "convert to CSV", "generate reference map"
- "find the code for this plan", "show me where this is implemented"

### 2. Plan Pattern Detection (Seed Point 2)
**Automatic detection of numbered/bulleted technical plans:**
- Numbered lists: "1. Fix auth bug 2. Add tests 3. Deploy to staging"
- Bullet lists with technical tasks: "- Implement user registration - Add password validation"
- Checklist format: "☐ Fix authentication ☐ Update tests ☐ Deploy"

### 3. Conversation Context Inheritance (Seed Point 3)
**Previous plan discussions in thread history:**
- Following up: "continue with that auth plan we discussed"
- Building on prior: "expand on yesterday's implementation plan"
- Referencing context: "update the plan from earlier"

### 4. Board/Task Import Integration (Seed Point 4)
**Project management tool exports (Jira, GitHub Projects, etc.):**
- "Import this Jira ticket", "convert this GitHub issue to references"
- Pasted board content with technical implementation steps
- Task exports with development requirements

### 5. IDE Integration Points (Seed Points 5-6)
**Workflow chaining and config review:**
- After reference resolution: "also check IDE config for these files"
- Config file references: "review these settings against standards"
- Cross-IDE consistency: "verify this works in VS Code and Cursor"

### 6. Documentation Enhancement (Seed Point 7)
**Documentation gap identification:**
- "document this implementation", "create README for this plan"
- "add architecture diagram for this flow"
- "update docs with these references"

### 7. Development Discipline (Seed Point 8)
**Standards enforcement and validation:**
- "check this against GRID standards", "validate against discipline rules"
- "ensure backend standards compliance"
- "verify security practices"

### 8. Error Recovery (Seed Point 9)
**Unresolved reference investigation:**
- When resolution fails: "find similar files", "search for alternatives"
- Path issues: "what's inside workspace boundary"
- Missing symbols: "find related functions"

### 9. Format Pivot (Seed Point 10)
**Output format conversion requests:**
- "export to CSV for Jira", "convert to markdown table"
- "generate mermaid diagram", "create verification chain"

**Do NOT activate** for generic lists (shopping, meeting notes, non-technical checklists) unless user explicitly requests resolution.

## Core Instructions

### 1. Pull Conversation Thread

Before processing any plan:

- Read recent conversation context
- Identify project structure and standards
- Capture user preferences and constraints
- Note any previous references or file mentions

### 2. Resolve to References

For each plan item:

- Map to `path:symbol` or `path` format
- Use `@docs`, `@.claude/rules`, `@.cursor/skills` for context
- Verify file/symbol existence
- Mark unresolved items clearly
- **Workspace boundary**: Resolve only to paths within workspace root; reject or mark unresolved any paths outside workspace (e.g., `C:\Users\...`, `../etc/`)

### 3. Apply Transform Mode

Based on user request or context:

**Reference Map**: Default output for plan resolution

- Structured mapping with severity/impact
- Executive summary format
- Verification steps

**Format Pivot**: When user requests conversion

- Plan → CSV for board import
- Plan → Markdown for documentation
- Preserve item order and metadata

**Flow Trace**: When user requests visualization

- Mermaid diagram of plan flow
- Stage connections and dependencies
- Documentation-ready format

**Verification Chain**: When user requests workflow mapping

- Prompt → Workflow → Result → Verification → Final
- Map each stage to concrete artifacts
- Include verification checkpoints

## Resolution Priority

1. **Direct Matches**: Exact file/symbol names in plan
2. **Contextual Matches**: References from conversation thread
3. **Pattern Matches**: Similar files/symbols in project
4. **Standard Matches**: THE GRID standards and rules
5. **Unresolved**: Mark for manual resolution

## Output Requirements

### Reference Map Format

```markdown
# Plan Reference Map

## Executive Summary

## Reference Mapping

## Verification Steps
```

### Format Pivot Format

- CSV: `Item,Reference,Severity,Impact,Status`
- MD: Table format with headers

### Flow Trace Format

- Mermaid flowchart syntax
- Clear stage connections
- Decision points where applicable

### Verification Chain Format

- Numbered stages
- Input/Output for each stage
- Reference to concrete artifacts

## Integration Points

### With IDE Verification

- When reference map generated, offer config review
- Check referenced files against standards
- Verify IDE settings for referenced paths

### With Config Reviewer

- Review referenced config files
- Check standards compliance
- Identify conflicts or gaps

## Constraints

1. **No Invention**: Never create references that don't exist
2. **Thread Context**: Always use conversation for grounding
3. **Clear Marking**: Unresolved items must be marked
4. **Order Preservation**: Maintain plan sequence
5. **Standards Alignment**: Use THE GRID severity/impact model
6. **Workspace Boundary**: Only resolve to paths under workspace root; never reference paths outside workspace

## Examples

### Example 1: User provides numbered plan

**User Input:**

```
1. Fix authentication bug
2. Add password history
3. Update tests
4. Deploy to staging
```

**Agent Action:**

1. Pull thread (note: auth system, password history recently added)
2. Resolve:
   - "Fix authentication bug" → `src/grid/api/routers/auth.py:login_for_access_token`
   - "Add password history" → `src/grid/models/password_history.py`
   - "Update tests" → `tests/integration/test_auth_flow.py`
   - "Deploy to staging" → `infrastructure/kubernetes/api-deployment.yaml`
3. Generate reference map with verification steps

### Example 2: User requests format pivot

**User Input:**
"Convert this plan to CSV for import"

**Agent Action:**

1. Resolve plan items to references
2. Generate CSV with columns: Item,Reference,Severity,Impact,Status
3. Include metadata for board import

### Example 3: User requests flow trace

**User Input:**
"Create a flow trace for this deployment plan"

**Agent Action:**

1. Resolve deployment stages to concrete files
2. Generate Mermaid flowchart
3. Include decision points and verification gates

## Verification Checklist

Before final output:

- [ ] Conversation thread pulled and used
- [ ] All plan items resolved or marked unresolved
- [ ] References verified to exist
- [ ] Output format matches user request
- [ ] Severity/impact classification applied
- [ ] Verification steps included

## Related Rules

- **IDE Verification**: `.claude/rules/ide-config-standards.md`
- **Development Discipline**: `.claude/rules/discipline.md`
- **Security Standards**: `.claude/rules/safety.md`
- **Backend Standards**: `.claude/rules/backend.md`
