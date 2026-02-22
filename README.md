# Acoruss Website

> Empowering Businesses Through Technology

The official website for [Acoruss](https://acoruss.com) — a technology consulting company that helps businesses harness software, AI, and strategic technology without the heavy costs of building from scratch.

## Tech Stack

- **Backend:** Django 5.1+ (Python 3.13) with async ASGI (Gunicorn + Uvicorn)
- **Frontend:** Tailwind CSS 3 + DaisyUI components, Urbanist font
- **Database:** PostgreSQL 16
- **Email:** django-anymail with Mailgun (console backend in development)
- **Static Files:** WhiteNoise
- **Containerisation:** Docker & Docker Compose

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Node.js](https://nodejs.org/) 18+ (for Tailwind CSS build)
- Make

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/acoruss/acoruss.github.io.git
cd acoruss.github.io

# 2. Copy the environment file and configure
cp .env_sample .env

# 3. Start development (builds containers, installs frontend deps, builds CSS)
make dev
```

The application will be available at **http://localhost:8083**.

### Create a superuser

```bash
make createsuperuser
```

Access the admin dashboard at http://localhost:8083/dashboard.

## Available Make Commands

### Development

| Command      | Description                            |
| ------------ | -------------------------------------- |
| `make dev`   | Start development environment (Docker) |
| `make down`  | Stop development environment           |
| `make logs`  | View Docker container logs             |
| `make shell` | Open Django shell                      |

### Django Management

| Command                | Description             |
| ---------------------- | ----------------------- |
| `make migrate`         | Run database migrations |
| `make makemigrations`  | Create new migrations   |
| `make createsuperuser` | Create a superuser      |
| `make collectstatic`   | Collect static files    |

### Code Quality

| Command              | Description                  |
| -------------------- | ---------------------------- |
| `make format`        | Format code with ruff        |
| `make lint`          | Lint code with ruff          |
| `make test`          | Run tests with pytest        |
| `make template-test` | Test that all templates load |

### Frontend (Tailwind CSS)

| Command                 | Description                        |
| ----------------------- | ---------------------------------- |
| `make tailwind-build`   | Build Tailwind CSS for production  |
| `make tailwind-watch`   | Watch Tailwind CSS for dev changes |
| `make tailwind-install` | Install frontend dependencies      |

### Production

| Command                   | Description                        |
| ------------------------- | ---------------------------------- |
| `make docker-build`       | Build production Docker image      |
| `make docker-push`        | Push image to GHCR                 |
| `make prod-up`            | Start production containers        |
| `make prod-down`          | Stop production containers         |
| `make prod-restart`       | Restart production web container   |
| `make prod-logs`          | View production logs               |
| `make prod-pull`          | Pull latest image from GHCR        |
| `make prod-migrate`       | Run migrations in production       |
| `make prod-collectstatic` | Collect static files in production |

## Project Structure

```
.
├── AGENTS.md                   # AI agent instructions
├── Makefile                    # Build & dev commands
├── pyproject.toml              # Python dependencies & tool config
├── docker/
│   ├── Dockerfile              # Multi-stage Docker build
│   ├── compose.dev.yml         # Development compose
│   └── compose.prod.yml        # Production compose
├── docs/
│   ├── DESIGN.md               # Design system & guidelines
│   └── UPGRADE_WORK.md         # Migration progress tracker
├── frontend/
│   ├── package.json            # Tailwind/PostCSS deps
│   ├── tailwind.config.js      # Tailwind configuration
│   └── src/input.css           # Tailwind source CSS
├── src/
│   ├── manage.py
│   ├── apps/
│   │   ├── accounts/           # Custom user model
│   │   ├── core/               # Main app (views, models, services)
│   │   └── payments/           # Paystack integration
│   ├── config/
│   │   ├── urls.py             # Root URL configuration
│   │   └── settings/
│   │       ├── base.py         # Shared settings
│   │       ├── dev.py          # Development overrides
│   │       ├── prod.py         # Production overrides
│   │       └── test.py         # Test overrides
│   ├── static/
│   │   ├── css/main.css        # Compiled Tailwind CSS
│   │   ├── js/main.js          # Client-side JavaScript
│   │   └── images/             # Logos, favicons
│   └── templates/
│       ├── base.html           # Base layout
│       ├── index.html          # Homepage
│       ├── dashboard/          # Admin dashboard templates
│       └── emails/             # Email notification templates
├── tests/                      # pytest test suite
└── scripts/                    # Utility scripts
```

## Environment Variables

Copy `.env_sample` to `.env` and configure:

| Variable                      | Description                         | Required |
| ----------------------------- | ----------------------------------- | -------- |
| `SECRET_KEY`                  | Django secret key                   | Yes      |
| `DEBUG`                       | Debug mode (True/False)             | Yes      |
| `ALLOWED_HOSTS`               | Comma-separated allowed hosts       | Yes      |
| `DATABASE_URL`                | PostgreSQL connection URL           | Yes      |
| `MAILGUN_API_KEY`             | Mailgun API key for email           | Prod     |
| `MAILGUN_SENDER_DOMAIN`       | Mailgun sender domain               | Prod     |
| `PAYSTACK_SECRET_KEY`         | Paystack secret key                 | Prod     |
| `PAYSTACK_PUBLIC_KEY`         | Paystack public key                 | Prod     |
| `GOOGLE_ANALYTICS_ID`         | Google Analytics measurement ID     | Prod     |
| `CONTACT_NOTIFICATION_EMAILS` | Comma-separated notification emails | No       |
| `SITE_URL`                    | Base URL for the site               | No       |

## License

Copyright © 2024 Acoruss. All rights reserved.
