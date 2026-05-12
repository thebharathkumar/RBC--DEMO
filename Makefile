# rbc-research-agent-platform local task runner
#
# Targets are thin wrappers over the underlying tools so a fresh checkout has
# one canonical way to run lint, test, format, and the dev stack.

SHELL := /usr/bin/env bash
API_DIR := apps/api
WEB_DIR := apps/web
COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: help install install-api install-web fmt fmt-check lint typecheck \
        test test-cov eval up down logs ps build clean

help: ## Show this help.
	@awk 'BEGIN{FS=":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: install-api install-web ## Install all dependencies.

install-api: ## Install Python deps (editable, with dev extras).
	cd $(API_DIR) && python -m pip install -e ".[dev]"

install-web: ## Install JS deps.
	cd $(WEB_DIR) && pnpm install

fmt: ## Apply formatters.
	cd $(API_DIR) && ruff check --fix src tests && black src tests
	cd $(WEB_DIR) && pnpm format

fmt-check: ## Verify formatters would not change files.
	cd $(API_DIR) && ruff format --check src tests && black --check src tests
	cd $(WEB_DIR) && pnpm format:check

lint: ## Run linters.
	cd $(API_DIR) && ruff check src tests
	cd $(WEB_DIR) && pnpm lint

typecheck: ## Run type checkers.
	cd $(API_DIR) && mypy src
	cd $(WEB_DIR) && pnpm typecheck

test: ## Run unit and integration tests.
	cd $(API_DIR) && pytest

test-cov: ## Run tests with coverage.
	cd $(API_DIR) && pytest --cov=src --cov-report=term-missing

eval: ## Run the eval suite against pinned tickers.
	cd $(API_DIR) && pytest -m eval

up: ## Start the full dev stack.
	$(COMPOSE) up --build -d

down: ## Stop and remove the dev stack.
	$(COMPOSE) down

logs: ## Tail logs from the dev stack.
	$(COMPOSE) logs -f

ps: ## List dev stack services.
	$(COMPOSE) ps

build: ## Build all container images.
	$(COMPOSE) build

clean: ## Remove caches and build artifacts.
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache -o -name dist -o -name build \) -prune -exec rm -rf {} +
	rm -rf $(WEB_DIR)/dist $(WEB_DIR)/node_modules/.vite
