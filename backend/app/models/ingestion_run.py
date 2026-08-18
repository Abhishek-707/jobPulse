from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class IngestionRunStatus(str):
    """Status of an ingestion run."""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class IngestionRun(Base):
    """Tracks each ingestion execution."""
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default=IngestionRunStatus.SUCCESS)
    jobs_found = Column(Integer, default=0)
    jobs_added = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_duplicate = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<IngestionRun(id={self.id}, source_id={self.source_id}, status={self.status})>"