from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobCreate(BaseModel):
    """Schema for creating a job."""
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source_id: int
    source_name: str
    external_id: Optional[str] = None
    job_type: Optional[str] = None
    published_at: Optional[datetime] = None
    content_hash: Optional[str] = None


class JobResponse(BaseModel):
    """Schema for returning a job."""
    id: int
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    url: Optional[str]
    source_name: str
    job_type: Optional[str]
    published_at: Optional[datetime]
    collected_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True