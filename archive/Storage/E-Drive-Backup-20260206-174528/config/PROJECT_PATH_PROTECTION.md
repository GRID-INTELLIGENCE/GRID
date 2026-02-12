# Project Path Configuration - IMMUTABLE
# DO NOT MODIFY THESE PATHS - EXPLICITLY PROTECTED

## Critical Project Paths

These paths are **IMMUTABLE** and **EXPLICITLY PROTECTED**:

```json
{
  "protected_projects": {
    "grid": {
      "canonical_path": "E:\\_projects\\grid",
      "alternate_paths": ["E:/_projects/grid", "e:\\_projects\\grid"],
      "protection_level": "EXPLICIT",
      "modification_allowed": false,
      "reason": "User explicit request - never move or modify"
    },
    "coinbase": {
      "canonical_path": "E:\\_projects\\Coinbase\\coinbase",
      "alternate_paths": ["E:/_projects/Coinbase/coinbase", "e:\\_projects\\Coinbase\\coinbase"],
      "protection_level": "EXPLICIT",
      "modification_allowed": false,
      "reason": "User explicit request - never move or modify"
    },
    "wellness_studio": {
      "canonical_path": "E:\\_projects\\wellness_studio",
      "alternate_paths": ["E:/_projects/wellness_studio", "e:\\_projects\\wellness_studio"],
      "protection_level": "EXPLICIT",
      "modification_allowed": false,
      "reason": "User explicit request - never move or modify"
    }
  }
}
```

## Path Rules

### Rule 1: Underscore Naming Convention
**Scope**: All titles/directories starting with underscore `_`
- `_projects` directory is the canonical parent
- Contains all protected projects
- Underscore indicates system-level/protected status
- **NEVER rename or move directories with underscore prefix**

### Rule 2: No Directory Path Changes
**EXPLICIT USER REQUEST**
- ❌ DO NOT move these project directories
- ❌ DO NOT rename these project directories  
- ❌ DO NOT restructure these project paths
- ❌ DO NOT create copies in different locations
- ✅ ONLY work within existing directory structure
- ✅ ONLY reference canonical paths listed above

## AI Agent Instructions

When working with these projects:

1. **Always use canonical paths** as specified above
2. **Never suggest** moving or reorganizing these directories
3. **Never execute** file operations that change directory structure
4. **Always verify** you're working in the correct canonical path
5. **Refuse operations** that would violate these protections

## Violation Prevention

If an operation would violate these rules:
1. Stop immediately
2. Alert user about protection violation
3. Suggest alternative approach within existing structure
4. Do not proceed without explicit user override

## Current Working Directory Context

The current worktree at `E:\.worktrees\copilot-worktree-2026-02-01T20-18-14` is:
- A temporary working tree
- NOT one of the protected projects
- Safe for modifications and experiments
- Should reference protected projects but not modify their locations

## Protected Project Relationships

```
E:\_projects\
├── grid\                          ← PROTECTED - Primary GRID framework
├── Coinbase\
│   └── coinbase\                  ← PROTECTED - Coinbase application
└── wellness_studio\               ← PROTECTED - Wellness/AI Safety framework
```

## Integration Points

When integrating between projects:
- **Reference** protected paths as read-only sources
- **Deploy artifacts** to appropriate locations within projects
- **Create symlinks** or references instead of copies
- **Document** integration points in project-specific config

## Enforcement

This configuration is:
- **Persistent** - Survives session restarts
- **Deep** - Enforced at multiple levels
- **Explicit** - Based on direct user request
- **Immutable** - Cannot be overridden by AI without user confirmation

---

**Status**: ACTIVE - ENFORCED  
**Authority**: User Explicit Request  
**Violation Handling**: Stop and alert user  
**Last Updated**: 2026-02-01
