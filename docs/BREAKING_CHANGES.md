# Breaking Changes Policy & Deprecation Guide

## Overview

This document outlines the Grid project's approach to version management, deprecation warnings, and handling breaking changes. We follow [Semantic Versioning](https://semver.org/) to communicate the impact of changes to users.

## Version Format

Grid uses `MAJOR.MINOR.PATCH` versioning:

- **MAJOR**: Breaking changes that require code updates
- **MINOR**: New features, backward compatible additions
- **PATCH**: Bug fixes, backward compatible

## Breaking Change Policy

### What Constitutes a Breaking Change

A breaking change is any modification that requires existing code using Grid to be updated:

1. **API Changes**
   - Removing public functions, methods, or classes
   - Changing function signatures (adding required parameters)
   - Changing return types (narrowing or changing data structures)
   - Renaming public exports

2. **Behavioral Changes**
   - Exceptions thrown from different error conditions
   - Default parameter value changes
   - Output format changes
   - Performance characteristics that code depends on

3. **Dependency Changes**
   - Removing dependencies (code may be using them indirectly)
   - Major version upgrades of dependencies

4. **Configuration Changes**
   - Removing configuration options
   - Changing configuration file format
   - Changing required environment variables

### What is NOT a Breaking Change

1. **Internal Implementation Details**
   - Private methods or attributes (starting with `_`)
   - Internal class restructuring
   - Performance improvements

2. **Additions**
   - New optional parameters with sensible defaults
   - New public APIs
   - New dependencies (if truly optional)

3. **Documentation**
   - Clarifications and corrections
   - Updated examples

## Deprecation Strategy

### Deprecation Process (3-Release Timeline)

We follow a structured deprecation process to minimize disruption:

```
Release N: Feature X marked @deprecated
  ↓ (users have time to migrate)
Release N+1: Deprecation warning shown at runtime
  ↓ (users must update code)
Release N+2: Feature removed entirely
```

### Deprecation Warnings

Use the provided deprecation utilities in Grid:

```python
from grid.exceptions import DeprecationWarning
import warnings

def old_function(arg):
    """Deprecated: Use new_function instead.

    Deprecated:
        This function is deprecated as of Grid 2.0
        and will be removed in Grid 3.0.
        Use new_function() instead.
    """
    warnings.warn(
        "old_function() is deprecated, use new_function() instead",
        DeprecationWarning,
        stacklevel=2
    )
    # ... implementation
```

### Docstring Format

Mark deprecated items in docstrings:

```python
def legacy_method(self) -> str:
    """Get something using legacy approach.

    Deprecated:
        1.5.0: Use new_method() instead.
        2.0.0: Will be removed. Use new_method().

    Returns:
        Legacy data format
    """
    pass
```

## Migration Guides

For each breaking change in a MAJOR release, provide:

1. **What Changed**: Clear description of the change
2. **Why**: Rationale for the change
3. **Migration Steps**: Step-by-step instructions to update code
4. **Examples**: Before and after code samples

### Template

```markdown
## Migrating from Grid 2.x to 3.0

### Change: Function signature update

**Before (Grid 2.x):**
```python
result = grid.analyze(data, model)
```

**After (Grid 3.0):**
```python
result = grid.analyze(data, config={"model": model})
```

**Why:** Improved configurability and extensibility

**Steps:**
1. Update all calls to `grid.analyze()` to use `config` parameter
2. See [docs/api.md](docs/api.md) for full configuration options
3. Run tests to ensure compatibility
```

## Exception Hierarchy Changes

Grid defines a comprehensive exception hierarchy. Ensure:

1. **New Exceptions**: Add to appropriate level of hierarchy
2. **Removed Exceptions**: Mark as deprecated before removal
3. **Exception Behavior**: Document what changed in release notes

Example hierarchy:
```python
GridException (base)
├── TaskException
├── WorkflowException
├── ValidationException
├── PatternRecognitionError
│   ├── MistDetectionError
│   └── VectorSearchError
├── DataLoadError
├── DataSaveError
└── ServiceUnavailableError
```

## Configuration Management

### Deprecating Configuration Options

```python
# In config.py with deprecation warning
class Settings(BaseSettings):
    # Old way (deprecated)
    legacy_option: str = Field(
        default="default",
        description="DEPRECATED: Use new_option instead (Grid 3.0)"
    )

    # New way
    new_option: str = Field(
        default="default",
        description="Configuration option"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if hasattr(self, 'legacy_option') and self.legacy_option:
            warnings.warn(
                "legacy_option is deprecated, use new_option",
                DeprecationWarning,
                stacklevel=2
            )
```

## Type Hints & Python Version Support

### Type Hint Modernization

We use modern Python 3.10+ type hints:

```python
# Modern (Grid 2.0+)
def process(items: list[str]) -> dict[str, int]:
    pass

# Avoid (pre-3.10)
from typing import List, Dict
def process(items: List[str]) -> Dict[str, int]:
    pass
```

If dropping Python 3.9 support, update CI/CD and documentation.

## Release Notes Format

Every release should include:

```markdown
## Grid 3.0.0 (2025-12-XX)

### ⚠️ Breaking Changes
- Removed `legacy_function()` - use `new_function()` instead
- Changed `Entity.analyze()` return type from list to dict
- See [MIGRATION.md](MIGRATION.md) for detailed migration guide

### 🆕 New Features
- Added support for async patterns in core APIs
- New `Pattern.async_match()` method

### ✨ Improvements
- Type coverage increased to 95%
- Test coverage increased to 85%

### 🐛 Bug Fixes
- Fixed memory leak in pattern cache

### 📚 Deprecated
- `old_api()` - will be removed in Grid 4.0
- Use `new_api()` instead
```

## Testing Breaking Changes

Ensure comprehensive testing:

1. **Compatibility Tests**: Verify old code fails with clear errors
2. **Migration Tests**: Verify new code works correctly
3. **Deprecation Tests**: Verify warnings are shown

```python
import warnings

def test_legacy_function_shows_deprecation():
    """Verify deprecation warning is shown."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = legacy_function()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "use new_function()" in str(w[0].message)
```

## Communication

### Before Release

1. **Announce 3+ releases before**: If breaking change will happen
2. **Include migration guide**: When deprecating
3. **Provide examples**: Show before/after code
4. **Answer questions**: Respond to issues/discussions

### In Release

1. **Changelog entry**: Clear description of breaking change
2. **Migration section**: Detailed upgrade instructions
3. **Warning messages**: Helpful deprecation messages in code

### After Release

1. **Support**: Answer migration questions
2. **Document**: Add FAQ for common issues
3. **Examples**: Update all example code

## Versioning Schedule

- **Patch releases**: Every 2-4 weeks (bug fixes)
- **Minor releases**: Every 6-8 weeks (new features)
- **Major releases**: Every 6 months (breaking changes)

## Exception: Critical Security Issues

Security fixes override normal deprecation timelines:

1. **Severe bugs**: May be fixed without deprecation period
2. **Security issues**: May require immediate action
3. **Communication**: Always document in release notes with explanation

---

## Related Documentation

- [Semantic Versioning](https://semver.org/)
- [Python Deprecation Guidelines](https://docs.python.org/3/library/warnings.html)
- [Grid API Documentation](api.md)
- [Contributing Guide](../CONTRIBUTING.md)
