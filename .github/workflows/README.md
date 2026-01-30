# GitHub Actions CI/CD Workflows

This directory contains automated testing and quality gates for the GRID project.

## Workflows Overview

### 1. **ci-test.yml** – Test Execution with Coverage

Runs comprehensive test suite across Python 3.11, 3.12, and 3.13.

**Triggers:**

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch (via Actions tab)

**Key Steps:**

- ✅ Matrix test across Python 3.11, 3.12, 3.13 (parallel execution)
- ✅ Unit tests + integration tests
- ✅ Coverage reporting (fails if <80%)
- ✅ Uploads coverage to Codecov
- ✅ Generates HTML coverage report
- ✅ HTML test report with details

**Coverage Requirements:**

- Minimum: **80%** of `grid/`, `src/`, `tools/` modules
- Reports archived as artifacts for download
- Coverage trends tracked in Codecov dashboard

**Duration:** ~5-8 minutes per Python version (15-24 min total)

---

### 2. **ci-quality.yml** – Code Quality Gates

Enforces code formatting, linting, type checking, and security standards.

**Triggers:**

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Quality Checks:**

| Tool           | Purpose                    | Failure Action               |
| -------------- | -------------------------- | ---------------------------- |
| **Black**      | Code formatting            | Report diff, continue        |
| **Ruff**       | Linting & style            | Report violations, continue  |
| **mypy**       | Type checking              | Report errors, continue      |
| **Bandit**     | Security scanning          | Report issues, always passes |
| **Safety**     | Dependency vulnerabilities | Report issues, always passes |
| **pre-commit** | Local hooks suite          | Fail if violations           |

**Duration:** ~2-3 minutes

---

### 3. **ci.yml** – Main Orchestration

Calls specialized workflows and verifies services are functional.

**Flow:**

```
ci.yml (main orchestrator)
├── ci-quality.yml (code quality checks)
├── ci-test.yml (test suite with coverage)
└── verify-services (MCP servers, Ghost Registry handlers)
    └── all-checks (summary: pass/fail)
```

**Duration:** ~20-30 minutes total (parallel quality + test, then verification)

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
2. Select a workflow (e.g., "Code Quality Checks")
3. Click **Run workflow**
4. Select branch and click **Run**

### Manually with GitHub CLI

```bash
# Run specific workflow
gh workflow run ci-test.yml --ref main

# List all workflows
gh workflow list

# View workflow runs
gh run list --workflow ci-test.yml
```

---

## Branch Protection Rules

**Recommended Protection (main & develop branches):**

```
✓ Require status checks to pass before merging:
  - All Checks Passed (ci.yml)
  - Code Quality (ci-quality.yml)
  - Test Summary (ci-test.yml)

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
3. Click **View logs** for full output
4. Run locally: `pytest tests/ -v`

### Workflow Failed: "Coverage below 80%"

1. Check **Details** → **Check coverage threshold** step
2. Download **coverage-reports** artifact
3. Review `htmlcov/index.html` (HTML report)
4. Add tests for uncovered code

### Workflow Failed: "Format check"

1. Run locally: `black src/ tests/ scripts/`
2. Format will auto-fix files
3. Commit formatted changes
4. Re-push

### Workflow Failed: "Type check"

1. Check **Details** → **Type check with mypy** step
2. Run locally: `mypy src/ --ignore-missing-imports`
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

### ci-test.yml

- `coverage-reports-*.zip` – HTML coverage reports
- `test-report-*.html` – Detailed test results

### ci-quality.yml

- `quality-reports/` – mypy JSON reports
- `security-reports/` – Bandit & Safety findings

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
PYTEST_TIMEOUT=300           # 5 min timeout per test
```

**To add secrets (e.g., API keys):**

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add secret (e.g., `DATABRICKS_TOKEN`)
4. Reference in workflow: `${{ secrets.DATABRICKS_TOKEN }}`

---

## Monitoring & Dashboards

### GitHub Actions Tab

- **All workflows** status visible at `/actions`
- **Badges** available (copy from workflow details)

### Example Badge Markdown

```markdown
![Tests](https://github.com/YOUR_ORG/grid/actions/workflows/ci-test.yml/badge.svg)
![Quality](https://github.com/YOUR_ORG/grid/actions/workflows/ci-quality.yml/badge.svg)
```

### Codecov Integration

Coverage reports auto-upload to [codecov.io](https://codecov.io)

- View trends at `https://codecov.io/gh/YOUR_ORG/grid`
- Badge available for README

---

## Best Practices

### For Developers

1. **Run locally before pushing:**

   ```bash
   make test        # Run tests locally
   make lint        # Run linting
   make format      # Auto-format code
   ```

2. **Fix issues before PR:**
   - Failed tests: Run `pytest` and fix
   - Format: Run `black src/ tests/`
   - Type errors: Run `mypy src/` and fix

3. **Use `workflow_call` for reusability:**
   - Other workflows can call `ci-test.yml` and `ci-quality.yml`
   - See `ci.yml` for example

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
| ci-test.yml    | push/PR | 15-24 min | Blocks merge |
| ci-quality.yml | push/PR | 2-3 min   | Advisory     |
| ci.yml         | push/PR | 20-30 min | Blocks merge |

---

## Support

- **Documentation:** See `.github/workflows/*.yml` for inline comments
- **Issues:** File GitHub issue with workflow failure details
- **Questions:** Consult project README or team documentation
