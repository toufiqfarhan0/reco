"""Structured logging system for Reco with secret masking and standardized formatting."""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# Patterns for sensitive data redaction
SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|bearer|password)\s*[:=]\s*["\']?([^"\'\s,]+)["\']?'),
    re.compile(r'(?i)(tmx_[a-f0-9]{32}|gho_[a-zA-Z0-9]+|sk-[a-zA-Z0-9]{32,})'),
]


def redact_secrets(text: str) -> str:
    """Mask any detected API keys, secrets, or tokens in text."""
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1: [REDACTED]", redacted)
    return redacted


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured JSON or clean standardized text."""

    def __init__(self, json_format: bool = False):
        super().__init__()
        self.json_format = json_format

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        message = redact_secrets(record.getMessage())

        # Extract extra fields if provided
        run_id = getattr(record, "run_id", None)
        case_id = getattr(record, "case_id", None)

        if self.json_format:
            log_payload: Dict[str, Any] = {
                "timestamp": timestamp,
                "level": record.levelname,
                "module": record.name,
                "message": message,
            }
            if run_id:
                log_payload["run_id"] = run_id
            if case_id:
                log_payload["case_id"] = case_id
            if record.exc_info:
                log_payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_payload)

        # Clean text format
        extra_ctx = ""
        if run_id:
            extra_ctx += f" [run_id={run_id}]"
        if case_id:
            extra_ctx += f" [case_id={case_id}]"

        base_str = f"[{timestamp}] [{record.levelname:<7}] [{record.name}]{extra_ctx} {message}"
        if record.exc_info:
            base_str += f"\n{self.formatException(record.exc_info)}"
        return base_str


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Initialize root logger with structured handler."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter(json_format=json_format))
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    return logging.getLogger(f"reco.{name}")
