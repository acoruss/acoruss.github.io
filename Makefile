.PHONY: help dev run migrate makemigrations createsuperuser collectstatic \
       format lint test template-test \
       tailwind-build tailwind-watch tailwind-install \
       docker-up docker-down docker-build docker-logs \
       setup clean copy-images shell

SHELL := /bin/zsh
DC := docker compose -f docker/compose.dev.yml
DC_EXEC := $(DC) exec web
DC_RUN := $(DC) run --rm web

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Development ──────────────────────────────────────────────

setup: ## Initial project setup (install frontend deps, build CSS, copy images)
	cd frontend && npm install
	$(MAKE) tailwind-build
	$(MAKE) copy-images

dev: setup ## Start development environment (Docker)
	$(DC) up --build

run: dev ## Alias for dev

down: ## Stop development environment
	$(DC) down

logs: ## View Docker container logs
	$(DC) logs -f

# ─── Django Management ───────────────────────────────────────

migrate: ## Run database migrations
	$(DC_EXEC) sh -c "cd /app/src && python manage.py migrate"

makemigrations: ## Create new migrations
	$(DC_EXEC) sh -c "cd /app/src && python manage.py makemigrations"

createsuperuser: ## Create a superuser
	$(DC_EXEC) sh -c "cd /app/src && python manage.py createsuperuser"

collectstatic: ## Collect static files
	$(DC_EXEC) sh -c "cd /app/src && python manage.py collectstatic --noinput"

shell: ## Open Django shell
	$(DC_EXEC) sh -c "cd /app/src && python manage.py shell"

# ─── Code Quality ────────────────────────────────────────────

format: ## Format code with ruff
	$(DC_EXEC) ruff format src/ tests/
	$(DC_EXEC) ruff check --fix src/ tests/

lint: ## Lint code with ruff
	$(DC_EXEC) ruff check src/ tests/
	$(DC_EXEC) ruff format --check src/ tests/

test: ## Run tests with pytest
	$(DC_EXEC) sh -c "cd /app/src && DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest ../tests/ -v"

template-test: ## Test that all templates load correctly
	$(DC_EXEC) sh -c "cd /app/src && python -c \"import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'; import django; django.setup(); from django.template.loader import get_template; templates = ['index.html', 'base.html', 'services.html', 'pricing.html', 'projects.html', 'about.html', 'contact.html', 'privacy_policy.html', 'terms_of_service.html', 'dashboard/base.html', 'dashboard/home.html', 'dashboard/login.html']; [print(f'  ok {t}') or get_template(t) for t in templates]; print('All templates loaded successfully!')\""

# ─── Frontend ────────────────────────────────────────────────

tailwind-install: ## Install frontend dependencies
	cd frontend && npm install

tailwind-build: ## Build Tailwind CSS (production)
	cd frontend && npm run build

tailwind-watch: ## Watch Tailwind CSS for changes (development)
	cd frontend && npm run watch

copy-images: ## Copy public images to static directory
	mkdir -p src/static/images/logos
	cp -r public/images/logos/* src/static/images/logos/

# ─── Docker ──────────────────────────────────────────────────

docker-build: ## Build Docker image for production
	docker build -f docker/Dockerfile -t acoruss-web .

docker-prod-up: ## Start production Docker containers
	docker compose -f docker/compose.prod.yml up -d

docker-prod-down: ## Stop production Docker containers
	docker compose -f docker/compose.prod.yml down

# ─── Cleanup ─────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf staticfiles/ 2>/dev/null || true