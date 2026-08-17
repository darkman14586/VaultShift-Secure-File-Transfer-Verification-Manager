"""Structured logging with audit support."""
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

from core.config import settings

# Audit logger — separate handler for audit events
audit_logger = logging.getLogger("vaultshift.audit")
audit_handler = logging.FileHandler(
    Path(settings.VAULTSHIFT_DATA_DIR) / "audit.log", mode="a"
)
audit_handler.setFormatter(logging.Formatter(
    "%(asctime)s | AUDIT | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False

# Main app logger
logger = logging.getLogger("vaultshift")
logger.setLevel(getattr(logging, settings.VAULTSHIFT_LOG_LEVEL.upper(), logging.INFO))

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
))
logger.addHandler(handler)


def audit_log(level: str, category: str, message: str, job_id=None, details=None):
    """Write an audit event."""
    parts = [f"[{category}]", f"{message}"]
    if job_id:
        parts.append(f"job={job_id}")
    if details:
        parts.append(str(details))
    audit_logger.info(" | ".join(parts))
