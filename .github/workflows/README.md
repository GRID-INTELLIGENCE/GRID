# GitHub Actions CI/CD Workflows

This directory contains automated testing and quality gates for the GRID project.

## Workflows Overview

### 1. **ci-main.yml** – Primary CI/CD Pipeline

Comprehensive quality checks, security, tests, and build verification.

**Triggers:**
- Push to `main`, `develop`, `feature/**`, `release/**`, `hotfix/**`, `architecture/**` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Key Jobs:**
- ✅ **secrets-scan**: Heuristic secret scanning
- ✅ **smoke-test**: Quick environment verification and import checks
- ✅ **lint**: Code quality (ruff, black, mypy, pre-commit)
- ✅ **security**: Security scanning (bandit, pip-audit)
- ✅ **test**: Matrix tests across Python 3.11, 3.12, 3.13 with coverage
- ✅ **integration**: Integration tests (main branch only)
- ✅ **build**: Package building and verification
- ✅ **verify-dist**: Distribution package verification
- ✅ **verify-deployment**: MCP server and Ghost Registry verification (main branch only)

**Coverage Requirements:**
- Minimum: **80%** of `grid/`, `src/`, `tools/` modules
- Reports archived as artifacts

**Duration:** ~20-30 minutes total

---

### 2. **agent_validation.yml** – Agent & Schema Validation

Validates agent contracts and schemas.

**Triggers:**
- Pull requests affecting `manifest.json`, `modules/`, `contracts/`, or validation tools
- Push to `main` or `develop` branches

**Key Jobs:**
- unit_test: Unit tests for agent components
- contract_test: OpenAPI and JSON schema validation
- integration_test: Integration tests
- analyze: Contract coverage analysis (isolated, non-blocking)
- schema-validation: Schema validation (consolidated from schema-validation.yml)

**Duration:** ~5-10 minutes

---

### 3. **skills-quality.yml** – Skills Continuous Quality

Continuous quality monitoring for skills with auto-tuning capabilities.

**Triggers:**
- Schedule: Every 4 hours
- Manual workflow dispatch
- Push/PR to `src/grid/skills/**` or `tests/skills/**`

**Key Jobs:**
- unit-tests: Unit tests with coverage (80% threshold)
- integration-tests: Integration tests
- signal-quality-check: NSR (noise-to-signal ratio) analysis
- performance-regression-check: Performance degradation detection
- nightly-full-tests: Complete test suite (scheduled runs)
- threshold-tuning: Auto-tune NSR thresholds (scheduled runs)

**Duration:** ~15-60 minutes (varies by schedule)

---

### 4. **docker-build.yml** – Docker Image Building

Builds Docker images and runs security scanning.

**Triggers:**
- Push to `main` or `architecture/**` branches
- Tags matching `v*`
- Pull requests to `main`
- Manual workflow dispatch

**Key Jobs:**
- build: Multi-platform Docker image building
- scan: Trivy vulnerability scanning (non-blocking)

**Duration:** ~10-15 minutes

---

### 5. **release.yml** – Release & Publishing

Automated release workflow for versioning, changelog generation, and PyPI publishing.

**Triggers:**
- Tags matching `v*.*.*`
- Manual workflow dispatch with version bump options

**Key Jobs:**
- prepare: Version determination and changelog generation
- test: Tests before release
- build: Package building
- publish-pypi: Publish to PyPI
- release: Create GitHub release

**Duration:** ~10-15 minutes

---

## Running Workflows

### Automatically (on push/PR)

Just push to `main` or `develop`:

```bash
git push origin feature-branch
# Workflows trigger automatically
```

### Manually from Actions Tab

1. Go to **Actions** tab on GitHub
2. Select a workflow
3. Click **Run workflow**
4. Select branch and click **Run**

### Manually with GitHub CLI

```bash
# Run specific workflow
gh workflow run ci-main.yml --ref main

# List all workflows
gh workflow list

# View workflow runs
gh run list --workflow ci-main.yml
```

---

## Branch Protection Rules

**Recommended Protection (main & develop branches):**

```
✓ Require status checks to pass before merging:
  - All Checks Passed (ci-main.yml)
  - Agent & Schema Validation (agent_validation.yml)

✓ Require code review: minimum 1 approval

✓ Dismiss stale reviews: when new commits pushed

✓ Restrict who can push: only admins (optional)
```

**To configure:**

1. Go to **Settings → Branches**
2. Select `main` (or `develop`)
3. Under "Require status checks to pass before merging":
   - Select workflow checks above
   - Check "Require branches to be up to date before merging"
4. Click **Save changes**

---

## Troubleshooting

### Workflow Failed: "Tests failed"

1. Check **Details** → **Run tests** step
2. Look for test failures in output
3. Run locally: `pytest tests/ -v`

### Workflow Failed: "Coverage below 80%"

1. Download **coverage-reports** artifact
2. Review `htmlcov/index.html` (HTML report)
3. Add tests for uncovered code

### Workflow Failed: "Format check"

1. Run locally: `uv run black src/ tests/ scripts/`
2. Format will auto-fix files
3. Commit formatted changes
4. Re-push

### Workflow Failed: "Type check"

1. Check **Details** → **Type check with mypy** step
2. Run locally: `uv run mypy src/ --ignore-missing-imports`
3. Add type annotations to flagged code
4. Re-push

### Workflow Timed Out (>15 min)

1. May indicate flaky/slow tests
2. Check **Run unit tests** and **Run integration tests** steps
3. Mark slow tests: `@pytest.mark.slow`
4. Run fast tests locally: `pytest tests/ -m "not slow"`

---

## Artifacts & Reports

Each workflow run generates downloadable artifacts:

### ci-main.yml
- `coverage-reports-*.zip` – HTML coverage reports
- `test-report-*.html` – Detailed test results
- `security-reports` – Bandit findings
- `dist-packages` – Built distribution packages

### agent_validation.yml
- `inventory` – Agent inventory report
- `schema-validation-report` – Schema validation results

### skills-quality.yml
- `integration-test-results` – Integration test results
- `signal-quality-report` – NSR analysis
- `nightly-test-results` – Scheduled test results

### How to Download

1. Go to **Actions** → select run
2. Scroll to **Artifacts** section
3. Click artifact name to download
4. Extract and review locally

---

## Environment Variables

Workflows inherit environment from `pyproject.toml` and `.env` files.

**Key Variables (for CI):**

```bash
PYTHONDONTWRITEBYTECODE=1    # Skip .pyc generation
PYTHONUNBUFFERED=1           # Unbuffered output
GRID_ENVIRONMENT=testing     # Environment mode
```

**To add secrets (e.g., API keys):**

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add secret (e.g., `MOTHERSHIP_TEST_SECRET_KEY`)
4. Reference in workflow: `${{ secrets.MOTHERSHIP_TEST_SECRET_KEY }}`

---

## Monitoring & Dashboards

### GitHub Actions Tab

- **All workflows** status visible at `/actions`
- **Badges** available (copy from workflow details)

### Example Badge Markdown

```markdown
![CI](https://github.com/YOUR_ORG/grid/actions/workflows/ci-main.yml/badge.svg)
![Agent Validation](https://github.com/YOUR_ORG/grid/actions/workflows/agent_validation.yml/badge.svg)
```

---

## Best Practices

### For Developers

1. **Run locally before pushing:**

   ```bash
   uv run pytest tests/ -v      # Run tests
   uv run ruff check src/       # Run linting
   uv run black src/ tests/     # Format code
   uv run mypy src/             # Type check
   ```

2. **Fix issues before PR:**
   - Failed tests: Run `pytest` and fix
   - Format: Run `black` to auto-fix
   - Type errors: Run `mypy` and fix

### For Reviewers

1. **Check workflow status before approval:**
   - All checks must pass (green ✅)
   - Click **Details** to investigate failures
   - Request fixes before merging

2. **Review coverage changes:**
   - Look for significant drops (<5% acceptable)
   - Suggest tests for new code

### For Maintainers

1. **Monitor workflow performance:**
   - Set alerts if avg run time increases
   - Consider caching dependencies if >10 min

2. **Update Python versions quarterly:**
   - Keep test matrix current (3.11, 3.12, 3.13)
   - Test new Python releases before updating

3. **Review security reports:**
   - Monthly check of Bandit findings
   - Monthly check of Safety vulnerabilities
   - Update vulnerable dependencies promptly

---

## Quick Reference

| Workflow       | Trigger | Duration  | Fail Action  |
| -------------- | ------- | --------- | ------------ |
| ci-main.yml    | push/PR | 20-30 min | Blocks merge |
| agent_validation.yml | push/PR | 5-10 min | Advisory     |
| skills-quality.yml | schedule | 15-60 min | Advisory     |
| docker-build.yml | push/tag | 10-15 min | Advisory     |
| release.yml    | tag/dispatch | 10-15 min | Publishes    |

---

## Support

- **Documentation:** See inline comments in workflow files
- **Issues:** File GitHub issue with workflow failure details
- **Questions:** Consult project README or team documentation
