# Makefile for GRID Development
# Streamlines local development with uv
# Note: Dotfiles (.agentignore, .cursorrules, .python-version, .secrets.baseline) in config/

.PHONY: help install run test lint format export-requirements check-venv clean guard-no-debug docker-build docker-build-prod docker-up docker-down docker-logs docker-shell

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)GRID Development Commands$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Sync dependencies via uv
	@echo "$(BLUE)Syncing environment...$(NC)"
	uv sync

run: ## Run the Mothership API locally
	@echo "$(GREEN)Starting Mothership API...$(NC)"
	uv run python -m application.mothership.main

test: ## Run tests (unit, integration, security, api guardrails)
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest tests/unit tests/integration tests/security tests/api -q --tb=short

lint: ## Run static analysis (Ruff + Mypy)
	@echo "$(BLUE)Linting...$(NC)"
	uv run ruff check .
	@echo "$(BLUE)Type checking...$(NC)"
	-uv run mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/

guard-no-debug: ## Assert no DEBUG/ENABLE_DEV_TOKEN in production (run after test+lint for Session Verify)
	@echo "$(BLUE)Checking no debug flags in production...$(NC)"
	GRID_ENV=production uv run python scripts/assert_no_debug_in_prod.py

format: ## Auto-format code
	@echo "$(BLUE)Formatting...$(NC)"
	uv run ruff format .
	uv run ruff check . --fix

check-venv: ## Validate virtual environment health
	@echo "$(BLUE)Checking venv health...$(NC)"
	uv run python scripts/validate_venv.py

export-requirements: ## Export pinned requirements.txt from uv.lock (for legacy/CI compatibility)
	@echo "$(BLUE)Exporting requirements...$(NC)"
	uv export -f requirements-txt --no-hashes -o requirements-pip.txt

clean: ## Clean build artifacts and caches
	@echo "$(RED)Cleaning...$(NC)"
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-build: ## Build GRID Docker image (dev)
	docker build -t grid:dev --target dev .

docker-build-prod: ## Build GRID Docker image (prod)
	docker build -t grid:prod --target prod .

docker-up: ## Start GRID with Redis + Ollama
	docker compose up -d

docker-down: ## Stop GRID containers
	docker compose down

docker-logs: ## Tail GRID container logs
	docker compose logs -f --tail=50

docker-shell: ## Shell into GRID container
	docker compose exec grid-mothership bash
