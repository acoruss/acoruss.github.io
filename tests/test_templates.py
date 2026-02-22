"""Dynamic template loading tests.

Discovers all .html templates in the templates directory and verifies
each one can be loaded by Django's template engine without syntax errors.
This replaces the old hardcoded template list in the Makefile.
"""

import pytest
from django.conf import settings
from django.template.loader import get_template


def _discover_templates() -> list[str]:
    """Walk the templates directory and return relative template paths."""
    templates_dir = settings.BASE_DIR / "templates"
    if not templates_dir.exists():
        return []
    return sorted(str(path.relative_to(templates_dir)) for path in templates_dir.rglob("*.html"))


# Collect at module import time so parametrize works
_TEMPLATES = _discover_templates()


@pytest.mark.parametrize("template_name", _TEMPLATES, ids=_TEMPLATES)
def test_template_loads(template_name: str) -> None:
    """Verify that each discovered template loads without syntax errors."""
    tpl = get_template(template_name)
    assert tpl is not None, f"Template '{template_name}' failed to load"


def test_templates_directory_not_empty() -> None:
    """Ensure the template discovery found at least one template."""
    assert len(_TEMPLATES) > 0, "No templates found — check TEMPLATES_DIR setting"


def test_required_templates_present() -> None:
    """Core templates that must always exist."""
    required = [
        "base.html",
        "index.html",
        "dashboard/base.html",
        "dashboard/home.html",
        "dashboard/login.html",
    ]
    for name in required:
        assert name in _TEMPLATES, f"Required template '{name}' not found"
