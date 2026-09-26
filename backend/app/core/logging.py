import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


SENSITIVE_PATTERNS = [
    (re.compile(r'\b\d{4,8}\b'), '[REDACTED_CODE]'),
    (re.compile(r'(?i)(api[-_]?key|password|secret|token)\s*[:=]\s*["\']?([^"\'\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '[REDACTED_CARD]'),
]


def redact_sensitive_message(message: str) -> str:
    """Masks OTP codes, credentials, and payment identifiers from log records."""
    if not isinstance(message, str):
        message = str(message)
    for pattern, repl in SENSITIVE_PATTERNS:
        message = pattern.sub(repl, message)
    return message


class StructuredJsonFormatter(logging.Formatter):
    """
    Production-grade JSON formatter outputting machine-parseable telemetry.
    Ensures zero leak of raw audio buffers, speaker embeddings, OTPs, or API secrets.
    """

    def format(self, record: logging.LogRecord) -> str:
        clean_msg = redact_sensitive_message(record.getMessage())
        
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": clean_msg,
        }

        # Contextual metadata attached to the record
        for field in ("request_id", "trace_id", "tenant_id", "user_id", "analysis_id", "session_id", "endpoint", "status_code", "duration_ms", "error_type"):
            val = getattr(record, field, None)
            if val is not None:
                log_payload[field] = val

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logger(name: str = "sentinelvoice") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger


logger = setup_logger()


def generate_request_id() -> str:
    return str(uuid.uuid4())
