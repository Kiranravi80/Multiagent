"""
PAIOS Structured Logging.

Provides a consistent, structured logging setup using structlog.
- Development: colored, human-readable console output.
- Production: JSON lines for log aggregation.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("job_collected", source="remoteok", count=42)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(*, log_level: str = "INFO", log_format: str = "console") -> None:
    """
    Configure structured logging for the entire application.

    Must be called once at application startup (from kernel.py).

    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "console" for dev, "json" for production.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=40,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Configure root stdlib handler
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore", "motor", "pymongo"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str = __name__, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Return a structured logger bound to the given module name.

    Args:
        name: Logger name (typically ``__name__``).
        **initial_context: Key-value pairs permanently bound to this logger.

    Returns:
        A structlog BoundLogger instance.

    Example:
        logger = get_logger(__name__, agent="career")
        logger.info("started", task_count=5)
        # Output: 2026-06-25T10:00:00Z [info] started  agent=career task_count=5
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger
