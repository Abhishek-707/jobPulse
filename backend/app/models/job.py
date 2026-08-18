from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class Job(Base):
    """Represents a normalized job listing."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    external_id = Column(String(500), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    source_name = Column(String(100), nullable=False)
    job_type = Column(String(100), nullable=True)  # Full-time, Part-time, Contract, etc.
    published_at = Column(DateTime, nullable=True, index=True)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    content_hash = Column(String(64), nullable=True, unique=True, index=True)  # SHA256 hash for deduplication
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, company={self.company})>"