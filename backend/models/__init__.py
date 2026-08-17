"""VaultShift database models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Integer, BigInteger, DateTime, Text, ForeignKey, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import VaultBase


# ─── Enums ────────────────────────────────────────────────────────

class JobState(str, Enum):
    QUEUED = "QUEUED"
    SCANNING = "SCANNING"
    COPYING = "COPYING"
    VERIFYING = "VERIFYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TransferMode(str, Enum):
    COPY = "COPY"
    MOVE = "MOVE"
    VERIFY = "VERIFY"


class ConflictStrategy(str, Enum):
    SKIP = "SKIP"
    VERIFY = "VERIFY"
    OVERWRITE = "OVERWRITE"
    RENAME = "RENAME"


class FileStatus(str, Enum):
    PENDING = "PENDING"
    COPYING = "COPYING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CONFLICT = "CONFLICT"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    CORRUPTED = "CORRUPTED"
    MISSING = "MISSING"
    QUARANTINED = "QUARANTINED"


class AuditLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"


# ─── Models ──────────────────────────────────────────────────────

class Job(VaultBase):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(256), nullable=True)
    source_path: Mapped[str] = mapped_column(Text)
    dest_path: Mapped[str] = mapped_column(Text)
    mode: Mapped[TransferMode] = mapped_column(String(16), default=TransferMode.COPY)
    conflict_strategy: Mapped[ConflictStrategy] = mapped_column(String(16), default=ConflictStrategy.SKIP)
    state: Mapped[JobState] = mapped_column(String(32), default=JobState.QUEUED)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    completed_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    transferred_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    include_subdirs: Mapped[bool] = mapped_column(Boolean, default=True)
    preserve_metadata: Mapped[bool] = mapped_column(Boolean, default=True)
    hash_algorithm: Mapped[str] = mapped_column(String(16), default="sha256")
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    current_file_path: Mapped[str] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    speed_bytes_per_sec: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    files: Mapped[list["FileRecord"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class FileRecord(VaultBase):
    __tablename__ = "file_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"))
    rel_path: Mapped[str] = mapped_column(Text)
    source_path: Mapped[str] = mapped_column(Text)
    dest_path: Mapped[str] = mapped_column(Text, nullable=True)
    source_size: Mapped[int] = mapped_column(BigInteger, default=0)
    dest_size: Mapped[int] = mapped_column(BigInteger, default=0)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    dest_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[FileStatus] = mapped_column(String(32), default=FileStatus.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="files")


class AuditEvent(VaultBase):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    level: Mapped[AuditLevel] = mapped_column(String(16), default=AuditLevel.INFO)
    category: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    job_id: Mapped[str] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)


class Setting(VaultBase):
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[str] = mapped_column(Text)


class StorageLocation(VaultBase):
    __tablename__ = "storage_locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path: Mapped[str] = mapped_column(Text, unique=True)
    label: Mapped[str] = mapped_column(String(256), nullable=True)
    fstype: Mapped[str] = mapped_column(String(32), default="local")
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    free_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    mounted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_checked: Mapped[datetime] = mapped_column(DateTime, nullable=True)
