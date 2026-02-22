.PHONY: help dev run migrate makemigrations createsuperuser collectstatic \
       format lint test template-test \
       tailwind-build tailwind-watch tailwind-install \
       docker-build docker-push prod-up prod-down \
       prod-logs prod-pull prod-migrate prod-collectstatic prod-restart \
       setup clean copy-images shell

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
	$(DC_EXEC) sh -c "cd /app/src && DATABASE_URL=postgres://acoruss:acoruss@db:5432/acoruss_test DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest ../tests/ -v"

template-test: ## Test that all templates load correctly
	$(DC_EXEC) sh -c "cd /app/src && python -c \"import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'; import django; django.setup(); from django.template.loader import get_template; templates = ['index.html', 'base.html', 'services.html', 'pricing.html', 'projects.html', 'about.html', 'contact.html', 'privacy_policy.html', 'terms_of_service.html', 'dashboard/base.html', 'dashboard/home.html', 'dashboard/login.html', 'dashboard/contacts/list.html', 'dashboard/contacts/detail.html', 'dashboard/payments/list.html', 'dashboard/analytics.html', 'payments/pay.html', 'emails/contact_notification.html']; [print(f'  ok {t}') or get_template(t) for t in templates]; print('All templates loaded successfully!')\""

# ─── Frontend ────────────────────────────────────────────────

tailwind-install: ## Install frontend dependencies
	cd frontend && npm install

tailwind-build: ## Build Tailwind CSS (production)
	cd frontend && npm run build

tailwind-watch: ## Watch Tailwind CSS for changes (development)
	cd frontend && npm run watch

copy-images: ## Copy public images to static directory
	mkdir -p src/static/images/logos
	cp -r public/images/* src/static/images/

# ─── Docker ──────────────────────────────────────────────────

IMAGE_NAME := ghcr.io/acoruss/acoruss.github.io
IMAGE_TAG  ?= latest
DC_PROD := docker compose -f docker/compose.prod.yml
DC_PROD_EXEC := $(DC_PROD) exec web

docker-build: ## Build Docker production image locally
	docker build -f docker/Dockerfile --target production -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-push: ## Push Docker image to GHCR (requires docker login)
	docker push $(IMAGE_NAME):$(IMAGE_TAG)

prod-up: ## Start production containers and collect static files
	$(DC_PROD) up -d
	$(DC_PROD_EXEC) python manage.py collectstatic --noinput
	$(DC_PROD) restart web

prod-down: ## Stop production Docker containers
	$(DC_PROD) down

prod-restart: ## Restart production web container
	$(DC_PROD) restart web

prod-logs: ## View production Docker container logs
	$(DC_PROD) logs -f

prod-pull: ## Pull latest production image from GHCR
	docker pull $(IMAGE_NAME):$(IMAGE_TAG)

prod-migrate: ## Run database migrations in production
	$(DC_PROD_EXEC) python manage.py migrate

prod-collectstatic: ## Collect static files in production
	$(DC_PROD_EXEC) python manage.py collectstatic --noinput

# ─── Cleanup ─────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf staticfiles/ 2>/dev/null || true