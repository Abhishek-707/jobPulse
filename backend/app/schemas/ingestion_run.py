from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class IngestionRunResponse(BaseModel):
    """Schema for returning an ingestion run."""
    id: int
    source_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    jobs_found: int
    jobs_added: int
    jobs_updated: int
    jobs_duplicate: int
    jobs_failed: int
    error_count: int
    duration_ms: Optional[int]

    class Config:
        from_attributes = True