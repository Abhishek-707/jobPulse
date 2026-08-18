from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class AIEnrichmentStatus(str):
    """Status of AI enrichment for a job."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AIEnrichment(Base):
    """Stores AI-enriched data for jobs."""
    __tablename__ = "ai_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True, index=True)
    status = Column(String(50), default=AIEnrichmentStatus.PENDING.value)
    category = Column(String(255), nullable=True)
    skills = Column(Text, nullable=True)  # JSON or comma-separated
    experience_level = Column(String(100), nullable=True)  # Junior, Mid, Senior
    summary = Column(Text, nullable=True)
    seniority = Column(String(100), nullable=True)
    technology_stack = Column(Text, nullable=True)  # JSON or comma-separated
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AIEnrichment(id={self.id}, job_id={self.job_id}, status={self.status})>"