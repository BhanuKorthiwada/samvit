"""Structured logging configuration for the Samvit application."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # These will be set by middleware if available
        if not hasattr(record, "request_id"):
            record.request_id = "-"  # type: ignore[attr-defined]
        if not hasattr(record, "tenant_id"):
            record.tenant_id = "-"  # type: ignore[attr-defined]
        return True


def setup_logging() -> None:
    """Configure application logging based on settings."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Choose formatter based on environment
    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(request_id)s] [%(tenant_id)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    # Add context filter
    handler.addFilter(RequestContextFilter())

    # Configure root logger
    logging.root.handlers = [handler]
    logging.root.setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: The name for the logger, typically __name__

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
