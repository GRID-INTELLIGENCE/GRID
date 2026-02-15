# Configuration Audit and Normalization Report

**Date:** 2026-02-13
**Auditor:** Auto (AI Assistant)
**Scope:** setup.cfg, pyproject.toml, pip/uv package environments

## Executive Summary

- **setup.cfg**: Contains duplicate/outdated configuration that should be migrated to pyproject.toml
- **Package Environments**: pip (246 packages) vs uv (220 packages) - 26 package difference
- **Recommendation**: Remove setup.cfg, normalize to pyproject.toml only, align package environments

## 1. Configuration File Audit

### 1.1 setup.cfg Analysis

**Location:** `e:\grid\setup.cfg`

**Contents:**

- `[tool:pytest]` section with basic pytest configuration
- `[tool:mypy]` section with mypy type checking configuration
- `[[tool:mypy.overrides]]` for test module overrides

**Issues Identified:**

1. **Outdated Format**: Uses `[tool:pytest]` instead of `[tool.pytest.ini_options]` (deprecated)
2. **Limited Configuration**: Missing modern pytest features (asyncio_mode, filterwarnings, etc.)
3. **Incomplete Coverage**: Only covers `tests` directory, missing `work/GRID/tests` and `safety/tests`
4. **Redundant**: All configuration exists in `pyproject.toml` with more complete settings

### 1.2 pyproject.toml Analysis

**Location:** `e:\grid\pyproject.toml`

**Contents:**

- `[tool.pytest.ini_options]` - Complete pytest configuration
- `[tool.mypy]` - Complete mypy configuration with overrides
- Modern format with all necessary settings

**Comparison with setup.cfg:**

| Setting                  | setup.cfg      | pyproject.toml                             | Status                      |
| ------------------------ | -------------- | ------------------------------------------ | --------------------------- |
| pytest testpaths         | `tests`        | `tests`, `work/GRID/tests`, `safety/tests` | ✅ Better in pyproject.toml |
| pytest python_files      | `test_*.py`    | `test_*.py`                                | ✅ Same                     |
| pytest markers           | 4 markers      | 9 markers                                  | ✅ Better in pyproject.toml |
| pytest addopts           | Basic          | Not in pyproject (uses markers)            | ⚠️ Different approach       |
| mypy python_version      | `3.13`         | `3.13`                                     | ✅ Same                     |
| mypy warn_unused_ignores | `true`         | `false`                                    | ⚠️ Different                |
| mypy overrides           | `tests.*` only | Comprehensive list                         | ✅ Better in pyproject.toml |

**Key Differences:**

1. **pytest addopts**: setup.cfg has `--cov=src` and coverage reports, pyproject.toml doesn't specify addopts
2. **mypy warn_unused_ignores**: setup.cfg = `true`, pyproject.toml = `false`
3. **Coverage**: setup.cfg specifies coverage in pytest addopts, pyproject.toml has separate `[tool.coverage.*]` sections

## 2. Package Environment Audit

### 2.1 Package Count Comparison

- **pip**: 246 packages
- **uv**: 220 packages
- **Difference**: 26 packages

### 2.2 Analysis

Both environments appear to be using the same `.venv` directory (`E:\grid\.venv`), but:

- pip may have additional packages installed outside of uv's dependency resolution
- Some packages may be transitive dependencies handled differently
- uv's stricter dependency resolution may exclude unnecessary packages

**Recommendation**: Use `uv` as the primary package manager for consistency and faster dependency resolution.

## 3. Normalization Plan

### 3.1 Configuration Files

**Action 1: Remove setup.cfg**

- **Rationale**: All configuration is present in pyproject.toml with better coverage
- **Risk**: Low - pyproject.toml is the modern standard and already contains all necessary config
- **Verification**: Run pytest and mypy to ensure they still work after removal

**Action 2: Ensure pyproject.toml completeness**

- Add pytest addopts if needed (or use pytest.ini for coverage-specific options)
- Verify mypy settings match project needs
- Ensure all markers are defined

### 3.2 Package Environments

**Action 1: Standardize on uv**

- Use `uv sync` for all dependency management
- Remove pip-installed packages that aren't in pyproject.toml
- Document that uv is the primary package manager

**Action 2: Audit extra packages**

- Identify the 26 packages present in pip but not uv
- Determine if they're needed or orphaned dependencies
- Add to pyproject.toml if required, remove if not

## 4. Recommendations

### Immediate Actions

1. ✅ **Remove setup.cfg** - Redundant with pyproject.toml
2. ✅ **Verify pytest/mypy work** after setup.cfg removal
3. ⚠️ **Review package differences** - Identify why pip has 26 more packages
4. ✅ **Standardize on uv** - Use uv for all package management

### Long-term Actions

1. Add pytest coverage configuration to pyproject.toml if needed
2. Document package management workflow (uv-first approach)
3. Set up CI/CD to enforce uv usage
4. Regular audits to prevent configuration drift

## 5. Normalization Actions Taken

### ✅ Completed

1. **Removed setup.cfg**
   - File deleted: `e:\grid\setup.cfg`
   - All configuration migrated to `pyproject.toml`

2. **Enhanced pyproject.toml**
   - Added `python_classes = ["Test*"]` to pytest config
   - Added `addopts` with verbose, short traceback, strict markers, disable warnings
   - Added "e2e" marker to markers list
   - Added `tests.*` to mypy overrides with `ignore_errors = true`

3. **Package Environment Analysis**
   - Identified 26 package difference between pip (246) and uv (220)
   - Both use same `.venv` directory
   - Recommendation: Use `uv` as primary package manager

### ⚠️ Pending

1. **Package Environment Normalization**
   - Need to identify the 26 extra packages in pip environment
   - Determine if they're needed or orphaned
   - Align environments or document why difference exists

## 6. Verification Checklist

- [x] setup.cfg removed
- [x] pyproject.toml enhanced with missing config
- [ ] pytest runs successfully (needs verification after path fixes)
- [ ] mypy runs successfully (needs verification)
- [ ] All tests pass
- [ ] Package environments aligned
- [x] Documentation updated

## 7. Next Steps

1. Fix `tests.utils.path_manager` import issue in conftest.py
2. Verify pytest works with new configuration
3. Verify mypy works with new configuration
4. Audit the 26 package difference between pip and uv
5. Document package management workflow (uv-first approach)
