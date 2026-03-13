"""Gunicorn configuration for production."""

import logging


class HealthCheckFilter(logging.Filter):
    """Suppress access log entries for health check requests."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        # Filter out health check endpoint from access logs
        return not ("/healthz/" in message and "200" in message)


# Apply the filter to uvicorn's access logger
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "health_check": {
            "()": HealthCheckFilter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["health_check"],
        },
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "filters": ["health_check"],
        },
    },
    "formatters": {
        "default": {
            "format": "%(levelname)s:     %(message)s",
        },
        "access": {
            "format": "%(message)s",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
