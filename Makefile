# Workspace Makefile
# Unified commands for the entire Python workspace
# Usage: make <target>

.PHONY: help install sync test lint format audit clean lock export-deps

.DEFAULT_GOAL := help

# ── Colors ─────────────────────────────────────────────────────────
BLUE  := \033[0;34m
GREEN := \033[0;32m
RED   := \033[0;31m
CYAN  := \033[0;36m
NC    := \033[0m

help: ## Show available commands
	@echo "$(CYAN)Workspace Commands$(NC)"
	@echo "$(CYAN)──────────────────$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'

# ── Environment ────────────────────────────────────────────────────

install: ## Full install: create venv + sync all deps
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	uv venv --python 3.13
	@echo "$(BLUE)Syncing all dependencies...$(NC)"
	uv sync --all-groups
	@echo "$(GREEN)Environment ready. Activate: source .venv/bin/activate$(NC)"

sync: ## Sync dependencies (fast, uses lockfile)
	@echo "$(BLUE)Syncing...$(NC)"
	uv sync --all-groups

# ── Quality ────────────────────────────────────────────────────────

lint: ## Run linters (ruff + mypy)
	@echo "$(BLUE)Ruff check...$(NC)"
	uv run ruff check work/ boundaries/ safety/ scripts/
	@echo "$(BLUE)Type check...$(NC)"
	-uv run mypy work/GRID/src/grid work/Coinbase/src/coinbase work/wellness_studio/src/wellness_studio

format: ## Auto-format code (black + ruff fix)
	@echo "$(BLUE)Formatting...$(NC)"
	uv run black work/ boundaries/ safety/ scripts/
	uv run ruff check --fix work/ boundaries/ safety/ scripts/
	@echo "$(GREEN)Formatted.$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest -q --tb=short

test-grid: ## Run GRID tests only
	uv run pytest work/GRID/tests -q --tb=short

test-coinbase: ## Run Coinbase tests only
	uv run pytest work/Coinbase/tests -q --tb=short

test-wellness: ## Run wellness_studio tests only
	uv run pytest work/wellness_studio/tests -q --tb=short

# ── Security & Audit ──────────────────────────────────────────────

audit: ## Run dependency audit (vulnerabilities + outdated)
	@echo "$(BLUE)Checking for vulnerabilities...$(NC)"
	uv run pip-audit
	@echo "$(BLUE)Running bandit security scan...$(NC)"
	uv run bandit -r work/ boundaries/ safety/ -c pyproject.toml -q

audit-quick: ## Quick vulnerability check only
	uv run pip-audit --progress-spinner off

# ── Lock & Export ─────────────────────────────────────────────────

lock: ## Generate uv.lock
	@echo "$(BLUE)Locking dependencies...$(NC)"
	uv lock
	@echo "$(GREEN)uv.lock updated.$(NC)"

export-deps: ## Export requirements.txt with hashes
	@echo "$(BLUE)Exporting requirements.txt...$(NC)"
	uv export --format requirements-txt --output-file requirements.txt
	@echo "$(GREEN)requirements.txt written.$(NC)"

lock-all: lock export-deps ## Generate both uv.lock and requirements.txt

# ── Project Commands ──────────────────────────────────────────────

run-grid: ## Start GRID Mothership API
	uv run python -m application.mothership.main

run-coinbase: ## Start Coinbase CLI
	uv run coinbase

run-wellness: ## Start Wellness Studio
	uv run wellness-studio

# ── Maintenance ───────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	@echo "$(RED)Cleaning...$(NC)"
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean.$(NC)"

nuke: ## Remove venv + caches (full reset)
	@echo "$(RED)Nuking environment...$(NC)"
	rm -rf .venv .uv-cache
	$(MAKE) clean
	@echo "$(RED)Run 'make install' to rebuild.$(NC)"

info: ## Show environment info
	@echo "$(CYAN)Python:$(NC)  $$(uv run python --version)"
	@echo "$(CYAN)UV:$(NC)      $$(uv --version)"
	@echo "$(CYAN)Venv:$(NC)    $$(which python 2>/dev/null || echo 'not activated')"
	@echo "$(CYAN)Packages:$(NC) $$(uv run pip list 2>/dev/null | wc -l) installed"
