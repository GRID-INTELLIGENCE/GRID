# Evaluation Metrics & Acceptance Criteria

Quantitative and qualitative metrics for evaluating system evolution and agent-generated changes.

## Core Metrics (Quantitative + Qualitative)

### Contract Coverage
- **Target**: 100% of modules have parseable `interface_schema`
- **Measurement**: `(modules_with_schema / total_modules) * 100`
- **Validation**: `python tools/agent_validate.py --check-contracts`

### Contract Tests Passing
- **Target**: 100% passing in CI for gated merges
- **Measurement**: `(passing_contract_tests / total_contract_tests) * 100`
- **Validation**: CI job `contract_test` must exit with code 0

### Unit Test Coverage
- **Target**: ≥80% for core modules (grid/, application/)
- **Measurement**: `pytest --cov=grid --cov-report=term-missing`
- **Validation**: Coverage report must show ≥80% for modified modules

### Validation Pass Rate
- **Target**: 100% on PRs
- **Measurement**: `validate_system.py` exit code must be 0
- **Validation**: Pre-merge check in CI

### Integration Smoke Tests
- **Target**: `composition_root.py --dry-run` success (exit code 0)
- **Measurement**: Dry-run execution without errors
- **Validation**: CI job `integration_test` must pass

### Reliability Guardrails
- **Rule**: No change to orchestrator without owner approval
- **Measurement**: Manual approval required for `composition_root.py` changes
- **Validation**: PR must have approval from code owner

### Adaptive Learning Metrics (for ML modules)
- **A/B Metrics**: Delta in decision quality (accuracy, F1, etc.)
- **Model Drift Score**: Must be < threshold (default: 0.3)
- **Measurement**: Compare model performance before/after update
- **Validation**: Automated drift detection in CI

## Acceptance Criteria Template

For each task/story, acceptance criteria must include:

### Required Criteria

1. **Code Quality**
   - [ ] All modified files pass `flake8` (or project linter)
   - [ ] All modified files pass `mypy` type checking
   - [ ] No new linting errors introduced

2. **Validation**
   - [ ] `validate_system.py` returns exit code 0 locally
   - [ ] `validate_system.py` returns exit code 0 in CI
   - [ ] All contract schemas are parseable

3. **Testing**
   - [ ] New contract tests added (if applicable)
   - [ ] New contract tests passing in CI
   - [ ] Unit test coverage ≥80% for modified modules
   - [ ] Integration tests pass (if applicable)

4. **Documentation**
   - [ ] README updated (if interface changed)
   - [ ] Changelog entry added
   - [ ] API documentation updated (if applicable)

5. **Rollback**
   - [ ] Rollback command documented
   - [ ] Rollback command tested (dry-run)
   - [ ] Previous artifact tagged for restore

### Example Acceptance Criteria

```markdown
## Acceptance Criteria

- [ ] `validate_system.py manifest.json` exits with code 0
- [ ] All modules in `modules/` declare `interface_schema` and `version` matching SemVer
- [ ] Contract tests added for module `analog_bass` and passing in CI
- [ ] Unit test coverage for `grid/patterns/hybrid_detection.py` ≥80%
- [ ] CI pipeline includes `contract_test` stage
- [ ] Rollback command: `git revert <commit_hash> && python validate_system.py`
```

## Rollback Patterns

### Fast Rollback
```bash
# Revert the merge commit and re-deploy artifact from prior CI release
git revert <merge_commit_hash>
git push origin main
# Re-deploy previous artifact from CI artifact registry
```

### Canary Rollback
```bash
# If canary deployment shows degradation
# 1. Stop canary traffic
# 2. Revert to previous version
git revert <commit_hash>
# 3. Re-deploy
```

### Audit Trail Rollback
```bash
# Every release must include manifest and validation report
# Rollback restores previous manifest and validation report
git checkout <previous_tag> -- manifest.json
python validate_system.py manifest.json
```

## Metric Collection Script

Example script for collecting metrics:

```python
#!/usr/bin/env python3
"""Collect evaluation metrics for system evolution."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

def get_contract_coverage(repo_root: Path) -> float:
    """Calculate contract coverage percentage."""
    # Implementation: count modules with interface_schema / total modules
    pass

def get_test_coverage(repo_root: Path) -> Dict[str, float]:
    """Get test coverage for modules."""
    result = subprocess.run(
        ['pytest', '--cov=grid', '--cov-report=json'],
        capture_output=True,
        text=True
    )
    # Parse coverage.json
    return {"overall": 0.85, "grid/patterns": 0.90}

def get_validation_status(repo_root: Path) -> bool:
    """Check if validation passes."""
    result = subprocess.run(
        ['python', 'validate_system.py', 'manifest.json'],
        cwd=repo_root,
        capture_output=True
    )
    return result.returncode == 0

def collect_metrics(repo_root: Path) -> Dict[str, Any]:
    """Collect all evaluation metrics."""
    return {
        "contract_coverage": get_contract_coverage(repo_root),
        "test_coverage": get_test_coverage(repo_root),
        "validation_passing": get_validation_status(repo_root),
        "contract_tests_passing": True,  # Would check CI logs
        "integration_tests_passing": True  # Would check CI logs
    }

if __name__ == '__main__':
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    metrics = collect_metrics(repo_root)
    print(json.dumps(metrics, indent=2))
```

## Metric Thresholds

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Contract Coverage | 100% | <95% | <90% |
| Contract Tests Passing | 100% | <95% | <90% |
| Unit Test Coverage (core) | ≥80% | <75% | <70% |
| Validation Pass Rate | 100% | <95% | <90% |
| Integration Tests | 100% | <95% | <90% |
| Model Drift Score | <0.2 | 0.2-0.3 | >0.3 |

## Reporting Format

Metrics should be reported in this format:

```json
{
  "timestamp": "2025-01-08T10:00:00Z",
  "task_id": "STORY-1",
  "metrics": {
    "contract_coverage": 1.0,
    "contract_tests_passing": 1.0,
    "unit_test_coverage": {
      "overall": 0.85,
      "modified_modules": {
        "grid/patterns/hybrid_detection.py": 0.90
      }
    },
    "validation_exit_code": 0,
    "integration_tests_passing": true,
    "model_drift_score": 0.15
  },
  "thresholds_met": {
    "contract_coverage": true,
    "contract_tests": true,
    "unit_coverage": true,
    "validation": true,
    "integration": true,
    "drift": true
  },
  "status": "pass|fail|warning"
}
```
