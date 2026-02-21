#!/usr/bin/env bash
set -euo pipefail

echo "=== Formatting ==="
ruff format src/ tests/

echo "=== Linting ==="
ruff check src/ tests/

echo "=== Running tests ==="
DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest tests/ -v

echo "=== All checks passed ==="