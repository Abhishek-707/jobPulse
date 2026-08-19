from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class ErrorType:
    """Known ingestion error categories."""

    TIMEOUT = "TIMEOUT"
    HTTP_ERROR = "HTTP_ERROR"
    PARSER_ERROR = "PARSER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    STRUCTURE_CHANGE = "STRUCTURE_CHANGE"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN = "UNKNOWN"


class IngestionError(Base):
    """Stores ingestion failures and anomalies."""

    __tablename__ = "ingestion_errors"

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

    run_id = Column(
        Integer,
        ForeignKey("ingestion_runs.id"),
        nullable=True,
        index=True,
    )

    error_type = Column(
        String(50),
        nullable=False,
    )

    message = Column(
        String(1000),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"<IngestionError("
            f"id={self.id}, "
            f"error_type={self.error_type}"
            f")>"
        )