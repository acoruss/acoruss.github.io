# Acoruss Web Upgrade Plan

> Migrating from static Vite site (`old-web/`) to Django 5+ with async support, Tailwind CSS + DaisyUI, PostgreSQL, Docker, and CI/CD.

## Phase 1: Django Foundation & Infrastructure

- [x] `pyproject.toml` with all dependencies (Django 5+, gunicorn, uvicorn, whitenoise, psycopg, django-environ, etc.)
- [x] `src/manage.py` entry point
- [x] `src/config/` settings package: `base.py`, `dev.py`, `test.py`, `prod.py`, `urls.py`, `asgi.py`, `wsgi.py`
- [x] Custom user model in `src/apps/accounts/` (early to avoid migration pain)
- [x] `src/apps/core/` scaffolding: `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`
- [x] `src/templates/base.html` — HTML5 skeleton with Tailwind/DaisyUI
- [x] `src/templates/index.html` — dummy content, extends base
- [x] `src/templates/dashboard/base.html` — dashboard layout stub
- [x] `frontend/` — Tailwind 3 + DaisyUI + PostCSS config, build pipeline → `src/static/css/main.css`
- [x] `docker/Dockerfile` — multi-stage (Node + Python 3.13) with dev and prod targets
- [x] `docker/compose.dev.yml` — web + db services (project name: acoruss)
- [x] `docker/compose.prod.yml` — gunicorn + uvicorn workers + db
- [x] `.env_sample` with all required variables
- [x] `Makefile` with all utility targets (Docker-first approach)
- [x] `.gitignore` and `.dockerignore` updated
- [x] Verify: `make dev` serves dummy site on `localhost:8084` ✅ All pages load

## Phase 2: CI/CD & Code Quality

- [x] Add ruff, mypy to dev dependencies; configure in `pyproject.toml`
- [x] Add pytest, pytest-django, pytest-asyncio; configure `[tool.pytest.ini_options]`
- [x] `.github/workflows/lint-format-test.yml`
- [x] `.github/workflows/build-push.yml` — build & push to GHCR
- [x] Update `scripts/test.sh`
- [ ] Verify: CI runs green (requires push to GitHub)

## Phase 3: Website Redesign

- [ ] Template partials: navbar, hero, services, process, projects, blog, about, contact, footer
- [ ] `ContactSubmission` model
- [ ] `ContactFormView` — saves to DB, sends email via Mailgun
- [ ] Configure django-anymail[mailgun] email backend
- [ ] Privacy policy & terms of service pages
- [ ] Apply DaisyUI Agency Landing layout + brand colors
- [ ] Port JS: mobile menu, smooth scroll, scroll animations, BlogLoader RSS
- [ ] Google Analytics, meta tags, Open Graph, favicon
- [ ] Update README.md
- [ ] Verify: all pages load, contact form works, responsive, Playwright tested

## Phase 4: Integrations

- [ ] Paystack placeholder app: `src/apps/payments/` with models, views, services
- [ ] Payment page template (discovery call placeholder)
- [ ] Paystack webhook handler
- [ ] Mailgun transactional emails (contact notifications, payment receipts)
- [ ] Verify: Paystack test mode flow works

## Phase 5: Admin Dashboard

- [ ] Login view + template at `/dashboard/login/`
- [ ] `DashboardHomeView` — overview with key metrics
- [ ] `ContactSubmissionsListView` + `ContactSubmissionDetailView`
- [ ] `PaymentListView` — Paystack transactions
- [ ] `AnalyticsView` — analytics overview
- [ ] Dashboard templates (DaisyUI design): sidebar, stats cards, data tables
- [ ] Admin-only access middleware/mixin
- [ ] Verify: login works, all dashboard pages load, responsive

## Decisions

| Decision         | Choice                            | Rationale                           |
| ---------------- | --------------------------------- | ----------------------------------- |
| Server           | ASGI (Gunicorn + Uvicorn workers) | AGENTS.md mandates async Django     |
| Linter/Formatter | Ruff                              | Single tool, fast, modern           |
| Email            | django-anymail[mailgun]           | Battle-tested Mailgun integration   |
| Payments         | Paystack (placeholder)            | Scaffold now, define products later |
| User model       | Custom from Phase 1               | Avoids painful migration later      |
| Templates        | Partials pattern                  | Modular, testable sections          |
| CSS              | Tailwind 3 + DaisyUI              | Per AGENTS.md and DESIGN.md         |

## Progress

- **Current Phase**: 1 ✅ Complete — Foundation & Infrastructure
- **Phase 2**: CI/CD & Code Quality — workflows created, verify on push
- **Status**: Ready for Phase 3 — Website Redesign
