# Acoruss Web Upgrade Plan

> Migrated from static Vite site to Django 5+ with async support, Tailwind CSS + DaisyUI, PostgreSQL, Docker, and CI/CD. The old static site (`old-web/`) has been removed.

## Phase 1: Django Foundation & Infrastructure

- [x] `pyproject.toml` with all dependencies (Django 5+, gunicorn, uvicorn, whitenoise, psycopg, django-environ, etc.)
- [x] `src/manage.py` entry point
- [x] `src/config/` settings package: `base.py`, `dev.py`, `test.py`, `prod.py`, `urls.py`, `asgi.py`, `wsgi.py`
- [x] Custom user model in `src/apps/accounts/` (early to avoid migration pain)
- [x] `src/apps/core/` scaffolding: `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`
- [x] `src/templates/base.html` - HTML5 skeleton with Tailwind/DaisyUI
- [x] `src/templates/index.html` - dummy content, extends base
- [x] `src/templates/dashboard/base.html` - dashboard layout stub
- [x] `frontend/` - Tailwind 3 + DaisyUI + PostCSS config, build pipeline → `src/static/css/main.css`
- [x] `docker/Dockerfile` - multi-stage (Node + Python 3.13) with dev and prod targets
- [x] `docker/compose.dev.yml` - web + db services (project name: acoruss)
- [x] `docker/compose.prod.yml` - gunicorn + uvicorn workers + db
- [x] `.env_sample` with all required variables
- [x] `Makefile` with all utility targets (Docker-first approach)
- [x] `.gitignore` and `.dockerignore` updated
- [x] Verify: `make dev` serves dummy site on `localhost:8083` ✅ All pages load

## Phase 2: CI/CD & Code Quality

- [x] Add ruff, mypy to dev dependencies; configure in `pyproject.toml`
- [x] Add pytest, pytest-django, pytest-asyncio; configure `[tool.pytest.ini_options]`
- [x] `.github/workflows/lint-format-test.yml`
- [x] `.github/workflows/build-push.yml` - build & push to GHCR
- [x] Update `scripts/test.sh`
- [x] Verify: CI runs green ✅

## Phase 3: Website Redesign

- [x] Template partials: navbar, hero, services, process, projects, blog, about, contact, footer
- [x] `ContactSubmission` model (name, email, company, phone, project_type, message, is_read)
- [x] `ContactSubmitView` - async POST handler, saves to DB, redirects with success message
- [x] Configure django-anymail[mailgun] email backend (send email on contact submit)
- [x] Privacy policy & terms of service pages (expanded content, info@acoruss.com)
- [x] Apply DaisyUI Agency Landing layout + brand colors (acoruss theme: primary #590303)
- [x] Port JS: mobile menu (DaisyUI drawer), smooth scroll
- [x] BlogLoader RSS (Substack feed via server-side proxy `/api/blog-feed/` + JS loader)
- [x] Google Analytics, meta tags, Open Graph, Twitter Card, favicon
- [x] Update README.md (rewritten for Django/Docker stack)
- [x] Verify: all 8 pages load, contact form works, Playwright tested

## Phase 4: Integrations

- [x] Paystack placeholder app: `src/apps/payments/` with models, views, services
- [x] Payment page template (`/payments/` - discovery call / service payments)
- [x] Paystack webhook handler (`/payments/webhook/`)
- [x] Mailgun transactional emails (contact notifications, payment receipts)
- [x] Verify: Paystack test mode flow works ✅

## Phase 5: Admin Dashboard

- [x] Login view + template at `/dashboard/login/`
- [x] `DashboardHomeView` - overview with key metrics (contacts + payments)
- [x] `ContactSubmissionsListView` + `ContactSubmissionDetailView`
- [x] `PaymentListView` - Paystack transactions list with filter/search/pagination
- [x] `AnalyticsView` - analytics overview (contacts, payments, revenue)
- [x] Dashboard templates (DaisyUI design): sidebar, stats cards, data tables
- [x] Admin-only access middleware/mixin
- [x] Verify: login works, all dashboard pages load, responsive

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

- **Phase 1**: ✅ Complete - Foundation & Infrastructure
- **Phase 2**: ✅ Complete - CI/CD & Code Quality
- **Phase 3**: ✅ Complete - Website Redesign
- **Phase 4**: ✅ Complete - Integrations (Paystack + Mailgun)
- **Phase 5**: ✅ Complete - Admin Dashboard
- **Current Status**: All phases complete. Full Django stack live with async support, Paystack payments, Mailgun emails, and admin dashboard.
