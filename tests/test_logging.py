"""Tests for structured logging and secret redaction."""

import logging
from reco.logging import StructuredFormatter, redact_secrets


def test_redact_secrets():
    """Verify API keys and sensitive tokens are masked."""
    dummy_key = "tmx_0123456789abcdef0123456789abcdef"
    raw_log = f"Error connecting with api_key={dummy_key} and secret: 'my_secret_token'"
    redacted = redact_secrets(raw_log)
    assert dummy_key not in redacted
    assert "[REDACTED]" in redacted


def test_structured_formatter_json():
    """Verify JSON output format."""
    formatter = StructuredFormatter(json_format=True)
    record = logging.LogRecord(
        name="reco.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Benchmark started",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert '"module": "reco.test"' in formatted
    assert '"message": "Benchmark started"' in formatted
    assert '"level": "INFO"' in formatted
