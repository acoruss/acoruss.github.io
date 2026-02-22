# Acoruss Website

> Empowering Businesses Through Technology

The official website for Acoruss - a technology consulting company that helps businesses harness software, AI, and strategic technology without the heavy costs of building from scratch.

## Architecture

Django web application, with tailwind css and Daisy UI components framework.

## Rules

### Python

1. Use Python 3.13+.
1. Modern Python with async.
1. Always follow PEP-8 rules.
1. Run `make format lint` after finishing your implementations. Fix any issues

### Django

1. Use modern Django version 5+ constructs
1. Always use class based views.
1. You can create temporary management commands but always ask to keep them or remove them.
1. Run `make template-test` to test that all templates are loading correctly.
1. Follow all Python rules. Use async django.

### Frontend

1. Use tailwind and Daisy UI components.
1. Follow the laid out designs guidelines in [./docs/DESIGN.md](./docs/DESIGN.md)
1. Always ensure that the final build for the css is in the src folder.
1. Always update the [DESIGN.md](./docs/DESIGN.md) file with new design decisions you make.

### Dashboard

This is only accessible to admin users on http://localhost:8083/dashboard with username/password or email(@acoruss.com emails.)
Use the design in [DESIGN.md](./docs/DESIGN.md) for dashboards to update the UI.
Use the Frontend rules in development.

### General

1. Always test the UI changes with playwright mcp server on http://localhost:8083
1. Run `make dev` to run the application.
1. Always use commands in the Makefile first. If you use extra commands and they are common in the session, propose to add them to the Makefile.
1. Any changes to the payment service should be updated in the [PRODUCT_PAYMENTS.md](./docs/PRODUCT_PAYMENTS.md) file. This ensures that all payment changes are well tracked.

## Project layout

.
├── AGENTS.md # agent file for AI agents
├── Makefile # utility make commands
├── README.md #about the project
├── docker # docker and docker compose files
│ ├── Dockerfile
│ ├── compose.dev.yml
│ └── compose.prod.yml
├── docs # website upgrade and design documents
│ ├── AcorussWebUpgrade.pdf
│ ├── DESIGN.md
│ └── InfoAndLinks.md
├── frontend # utility to create frontend assets
│ ├── package.json
│ ├── postcss.config.json
│ └── tailwind.config.js
├── old-web # NOTE: This is being removed
├── public # images logos
│ └── images
│ └── logos
│ ├── dark-name-horizontal.png
│ ├── dark-name-vertical.png
│ ├── dark-rounded-bg.png
│ ├── dark.png
│ ├── white-name-horizontal.png
│ ├── white-name-vertical.png
│ ├── white-rounded-bg.png
│ └── white.png
├── scripts # utility scripts
│ └── test.sh
├── src # web application code
│ ├── apps
│ │ ├── **init**.py
│ │ └── core
│ ├── config
│ │ └── **init**.py
│ ├── static
│ │ ├── css
│ │ │ └── main.css
│ │ └── js
│ │ └── main.js
│ └── templates
│ ├── base.html
│ └── index.html
└── tests # test files
└── **init**.py
