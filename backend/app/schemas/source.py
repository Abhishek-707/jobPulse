from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SourceResponse(BaseModel):
    """Schema for returning a source."""
    id: int
    name: str
    type: str
    base_url: Optional[str]
    status: str
    health_score: float
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    last_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True