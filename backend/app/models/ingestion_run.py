import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.sql import func

from app.database import Base


class IngestionRunStatus(str, enum.Enum):
    """Status of an ingestion execution."""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class IngestionRun(Base):
    """Tracks each ingestion execution."""

    __tablename__ = "ingestion_runs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    source_id = Column(
        Integer,
        ForeignKey("sources.id"),
        nullable=False,
        index=True,
    )

    started_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    finished_at = Column(
        DateTime,
        nullable=True,
    )

    status = Column(
        Enum(
            IngestionRunStatus,
            name="ingestion_run_status",
        ),
        nullable=False,
        default=IngestionRunStatus.RUNNING,
    )

    jobs_found = Column(
        Integer,
        default=0,
        nullable=False,
    )

    jobs_added = Column(
        Integer,
        default=0,
        nullable=False,
    )

    jobs_updated = Column(
        Integer,
        default=0,
        nullable=False,
    )

    jobs_duplicate = Column(
        Integer,
        default=0,
        nullable=False,
    )

    jobs_failed = Column(
        Integer,
        default=0,
        nullable=False,
    )

    error_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    duration_ms = Column(
        Integer,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"<IngestionRun("
            f"id={self.id}, "
            f"source_id={self.source_id}, "
            f"status={self.status}"
            f")>"
        )