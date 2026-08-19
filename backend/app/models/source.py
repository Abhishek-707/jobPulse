import enum

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class SourceType(str, enum.Enum):
    """Supported job source types."""

    RSS = "RSS"
    API = "API"
    BROWSER = "BROWSER"
    SANDBOX = "SANDBOX"


class SourceStatus(str, enum.Enum):
    """Health status of a job source."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class Source(Base):
    """Represents a job source."""

    __tablename__ = "sources"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    type = Column(
        String(50),
        nullable=False,
    )

    base_url = Column(
        String(500),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default=SourceStatus.UNKNOWN.value,
    )

    last_success_at = Column(
        DateTime,
        nullable=True,
    )

    last_failure_at = Column(
        DateTime,
        nullable=True,
    )

    last_run_at = Column(
        DateTime,
        nullable=True,
    )

    health_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return (
            f"<Source("
            f"id={self.id}, "
            f"name={self.name}, "
            f"status={self.status}"
            f")>"
        )