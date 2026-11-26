.PHONY: help env venv install install-dev run test check clean \
	build up down restart logs ps shell update prune

.DEFAULT_GOAL := help

PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

help: ## Show available local & production commands
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ==============================================================================
# Local Development
# ==============================================================================

env: ## Create .env from .env.example if missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists"; fi

venv: ## Create Python 3.12 virtual environment in .venv
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: venv ## Install runtime dependencies into .venv
	$(BIN)/pip install -r requirements.txt

install-dev: venv ## Install runtime + dev/test dependencies into .venv
	$(BIN)/pip install -r requirements-dev.txt

run: ## Run the bot locally
	$(BIN)/python main.py

test: ## Run pytest suite
	$(BIN)/pytest -v

check: ## Run syntax compilation check and pytest suite
	$(BIN)/python -m compileall -q data filters handlers keyboards middlewares states utils main.py
	$(BIN)/pytest -v

clean: ## Remove local caches and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

# ==============================================================================
# Docker / Production
# ==============================================================================

build: ## Build Docker image without cache
	docker compose build

up: env ## Build and start bot in background (production)
	docker compose up -d --build

down: ## Stop and remove bot container
	docker compose down

restart: ## Restart running bot container
	docker compose restart

logs: ## Follow bot container logs
	docker compose logs -f --tail=100 bot

ps: ## Show container status
	docker compose ps

shell: ## Open shell inside running bot container
	docker compose exec bot /bin/sh

update: ## Pull latest code and redeploy container
	git pull --ff-only
	docker compose up -d --build --remove-orphans

prune: ## Remove unused Docker images and build cache
	docker image prune -f
	docker builder prune -f
