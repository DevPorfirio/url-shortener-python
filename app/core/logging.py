import logging
from typing import Any

import structlog

from app.core.config import settings


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.app_debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
        if settings.app_debug
        else [logging.StreamHandler()],
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)


def log_event(event: str, **kwargs: Any) -> None:
    logger = get_logger("event")
    logger.info(event, **kwargs)
