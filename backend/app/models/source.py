from sqlalchemy import Column, Integer, String, DateTime, Float, Enum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class SourceType(str, enum.Enum):
    """Type of job source."""
    RSS = "RSS"
    API = "API"
    BROWSER = "BROWSER"
    SANDBOX = "SANDBOX"


class SourceStatus(str, enum.Enum):
    """Health status of a source."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class Source(Base):
    """Represents a job source (RSS, API, browser, etc.)."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # RSS, API, BROWSER, SANDBOX
    base_url = Column(String(500), nullable=True)
    status = Column(String(50), default=SourceStatus.UNKNOWN.value)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    health_score = Column(Float, default=0.0)  # 0.0 to 1.0
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Source(id={self.id}, name={self.name}, status={self.status})>"