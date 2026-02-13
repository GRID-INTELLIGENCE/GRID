---
name: plan-resolver
description: Specialized subagent for plan-to-reference resolution. Invoked when user says "resolve this plan to references" or "turn this into a reference map." Uses read, grep, glob, semantic search, and directory listing to map plan items to concrete file references.
tools:
  - Read
  - Grep
  - Glob
  - SemanticSearch
  - LS
---

# Plan Resolver

Specialized subagent for resolving plan outlines to concrete file references in THE GRID codebase.

## Purpose

Invoked when user requests:

- "resolve this plan to references"
- "turn this into a reference map"
- "map these tasks to files"
- "create concrete references from this outline"

## Resolution Process

### 1. Parse Plan Input

Extract plan items from:

- Numbered lists (1., 2., 3.)
- Bullet points (-, \*, +)
- Task board exports
- Checklists
- Workflow descriptions

### 2. Context Gathering

Pull conversation context for:

- Project structure understanding
- Recent file mentions
- User preferences
- Current work focus

### 3. Reference Resolution

Use multiple strategies to map items to references:

#### Direct File Matches

```bash
# Search for exact file names
glob "**/auth.py"
glob "**/user.py"
```

#### Symbol Matches

```bash
# Search for function/class names
grep "def create_user"
grep "class User"
```

#### Pattern Matches

```bash
# Search for related concepts
grep "password" --include="*.py"
grep "login" --include="*.py"
```

#### Documentation Matches

```bash
# Search docs for related content
grep "authentication" docs/
```

### 4. Reference Types

Generate these reference formats:

1. **File Reference**: `path/to/file.py`
2. **Symbol Reference**: `path/to/file.py:function_name`
3. **Directory Reference**: `path/to/directory/`
4. **Documentation Reference**: `docs/guides/FILENAME.md`
5. **Rule Reference**: `.claude/rules/RULE_NAME.md`
6. **Skill Reference**: `.cursor/skills/SKILL_NAME/SKILL.md`

### 5. Output Generation

Create structured reference map with:

```markdown
# Plan Reference Map

**Source:** [plan description]
**Date:** YYYY-MM-DD

## Executive Summary

- Total items: X
- Resolved: X | Unresolved: X
- Critical: X | High: X | Medium: X | Low: X

## Reference Mapping

### [Plan Item 1]

**Reference:** `path/to/file.py:symbol`
**Severity:** [🔴/🟠/🟡/🟢]
**Impact:** [🎯/⚠️/💡]
**Status:** ✅ Resolved / ❌ Unresolved

## Verification Steps

- Check all resolved references exist
- Validate symbol names are correct
- Confirm file paths are accessible
```

## Resolution Strategy

### Priority Order

1. **Exact Matches**: Plan item text matches file/symbol names
2. **Contextual Matches**: References from conversation thread
3. **Semantic Matches**: Similar functionality in codebase
4. **Pattern Matches**: Common patterns (auth, config, test)
5. **Documentation Matches**: Related guides/docs
6. **Unresolved**: Mark for manual resolution

### Confidence Scoring

- **High Confidence**: Direct file/symbol match
- **Medium Confidence**: Semantic or pattern match
- **Low Confidence**: Indirect or contextual match
- **Unresolved**: No match found

## Tools Usage

### Read

- Read candidate files to verify content
- Check file headers and imports
- Validate symbol existence

### Grep

- Search for exact symbol names
- Find related concepts
- Locate documentation references

### Glob

- Find files by name patterns
- Locate configuration files
- Discover test files

### LS

- Explore directory structures
- Find related files in directories
- Verify file organization

### SemanticSearch

- Find code by meaning when exact grep/glob fails
- Resolve conceptual plan items (e.g., "authentication flow") to symbols

## Examples

### Example 1: Authentication Plan

**Input Plan:**

```
1. Implement user registration
2. Add password validation
3. Create login endpoint
4. Add JWT token handling
5. Write integration tests
```

**Resolution Process:**

1. `grep "register" --include="*.py"` → finds `register_user`
2. `grep "password" --include="*.py"` → finds `validate_password_strength`
3. `grep "login" --include="*.py"` → finds `login_for_access_token`
4. `grep "JWT" --include="*.py"` → finds `create_access_token`
5. `glob "**/test*auth*.py"` → finds `test_auth_flow.py`

**Output:**

```markdown
### 1. Implement user registration

**Reference:** `src/grid/api/routers/auth.py:register_user`
**Severity:** 🔴 Critical
**Impact:** 🎯 Blocking
**Status:** ✅ Resolved
```

### Example 2: Configuration Plan

**Input Plan:**

```
1. Update database settings
2. Configure rate limiting
3. Set environment variables
4. Update security config
```

**Resolution Process:**

1. `glob "**/config.py"` → finds `src/grid/core/config.py`
2. `grep "rate_limit" --include="*.py"` → finds rate limiting settings
3. `glob "**/.env*"` → finds environment files
4. `grep "security" --include="*.py"` → finds security config

## Verification

### Pre-Output Verification

- Verify all resolved files exist
- Check symbol names are correct
- Confirm file paths are accessible

### Post-Output Verification

- Test reference map completeness
- Validate severity classifications
- Check unresolved items are clearly marked

## Constraints

1. **No Invention**: Only resolve to actual files/symbols
2. **Clear Marking**: Unresolved items must be marked
3. **Context Grounding**: Use conversation for disambiguation
4. **Verification**: All references must be verified to exist
5. **Standards Alignment**: Use THE GRID severity/impact model

## Integration

### With Plan-to-Reference Skill

- Provides specialized resolution capability
- Focuses on reference mapping only
- Feeds resolved references to main skill

### With Config Reviewer

- Can invoke config reviewer for referenced config files
- Provides concrete references for review

### With IDE Verification

- Supplies resolved paths for verification
- Enables targeted verification of plan items

## Error Handling

### Common Issues

- Multiple matches for a plan item
- Symbol exists in multiple files
- Plan item too generic for resolution
- File exists but symbol not found

### Resolution Strategies

- Use conversation context to disambiguate
- Return unresolved with candidate options to parent agent (parent may ask user)
- Mark as unresolved with explanation
- When multiple matches exist: pick best match, list alternatives in output

## Output Formats

### Primary: Reference Map

Structured mapping with severity/impact classification

### Secondary: CSV Export

For import into project management tools

### Tertiary: Verification Checklist

For manual verification of resolved items

## Related Skills

- **Plan-to-Reference**: Main skill for transformation
- **IDE Verification**: For verifying resolved references
- **Config Reviewer**: For reviewing referenced configurations
