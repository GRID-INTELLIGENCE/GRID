# Workspace Makefile
# Unified commands for the entire Python workspace
# Usage: make <target>

.PHONY: help install sync test lint format audit clean lock export-deps

.DEFAULT_GOAL := help

# â”€â”€ Colors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BLUE  := \033[0;34m
GREEN := \033[0;32m
RED   := \033[0;31m
CYAN  := \033[0;36m
NC    := \033[0m

help: ## Show available commands
	@echo "$(CYAN)Workspace Commands$(NC)"
	@echo "$(CYAN)â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'

# â”€â”€ Environment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

install: ## Full install: create venv + sync all deps
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	uv venv --python 3.13
	@echo "$(BLUE)Syncing all dependencies...$(NC)"
	uv sync --all-groups
	@echo "$(GREEN)Environment ready. Activate: source .venv/bin/activate$(NC)"

sync: ## Sync dependencies (fast, uses lockfile)
	@echo "$(BLUE)Syncing...$(NC)"
	uv sync --all-groups

# â”€â”€ Quality â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

lint: ## Run linters (ruff + mypy)
	@echo "$(BLUE)Ruff check...$(NC)"
	uv run ruff check work/ boundaries/ safety/ scripts/
	@echo "$(BLUE)Type check...$(NC)"
	-uv run mypy work/GRID/src/grid work/Coinbase/src/coinbase work/wellness_studio/src/wellness_studio

format: ## Auto-format code (ruff format + ruff check fix)
	@echo "$(BLUE)Formatting...$(NC)"
	uv run ruff format work/ boundaries/ safety/ security/ scripts/
	uv run ruff check --fix work/ boundaries/ safety/ security/ scripts/
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

# â”€â”€ Security & Audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

audit: ## Run dependency audit (vulnerabilities + outdated)
	@echo "$(BLUE)Checking for vulnerabilities...$(NC)"
	uv run pip-audit
	@echo "$(BLUE)Running bandit security scan...$(NC)"
	uv run bandit -r work/ boundaries/ safety/ -c pyproject.toml -q

audit-quick: ## Quick vulnerability check only
	uv run pip-audit --progress-spinner off

# â”€â”€ Lock & Export â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

lock: ## Generate uv.lock
	@echo "$(BLUE)Locking dependencies...$(NC)"
	uv lock
	@echo "$(GREEN)uv.lock updated.$(NC)"

export-deps: ## Export requirements.txt with hashes
	@echo "$(BLUE)Exporting requirements.txt...$(NC)"
	uv export --format requirements-txt --output-file requirements.txt
	@echo "$(GREEN)requirements.txt written.$(NC)"

lock-all: lock export-deps ## Generate both uv.lock and requirements.txt

# â”€â”€ Project Commands â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

run-grid: ## Start GRID Mothership API
	uv run python -m application.mothership.main

run-coinbase: ## Start Coinbase CLI
	uv run coinbase

run-wellness: ## Start Wellness Studio
	uv run wellness-studio

# â”€â”€ Maintenance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

# â”€â”€ Discipline Routines â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

wall: ## Daily: verify tests + lint pass before any new work
	@echo "$(CYAN)â•â•â• Verifying the Wall â•â•â•$(NC)"
	@echo "$(BLUE)Tests...$(NC)"
	uv run python -m pytest -q --tb=short
	@echo "$(BLUE)Lint...$(NC)"
	uv run ruff check work/ safety/ security/ boundaries/
	@echo "$(GREEN)Wall holds. Ready to work.$(NC)"

guard: ## Scan for eval/exec/pickle in production code
	@echo "$(CYAN)â•â•â• Security Invariant Guard â•â•â•$(NC)"
	@rg -n 'eval\(|exec\(|pickle\.' work/ safety/ security/ boundaries/ --glob '*.py' --glob '!*test*' --glob '!*archive*' && echo "$(RED)VIOLATIONS FOUND$(NC)" && exit 1 || echo "$(GREEN)CLEAN: No eval/exec/pickle found$(NC)"

weekly: ## Weekly: security audit + performance budget + invariant scan
	@echo "$(CYAN)â•â•â• Weekly Discipline â•â•â•$(NC)"
	@echo "$(BLUE)1/4 Security invariant guard...$(NC)"
	$(MAKE) guard
	@echo "$(BLUE)2/4 Dependency audit...$(NC)"
	-uv run pip-audit --progress-spinner off
	@echo "$(BLUE)3/4 Bandit scan...$(NC)"
	-uv run bandit -r safety/ security/ boundaries/ -q
	@echo "$(BLUE)4/4 Performance budget (30s target)...$(NC)"
	uv run python -m pytest -q --tb=short --durations=10
	@echo "$(GREEN)Weekly review complete.$(NC)"

test-safety: ## Run safety + boundaries tests only
	uv run python -m pytest safety/tests boundaries/tests -q --tb=short

test-frontend: ## Run frontend tests (Vitest)
	cd frontend && npm test

# â”€â”€ Claude Code â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

claude-doctor: ## Validate Claude Code configuration
	@echo "$(BLUE)Checking Claude Code setup...$(NC)"
	@echo "$(CYAN)Rules:$(NC)"
	@ls -1 .claude/rules/*.md 2>/dev/null || echo "  No rules found"
	@echo "$(CYAN)Settings:$(NC)"
	@cat .claude/settings.json 2>/dev/null | head -5
	@echo "$(CYAN)Profile:$(NC)"
	@if [ -f .claude/user-profile.json ]; then echo "  $(GREEN)âœ“ User profile found$(NC)"; else echo "  $(RED)âœ— User profile missing$(NC)"; fi

claude-chat: ## Start interactive Claude Code session
	claude

# â”€â”€ Info â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

info: ## Show environment info
	@echo "$(CYAN)Python:$(NC)   $$(uv run python --version)"
	@echo "$(CYAN)UV:$(NC)       $$(uv --version)"
	@echo "$(CYAN)Node:$(NC)     $$(node --version 2>/dev/null || echo 'not installed')"
	@echo "$(CYAN)Git:$(NC)      $$(git --version)"
	@echo "$(CYAN)Branch:$(NC)   $$(git branch --show-current)"
	@echo "$(CYAN)Remote:$(NC)   $$(git remote get-url origin 2>/dev/null || echo 'none')"
	@echo "$(CYAN)Tests:$(NC)    $$(uv run python -m pytest --collect-only -q 2>/dev/null | tail -1)"
